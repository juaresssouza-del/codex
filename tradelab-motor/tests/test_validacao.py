import numpy as np
import pytest

from motor import metricas, validacao
from motor.backtest import Risco, executar
from motor.estrategias import ESTRATEGIAS
from motor.mercado import SEM_FILTROS

from .util import serie

MES_15M = 30 * 96


def test_metricas_basicas(amostra):
    e = ESTRATEGIAS["sma"]
    r = executar(amostra, e.sinais(amostra, **e.padrao), aquecimento=e.aquecimento(e.padrao), mercado=SEM_FILTROS)
    m = metricas.calcular(r)
    assert m["operacoes"] == 15
    assert m["taxa_acerto_pct"] == pytest.approx(100 / 15)
    assert m["fator_lucro"] == pytest.approx(0.0406, abs=1e-3)
    assert m["resultado_liquido"] == pytest.approx(-7.35225536, abs=1e-6)
    assert m["expectativa"] == pytest.approx(-7.35225536 / 15, abs=1e-6)
    assert m["custos_totais"] > 0


def test_walk_forward_so_conta_operacoes_fora_da_amostra():
    df = serie(8 * MES_15M, semente=21, vol=0.003)
    wf = validacao.walk_forward(df, ESTRATEGIAS["sma"], treino_meses=3, teste_meses=1, min_operacoes_treino=5)
    assert len(wf.janelas) >= 4
    for j in wf.janelas:
        assert j.teste_inicio_ts >= j.treino_fim_ts
        ops = wf.operacoes[wf.operacoes.janela == j.indice]
        assert (ops.ts_entrada >= j.teste_inicio_ts).all() and (ops.ts_entrada < j.teste_fim_ts).all()
        assert j.parametros in ESTRATEGIAS["sma"].combinacoes()
    # o capital passa de uma janela para a seguinte
    assert wf.janelas[1].capital_inicial == pytest.approx(wf.janelas[0].capital_final)
    assert wf.capital_final == pytest.approx(wf.janelas[-1].capital_final)


def test_monte_carlo_aleatorio_e_deterministico():
    df = serie(4 * MES_15M, semente=2)
    e = ESTRATEGIAS["sma"]
    r = executar(df, e.sinais(df, **e.padrao), aquecimento=e.aquecimento(e.padrao))
    a = validacao.aleatorio_monte_carlo(df, r, n=30, semente=9)
    b = validacao.aleatorio_monte_carlo(df, r, n=30, semente=9)
    assert np.array_equal(a.resultados, b.resultados) and 0 <= a.percentil <= 100
    assert len(a.resultados) == 30


def test_comprar_e_segurar_usa_a_mesma_exposicao():
    df = serie(500, semente=4)
    r = validacao.comprar_e_segurar(df, Risco(exposicao_max=0.1))
    assert len(r.operacoes) == 1 and r.operacoes.iloc[0].motivo == "fim"


def test_criterios_reprovam_e_explicam():
    crit = {"min_operacoes": 200, "fator_lucro_min": 1.3, "expectativa_min": 0.0,
            "drawdown_max_pct": 10.0, "percentil_aleatorio_min": 95.0}
    m = {"operacoes": 150, "fator_lucro": 1.5, "expectativa": 0.2, "drawdown_minimo_pct": 3.0}
    v = validacao.avaliar(m, 97.0, crit)
    assert v.aprovado is False
    assert [c.nome for c in v.itens if not c.passou] == ["min_operacoes"]
    ok = validacao.avaliar({**m, "operacoes": 250}, 97.0, crit)
    assert ok.aprovado is True


def test_reserva_corta_o_periodo_final():
    df = serie(4 * MES_15M)  # começa em 2026-01
    corte = validacao.cortar_reserva(df, "2026-03")
    assert corte.ts_abertura.max() < 1_772_323_200_000  # 2026-03-01 UTC
    assert len(corte) == (31 + 28) * 96
    assert len(validacao.cortar_reserva(df, None)) == len(df)


def test_resultado_antes_dos_custos(amostra):
    e = ESTRATEGIAS["sma"]
    r = executar(amostra, e.sinais(amostra, **e.padrao), aquecimento=e.aquecimento(e.padrao), mercado=SEM_FILTROS)
    m = metricas.calcular(r)
    assert m["resultado_bruto"] == pytest.approx(m["resultado_liquido"] + m["custos_totais"])


def test_walk_forward_continuo_carrega_a_posicao_entre_janelas():
    df = serie(10 * MES_15M, semente=33, deriva=0.0003, vol=0.003)
    e = ESTRATEGIAS["rompimento"]
    risco = Risco(stop=0.05, alvo=None, risco_por_trade=0.005)
    corte = validacao.walk_forward(df, e, risco, treino_meses=3, min_operacoes_treino=5)
    cont = validacao.walk_forward(df, e, risco, treino_meses=3, min_operacoes_treino=5, continuo=True)
    # mesmas escolhas de parâmetros: o treino não muda
    assert [j.parametros for j in cont.janelas] == [j.parametros for j in corte.janelas]
    # no modo contínuo só a última posição pode sair por "fim"
    assert (corte.operacoes.motivo == "fim").sum() > 1
    assert (cont.operacoes.motivo == "fim").sum() <= 1
    # alguma operação atravessa a virada de janela
    fim_janela = {j.indice: j.teste_fim_ts for j in cont.janelas}
    assert (cont.operacoes.ts_saida > cont.operacoes.janela.map(fim_janela)).any()
    # capital encadeado e coerente com o resultado
    assert cont.janelas[0].capital_inicial == pytest.approx(risco.capital)
    assert cont.capital_final == pytest.approx(risco.capital + cont.operacoes.pnl.sum())
    for a, b in zip(cont.janelas, cont.janelas[1:]):
        assert b.capital_inicial == pytest.approx(a.capital_final)


def test_agregar_soma_operacoes_e_exige_o_pior_ativo():
    crit = {"min_operacoes": 200, "fator_lucro_min": 1.3, "expectativa_min": 0.0,
            "drawdown_max_pct": 10.0, "percentil_aleatorio_min": 95.0}
    def rel(pnls, dd, pct):
        return {"operacoes": [{"pnl": p} for p in pnls], "metricas_fora_da_amostra": {"drawdown_minimo_pct": dd},
                "aleatorias": {"percentil": pct}}
    a = rel([3.0] * 60 + [-1.0] * 60, 4.0, 99.0)
    b = rel([2.0] * 50 + [-1.0] * 50, 6.0, 96.0)
    m, v = validacao.agregar([a, b], crit)
    assert m["operacoes"] == 220 and m["fator_lucro"] == pytest.approx(280 / 110)
    assert m["drawdown_minimo_pct"] == 6.0 and m["percentil"] == 96.0
    assert v.aprovado
    _, v = validacao.agregar([a, rel([2.0] * 50 + [-1.0] * 50, 6.0, 90.0)], crit)
    assert not v.aprovado and [i.nome for i in v.itens if not i.passou] == ["percentil_aleatorio_min"]
