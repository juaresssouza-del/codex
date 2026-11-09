"""Séries sintéticas para os testes. Nunca use isto como evidência de estratégia."""
import numpy as np
import pandas as pd

PASSO_15M = 900_000
INICIO = 1_767_225_600_000  # 2026-01-01 00:00 UTC


def serie(n=600, semente=1, deriva=0.0, vol=0.004, inicio=INICIO, passo=PASSO_15M, preco=100.0):
    rng = np.random.default_rng(semente)
    ret = rng.normal(deriva, vol, n)
    fech = preco * np.exp(np.cumsum(ret))
    abert = np.concatenate([[preco], fech[:-1]])
    amp = np.abs(rng.normal(0, vol / 2, n)) * fech
    ts = inicio + np.arange(n, dtype=np.int64) * passo
    return pd.DataFrame({
        "ts_abertura": ts,
        "abertura": abert,
        "maxima": np.maximum(abert, fech) + amp,
        "minima": np.minimum(abert, fech) - amp,
        "fechamento": fech,
        "volume": rng.uniform(10, 100, n),
        "ts_fechamento": ts + passo - 1,
    })


def plana(n=50, preco=100.0, inicio=INICIO, passo=PASSO_15M):
    ts = inicio + np.arange(n, dtype=np.int64) * passo
    p = np.full(n, preco)
    return pd.DataFrame({"ts_abertura": ts, "abertura": p, "maxima": p, "minima": p,
                         "fechamento": p, "volume": np.ones(n), "ts_fechamento": ts + passo - 1})


def sinais(n, **pos):
    """sinais(50, **{"10": 1, "20": -1}) -> vetor com +1 no índice 10 e -1 no 20."""
    s = np.zeros(n, dtype=np.int8)
    for i, v in pos.items():
        s[int(i)] = v
    return s
