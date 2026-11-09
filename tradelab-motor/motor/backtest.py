"""Execução candle a candle, só comprado, uma posição por vez.

Regras de execução (as mesmas do simulador do TradeLab, para que os números batam):
- o sinal é lido no fechamento do candle i e executado na abertura de i+1;
- stop e alvo são conferidos dentro do candle; se os dois cabem no mesmo candle,
  vale o stop (não dá para saber a ordem dos preços dentro do candle);
- gap abaixo do stop sai na abertura, não no stop;
- taxa e slippage em cada lado; posição aberta no fim é encerrada no último fechamento.

Acréscimos do motor: filtros da Binance, lacunas no histórico, limite de perda diária,
limite de operações por dia e o início da janela de operação (walk-forward).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .mercado import Custos, Mercado

ENTRAR, SAIR = 1, -1
_DIA_MS = 86_400_000
_BRT_MS = 3 * 3_600_000  # Brasília é UTC-3 o ano todo desde 2019


@dataclass(frozen=True)
class Risco:
    capital: float = 1000.0
    risco_por_trade: float = 0.0025   # perda no stop como fração do caixa
    exposicao_max: float = 0.10       # valor da posição como fração do caixa
    stop: float | None = 0.01
    alvo: float | None = 0.02
    perda_diaria_max: float | None = None   # fração do patrimônio no início do dia (BRT)
    max_operacoes_dia: int | None = None

    def __post_init__(self):
        if not 0 < self.capital:
            raise ValueError("Capital precisa ser positivo.")
        if not 0 < self.exposicao_max <= 1 or not 0 < self.risco_por_trade <= 1:
            raise ValueError("Exposição e risco por operação precisam estar entre 0 e 1.")
        for nome in ("stop", "alvo"):
            v = getattr(self, nome)
            if v is not None and not 0 < v < 1:
                raise ValueError(f"{nome} precisa estar entre 0 e 1.")


@dataclass
class Resultado:
    operacoes: pd.DataFrame
    ts: np.ndarray
    patrimonio: np.ndarray
    patrimonio_minimo: np.ndarray
    capital_inicial: float
    capital_final: float
    drawdown_fechamento: float
    drawdown_minimo: float
    rejeitadas_filtro: int = 0
    bloqueadas_risco: int = 0
    candles_posicionado: int = 0
    candles_operaveis: int = 0
    risco: Risco = field(default_factory=Risco)
    custos: Custos = field(default_factory=Custos)


_COLS_OPS = ["ts_entrada", "ts_saida", "i_entrada", "i_saida", "preco_entrada", "preco_saida",
             "quantidade", "motivo", "pnl", "retorno_pct", "custos"]


def executar(df: pd.DataFrame, sinais: np.ndarray, risco: Risco = Risco(), custos: Custos = Custos(),
             mercado: Mercado = Mercado(), aquecimento: int = 0, inicio: int = 0) -> Resultado:
    """`sinais[i]` = +1 quer entrar, -1 quer sair, 0 nada. `aquecimento` = candles contínuos
    que o indicador precisa (inclusive o atual); `inicio` = primeiro candle em que sinais valem."""
    n = len(df)
    if len(sinais) != n:
        raise ValueError("Vetor de sinais com tamanho diferente dos candles.")
    ts_a = df.ts_abertura.to_numpy(np.int64)
    ts_f = df.ts_fechamento.to_numpy(np.int64)
    passo = int(ts_f[0] - ts_a[0] + 1) if n else 0
    seq = np.zeros(n, dtype=np.int64)  # candles contínuos antes deste, no mesmo trecho
    for i in range(1, n):
        seq[i] = seq[i - 1] + 1 if ts_a[i] - ts_a[i - 1] == passo else 0
    valido = (seq >= max(aquecimento - 1, 0)) & (np.arange(n) >= inicio)
    O, H, L, C = (df[c].to_numpy(float).tolist() for c in ("abertura", "maxima", "minima", "fechamento"))
    S, V, Q = np.asarray(sinais).tolist(), valido.tolist(), seq.tolist()
    dia = ((ts_a - _BRT_MS) // _DIA_MS).tolist()

    taxa, slip = custos.taxa, custos.slippage
    caixa = float(risco.capital)
    pos = None  # dict da posição aberta
    pendente = 0
    ops, patr, patr_min = [], np.empty(n), np.empty(n)
    pico, dd_f, dd_m = caixa, 0.0, 0.0
    rejeitadas = bloqueadas = posicionado = 0
    dia_atual, base_dia, pnl_dia, entradas_dia = None, caixa, 0.0, 0

    def vender(preco, motivo, ts, i):
        nonlocal caixa, pos, pnl_dia
        fill = preco * (1 - slip)
        receita = pos["q"] * fill * (1 - taxa)
        caixa += receita
        pnl = receita - pos["custo"]
        pnl_dia += pnl
        gasto = pos["q"] * (pos["entrada"] * taxa + fill * taxa + (pos["entrada"] - pos["bruto"]) + (preco - fill))
        ops.append((pos["ts"], ts, pos["i"], i, pos["entrada"], fill, pos["q"], motivo, pnl,
                    pnl / pos["custo"] * 100, gasto))
        pos = None

    for i in range(n):
        if dia[i] != dia_atual:
            dia_atual, base_dia, pnl_dia, entradas_dia = dia[i], (patr[i - 1] if i else caixa), 0.0, 0
        o, h, l, c = O[i], H[i], L[i], C[i]

        if pendente == SAIR and pos is not None:
            vender(o, "sinal", int(ts_a[i]), i)
        elif pendente == ENTRAR and pos is None and Q[i] > 0:  # Q[i]==0: ordem não atravessa lacuna
            if (risco.max_operacoes_dia is not None and entradas_dia >= risco.max_operacoes_dia) or \
               (risco.perda_diaria_max is not None and -pnl_dia >= risco.perda_diaria_max * base_dia):
                bloqueadas += 1
            else:
                entrada = o * (1 + slip)
                stop = mercado.arredonda_preco(entrada * (1 - risco.stop)) if risco.stop else None
                q = caixa * risco.exposicao_max / (entrada * (1 + taxa))
                if stop is not None:
                    q = min(caixa * risco.risco_por_trade / (entrada * (1 + taxa) - stop * (1 - slip) * (1 - taxa)), q)
                q = mercado.arredonda_qtd(q)
                if not mercado.aceita(q, entrada):
                    rejeitadas += 1
                else:
                    custo = q * entrada * (1 + taxa)
                    caixa -= custo
                    entradas_dia += 1
                    alvo = mercado.arredonda_preco(entrada * (1 + risco.alvo)) if risco.alvo else None
                    pos = {"entrada": entrada, "bruto": o, "stop": stop, "alvo": alvo, "q": q,
                           "custo": custo, "ts": int(ts_a[i]), "i": i}
        pendente = 0

        if pos is not None:
            if pos["stop"] is not None and l <= pos["stop"]:
                vender(min(o, pos["stop"]), "stop", int(ts_f[i]), i)
            elif pos["alvo"] is not None and h >= pos["alvo"]:
                vender(pos["alvo"], "alvo", int(ts_f[i]), i)

        if pos is not None:
            posicionado += 1
            liq = pos["q"] * (1 - slip) * (1 - taxa)
            valor, minimo = caixa + liq * c, caixa + liq * l
        else:
            valor = minimo = caixa
        patr[i], patr_min[i] = valor, minimo
        pico = max(pico, valor)
        dd_f = max(dd_f, (pico - valor) / pico)
        dd_m = max(dd_m, (pico - minimo) / pico)

        if V[i] and i < n - 1:
            if S[i] == ENTRAR and pos is None:
                pendente = ENTRAR
            elif S[i] == SAIR and pos is not None:
                pendente = SAIR

    if pos is not None:
        vender(C[-1], "fim", int(ts_f[-1]), n - 1)

    return Resultado(
        operacoes=pd.DataFrame(ops, columns=_COLS_OPS),
        ts=ts_f, patrimonio=patr, patrimonio_minimo=patr_min,
        capital_inicial=float(risco.capital), capital_final=caixa,
        drawdown_fechamento=dd_f, drawdown_minimo=dd_m,
        rejeitadas_filtro=rejeitadas, bloqueadas_risco=bloqueadas,
        candles_posicionado=posicionado, candles_operaveis=int(valido.sum()),
        risco=risco, custos=custos,
    )
