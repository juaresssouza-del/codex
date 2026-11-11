"""Preços e resultados artificiais: execução, causalidade e contrafactuais."""
import json

import numpy as np
import pandas as pd
import pytest

from motor import adaptativo as a, futuros
from motor.__main__ import main
from motor.backtest import _BRT_MS


def barras(dias=("2024-01-02", "2024-01-03", "2025-02-03"), minutos=5, contrato="WIN"):
    rng = np.random.default_rng(83)
    tick = futuros.CONTRATOS[contrato].tick
    ts = np.concatenate([pd.date_range(d + " 09:00", periods=540 // minutos, freq=f"{minutos}min",
                                      tz="America/Sao_Paulo").as_unit("ms").asi8 for d in dias])
    base = 120_000 if contrato == "WIN" else 6000
    close = base + np.cumsum(rng.integers(-3, 4, len(ts))) * tick
    op = np.r_[base, close[:-1]]
    return pd.DataFrame({"ts_abertura": ts, "ts_fechamento": ts + minutos * 60_000 - 1,
                         "abertura": op, "fechamento": close,
                         "maxima": np.maximum(op, close) + 2 * tick,
                         "minima": np.minimum(op, close) - 2 * tick, "volume": 100.0})


def sombra(pnls):
    return pd.DataFrame({"i_entrada": np.arange(len(pnls)) * 2 + 1,
                         "i_saida": np.arange(len(pnls)) * 2 + 2, "pnl": pnls})


@pytest.mark.parametrize("contrato", ["WIN", "WDO"])
@pytest.mark.parametrize("minutos", [5, 15, 30])
def test_indicadores_prefixo_independente_do_futuro(contrato, minutos):
    df = barras(dias=("2024-01-02", "2024-01-03", "2024-02-14"), minutos=minutos, contrato=contrato)
    # Inclui um vencimento WIN no futuro e verifica que não muda sinais no prefixo.
    for corte in (2 * 540 // minutos, len(df) - 12):
        futuro = df.copy()
        for col in ("abertura", "maxima", "minima", "fechamento"):
            futuro.loc[corte:, col] += 5000
        _, ctx1, s1 = a.preparar(df.iloc[:corte], contrato)
        _, ctx2, s2 = a.preparar(futuro, contrato)
        np.testing.assert_array_equal(ctx1, ctx2[:corte])
        for nome in s1:
            np.testing.assert_array_equal(s1[nome], s2[nome][:corte])


def test_lacuna_intradaria_reinicia_contexto_e_sinais():
    df = barras(dias=("2024-01-02",)).drop(index=60).reset_index(drop=True)
    _, ctx, sinais = a.preparar(df, "WIN")
    assert ctx[59] != "aquecimento"
    assert ctx[60] == "aquecimento"
    assert all(s[60] == 0 for s in sinais.values())


def test_nao_usa_operacao_fechada_no_mesmo_candle():
    n = 120
    sel = a.Seletor(["alta"] * n, {"x": np.ones(n)}, {"x": sombra([10] * 30)}, np.arange(n))
    assert sel.escolher(60, "alta")[0] is None  # só 29 fechamentos anteriores
    nome, _, total, media, ultimo = sel.escolher(61, "alta")
    assert (nome, total, media, ultimo) == ("x", 30, 10, 60)


def test_premiar_especialista_no_futuro_nao_muda_escolha_anterior():
    n = 200
    sinais = {"x": np.ones(n), "y": np.ones(n)}
    antes = {"x": sombra([3] * 30), "y": sombra([-3] * 30)}
    depois = {**antes, "y": sombra([-3] * 30 + [1e6] * 30)}
    s1 = a.Seletor(["alta"] * n, sinais, antes, np.arange(n))
    s2 = a.Seletor(["alta"] * n, sinais, depois, np.arange(n))
    assert s1.escolher(61, "alta") == s2.escolher(61, "alta")


def test_aprendizado_muda_sem_mudar_regra_e_memoria_e_limitada():
    n = 300
    sel = a.Seletor(["alta"] * n, {"x": np.ones(n), "y": np.ones(n)},
                    {"x": sombra([10] * 30 + [-100] * 60), "y": sombra([-10] * 30 + [10] * 60)}, np.arange(n))
    assert sel.escolher(61, "alta")[0] == "x"
    assert sel.escolher(181, "alta")[0] == "y"
    assert len(sel.memoria["x", "alta"]) == a.MEMORIA


def test_memoria_separada_por_contexto_e_ficar_de_fora():
    n = 120
    sel = a.Seletor(["alta"] * n, {"x": np.ones(n)}, {"x": sombra([10] * 30)}, np.arange(n))
    assert sel.escolher(61, "lateral")[0] is None
    assert sel.escolher(62, "choque")[0] is None
    assert sel.escolher(63, "alta")[0] == "x"


def test_amostra_perdedora_nao_e_elegivel():
    n = 120
    sel = a.Seletor(["alta"] * n, {"x": np.ones(n)}, {"x": sombra([-10] * 30)}, np.arange(n))
    assert sel.escolher(61, "alta")[:2] == (None, "sem_vantagem_na_memoria")


def test_posicao_mantem_dona_e_oposto_fecha_sem_virar():
    n = 120
    ctx = ["alta"] * n
    ctx[62] = "choque"
    sinais = np.ones(n, dtype=int)
    sinais[63] = -1
    # Horários de fechamento de barras M5 antes do limite de entrada.
    ts = pd.Timestamp("2024-01-02 12:00", tz="America/Sao_Paulo").value // 1_000_000 + np.arange(n) * 1000
    sel = a.Seletor(ctx, {"x": sinais}, {"x": sombra([10] * 30)}, ts)
    assert sel(61, 0) == 1
    assert sel(62, 1) == 0
    assert sel.dona == "x"
    assert sel(63, 1) == futuros.SAIR
    assert sel.decisoes[-1]["especialista"] == "x"


def test_empate_deterministico_e_rejeita_voltar_no_tempo():
    n = 120
    sel = a.Seletor(["alta"] * n, {"b": np.ones(n), "a": np.ones(n)},
                    {"a": sombra([10] * 30), "b": sombra([10] * 30)}, np.arange(n))
    assert sel.escolher(61, "alta")[0] == "a"
    with pytest.raises(ValueError, match="cronológica"):
        sel.escolher(60, "alta")


def test_virada_nao_transmite_nova_posicao():
    assert a._sem_virada(-1, 1) == futuros.SAIR
    assert a._sem_virada(1, -1) == futuros.SAIR
    assert a._sem_virada(futuros.SAIR_VENDIDO, 1) == 0
    assert a._sem_virada(futuros.SAIR_COMPRADO, -1) == 0
    assert a._sem_virada(-1, 0) == -1


def test_seletor_com_executor_real_entra_apos_sinal_e_sai_sem_virar():
    df = barras(dias=("2024-01-02",)).iloc[:80]
    sinais = np.ones(len(df), dtype=int)
    sinais[65], sinais[66:] = -1, 0
    sel = a.Seletor(["alta"] * len(df), {"x": sinais}, {"x": sombra([10] * 30)}, df.ts_fechamento.to_numpy())
    c = futuros.com_lado(futuros.CONTRATOS["WIN"], "ambos")
    r = futuros.executar_futuros(df, sel, a.RISCO_PESQUISA, mercado=c, inicio=61)
    assert len(r.operacoes) == 1
    assert r.operacoes.i_entrada.iloc[0] == 62
    assert r.operacoes.i_saida.iloc[0] == 66
    assert r.operacoes.lado.iloc[0] == 1
    assert r.operacoes.motivo.iloc[0] == "sinal"
    assert r.operacoes.quantidade.iloc[0] == 1
    assert r.operacoes.custos.iloc[0] > 0


def test_diagnostico_inverso_conta_custos_e_nao_usa_extremo_apos_saida():
    df = barras(dias=("2024-01-02",)).iloc[:3].copy()
    df.loc[2, "maxima"] = 1e9  # ocorre na barra em que já houve saída
    ops = pd.DataFrame([dict(i_entrada=1, i_saida=2, pnl=-4.7, custos=4.7, lado=1,
                             quantidade=1, preco_entrada=df.abertura.iloc[1], motivo="stop")])
    diag = a.diagnosticar(df, ops, ["alta"] * len(df), 0.2).iloc[0]
    assert diag.inverso_mesmos_instantes_custo_simetrico == pytest.approx(-4.7)
    assert diag.mfe_barras_anteriores_saida_reais < 100
    assert diag.contexto_entrada == "alta"


def test_oraculo_diario_inclui_ficar_de_fora_e_e_somente_descritivo():
    df = barras(dias=("2024-01-02", "2024-01-03"))
    def resultado(p1, p2):
        r = futuros.executar_futuros(df, np.zeros(len(df)), a.RISCO_PESQUISA)
        r.operacoes = pd.DataFrame({"ts_saida": [df.ts_fechamento.iloc[50], df.ts_fechamento.iloc[150]],
                                    "pnl": [p1, p2]})
        return r
    tabela = a.comparar_dias(df, {"x": resultado(10, -20), "y": resultado(-10, -1)}, resultado(-5, -5), 0)
    assert tabela.melhor_depois_do_fechamento.tolist() == ["x", "ficar_de_fora"]
    assert tabela.liquido_melhor_depois_do_fechamento.tolist() == [10, 0]


def test_pesquisa_separa_primeiro_ano_e_nao_fabrica_operacoes():
    estudo = a.pesquisar(barras(), "WIN")
    assert len(estudo.resultado.operacoes) == 0  # memória insuficiente neste cenário
    assert estudo.resultado.capital_final == a.RISCO_PESQUISA.capital
    assert len(estudo.controles) == 6
    assert pd.to_datetime(estudo.resultado.ts[0], unit="ms").year == 2025
    if len(estudo.decisoes):
        usados = estudo.decisoes.dropna(subset=["ultimo_i_saida_usado_na_escolha"])
        assert (usados.ultimo_i_saida_usado_na_escolha < usados.i).all()


@pytest.mark.parametrize("mutacao", ["reserva", "intervalo", "tick", "ohlc", "duplicata"])
def test_bloqueia_entradas_invalidas(mutacao):
    df = barras()
    if mutacao == "reserva":
        df.loc[len(df) - 1, "ts_abertura"] = pd.Timestamp("2026-07-01", tz="UTC").value // 1_000_000 + _BRT_MS
    elif mutacao == "intervalo":
        df["ts_fechamento"] = df.ts_abertura + 600_000 - 1
    elif mutacao == "tick":
        df.loc[0, "maxima"] += 0.25
    elif mutacao == "ohlc":
        df.loc[0, "maxima"] = 1
    else:
        df.loc[1, "ts_abertura"] = df.ts_abertura.iloc[0]
    with pytest.raises(ValueError):
        a.preparar(df, "WIN")


def test_historico_curto_nao_vira_validacao():
    with pytest.raises(ValueError, match="12 meses"):
        a.pesquisar(barras(dias=("2024-01-02",)), "WIN")


def test_cli_conferencia_execucao_exportacao_e_bloqueio_reserva(tmp_path):
    df = barras(contrato="WDO")
    datas = pd.to_datetime(df.ts_abertura, unit="ms", utc=True).dt.tz_convert("America/Sao_Paulo")
    mt5 = pd.DataFrame({"<DATE>": datas.dt.strftime("%Y.%m.%d"), "<TIME>": datas.dt.strftime("%H:%M:%S"),
                        "<OPEN>": df.abertura, "<HIGH>": df.maxima, "<LOW>": df.minima,
                        "<CLOSE>": df.fechamento, "<VOL>": df.volume})
    arquivo = tmp_path / "artificial.csv"
    mt5.to_csv(arquivo, sep="\t", index=False)
    args = ["adaptativo-b3", "--arquivo", str(arquivo), "--contrato", "WDO", "--origem", "ARTIFICIAL",
            "--minutos", "5", "--saida", str(tmp_path / "resultados")]
    main(args)
    saidas = list((tmp_path / "resultados").glob("*/relatorio.json"))
    assert len(saidas) == 1
    registro = json.loads(saidas[0].read_text())
    assert registro["aleatorias"]["n"] == 200
    assert registro["hipotese"] == 55
    assert registro["aprovado_para_conta_real"] is False
    assert registro["conferencia_dados"]["origem_declarada"] == "ARTIFICIAL"
    assert not registro["veredito_criterios_deste_relatorio"]["aprovado"]
    assert all((saidas[0].parent / (n + ".csv")).exists() for n in ["decisoes", "operacoes", "diagnostico", "por_dia"])
    with pytest.raises(SystemExit) as erro:
        main(args + ["--usar-reserva"])
    assert erro.value.code == 2


def test_cli_bloqueia_arquivo_com_lacuna_antes_de_sinais(tmp_path, monkeypatch):
    df = barras(dias=("2024-01-02",)).drop(index=40)
    datas = pd.to_datetime(df.ts_abertura, unit="ms", utc=True).dt.tz_convert("America/Sao_Paulo")
    mt5 = pd.DataFrame({"<DATE>": datas.dt.strftime("%Y.%m.%d"), "<TIME>": datas.dt.strftime("%H:%M:%S"),
                        "<OPEN>": df.abertura, "<HIGH>": df.maxima, "<LOW>": df.minima,
                        "<CLOSE>": df.fechamento, "<VOL>": df.volume})
    arquivo = tmp_path / "com-lacuna.csv"
    mt5.to_csv(arquivo, sep="\t", index=False)
    def proibido(*args, **kwargs):
        pytest.fail("Calculou sinais antes de bloquear os dados")
    monkeypatch.setattr(a, "pesquisar", proibido)
    with pytest.raises(SystemExit) as erro:
        main(["adaptativo-b3", "--arquivo", str(arquivo), "--contrato", "WIN", "--origem", "ARTIFICIAL", "--minutos", "5"])
    assert erro.value.code == 2
