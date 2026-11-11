"""Regressões da auditoria. Só preços inventados; não validam hipótese de lucro."""
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from motor import futuros, metricas, validacao
from motor.backtest import Risco, executar
from motor.estrategias import ESTRATEGIAS
from motor.futuros import CustosFuturo, executar_futuros
from motor.mercado import Custos, Mercado, SEM_FILTROS

from .test_futuros import pregoes, WIN, WIN_AMBOS, SEM_CUSTO
from .util import plana, sinais


def meses_planos():
    ts = np.concatenate([
        int(p.start_time.value // 1_000_000) + np.arange(40) * 900_000
        for p in pd.period_range("2024-01", "2024-05", freq="M")
    ])
    df = plana(len(ts))
    df["ts_abertura"], df["ts_fechamento"] = ts, ts + 900_000 - 1
    return df


def test_validacao_sem_combinacao_preserva_periodo_e_reprova():
    df = meses_planos()
    wf = validacao.walk_forward(df, ESTRATEGIAS["sma"], treino_meses=2, min_operacoes_treino=30)
    esperado = df[df.ts_abertura >= wf.inicio_teste_ts].ts_fechamento.to_numpy()
    np.testing.assert_array_equal(wf.resultado.ts, esperado)
    m = metricas.calcular(wf.resultado)
    assert m["operacoes"] == 0 and m["resultado_liquido"] == 0
    assert not validacao.avaliar(m, 50, {"min_operacoes": 200}).aprovado


@pytest.mark.parametrize("motor", ["spot", "futuro"])
def test_queda_no_candle_da_saida_por_alvo_nao_desaparece(motor):
    if motor == "spot":
        df = plana(4)
        df.loc[2, ["maxima", "minima"]] = [103, 99.5]
        r = executar(df, sinais(4, **{"0": 1}), Risco(capital=1_000, exposicao_max=1,
                     risco_por_trade=1, stop=None, alvo=.02), Custos(0, 0), SEM_FILTROS)
        minimo, queda = 995, .005
    else:
        df = pregoes(dias=1, por_dia=4)
        df.loc[2, ["maxima", "minima"]] = [101_100, 99_500]
        r = executar_futuros(df, sinais(4, **{"0": 1}), Risco(capital=10_000, exposicao_max=1,
                             risco_por_trade=1, stop=None, alvo=.01, max_contratos=1), SEM_CUSTO, WIN)
        minimo, queda = 9_900, .01
    assert r.operacoes.iloc[0].motivo == "alvo"
    assert r.patrimonio_minimo[2] == pytest.approx(minimo)
    assert r.drawdown_minimo == pytest.approx(queda)


def test_queda_no_ultimo_candle_do_pregao_e_contabilizada():
    df = pregoes(dias=1, por_dia=3)
    df.loc[2, "minima"] = 99_000
    r = executar_futuros(df, sinais(3, **{"0": 1}), Risco(capital=10_000, exposicao_max=1,
                         risco_por_trade=1, stop=None, alvo=None, max_contratos=1), SEM_CUSTO, WIN)
    assert r.operacoes.iloc[0].motivo == "fim do dia"
    assert r.patrimonio_minimo[-1] == pytest.approx(9_800)
    assert r.drawdown_minimo == pytest.approx(.02)


def test_movimento_depois_de_saida_na_abertura_nao_entra_na_queda():
    df = pregoes(dias=1, por_dia=4)
    df.loc[2, ["maxima", "minima"]] = [102_000, 98_000]
    r = executar_futuros(df, sinais(4, **{"0": 1, "1": -1}), Risco(capital=10_000,
                         exposicao_max=1, stop=None, alvo=None, max_contratos=1), SEM_CUSTO, WIN)
    assert r.drawdown_minimo == 0


def test_reamostragem_nao_inventa_candle_com_pausa_no_meio():
    df = pregoes(dias=1, por_dia=9).drop(index=1).reset_index(drop=True)
    r = futuros.reamostrar(df, 15)
    assert r.ts_abertura.tolist() == [df.ts_abertura[2], df.ts_abertura[5]]
    assert len(r) == 2


def test_reamostragem_descarta_bloco_final_incompleto():
    df = pregoes(dias=1, por_dia=8)
    r = futuros.reamostrar(df, 15)
    assert len(r) == 2
    assert r.ts_fechamento.max() <= df.ts_fechamento.max()


def test_limitada_intracandle_nao_recebe_alvo_que_pode_ser_anterior_a_entrada():
    df = plana(4)
    df.loc[1, ["abertura", "maxima", "minima", "fechamento"]] = [101, 103, 99.5, 100]
    r = executar(df, sinais(4, **{"0": 1}), Risco(stop=.05, alvo=.02),
                 Custos(0, 0, entrada_limitada=True), SEM_FILTROS)
    assert r.operacoes.iloc[0].motivo == "fim"
    assert r.operacoes.iloc[0].pnl == 0


def test_limitada_pode_receber_alvo_se_fechamento_comprova_cruzamento_posterior():
    df = plana(4)
    df.loc[1, ["abertura", "maxima", "minima", "fechamento"]] = [101, 103, 99.5, 102.5]
    r = executar(df, sinais(4, **{"0": 1}), Risco(stop=.05, alvo=.02),
                 Custos(0, 0, entrada_limitada=True), SEM_FILTROS)
    assert r.operacoes.iloc[0].motivo == "alvo"


def test_passo_de_lote_que_nao_e_potencia_de_dez():
    m = Mercado(passo_preco=.25, passo_qtd=.25)
    assert m.arredonda_qtd(.76) == .75
    assert m.arredonda_preco(100.74) == 100.75


@pytest.mark.parametrize("kwargs", [{"capital": float("inf")}, {"max_contratos": -1},
                                    {"max_operacoes_dia": 1.5}, {"perda_diaria_max": -.1}])
def test_configuracao_de_risco_invalida_e_rejeitada(kwargs):
    with pytest.raises(ValueError):
        Risco(**kwargs)


@pytest.mark.parametrize("classe,kwargs", [(Custos, {"taxa": -.1}),
                                         (Custos, {"slippage": float("nan")}),
                                         (CustosFuturo, {"custo_lado": -1}),
                                         (CustosFuturo, {"slippage_ticks": -1})])
def test_custos_invalidos_nao_viram_lucro_artificial(classe, kwargs):
    with pytest.raises(ValueError):
        classe(**kwargs)


def test_futuros_sinal_sair_nao_abre_venda():
    df = pregoes(dias=1, por_dia=8)
    r = executar_futuros(df, sinais(8, **{"0": 1, "2": futuros.SAIR}),
                         Risco(capital=10_000, stop=None, alvo=None, max_contratos=1), SEM_CUSTO, WIN_AMBOS)
    assert len(r.operacoes) == 1
    assert r.operacoes.iloc[0].ts_saida == df.ts_abertura[3]
    assert r.operacoes.iloc[0].lado == 1


def test_zeragem_respeitada_mesmo_com_horario_de_entrada_incompativel():
    df = pregoes(dias=1, por_dia=113)
    mercado = replace(WIN, ultima_entrada=18 * 60 + 25)
    i = int(np.flatnonzero(((df.ts_abertura - 3 * 3_600_000) % 86_400_000) // 60_000 == 18 * 60)[0])
    r = executar_futuros(df, sinais(len(df), **{str(i): 1}),
                         Risco(capital=10_000, stop=None, alvo=None, max_contratos=1), SEM_CUSTO, mercado)
    assert r.operacoes.empty


def test_monte_carlo_b3_distingue_saida_de_entrada_vendida(monkeypatch):
    df = pregoes(dias=3, por_dia=20)
    risco = Risco(capital=10_000, stop=None, alvo=None, max_contratos=1)
    ref = executar_futuros(df, sinais(len(df), **{"0": 1, "2": futuros.SAIR}), risco, SEM_CUSTO, WIN_AMBOS)
    chamadas = []
    def observar(dados, sinal, *args, **kwargs):
        assert callable(sinal), "A referência precisa consultar a posição efetiva; -1 não significa sair nos dois lados."
        saidas = {sinal(i, 1) for i in range(len(dados))}
        assert saidas <= {0, futuros.SAIR} and futuros.SAIR in saidas
        entradas = {sinal(i, 0) for i in range(len(dados))}
        assert entradas <= {-1, 0, 1}
        chamadas.append(1)
        return executar_futuros(dados, sinal, *args, **kwargs)
    monkeypatch.setattr(validacao, "executar_futuros", observar)
    mc = validacao.aleatorio_monte_carlo(df, ref, n=2, mercado=WIN_AMBOS)
    assert len(chamadas) == len(mc.resultados) == 2


def test_criterio_nao_aceita_metrica_infinita():
    assert not validacao.avaliar({"expectativa": float("inf")}, 99, {"expectativa_min": 0}).aprovado


def test_agregacao_nao_soma_reais_com_usdt():
    def rel(moeda):
        return {"moeda": moeda, "operacoes": [{"pnl": 1}],
                "metricas_fora_da_amostra": {"drawdown_minimo_pct": 1}, "aleatorias": {"percentil": 99}}
    with pytest.raises(ValueError, match="moeda"):
        validacao.agregar([rel("R$"), rel("USDT")], {"min_operacoes": 1})


def test_escolha_futura_nao_altera_aquecimento_do_passado_no_continuo():
    df = pregoes(dias=3, por_dia=40)
    e = ESTRATEGIAS["rompimento_curto"]
    risco = Risco(capital=10_000, stop=None, alvo=None, max_contratos=1)
    ts = df.ts_abertura.to_numpy()
    pequeno, grande = {"entrada": 6, "saida": 3}, {"entrada": 20, "saida": 12}
    def rodar(futuro):
        escolhas = [(ts[0], ts[40], ts[80], 40, 80, pequeno, {}),
                    (ts[0], ts[80], ts[-1] + 300_000, 80, 120, futuro, {})]
        s = lambda p: sinais(len(df), **{"47": 1, "50": -1})
        return validacao._walk_forward_continuo(df, e, escolhas, s, risco, SEM_CUSTO, WIN).resultado
    a, b = rodar(pequeno), rodar(grande)
    antes = lambda r: r.operacoes[r.operacoes.ts_saida < ts[80]].reset_index(drop=True)
    assert len(antes(a)) == 1
    pd.testing.assert_frame_equal(antes(a), antes(b))


@pytest.mark.parametrize("volume", [float("nan"), float("inf"), -1])
def test_volume_invalido_do_mt5_e_rejeitado(tmp_path, volume):
    from .test_futuros import MT5
    f = tmp_path / "sintetico.csv"
    f.write_text(MT5.replace("193637", str(volume)))
    with pytest.raises(ValueError, match="incoerente"):
        futuros.carregar_mt5(f)


@pytest.mark.parametrize("motor", ["spot", "futuro"])
@pytest.mark.parametrize("nivel", ["stop", "alvo"])
def test_protecao_arredondada_para_o_preco_de_entrada_e_recusada(motor, nivel):
    risco = Risco(capital=10_000, exposicao_max=1, risco_por_trade=1,
                  stop=.0000001 if nivel == "stop" else None,
                  alvo=.0000001 if nivel == "alvo" else None, max_contratos=1)
    if motor == "spot":
        df = plana(4)
        r = executar(df, sinais(4, **{"0": 1}), risco, Custos(0, 0), Mercado())
    else:
        df = pregoes(dias=1, por_dia=4)
        r = executar_futuros(df, sinais(4, **{"0": 1}), risco, SEM_CUSTO, WIN)
    assert r.operacoes.empty and r.rejeitadas_filtro == 1


def test_api_de_validacao_b3_escolhe_custos_do_contrato_quando_omitidos():
    df = pregoes(dias=95, por_dia=25)
    r = validacao.comprar_e_segurar(df, Risco(capital=10_000, max_contratos=1), mercado=WIN)
    assert isinstance(r.custos, CustosFuturo) and r.custos == futuros.CUSTOS["WIN"]
    wf = validacao.walk_forward(df, ESTRATEGIAS["abertura"], mercado=WIN,
                                treino_meses=1, min_operacoes_treino=30)
    assert isinstance(wf.resultado.custos, CustosFuturo)


@pytest.mark.parametrize("motor", ["spot", "futuro"])
def test_referencia_aleatoria_nao_opera_em_barras_inelegiveis(motor):
    if motor == "spot":
        df = plana(30)
        ref = executar(df, np.zeros(len(df)), aquecimento=100, custos=Custos(0, 0))
        mercado = Mercado()
    else:
        df = pregoes(dias=1, por_dia=30)
        ref = executar_futuros(df, np.zeros(len(df)), aquecimento=100, custos=SEM_CUSTO, mercado=WIN_AMBOS)
        mercado = WIN_AMBOS
    assert not ref.sinais_validos.any()
    mc = validacao.aleatorio_monte_carlo(df, ref, n=2, mercado=mercado)
    np.testing.assert_array_equal(mc.resultados, [0, 0])
    assert mc.percentil == 50
