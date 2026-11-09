import numpy as np
import pytest

from motor.backtest import Risco, executar
from motor.estrategias import ESTRATEGIAS
from motor.mercado import SEM_FILTROS, Custos, Mercado

from .util import PASSO_15M, plana, serie, sinais

SEM_CUSTOS = Custos(taxa=0, slippage=0)


def sma(df, **p):
    e = ESTRATEGIAS["sma"]
    params = {**e.padrao, **p}
    return e.sinais(df, **params), e.aquecimento(params)


def test_paridade_com_o_simulador_do_tradelab(amostra):
    """Mesmos dados e parâmetros do PWA: tem que dar o mesmo número, até a 6ª casa."""
    s, aq = sma(amostra)
    r = executar(amostra, s, aquecimento=aq, mercado=SEM_FILTROS)
    assert len(r.operacoes) == 15
    assert r.capital_final - 1000 == pytest.approx(-7.35225536, abs=1e-6)
    assert r.drawdown_fechamento * 100 == pytest.approx(0.80283351, abs=1e-6)
    assert (r.operacoes.pnl > 0).sum() == 1


def test_sem_antecipacao_mudar_o_futuro_nao_muda_o_passado():
    df = serie(800, semente=3)
    s, aq = sma(df)
    r = executar(df, s, aquecimento=aq)
    corte = 500
    futuro = df.copy()
    for col in ("abertura", "maxima", "minima", "fechamento"):
        futuro.loc[corte:, col] *= 2
    s2, _ = sma(futuro)
    r2 = executar(futuro, s2, aquecimento=aq)
    antes = lambda res: res.operacoes[res.operacoes.ts_saida < df.ts_abertura[corte]].reset_index(drop=True)
    assert len(antes(r)) > 3
    assert antes(r).equals(antes(r2))


def test_entrada_na_abertura_seguinte_com_custos():
    df = serie(60, semente=5)
    r = executar(df, sinais(60, **{"10": 1, "20": -1}), risco=Risco(stop=None, alvo=None), mercado=SEM_FILTROS)
    op = r.operacoes.iloc[0]
    assert op.ts_entrada == df.ts_abertura[11]
    assert op.preco_entrada == pytest.approx(df.abertura[11] * 1.0005)
    assert op.preco_saida == pytest.approx(df.abertura[21] * (1 - 0.0005))
    assert op.motivo == "sinal"
    # exposição máxima de 10% do caixa, já com a taxa
    assert op.quantidade * op.preco_entrada * 1.001 == pytest.approx(100)


def test_conservacao_do_caixa():
    df = serie(900, semente=8)
    s, aq = sma(df)
    r = executar(df, s, aquecimento=aq)
    assert r.capital_final == pytest.approx(1000 + r.operacoes.pnl.sum(), abs=1e-9)
    assert r.patrimonio[-1] == pytest.approx(r.capital_final)


def test_stop_tem_prioridade_sobre_alvo_no_mesmo_candle():
    df = plana(30)
    df.loc[11, ["maxima", "minima"]] = [110.0, 90.0]
    r = executar(df, sinais(30, **{"10": 1}), custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    op = r.operacoes.iloc[0]
    assert op.motivo == "stop" and op.preco_saida == pytest.approx(99.0)


def test_gap_abaixo_do_stop_sai_na_abertura():
    df = plana(30)
    df.loc[12, ["abertura", "maxima", "minima", "fechamento"]] = [80.0, 80.0, 79.0, 80.0]
    r = executar(df, sinais(30, **{"10": 1}), custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    op = r.operacoes.iloc[0]
    assert op.motivo == "stop" and op.preco_saida == pytest.approx(80.0)
    assert r.drawdown_minimo >= r.drawdown_fechamento


def test_alvo():
    df = plana(30)
    df.loc[13, "maxima"] = 103.0
    r = executar(df, sinais(30, **{"10": 1}), custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    op = r.operacoes.iloc[0]
    assert op.motivo == "alvo" and op.preco_saida == pytest.approx(102.0)


def test_risco_por_operacao_limita_quando_o_stop_e_largo():
    df = plana(30)
    r = executar(df, sinais(30, **{"10": 1}), risco=Risco(stop=0.05, alvo=None, exposicao_max=1.0),
                 custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    op = r.operacoes.iloc[0]
    # perda no stop = 0,25% de 1000 = 2,50 -> 2,5 / (100 * 0,05) = 0,5 unidade
    assert op.quantidade == pytest.approx(0.5)


def test_filtros_da_binance_arredondam_e_rejeitam():
    df = plana(30, preco=75_000.0)
    m = Mercado(passo_preco=0.01, passo_qtd=0.00001, qtd_minima=0.00001, notional_minimo=5.0)
    r = executar(df, sinais(30, **{"10": 1}), mercado=m, custos=SEM_CUSTOS)
    q = r.operacoes.iloc[0].quantidade
    assert q == pytest.approx(round(q, 5)) and q * 75_000 <= 100
    pequeno = executar(df, sinais(30, **{"10": 1}), risco=Risco(capital=40), mercado=m, custos=SEM_CUSTOS)
    assert len(pequeno.operacoes) == 0 and pequeno.rejeitadas_filtro == 1


def test_lacuna_bloqueia_sinais_ate_reaquecer_e_cancela_entrada_pendente():
    df = plana(60)
    depois = df.index >= 30
    df.loc[depois, "ts_abertura"] += 10 * PASSO_15M
    df.loc[depois, "ts_fechamento"] += 10 * PASSO_15M
    # sinal no último candle antes da lacuna: a ordem não atravessa a lacuna
    r = executar(df, sinais(60, **{"29": 1}), aquecimento=5, custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    assert len(r.operacoes) == 0
    # logo depois da lacuna o indicador ainda está "frio"
    r = executar(df, sinais(60, **{"31": 1}), aquecimento=5, custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    assert len(r.operacoes) == 0
    r = executar(df, sinais(60, **{"34": 1}), aquecimento=5, custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    assert len(r.operacoes) == 1


def test_sinais_antes_do_inicio_sao_ignorados():
    df = plana(40)
    r = executar(df, sinais(40, **{"5": 1, "25": 1}), inicio=20, custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    assert len(r.operacoes) == 1 and r.operacoes.iloc[0].ts_entrada == df.ts_abertura[26]


def test_limite_de_perda_diaria_bloqueia_novas_entradas_no_dia():
    df = plana(200)  # 15m: 96 candles por dia; começa 2026-01-01 00:00 UTC = 21:00 BRT do dia 31
    for i in (14, 24, 34):  # três stops seguidos no mesmo dia BRT
        df.loc[i, "minima"] = 90.0
    s = sinais(200, **{"12": 1, "22": 1, "32": 1, "42": 1, "160": 1})
    risco = Risco(perda_diaria_max=0.0015)  # 0,15% do patrimônio do início do dia
    r = executar(df, s, risco=risco, custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    # cada stop custa ~0,1% (10% de exposição x 1%): o 1º não bloqueia, o 2º sim
    assert list(r.operacoes.motivo[:2]) == ["stop", "stop"]
    assert r.bloqueadas_risco >= 2  # sinais 32 e 42 recusados
    assert r.operacoes.iloc[-1].ts_entrada == df.ts_abertura[161]  # dia seguinte volta a operar


def test_maximo_de_operacoes_por_dia():
    df = plana(80)
    s = np.zeros(80, dtype=np.int8)  # candles 12+ são o mesmo dia BRT
    s[[15, 25, 35, 45]] = 1
    s[[20, 30, 40, 50]] = -1
    r = executar(df, s, risco=Risco(max_operacoes_dia=2), custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    assert len(r.operacoes) == 2 and r.bloqueadas_risco == 2


def test_posicao_aberta_e_encerrada_no_fim():
    df = plana(20)
    r = executar(df, sinais(20, **{"5": 1}), risco=Risco(stop=None, alvo=None), custos=SEM_CUSTOS, mercado=SEM_FILTROS)
    assert r.operacoes.iloc[0].motivo == "fim" and r.operacoes.iloc[0].pnl == pytest.approx(0)


LIMITADA = Custos(taxa=0.00075, slippage=0.0005, entrada_limitada=True)


def test_ordem_limitada_executa_no_limite_quando_o_preco_volta():
    df = plana(30)
    df.loc[10, "fechamento"] = 100.0           # limite = fechamento do candle do sinal
    df.loc[11, ["abertura", "maxima", "minima", "fechamento"]] = [100.5, 101.0, 99.8, 100.5]
    r = executar(df, sinais(30, **{"10": 1}), risco=Risco(stop=None, alvo=None), custos=LIMITADA, mercado=SEM_FILTROS)
    op = r.operacoes.iloc[0]
    assert op.preco_entrada == pytest.approx(100.0)  # sem slippage na entrada
    assert op.quantidade * 100.0 * 1.00075 == pytest.approx(100)


def test_ordem_limitada_executa_na_abertura_se_ela_ja_esta_abaixo():
    df = plana(30)
    df.loc[11, ["abertura", "minima"]] = [99.5, 99.5]
    r = executar(df, sinais(30, **{"10": 1}), risco=Risco(stop=None, alvo=None), custos=LIMITADA, mercado=SEM_FILTROS)
    assert r.operacoes.iloc[0].preco_entrada == pytest.approx(99.5)


def test_ordem_limitada_nao_executada_quando_o_preco_dispara():
    df = plana(30)
    df.loc[11:, ["abertura", "maxima", "minima", "fechamento"]] = 105.0
    r = executar(df, sinais(30, **{"10": 1}), risco=Risco(stop=None, alvo=None), custos=LIMITADA, mercado=SEM_FILTROS)
    assert len(r.operacoes) == 0 and r.nao_executadas == 1
