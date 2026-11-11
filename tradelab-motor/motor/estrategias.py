"""Hipóteses de estratégia. Cada uma devolve, por candle, +1 (quer comprar), -1 (quer sair)
ou 0, usando só candles até o atual. O motor decide se e quando executa.

Nenhuma delas é recomendação: são hipóteses para o walk-forward derrubar ou não.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view


def sma(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = sliding_window_view(x, n).sum(axis=1) / n
    return out


def rsi(x: np.ndarray, n: int) -> np.ndarray:
    """RSI com média simples (Cutler): janela finita, então uma lacuna não contamina para sempre."""
    d = np.diff(x, prepend=np.nan)
    ganho = pd.Series(np.where(d > 0, d, 0.0)).rolling(n).mean().to_numpy()
    perda = pd.Series(np.where(d < 0, -d, 0.0)).rolling(n).mean().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        r = 100 - 100 / (1 + ganho / perda)
    r = np.where((perda == 0) & (ganho > 0), 100.0, r)
    r = np.where((perda == 0) & (ganho == 0), 50.0, r)
    r[:n] = np.nan
    return r


def _sinal(compra: np.ndarray, venda: np.ndarray) -> np.ndarray:
    return np.where(compra, 1, np.where(venda, -1, 0)).astype(np.int8)


def sinais_sma(df: pd.DataFrame, rapida: int, lenta: int) -> np.ndarray:
    c = df.fechamento.to_numpy(float)
    f, s = sma(c, rapida), sma(c, lenta)
    fa, sa = np.roll(f, 1), np.roll(s, 1)
    fa[0] = sa[0] = np.nan
    with np.errstate(invalid="ignore"):
        return _sinal((fa <= sa) & (f > s), (fa >= sa) & (f < s))


def sinais_rompimento(df: pd.DataFrame, entrada: int, saida: int) -> np.ndarray:
    topo = df.maxima.rolling(entrada).max().shift(1).to_numpy()
    fundo = df.minima.rolling(saida).min().shift(1).to_numpy()
    c = df.fechamento.to_numpy(float)
    with np.errstate(invalid="ignore"):
        return _sinal(c > topo, c < fundo)


def sinais_rsi(df: pd.DataFrame, periodo: int, compra: float, saida: float) -> np.ndarray:
    r = rsi(df.fechamento.to_numpy(float), periodo)
    with np.errstate(invalid="ignore"):
        return _sinal(r < compra, r > saida)


def sinais_abertura(df: pd.DataFrame, candles: int) -> np.ndarray:
    """Rompimento da faixa de abertura: máxima e mínima dos primeiros `candles` do pregão
    (dia em Brasília). Depois deles, +1 se fechar acima da faixa, -1 se fechar abaixo."""
    ts = df.ts_abertura.to_numpy(np.int64)
    dia = (ts - 3 * 3_600_000) // 86_400_000
    pos = pd.Series(dia).groupby(dia).cumcount().to_numpy()
    na_faixa = pos < candles
    g = pd.DataFrame({"dia": dia, "h": np.where(na_faixa, df.maxima, np.nan), "l": np.where(na_faixa, df.minima, np.nan)})
    topo = g.groupby("dia").h.transform("max").to_numpy()
    fundo = g.groupby("dia").l.transform("min").to_numpy()
    c = df.fechamento.to_numpy(float)
    depois = ~na_faixa
    return _sinal(depois & (c > topo), depois & (c < fundo))


def aleatoria(n: int, prob_entrada: float, prob_saida: float, semente: int) -> np.ndarray:
    """Linha de base: entra e sai ao acaso. Uma estratégia que não bate isto não tem vantagem."""
    u = np.random.default_rng(semente).random(n)
    return _sinal(u < prob_entrada, u > 1 - prob_saida)


@dataclass(frozen=True)
class Estrategia:
    nome: str
    descricao: str
    funcao: Callable[..., np.ndarray]
    padrao: dict
    grade: dict
    aquecimento: Callable[[dict], int]
    restricao: Callable[[dict], bool] = lambda p: True

    def sinais(self, df: pd.DataFrame, **params) -> np.ndarray:
        return self.funcao(df, **params)

    def combinacoes(self) -> list[dict]:
        chaves = list(self.grade)
        todas = (dict(zip(chaves, v)) for v in product(*(self.grade[k] for k in chaves)))
        return [p for p in todas if self.restricao(p)]


ESTRATEGIAS = {
    "sma": Estrategia(
        "sma", "Cruzamento de médias simples (a estratégia atual do TradeLab)", sinais_sma,
        padrao={"rapida": 9, "lenta": 21},
        grade={"rapida": [5, 9, 13, 20], "lenta": [21, 34, 50, 100]},
        aquecimento=lambda p: p["lenta"] + 1,
        restricao=lambda p: p["rapida"] < p["lenta"]),
    "rompimento": Estrategia(
        "rompimento", "Rompimento da máxima de N candles; sai na perda da mínima de M (Donchian)",
        sinais_rompimento,
        padrao={"entrada": 20, "saida": 10},
        grade={"entrada": [20, 40, 60, 96], "saida": [10, 20, 48]},
        aquecimento=lambda p: max(p["entrada"], p["saida"]) + 1,
        restricao=lambda p: p["saida"] <= p["entrada"]),
    "abertura": Estrategia(
        "abertura", "Rompimento da faixa de abertura do pregão (máxima/mínima dos primeiros candles)",
        sinais_abertura,
        padrao={"candles": 6},
        grade={"candles": [3, 6, 12]},
        aquecimento=lambda p: p["candles"] + 1),
    "rompimento_curto": Estrategia(
        "rompimento_curto", "Rompimento da máxima/mínima de N candles, com janelas que cabem num pregão",
        sinais_rompimento,
        padrao={"entrada": 12, "saida": 6},
        grade={"entrada": [6, 12, 20], "saida": [3, 6, 12]},
        aquecimento=lambda p: max(p["entrada"], p["saida"]) + 1,
        restricao=lambda p: p["saida"] <= p["entrada"]),
    "rsi": Estrategia(
        "rsi", "Reversão: compra com RSI baixo, sai quando ele recupera", sinais_rsi,
        padrao={"periodo": 14, "compra": 30, "saida": 55},
        grade={"periodo": [7, 14, 21], "compra": [20, 25, 30], "saida": [50, 55, 65]},
        aquecimento=lambda p: p["periodo"] + 1),
}
