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


def _forca(df: pd.DataFrame, periodo: int, k: float, corpo: float = 0.6) -> np.ndarray:
    """Candle de força: amplitude >= k vezes a média dos `periodo` candles anteriores e corpo
    >= `corpo` da amplitude. +1 se de alta, -1 se de baixa."""
    amp = (df.maxima - df.minima).to_numpy(float)
    media = pd.Series(amp).rolling(periodo).mean().shift(1).to_numpy()
    corpo_ = (df.fechamento - df.abertura).to_numpy(float)
    with np.errstate(invalid="ignore"):
        forte = (amp >= k * media) & (np.abs(corpo_) >= corpo * amp) & (amp > 0)
    return _sinal(forte & (corpo_ > 0), forte & (corpo_ < 0))


def sinais_forca(df: pd.DataFrame, periodo: int, k: float) -> np.ndarray:
    return _forca(df, periodo, k)


def sinais_forca_reversao(df: pd.DataFrame, periodo: int, k: float) -> np.ndarray:
    """Aposta contra o candle de força: exaustão."""
    return (-_forca(df, periodo, k)).astype(np.int8)


def canal(c: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Canal por regressão linear dos últimos `n` fechamentos (até o candle atual, inclusive).

    Devolve, por candle: linha média no candle atual, desvio padrão dos resíduos, R² e
    inclinação (pontos por candle). NaN antes de haver `n` candles."""
    out = [np.full(len(c), np.nan) for _ in range(4)]
    if len(c) < n:
        return tuple(out)
    y = sliding_window_view(c, n)
    x = np.arange(n) - (n - 1) / 2
    media_y = y.mean(axis=1)
    inclinacao = (y @ x) / (x @ x)
    ajuste = media_y[:, None] + inclinacao[:, None] * x[None, :]
    sse = ((y - ajuste) ** 2).sum(axis=1)
    sst = ((y - media_y[:, None]) ** 2).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        r2 = np.where(sst > 0, 1 - sse / sst, 0.0)
    out[0][n - 1:] = media_y + inclinacao * x[-1]
    out[1][n - 1:] = np.sqrt(sse / n)
    out[2][n - 1:] = r2
    out[3][n - 1:] = inclinacao
    return tuple(out)


SAIR = 2  # o motor da B3 entende como "encerrar a posição, sem abrir a contrária"


def _canal_sinais(df: pd.DataFrame, n: int, r2: float, compra: np.ndarray, venda: np.ndarray,
                  alta: np.ndarray, baixa: np.ndarray) -> np.ndarray:
    s = np.where(alta & compra, 1, np.where(baixa & venda, -1, 0))
    lateral = ~(alta | baixa)
    return np.where((s == 0) & lateral, SAIR, s).astype(np.int8)


def sinais_canal_rompimento(df: pd.DataFrame, n: int, r2: float) -> np.ndarray:
    """Só opera em canal (R² >= r2): rompimento da máxima/mínima dos 12 candles anteriores no
    sentido do canal. Lateral: não abre e manda sair."""
    c = df.fechamento.to_numpy(float)
    _, _, r2_, incl = canal(c, n)
    with np.errstate(invalid="ignore"):
        alta, baixa = (incl > 0) & (r2_ >= r2), (incl < 0) & (r2_ >= r2)
        topo = df.maxima.rolling(12).max().shift(1).to_numpy()
        fundo = df.minima.rolling(12).min().shift(1).to_numpy()
        return _canal_sinais(df, n, r2, c > topo, c < fundo, alta, baixa)


def sinais_canal_media(df: pd.DataFrame, n: int, r2: float) -> np.ndarray:
    """Só opera em canal: recuo até a linha média rejeitado (toca a média e fecha a favor)."""
    c = df.fechamento.to_numpy(float)
    m, _, r2_, incl = canal(c, n)
    with np.errstate(invalid="ignore"):
        alta, baixa = (incl > 0) & (r2_ >= r2), (incl < 0) & (r2_ >= r2)
        compra = (df.minima.to_numpy(float) <= m) & (c > m)
        venda = (df.maxima.to_numpy(float) >= m) & (c < m)
        return _canal_sinais(df, n, r2, compra, venda, alta, baixa)


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
    "forca": Estrategia(
        "forca", "Candle de força: entra a favor de um candle grande e de corpo cheio", sinais_forca,
        padrao={"periodo": 20, "k": 2.0},
        grade={"periodo": [10, 20], "k": [1.5, 2.0, 3.0]},
        aquecimento=lambda p: p["periodo"] + 1),
    "forca_reversao": Estrategia(
        "forca_reversao", "Candle de força ao contrário: entra contra um candle grande (exaustão)",
        sinais_forca_reversao,
        padrao={"periodo": 20, "k": 2.0},
        grade={"periodo": [10, 20], "k": [1.5, 2.0, 3.0]},
        aquecimento=lambda p: p["periodo"] + 1),
    "canal_rompimento": Estrategia(
        "canal_rompimento", "Só em canal (regressão, R² mínimo): rompimento a favor; lateral não opera e sai",
        sinais_canal_rompimento,
        padrao={"n": 24, "r2": 0.5},
        grade={"n": [24, 36], "r2": [0.5, 0.7]},
        aquecimento=lambda p: max(p["n"], 13) + 1),
    "canal_media": Estrategia(
        "canal_media", "Só em canal: recuo até a linha média rejeitado; lateral não opera e sai",
        sinais_canal_media,
        padrao={"n": 24, "r2": 0.5},
        grade={"n": [24, 36], "r2": [0.5, 0.7]},
        aquecimento=lambda p: p["n"] + 1),
    "rsi": Estrategia(
        "rsi", "Reversão: compra com RSI baixo, sai quando ele recupera", sinais_rsi,
        padrao={"periodo": 14, "compra": 30, "saida": 55},
        grade={"periodo": [7, 14, 21], "compra": [20, 25, 30], "saida": [50, 55, 65]},
        aquecimento=lambda p: p["periodo"] + 1),
}
