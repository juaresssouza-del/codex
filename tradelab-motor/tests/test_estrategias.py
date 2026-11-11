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
        assert set(np.unique(e.sinais(df, **params))) <= {-1, 0, 1, 2}  # 2 = sair (motor da B3)
    assert e.padrao in e.combinacoes()


def test_rsi_entre_0_e_100():
    r = rsi(serie(400).fechamento.to_numpy(), 14)
    assert np.nanmin(r) >= 0 and np.nanmax(r) <= 100 and np.isnan(r[13]) and not np.isnan(r[14])


def test_aleatoria_e_reprodutivel():
    a = aleatoria(1000, 0.02, 0.1, semente=4)
    assert np.array_equal(a, aleatoria(1000, 0.02, 0.1, semente=4))
    assert not np.array_equal(a, aleatoria(1000, 0.02, 0.1, semente=5))


# --- canal (rodada 7) -----------------------------------------------------------------------

from motor.estrategias import canal  # noqa: E402


def test_canal_igual_a_regressao_linear():
    df = serie(200, semente=12)
    m, desvio, r2, inclinacao = canal(df.fechamento.to_numpy(float), 24)
    i = 150
    y = df.fechamento.to_numpy(float)[i - 23:i + 1]
    b, a = np.polyfit(np.arange(24), y, 1)
    ajuste = a + b * np.arange(24)
    assert inclinacao[i] == pytest.approx(b)
    assert m[i] == pytest.approx(ajuste[-1])
    assert desvio[i] == pytest.approx(np.std(y - ajuste))
    assert r2[i] == pytest.approx(1 - np.sum((y - ajuste) ** 2) / np.sum((y - y.mean()) ** 2))
    assert np.isnan(m[22]) and not np.isnan(m[23])


def _tendencia(n, passo, ruido, semente=0):
    rng = np.random.default_rng(semente)
    df = serie(n, semente=semente)
    c = 100 + passo * np.arange(n) + rng.normal(0, ruido, n)
    df["fechamento"] = c
    df["abertura"] = np.r_[c[0], c[:-1]]
    df["maxima"] = np.maximum(df.abertura, df.fechamento) + ruido
    df["minima"] = np.minimum(df.abertura, df.fechamento) - ruido
    return df


def test_canal_de_alta_compra_e_lateral_sai():
    alta = _tendencia(120, 0.2, 0.05)
    s = ESTRATEGIAS["canal_rompimento"].sinais(alta, n=24, r2=0.7)
    assert (s[30:] == 1).sum() > 10 and (s == -1).sum() == 0
    lateral = _tendencia(120, 0.0, 0.5, semente=3)
    s = ESTRATEGIAS["canal_rompimento"].sinais(lateral, n=24, r2=0.7)
    assert set(np.unique(s[30:])) <= {0, 2} and (s[30:] == 2).sum() > 50


def test_canal_de_baixa_vende_no_rompimento():
    baixa = _tendencia(120, -0.2, 0.05)
    s = ESTRATEGIAS["canal_rompimento"].sinais(baixa, n=24, r2=0.7)
    assert (s[30:] == -1).sum() > 10 and (s == 1).sum() == 0


def test_canal_media_compra_no_toque_da_linha_media():
    alta = _tendencia(120, 0.2, 0.05)
    i = 80
    m, *_ = canal(alta.fechamento.to_numpy(float), 24)
    alta.loc[i, "minima"] = m[i] - 0.1          # toca a média...
    alta.loc[i, "fechamento"] = max(alta.fechamento[i], m[i] + 0.05)  # ...e fecha acima
    s = ESTRATEGIAS["canal_media"].sinais(alta, n=24, r2=0.7)
    assert s[i] == 1
