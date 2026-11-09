import hashlib
import io
import zipfile

import numpy as np
import pytest

from motor import dados


def linha(ts, o, h, l, c, v=1.0, passo=900_000, micro=False):
    fator = 1000 if micro else 1
    return f"{ts * fator},{o},{h},{l},{c},{v},{(ts + passo) * fator - 1},0,0,0,0,0"


def zip_de(nome_csv, linhas):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(nome_csv, "\n".join(linhas) + "\n")
    return buf.getvalue()


def test_microssegundos_viram_milissegundos():
    ms = 1_788_220_800_000
    df = dados.ler_csv("\n".join([linha(ms, 1, 2, 0.5, 1.5, micro=True)]))
    assert df.ts_abertura.iloc[0] == ms
    assert df.ts_fechamento.iloc[0] == ms + 900_000 - 1


def test_milissegundos_preservados_e_cabecalho_ignorado():
    ms = 1_717_200_000_000
    texto = "open_time,open,high,low,close,volume,close_time,a,b,c,d,e\n" + linha(ms, 1, 2, 0.5, 1.5)
    df = dados.ler_csv(texto)
    assert len(df) == 1 and df.ts_abertura.iloc[0] == ms and df.fechamento.iloc[0] == 1.5


class Servidor:
    """Imita data.binance.vision: devolve zip + CHECKSUM e registra as chamadas."""

    def __init__(self, arquivos, checksum_errado=False):
        self.arquivos, self.chamadas, self.errado = arquivos, [], checksum_errado

    def __call__(self, url):
        self.chamadas.append(url)
        nome = url.rsplit("/", 1)[1]
        if nome.endswith(".CHECKSUM"):
            alvo = nome[: -len(".CHECKSUM")]
            if alvo not in self.arquivos:
                raise dados.ArquivoAusente(url)
            h = "0" * 64 if self.errado else hashlib.sha256(self.arquivos[alvo]).hexdigest()
            return f"{h}  {alvo}\n".encode()
        if nome not in self.arquivos:
            raise dados.ArquivoAusente(url)
        return self.arquivos[nome]


def arquivos_mensais():
    jan = 1_767_225_600_000  # 2026-01-01
    fev = 1_769_904_000_000  # 2026-02-01
    return {
        "BTCUSDT-15m-2026-01.zip": zip_de("BTCUSDT-15m-2026-01.csv", [linha(jan + i * 900_000, 10, 11, 9, 10) for i in range(3)]),
        "BTCUSDT-15m-2026-02.zip": zip_de("BTCUSDT-15m-2026-02.csv", [linha(fev + i * 900_000, 10, 11, 9, 10, micro=True) for i in range(3)]),
    }


def test_baixar_confere_checksum_e_nao_rebaixa(tmp_path):
    srv = Servidor(arquivos_mensais())
    salvos = dados.baixar("BTCUSDT", "15m", "2026-01", "2026-02", tmp_path, obter=srv)
    assert [p.name for p in salvos] == ["BTCUSDT-15m-2026-01.zip", "BTCUSDT-15m-2026-02.zip"]
    assert "/data/spot/monthly/klines/BTCUSDT/15m/BTCUSDT-15m-2026-01.zip" in srv.chamadas[1]
    n = len(srv.chamadas)
    dados.baixar("BTCUSDT", "15m", "2026-01", "2026-02", tmp_path, obter=srv)
    assert all(u.endswith(".CHECKSUM") for u in srv.chamadas[n:])  # só reconfere


def test_checksum_divergente_nao_grava(tmp_path):
    with pytest.raises(dados.ErroIntegridade):
        dados.baixar("BTCUSDT", "15m", "2026-01", "2026-01", tmp_path, obter=Servidor(arquivos_mensais(), checksum_errado=True))
    assert not list(tmp_path.rglob("*.zip"))


def test_carregar_junta_meses_e_relata_lacuna(tmp_path):
    dados.baixar("BTCUSDT", "15m", "2026-01", "2026-02", tmp_path, obter=Servidor(arquivos_mensais()))
    df, rel = dados.carregar(tmp_path, "BTCUSDT", "15m")
    assert len(df) == 6 and df.ts_abertura.is_monotonic_increasing
    assert len(rel.lacunas) == 1 and rel.lacunas[0].candles_faltando > 2000


def test_duplicata_identica_removida_e_conflitante_rejeitada():
    base = 1_767_225_600_000
    df = dados.ler_csv("\n".join([linha(base, 10, 11, 9, 10), linha(base, 10, 11, 9, 10), linha(base + 900_000, 10, 11, 9, 10)]))
    limpo, rel = dados.validar(df, 900_000)
    assert len(limpo) == 2 and rel.duplicatas_removidas == 1
    conflito = dados.ler_csv("\n".join([linha(base, 10, 11, 9, 10), linha(base, 10, 12, 9, 10)]))
    with pytest.raises(ValueError, match="duplicad"):
        dados.validar(conflito, 900_000)


@pytest.mark.parametrize("o,h,l,c", [(10, 9, 8, 10), (10, 11, 10.5, 10), (0, 1, 0, 1), (np.nan, 1, 1, 1)])
def test_ohlc_inconsistente_rejeitado(o, h, l, c):
    df = dados.ler_csv(linha(1_767_225_600_000, o, h, l, c))
    with pytest.raises(ValueError):
        dados.validar(df, 900_000)


def test_le_amostra_do_tradelab(amostra):
    assert len(amostra) == 499
    _, rel = dados.validar(amostra, 900_000)
    assert rel.lacunas == []
