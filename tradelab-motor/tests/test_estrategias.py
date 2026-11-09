import numpy as np
import pytest

from motor.estrategias import ESTRATEGIAS, aleatoria, rsi, sma

from .util import serie


def test_sma_igual_a_media_simples():
    x = np.arange(1, 31, dtype=float)
    m = sma(x, 9)
    assert np.isnan(m[7]) and m[8] == pytest.approx(5.0) and m[29] == pytest.approx(np.mean(x[21:30]))


def test_cruzamento_de_medias_marca_compra_e_venda():
    precos = np.concatenate([np.full(30, 100.0), np.linspace(100, 120, 15), np.linspace(120, 90, 30)])
    df = serie(len(precos))
    df["fechamento"] = precos
    s = ESTRATEGIAS["sma"].sinais(df, rapida=3, lenta=8)
    compras, vendas = np.flatnonzero(s == 1), np.flatnonzero(s == -1)
    assert len(compras) == 1 and len(vendas) == 1 and 30 <= compras[0] < vendas[0]


@pytest.mark.parametrize("nome", sorted(ESTRATEGIAS))
def test_nenhuma_estrategia_olha_o_futuro(nome):
    """O sinal no candle i não pode mudar quando os candles depois de i mudam."""
    e = ESTRATEGIAS[nome]
    df = serie(500, semente=11)
    s = e.sinais(df, **e.padrao)
    for corte in (100, 250, 400):
        futuro = df.copy()
        for col in ("abertura", "maxima", "minima", "fechamento", "volume"):
            futuro.loc[corte + 1:, col] *= 1.7
        np.testing.assert_array_equal(s[: corte + 1], e.sinais(futuro, **e.padrao)[: corte + 1])


@pytest.mark.parametrize("nome", sorted(ESTRATEGIAS))
def test_grade_e_padrao_sao_validos(nome):
    e = ESTRATEGIAS[nome]
    df = serie(300)
    for params in e.combinacoes():
        assert set(np.unique(e.sinais(df, **params))) <= {-1, 0, 1}
    assert e.padrao in e.combinacoes()


def test_rsi_entre_0_e_100():
    r = rsi(serie(400).fechamento.to_numpy(), 14)
    assert np.nanmin(r) >= 0 and np.nanmax(r) <= 100 and np.isnan(r[13]) and not np.isnan(r[14])


def test_aleatoria_e_reprodutivel():
    a = aleatoria(1000, 0.02, 0.1, semente=4)
    assert np.array_equal(a, aleatoria(1000, 0.02, 0.1, semente=4))
    assert not np.array_equal(a, aleatoria(1000, 0.02, 0.1, semente=5))
