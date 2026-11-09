"""Histórico de candles da Binance Spot a partir de data.binance.vision.

Os arquivos públicos mensais (e diários) vêm em .zip com um .CHECKSUM SHA-256 ao
lado. Desde 2025-01-01 os timestamps de Spot vêm em microssegundos; antes, em
milissegundos. Aqui tudo vira milissegundos.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

BASE = "https://data.binance.vision/data/spot"
COLUNAS = ["ts_abertura", "abertura", "maxima", "minima", "fechamento", "volume", "ts_fechamento"]
PRECOS = ["abertura", "maxima", "minima", "fechamento"]
PASSO_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000, "1h": 3_600_000, "4h": 14_400_000}
_MICRO = 10**14  # acima disso o timestamp está em microssegundos


class ArquivoAusente(Exception):
    pass


class ErroIntegridade(Exception):
    pass


def _obter_http(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "tradelab-motor/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ArquivoAusente(url) from e
        raise


def _meses(inicio: str, fim: str) -> list[str]:
    a, b = pd.Period(inicio, "M"), pd.Period(fim, "M")
    if b < a:
        raise ValueError(f"Período invertido: {inicio} > {fim}")
    return [str(p) for p in pd.period_range(a, b, freq="M")]


def _baixar_um(url: str, destino: Path, obter) -> Path:
    esperado = obter(url + ".CHECKSUM").decode().split()[0].lower()
    if destino.exists() and hashlib.sha256(destino.read_bytes()).hexdigest() == esperado:
        return destino
    conteudo = obter(url)
    if hashlib.sha256(conteudo).hexdigest() != esperado:
        raise ErroIntegridade(f"Checksum não confere para {url}; arquivo descartado.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".parcial")
    tmp.write_bytes(conteudo)
    tmp.replace(destino)
    return destino


def baixar(simbolo: str, intervalo: str, inicio: str, fim: str, pasta: Path,
           diarios_ate: date | None = None, obter=_obter_http) -> list[Path]:
    """Baixa os meses fechados de `inicio` a `fim` (AAAA-MM) e, opcionalmente, os dias
    do mês seguinte até `diarios_ate` (inclusive). Reconfere o checksum de quem já existe."""
    if intervalo not in PASSO_MS:
        raise ValueError(f"Intervalo não suportado: {intervalo}")
    pasta = Path(pasta) / simbolo / intervalo
    salvos = []
    for mes in _meses(inicio, fim):
        nome = f"{simbolo}-{intervalo}-{mes}.zip"
        salvos.append(_baixar_um(f"{BASE}/monthly/klines/{simbolo}/{intervalo}/{nome}", pasta / nome, obter))
    if diarios_ate is not None:
        dia = (pd.Period(fim, "M") + 1).start_time.date()
        while dia <= diarios_ate:
            nome = f"{simbolo}-{intervalo}-{dia.isoformat()}.zip"
            salvos.append(_baixar_um(f"{BASE}/daily/klines/{simbolo}/{intervalo}/{nome}", pasta / "diarios" / nome, obter))
            dia = date.fromordinal(dia.toordinal() + 1)
    return salvos


def ler_csv(conteudo: str | bytes) -> pd.DataFrame:
    if isinstance(conteudo, bytes):
        conteudo = conteudo.decode()
    linhas = [l for l in conteudo.splitlines() if l.strip()]
    if linhas and not linhas[0].split(",")[0].strip().lstrip("-").isdigit():
        linhas = linhas[1:]  # cabeçalho
    if not linhas:
        return pd.DataFrame({c: pd.Series(dtype="int64" if c.startswith("ts_") else "float64") for c in COLUNAS})
    bruto = pd.read_csv(io.StringIO("\n".join(linhas)), header=None, usecols=range(7), dtype=str)
    df = pd.DataFrame({
        "ts_abertura": bruto[0].astype("int64"),
        "abertura": pd.to_numeric(bruto[1], errors="coerce"),
        "maxima": pd.to_numeric(bruto[2], errors="coerce"),
        "minima": pd.to_numeric(bruto[3], errors="coerce"),
        "fechamento": pd.to_numeric(bruto[4], errors="coerce"),
        "volume": pd.to_numeric(bruto[5], errors="coerce"),
        "ts_fechamento": bruto[6].astype("int64"),
    })
    for c in ("ts_abertura", "ts_fechamento"):
        micro = df[c] > _MICRO
        df.loc[micro, c] = df.loc[micro, c] // 1000
    return df


def ler_zip(caminho: Path) -> pd.DataFrame:
    with zipfile.ZipFile(caminho) as z:
        return pd.concat([ler_csv(z.read(n)) for n in z.namelist() if n.endswith(".csv")], ignore_index=True)


def ler_tradelab_json(caminho: Path) -> pd.DataFrame:
    """Lê a amostra/exportação JSON do TradeLab (PWA)."""
    c = pd.DataFrame(json.loads(Path(caminho).read_text())["candles"])
    return pd.DataFrame({"ts_abertura": c.opened.astype("int64"), "abertura": c.open, "maxima": c.high,
                         "minima": c.low, "fechamento": c.close, "volume": c.get("volume", np.nan),
                         "ts_fechamento": c.closed.astype("int64")})


@dataclass(frozen=True)
class Lacuna:
    depois_de_ts: int
    retoma_em_ts: int
    candles_faltando: int


@dataclass
class RelatorioDados:
    candles: int = 0
    duplicatas_removidas: int = 0
    parciais_removidos: int = 0
    lacunas: list[Lacuna] = field(default_factory=list)

    @property
    def candles_faltando(self) -> int:
        return sum(l.candles_faltando for l in self.lacunas)


def validar(df: pd.DataFrame, passo_ms: int) -> tuple[pd.DataFrame, RelatorioDados]:
    """Ordena, remove duplicatas idênticas e rejeita dado incoerente. Lacunas não são
    preenchidas (inventar candle é pior que não ter): são relatadas e o backtest as respeita."""
    df = df.sort_values("ts_abertura", kind="stable").reset_index(drop=True)
    antes = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    if df.ts_abertura.duplicated().any():
        ts = int(df.ts_abertura[df.ts_abertura.duplicated()].iloc[0])
        raise ValueError(f"Candle duplicado com valores diferentes em {pd.to_datetime(ts, unit='ms')} UTC.")
    # Candle que fechou antes da hora (parada da corretora) não é um candle completo: sai e vira lacuna.
    parcial = (df.ts_fechamento - df.ts_abertura).to_numpy() != passo_ms - 1
    df = df[~parcial].reset_index(drop=True)
    p = df[PRECOS].to_numpy()
    ruim = ~np.isfinite(p).all(axis=1) | (p <= 0).any(axis=1)
    ruim |= df.maxima.to_numpy() < np.maximum(df.abertura, df.fechamento).to_numpy()
    ruim |= df.minima.to_numpy() > np.minimum(df.abertura, df.fechamento).to_numpy()
    ruim |= df.volume.to_numpy() < 0
    ruim |= (df.ts_abertura % passo_ms).to_numpy() != 0
    if ruim.any():
        i = int(np.flatnonzero(ruim)[0])
        raise ValueError(f"Candle incoerente em {pd.to_datetime(int(df.ts_abertura[i]), unit='ms')} UTC: {df.iloc[i].to_dict()}")
    salto = np.diff(df.ts_abertura.to_numpy())
    lacunas = [Lacuna(int(df.ts_abertura[i]), int(df.ts_abertura[i + 1]), int(salto[i] // passo_ms - 1))
               for i in np.flatnonzero(salto != passo_ms)]
    return df, RelatorioDados(len(df), antes - len(df) - int(parcial.sum()), int(parcial.sum()), lacunas)


def movimento(df: pd.DataFrame) -> dict:
    """Quanto o preço anda num candle típico. Compare com o custo de uma operação completa."""
    a = df.abertura.to_numpy(float)
    return {"amplitude_mediana_pct": float(np.median((df.maxima - df.minima).to_numpy() / a * 100)),
            "corpo_mediano_pct": float(np.median(np.abs(df.fechamento.to_numpy() - a) / a * 100))}


def carregar(pasta: Path, simbolo: str, intervalo: str) -> tuple[pd.DataFrame, RelatorioDados]:
    base = Path(pasta) / simbolo / intervalo
    arquivos = sorted(base.glob(f"{simbolo}-{intervalo}-*.zip")) + sorted(base.glob(f"diarios/{simbolo}-{intervalo}-*.zip"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo em {base}. Rode primeiro: python -m motor baixar ...")
    return validar(pd.concat([ler_zip(a) for a in arquivos], ignore_index=True), PASSO_MS[intervalo])
