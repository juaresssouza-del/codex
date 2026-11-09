"""Métricas de um resultado. O foco é expectativa depois dos custos, não taxa de acerto."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .backtest import Resultado


def _maior_sequencia(perdeu: np.ndarray) -> int:
    maior = atual = 0
    for p in perdeu:
        atual = atual + 1 if p else 0
        maior = max(maior, atual)
    return maior


def calcular(r: Resultado) -> dict:
    ops = r.operacoes
    pnl = ops.pnl.to_numpy(float)
    ganhos, perdas = pnl[pnl > 0], pnl[pnl < 0]
    bruto_ganho, bruto_perda = ganhos.sum(), -perdas.sum()
    n = len(ops)
    dias = pd.Series(r.patrimonio, index=pd.to_datetime(r.ts, unit="ms")).resample("1D").last().dropna()
    ret_dia = dias.pct_change().dropna()
    meses = max((r.ts[-1] - r.ts[0]) / (30.44 * 86_400_000), 1e-9) if len(r.ts) else 0
    return {
        "operacoes": n,
        "ganhos": int(len(ganhos)),
        "perdas": int(len(perdas)),
        "taxa_acerto_pct": len(ganhos) / n * 100 if n else None,
        "fator_lucro": bruto_ganho / bruto_perda if bruto_perda > 0 else None,
        "expectativa": pnl.mean() if n else None,
        "expectativa_pct": ops.retorno_pct.mean() if n else None,
        "ganho_medio": ganhos.mean() if len(ganhos) else None,
        "perda_media": -perdas.mean() if len(perdas) else None,
        "resultado_liquido": r.capital_final - r.capital_inicial,
        "retorno_pct": (r.capital_final / r.capital_inicial - 1) * 100,
        "drawdown_fechamento_pct": r.drawdown_fechamento * 100,
        "drawdown_minimo_pct": r.drawdown_minimo * 100,
        "custos_totais": float(ops.custos.sum()),
        "resultado_bruto": r.capital_final - r.capital_inicial + float(ops.custos.sum()),
        "tempo_posicionado_pct": r.candles_posicionado / r.candles_operaveis * 100 if r.candles_operaveis else 0.0,
        "maior_sequencia_perdas": _maior_sequencia(pnl < 0),
        "operacoes_por_mes": n / meses if meses else None,
        "sharpe_anual": float(ret_dia.mean() / ret_dia.std() * np.sqrt(365)) if len(ret_dia) > 2 and ret_dia.std() > 0 else None,
        "por_motivo": ops.motivo.value_counts().to_dict(),
        "rejeitadas_filtro": r.rejeitadas_filtro,
        "nao_executadas": r.nao_executadas,
        "bloqueadas_risco": r.bloqueadas_risco,
    }
