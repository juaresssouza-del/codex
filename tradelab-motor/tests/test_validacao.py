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
