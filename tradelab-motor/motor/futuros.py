"""Minicontratos da B3 (WIN e WDO): leitura do MT5 e execução por pregão.

Diferenças em relação ao motor de cripto (`backtest.py`):
- resultado em pontos × valor do ponto, quantidade inteira de contratos;
- custo fixo em reais por contrato e por lado, slippage em ticks;
- comprado e vendido, com virada de mão;
- sem entrada perto do fim do pregão, zeragem obrigatória no horário da corretora e
  nada passa de um dia para o outro. Como a noite é uma lacuna para o motor, os
  indicadores reaquecem a cada pregão: o salto falso da troca de vencimento da série
  contínua não contamina o sinal.

As regras de execução são as do motor de cripto: sinal no fechamento, execução na
abertura seguinte, stop antes do alvo no mesmo candle, gap além do stop sai na abertura.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import _BRT_MS, _COLS_OPS, _DIA_MS, Resultado, Risco

COMPRAR, VENDER, SAIR = 1, -1, 2


@dataclass(frozen=True)
class Contrato:
    """Especificação (B3) e regras de operação. Horários em minutos do dia, em Brasília."""
    nome: str
    valor_ponto: float           # R$ por ponto por contrato
    tick: float                  # variação mínima, em pontos
    margem: float                # garantia de day trade por contrato (R$)
    zeragem: int = 18 * 60       # a XP troca a garantia 15 min antes do fim; WIN vincendo fecha às 18h
    ultima_entrada: int = 17 * 60 + 30
    lado: str = "comprado"       # "comprado" ou "ambos"

    def arredonda(self, p: float) -> float:
        return round(p / self.tick) * self.tick


def com_lado(c: Contrato, lado: str) -> Contrato:
    if lado not in ("comprado", "ambos"):
        raise ValueError("lado precisa ser 'comprado' ou 'ambos'")
    return replace(c, lado=lado)


# B3 (especificação dos contratos) e manual de risco da XP v67, consultados em 10/11/2026.
CONTRATOS = {
    "WIN": Contrato("WIN", valor_ponto=0.20, tick=5.0, margem=155.0),
    "WDO": Contrato("WDO", valor_ponto=10.0, tick=0.5, margem=140.0),
}


@dataclass(frozen=True)
class CustosFuturo:
    # Padrão WIN na XP para robô: corretagem R$ 1,00 + 9,65% de tributos (a promoção RLP
    # exclui automação) + tarifa B3 R$ 0,25 por lado. WDO: R$ 1,10 + ~R$ 1,14 = R$ 2,24.
    custo_lado: float = 1.35     # R$ por contrato, em cada lado
    slippage_ticks: int = 1      # ticks contra você em cada execução a mercado


CUSTOS = {"WIN": CustosFuturo(1.35, 1), "WDO": CustosFuturo(2.24, 1)}


@dataclass
class RelatorioB3:
    candles: int = 0
    pregoes: int = 0
    duplicatas_removidas: int = 0
    pausas: list[tuple[int, int]] = field(default_factory=list)  # (ts do candle que retoma, minutos sem negócio)


def carregar_mt5(caminho: Path) -> tuple[pd.DataFrame, RelatorioB3]:
    """CSV de 'Exportar barras' do MT5: tabulação, horário de Brasília."""
    d = pd.read_csv(caminho, sep="\t")
    d.columns = [c.strip("<>").lower() for c in d.columns]
    brt = pd.to_datetime(d["date"] + " " + d["time"], format="%Y.%m.%d %H:%M:%S")
    ts = brt.to_numpy().astype("datetime64[ms]").astype(np.int64) + _BRT_MS
    df = pd.DataFrame({"ts_abertura": ts, "abertura": d["open"].astype(float), "maxima": d["high"].astype(float),
                       "minima": d["low"].astype(float), "fechamento": d["close"].astype(float),
                       "volume": d["vol"].astype(float)}).sort_values("ts_abertura", kind="stable")
    antes = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    if df.ts_abertura.duplicated().any():
        raise ValueError("Candle duplicado com valores diferentes no arquivo do MT5.")
    p = df[["abertura", "maxima", "minima", "fechamento"]].to_numpy()
    ruim = ~np.isfinite(p).all(axis=1) | (p <= 0).any(axis=1)
    ruim |= df.maxima.to_numpy() < np.maximum(df.abertura, df.fechamento).to_numpy()
    ruim |= df.minima.to_numpy() > np.minimum(df.abertura, df.fechamento).to_numpy()
    if ruim.any():
        i = int(np.flatnonzero(ruim)[0])
        raise ValueError(f"Candle incoerente no arquivo do MT5: {df.iloc[i].to_dict()}")
    dia = (df.ts_abertura - _BRT_MS) // _DIA_MS
    salto = df.ts_abertura.diff()
    mesmo_dia = dia == dia.shift()
    passo = int(salto[mesmo_dia].min())
    df["ts_fechamento"] = df.ts_abertura + passo - 1
    pausa = mesmo_dia & (salto > passo)
    pausas = [(int(t), int((s - passo) // 60_000)) for t, s in zip(df.ts_abertura[pausa], salto[pausa])]
    return df, RelatorioB3(len(df), int(dia.nunique()), antes - len(df), pausas)


def reamostrar(df: pd.DataFrame, minutos: int) -> pd.DataFrame:
    """Agrega candles em blocos de `minutos` contados a partir das 9h00, sem cruzar pregões."""
    dia = (df.ts_abertura - _BRT_MS) // _DIA_MS
    minuto = ((df.ts_abertura - _BRT_MS) % _DIA_MS) // 60_000
    bloco = (minuto - 9 * 60) // minutos
    g = df.groupby([dia, bloco], sort=True)
    out = g.agg(abertura=("abertura", "first"), maxima=("maxima", "max"), minima=("minima", "min"),
                fechamento=("fechamento", "last"), volume=("volume", "sum")).reset_index(names=["dia", "bloco"])
    out["ts_abertura"] = (out.dia * _DIA_MS + _BRT_MS + (9 * 60 + out.bloco * minutos) * 60_000).astype("int64")
    out["ts_fechamento"] = out.ts_abertura + minutos * 60_000 - 1
    return out[["ts_abertura", "abertura", "maxima", "minima", "fechamento", "volume", "ts_fechamento"]]


def executar_futuros(df: pd.DataFrame, sinais: np.ndarray, risco: Risco = Risco(), custos: CustosFuturo | None = None,
                     mercado: Contrato = CONTRATOS["WIN"], aquecimento: int = 0, inicio: int = 0) -> Resultado:
    """`sinais[i]`: +1 quer ficar comprado, -1 quer ficar vendido (ou sair, se só comprado).

    `risco.exposicao_max` é a fração do patrimônio que pode virar margem."""
    c_ = mercado
    custos = custos or CUSTOS.get(c_.nome, CustosFuturo())
    n = len(df)
    if len(sinais) != n:
        raise ValueError("Vetor de sinais com tamanho diferente dos candles.")
    ts_a = df.ts_abertura.to_numpy(np.int64)
    ts_f = df.ts_fechamento.to_numpy(np.int64)
    passo = int(ts_f[0] - ts_a[0] + 1) if n else 0
    seq = np.zeros(n, dtype=np.int64)
    for i in range(1, n):
        seq[i] = seq[i - 1] + 1 if ts_a[i] - ts_a[i - 1] == passo else 0
    valido = (seq >= max(aquecimento - 1, 0)) & (np.arange(n) >= inicio)
    dia_arr = (ts_a - _BRT_MS) // _DIA_MS
    ultimo = np.append(dia_arr[1:] != dia_arr[:-1], True).tolist()
    minuto = (((ts_a - _BRT_MS) % _DIA_MS) // 60_000).tolist()
    O, H, L, C = (df[k].to_numpy(float).tolist() for k in ("abertura", "maxima", "minima", "fechamento"))
    S, V, Q, dia = np.asarray(sinais).tolist(), valido.tolist(), seq.tolist(), dia_arr.tolist()

    vp, cl = c_.valor_ponto, custos.custo_lado
    slip = custos.slippage_ticks * c_.tick
    ambos = c_.lado == "ambos"
    saldo = float(risco.capital)
    pos = None
    pendente = 0
    ops, patr, patr_min = [], np.empty(n), np.empty(n)
    pico, dd_f, dd_m = saldo, 0.0, 0.0
    rejeitadas = bloqueadas = posicionado = 0
    dia_atual, base_dia, pnl_dia, entradas_dia = None, saldo, 0.0, 0

    def fechar(bruto, motivo, ts, i, slip_saida):
        nonlocal saldo, pos, pnl_dia
        lado, q = pos["lado"], pos["q"]
        fill = bruto - lado * slip_saida
        pnl = lado * (fill - pos["entrada"]) * vp * q - 2 * cl * q
        saldo += pnl
        pnl_dia += pnl
        gasto = 2 * cl * q + (pos["slip"] + slip_saida) * vp * q
        ops.append((pos["ts"], ts, pos["i"], i, pos["entrada"], fill, q, motivo, pnl,
                    pnl / pos["base"] * 100, gasto, lado))
        pos = None

    def abrir(lado, o, i):
        nonlocal pos, rejeitadas, bloqueadas, entradas_dia
        if (risco.max_operacoes_dia is not None and entradas_dia >= risco.max_operacoes_dia) or \
           (risco.perda_diaria_max is not None and -pnl_dia >= risco.perda_diaria_max * base_dia):
            bloqueadas += 1
            return
        entrada = o + lado * slip
        stop = c_.arredonda(entrada * (1 - lado * risco.stop)) if risco.stop else None
        alvo = c_.arredonda(entrada * (1 + lado * risco.alvo)) if risco.alvo else None
        q = math.floor(saldo * risco.exposicao_max / c_.margem + 1e-9)
        if stop is not None:
            perda = (abs(entrada - stop) + slip) * vp + 2 * cl
            q = min(q, math.floor(saldo * risco.risco_por_trade / perda + 1e-9))
        if risco.max_contratos is not None:
            q = min(q, risco.max_contratos)
        if q < 1:
            rejeitadas += 1
            return
        entradas_dia += 1
        pos = {"lado": lado, "q": q, "entrada": entrada, "stop": stop, "alvo": alvo, "slip": slip,
               "ts": int(ts_a[i]), "i": i, "base": saldo}

    for i in range(n):
        if dia[i] != dia_atual:
            dia_atual, base_dia, pnl_dia, entradas_dia = dia[i], (patr[i - 1] if i else saldo), 0.0, 0
        o, h, l, c = O[i], H[i], L[i], C[i]

        if pos is not None and minuto[i] >= c_.zeragem:
            fechar(o, "zeragem", int(ts_a[i]), i, slip)
            pendente = 0
        if pendente in (COMPRAR, VENDER):
            if pos is not None and pos["lado"] != pendente:
                fechar(o, "sinal", int(ts_a[i]), i, slip)
            if pos is None and Q[i] > 0 and minuto[i] < c_.ultima_entrada:
                abrir(pendente, o, i)
        elif pendente == SAIR and pos is not None:
            fechar(o, "sinal", int(ts_a[i]), i, slip)
        pendente = 0

        if pos is not None:
            lado = pos["lado"]
            if pos["stop"] is not None and (l <= pos["stop"] if lado == 1 else h >= pos["stop"]):
                bruto = min(o, pos["stop"]) if lado == 1 else max(o, pos["stop"])
                fechar(bruto, "stop", int(ts_f[i]), i, slip)
            elif pos["alvo"] is not None and (h >= pos["alvo"] if lado == 1 else l <= pos["alvo"]):
                fechar(pos["alvo"], "alvo", int(ts_f[i]), i, 0.0)
        if pos is not None and ultimo[i]:
            fechar(c, "fim do dia", int(ts_f[i]), i, slip)

        if pos is not None:
            posicionado += 1
            lado, q = pos["lado"], pos["q"]
            liq = lambda p: lado * (p - lado * slip - pos["entrada"]) * vp * q - 2 * cl * q
            valor, minimo = saldo + liq(c), saldo + liq(l if lado == 1 else h)
        else:
            valor = minimo = saldo
        patr[i], patr_min[i] = valor, minimo
        pico = max(pico, valor)
        dd_f = max(dd_f, (pico - valor) / pico)
        dd_m = max(dd_m, (pico - minimo) / pico)

        if V[i] and not ultimo[i]:
            s = S[i]
            atual = pos["lado"] if pos is not None else 0
            if s == 1 and atual != 1:
                pendente = COMPRAR
            elif s == -1 and atual != -1:
                pendente = VENDER if ambos else (SAIR if atual == 1 else 0)

    return Resultado(
        operacoes=pd.DataFrame(ops, columns=_COLS_OPS + ["lado"]),
        ts=ts_f, patrimonio=patr, patrimonio_minimo=patr_min,
        capital_inicial=float(risco.capital), capital_final=saldo,
        drawdown_fechamento=dd_f, drawdown_minimo=dd_m,
        rejeitadas_filtro=rejeitadas, bloqueadas_risco=bloqueadas,
        candles_posicionado=posicionado, candles_operaveis=int(valido.sum()),
        risco=risco, custos=custos,
    )
