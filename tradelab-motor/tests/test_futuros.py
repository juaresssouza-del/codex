"""Motor de futuros da B3 (WIN/WDO): pregão diário, contratos, pontos, comprado e vendido."""
import numpy as np
import pandas as pd
import pytest

from motor import futuros, metricas, validacao
from motor.backtest import Risco
from motor.estrategias import ESTRATEGIAS
from motor.futuros import CONTRATOS, CustosFuturo, executar_futuros

from .util import sinais

BRT = 3 * 3_600_000
CINCO = 300_000
DIA0 = 1_767_225_600_000  # 2026-01-01 00:00 UTC (meia-noite UTC; 21h do dia 31 em Brasília)
SEM_CUSTO = CustosFuturo(custo_lado=0.0, slippage_ticks=0)


def pregoes(dias=3, por_dia=113, preco=100_000.0, passo=5.0, semente=None):
    """Pregões sintéticos de 5 min a partir das 9h00 de Brasília. Preço plano, salvo `semente`."""
    linhas = []
    rng = np.random.default_rng(semente) if semente is not None else None
    p = preco
    for d in range(dias):
        inicio = DIA0 + (d + 1) * 86_400_000 + 9 * 3_600_000 + BRT  # 9h00 BRT em UTC
        for k in range(por_dia):
            o = p
            c = o + (rng.choice([-1, 0, 1]) * passo * rng.integers(1, 20) if rng is not None else 0)
            h, l = max(o, c) + (passo if rng is not None else 0), min(o, c) - (passo if rng is not None else 0)
            ts = inicio + k * CINCO
            linhas.append((ts, o, h, l, c, 10.0, ts + CINCO - 1))
            p = c
    return pd.DataFrame(linhas, columns=["ts_abertura", "abertura", "maxima", "minima", "fechamento", "volume",
                                         "ts_fechamento"])


WIN = CONTRATOS["WIN"]
WIN_AMBOS = futuros.com_lado(WIN, "ambos")
RISCO = Risco(capital=10_000, risco_por_trade=0.01, exposicao_max=1.0, stop=0.005, alvo=0.01)
RISCO2 = Risco(capital=10_000, risco_por_trade=0.02, exposicao_max=1.0, stop=0.005, alvo=0.01)  # cabe 1 contrato com custos


# --- leitura do MT5 -----------------------------------------------------------------------

MT5 = ("<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\r\n"
       "2021.11.10\t09:00:00\t105740\t105760\t105260\t105395\t85553\t193637\t5\r\n"
       "2021.11.10\t09:05:00\t105390\t105450\t105260\t105385\t53851\t143391\t5\r\n"
       "2021.11.10\t09:20:00\t105385\t105400\t105300\t105310\t100\t200\t5\r\n"
       "2021.11.11\t09:00:00\t106000\t106100\t105900\t106050\t100\t200\t5\r\n")


def test_le_csv_do_mt5_em_horario_de_brasilia(tmp_path):
    f = tmp_path / "WIN.csv"
    f.write_text(MT5)
    df, rel = futuros.carregar_mt5(f)
    # 2021-11-10 09:00 BRT = 12:00 UTC
    assert df.ts_abertura.iloc[0] == int(pd.Timestamp("2021-11-10 12:00", tz="UTC").value // 1_000_000)
    assert df.ts_fechamento.iloc[0] == df.ts_abertura.iloc[0] + CINCO - 1
    assert rel.pregoes == 2 and rel.candles == 4
    # a noite entre pregões não é lacuna; a pausa de 10 min dentro do dia é
    assert len(rel.pausas) == 1 and rel.pausas[0][1] == 10


def test_csv_incoerente_e_rejeitado(tmp_path):
    f = tmp_path / "WIN.csv"
    f.write_text(MT5.replace("105740\t105760\t105260", "105740\t105700\t105260"))
    with pytest.raises(ValueError):
        futuros.carregar_mt5(f)


def test_reamostrar_respeita_o_pregao():
    df = pregoes(dias=2, semente=1)
    m15 = futuros.reamostrar(df, 15)
    assert len(m15) == 2 * 38  # 113 candles de 5 min = 37 completos + 1 parcial por dia
    dia = (m15.ts_abertura - BRT) // 86_400_000
    assert dia.nunique() == 2
    primeiro = df.iloc[:3]
    assert m15.maxima.iloc[0] == primeiro.maxima.max() and m15.abertura.iloc[0] == primeiro.abertura.iloc[0]
    assert m15.fechamento.iloc[0] == primeiro.fechamento.iloc[-1]
    assert (m15.ts_fechamento - m15.ts_abertura == 15 * 60_000 - 1).all()


# --- execução -----------------------------------------------------------------------------

def test_comprado_resultado_em_pontos_e_reais():
    df = pregoes(dias=1)
    df.loc[11:, ["abertura", "maxima", "minima", "fechamento"]] = 100_200.0
    r = executar_futuros(df, sinais(len(df), **{"5": 1, "20": -1}), RISCO, SEM_CUSTO, WIN)
    op = r.operacoes.iloc[0]
    assert op.lado == 1 and op.preco_entrada == 100_000 and op.preco_saida == 100_200
    assert op.motivo == "sinal"
    # stop 0,5% = 500 pontos = R$ 100 por contrato; risco 1% de 10.000 = R$ 100 -> 1 contrato
    assert op.quantidade == 1
    assert op.pnl == pytest.approx(200 * 0.20)


def test_custos_e_slippage_em_ticks():
    df = pregoes(dias=1)
    custos = CustosFuturo(custo_lado=1.35, slippage_ticks=1)
    r = executar_futuros(df, sinais(len(df), **{"5": 1, "20": -1}), RISCO2, custos, WIN)
    op = r.operacoes.iloc[0]
    assert op.preco_entrada == 100_005 and op.preco_saida == 99_995  # 1 tick contra em cada lado
    assert op.pnl == pytest.approx(-10 * 0.20 * op.quantidade - 2 * 1.35 * op.quantidade)
    assert op.custos == pytest.approx(2 * 1.35 * op.quantidade + 10 * 0.20 * op.quantidade)


def test_vendido_e_virada_de_mao():
    df = pregoes(dias=1)
    df.loc[11:, ["abertura", "maxima", "minima", "fechamento"]] = 99_800.0
    df.loc[31:, ["abertura", "maxima", "minima", "fechamento"]] = 99_900.0
    s = sinais(len(df), **{"5": -1, "30": 1})
    r = executar_futuros(df, s, RISCO, SEM_CUSTO, WIN_AMBOS)
    vend, comp = r.operacoes.iloc[0], r.operacoes.iloc[1]
    assert vend.lado == -1 and vend.pnl == pytest.approx(100 * 0.20)  # vendeu 100.000, recomprou 99.900
    assert vend.motivo == "sinal" and comp.lado == 1 and comp.ts_entrada == vend.ts_saida


def test_so_comprado_ignora_venda_a_descoberto():
    df = pregoes(dias=1)
    r = executar_futuros(df, sinais(len(df), **{"5": -1}), RISCO, SEM_CUSTO, WIN)
    assert len(r.operacoes) == 0


def test_zera_no_horario_e_nao_entra_perto_do_fim():
    df = pregoes(dias=1)
    minuto = ((df.ts_abertura - BRT) % 86_400_000) // 60_000
    i_zera = int(np.flatnonzero(minuto == WIN.zeragem)[0])
    i_tarde = int(np.flatnonzero(minuto == WIN.ultima_entrada)[0])
    r = executar_futuros(df, sinais(len(df), **{"5": 1}), Risco(capital=10_000, exposicao_max=1.0, stop=None, alvo=None),
                         SEM_CUSTO, WIN)
    op = r.operacoes.iloc[0]
    assert op.motivo == "zeragem" and op.ts_saida == df.ts_abertura[i_zera]
    tarde = executar_futuros(df, sinais(len(df), **{str(i_tarde): 1}), RISCO, SEM_CUSTO, WIN)
    assert len(tarde.operacoes) == 0


def test_nada_passa_de_um_dia_para_o_outro():
    df = pregoes(dias=2, por_dia=60)  # pregão curto: termina antes do horário de zeragem
    r = executar_futuros(df, sinais(len(df), **{"50": 1, "59": 1}), Risco(capital=10_000, exposicao_max=1.0, stop=None,
                         alvo=None), SEM_CUSTO, WIN)
    assert len(r.operacoes) == 1  # o sinal do último candle do dia não vira ordem no dia seguinte
    op = r.operacoes.iloc[0]
    assert op.motivo == "fim do dia" and op.ts_saida == df.ts_fechamento[59]


def test_stop_com_gap_sai_na_abertura_nos_dois_lados():
    df = pregoes(dias=1)
    df.loc[12, ["abertura", "maxima", "minima", "fechamento"]] = [99_000.0, 99_000.0, 98_900.0, 99_000.0]
    r = executar_futuros(df, sinais(len(df), **{"5": 1}), RISCO, SEM_CUSTO, WIN)
    assert r.operacoes.iloc[0].motivo == "stop" and r.operacoes.iloc[0].preco_saida == 99_000
    df2 = pregoes(dias=1)
    df2.loc[12, ["abertura", "maxima", "minima", "fechamento"]] = [101_000.0, 101_100.0, 101_000.0, 101_000.0]
    r2 = executar_futuros(df2, sinais(len(df2), **{"5": -1}), RISCO, SEM_CUSTO, WIN_AMBOS)
    assert r2.operacoes.iloc[0].motivo == "stop" and r2.operacoes.iloc[0].preco_saida == 101_000


def test_stop_antes_do_alvo_no_mesmo_candle():
    df = pregoes(dias=1)
    df.loc[8, ["maxima", "minima"]] = [102_000.0, 98_000.0]
    r = executar_futuros(df, sinais(len(df), **{"5": 1}), RISCO, SEM_CUSTO, WIN)
    assert r.operacoes.iloc[0].motivo == "stop" and r.operacoes.iloc[0].preco_saida == 99_500


def test_dimensionamento_por_risco_e_por_margem():
    df = pregoes(dias=1)
    # risco 1% de 100.000 = R$ 1.000; perda no stop 500 pts x R$ 0,20 = R$ 100 -> 10 contratos
    r = executar_futuros(df, sinais(len(df), **{"5": 1}), Risco(capital=100_000, risco_por_trade=0.01, exposicao_max=1.0,
                         stop=0.005, alvo=None), SEM_CUSTO, WIN)
    assert r.operacoes.iloc[0].quantidade == 10
    # margem: 10% de 10.000 = R$ 1.000 / R$ 155 -> no máximo 6 contratos
    r = executar_futuros(df, sinais(len(df), **{"5": 1}), Risco(capital=10_000, risco_por_trade=0.2, exposicao_max=0.1,
                         stop=0.005, alvo=None), SEM_CUSTO, WIN)
    assert r.operacoes.iloc[0].quantidade == 6
    # capital pequeno: nem 1 contrato cabe no risco -> recusada
    r = executar_futuros(df, sinais(len(df), **{"5": 1}), Risco(capital=500, risco_por_trade=0.01, exposicao_max=1.0,
                         stop=0.005, alvo=None), SEM_CUSTO, WIN)
    assert len(r.operacoes) == 0 and r.rejeitadas_filtro == 1


def test_limite_de_perda_diaria():
    df = pregoes(dias=2)
    for i in (8, 18):
        df.loc[i, "minima"] = 99_000.0
    s = sinais(len(df), **{"5": 1, "15": 1, "25": 1, "120": 1})
    # 1º stop: 2 contratos, perde R$ 200 (2%); 2º: 1 contrato, R$ 100; total 3% >= 2,5% bloqueia o 3º
    r = executar_futuros(df, s, Risco(capital=10_000, risco_por_trade=0.02, exposicao_max=1.0, stop=0.005, alvo=None,
                         perda_diaria_max=0.025), SEM_CUSTO, WIN)
    assert list(r.operacoes.motivo[:2]) == ["stop", "stop"] and r.bloqueadas_risco == 1
    assert r.operacoes.iloc[-1].ts_entrada == df.ts_abertura[121]


def test_conservacao_do_saldo():
    df = pregoes(dias=5, semente=3)
    e = ESTRATEGIAS["rompimento"]
    r = executar_futuros(df, e.sinais(df, entrada=10, saida=5), RISCO2, CustosFuturo(), WIN_AMBOS, aquecimento=11)
    assert len(r.operacoes) > 5
    assert r.capital_final == pytest.approx(RISCO2.capital + r.operacoes.pnl.sum())
    assert r.patrimonio[-1] == pytest.approx(r.capital_final)


def test_sem_antecipacao():
    df = pregoes(dias=6, semente=4)
    e = ESTRATEGIAS["abertura"]
    r = executar_futuros(df, e.sinais(df, candles=6), RISCO2, CustosFuturo(), WIN_AMBOS, aquecimento=7)
    corte = 3 * 113 + 50
    futuro = df.copy()
    for col in ("abertura", "maxima", "minima", "fechamento"):
        futuro.loc[corte:, col] += 3_000
    r2 = executar_futuros(futuro, e.sinais(futuro, candles=6), RISCO2, CustosFuturo(), WIN_AMBOS, aquecimento=7)
    antes = lambda x: x.operacoes[x.operacoes.ts_saida < df.ts_abertura[corte]].reset_index(drop=True)
    assert len(antes(r)) > 2 and antes(r).equals(antes(r2))


# --- estratégia de abertura e validação ---------------------------------------------------

def test_rompimento_da_faixa_de_abertura():
    df = pregoes(dias=1)
    df.loc[:5, "maxima"] = 100_050.0
    df.loc[:5, "minima"] = 99_950.0
    df.loc[10, ["maxima", "fechamento"]] = [100_100.0, 100_080.0]
    df.loc[20, ["minima", "fechamento"]] = [99_900.0, 99_920.0]
    s = ESTRATEGIAS["abertura"].sinais(df, candles=6)
    assert s[:6].tolist() == [0] * 6  # dentro da faixa não há sinal
    assert s[10] == 1 and s[20] == -1


def test_validacao_funciona_com_futuros():
    df = pregoes(dias=130, semente=5)
    e = ESTRATEGIAS["abertura"]
    wf = validacao.walk_forward(df, e, RISCO2, CustosFuturo(), WIN_AMBOS, treino_meses=2, teste_meses=1,
                                min_operacoes_treino=5)
    assert len(wf.janelas) >= 1 and (wf.operacoes.motivo != "fim").all()
    m = metricas.calcular(wf.resultado)
    assert m["operacoes"] == len(wf.operacoes)
    mc = validacao.aleatorio_monte_carlo(df, wf.resultado, n=5, mercado=WIN_AMBOS)
    assert len(mc.resultados) == 5
    bh = validacao.comprar_e_segurar(df, RISCO2, CustosFuturo(), WIN_AMBOS)
    dias = ((df.ts_abertura - BRT) // 86_400_000).nunique()
    assert len(bh.operacoes) == dias and set(bh.operacoes.lado) == {1}


def test_limite_fixo_de_contratos():
    """Capital pequeno, 1 contrato: o risco do stop passa do % por operação, mas o limite manda."""
    df = pregoes(dias=1)
    risco = Risco(capital=1_000, risco_por_trade=1.0, exposicao_max=1.0, stop=0.005, alvo=None, max_contratos=1)
    r = executar_futuros(df, sinais(len(df), **{"5": 1}), risco, SEM_CUSTO, WIN)
    assert r.operacoes.iloc[0].quantidade == 1


def test_rompimento_curto_cabe_no_pregao():
    e = ESTRATEGIAS["rompimento_curto"]
    assert all(e.aquecimento(p) <= 21 for p in e.combinacoes())  # 15 min: 37 candles por pregão
    df = pregoes(dias=2, semente=7)
    assert set(np.unique(e.sinais(df, **e.padrao))) <= {-1, 0, 1}
