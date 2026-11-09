"""Exportação para o importador JSON do TradeLab (PWA).

O importador aceita até 20.000 candles sem lacunas e recalcula tudo com a própria
estratégia SMA. Por isso exportamos só o trecho contínuo mais recente.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .backtest import Risco
from .mercado import Custos

LIMITE_IMPORTADOR = 20_000


def para_tradelab(df: pd.DataFrame, simbolo: str, intervalo: str, limite: int = LIMITE_IMPORTADOR,
                  risco: Risco = Risco(), custos: Custos = Custos()) -> dict:
    ts = df.ts_abertura.to_numpy(np.int64)
    passo = int(df.ts_fechamento.iloc[0] - ts[0] + 1)
    quebras = np.flatnonzero(np.diff(ts) != passo)
    inicio = int(quebras[-1]) + 1 if len(quebras) else 0
    trecho = df.iloc[max(inicio, len(df) - limite):]
    return {
        "mode": "historico",
        "symbol": simbolo,
        "interval": intervalo,
        "source": "data.binance.vision (tradelab-motor)",
        "config": {"capital": risco.capital, "fee": custos.taxa, "slip": custos.slippage,
                   "stop": risco.stop or 0.01, "target": risco.alvo or 0.02},
        "candles": [
            {"opened": int(r.ts_abertura), "closed": int(r.ts_fechamento), "open": float(r.abertura),
             "high": float(r.maxima), "low": float(r.minima), "close": float(r.fechamento), "volume": float(r.volume)}
            for r in trecho.itertuples(index=False)],
    }
