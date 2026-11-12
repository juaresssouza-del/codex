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
from typing import Callable

import numpy as np
import pandas as pd

from .backtest import _BRT_MS, _COLS_OPS, _DIA_MS, Resultado, Risco

COMPRAR, VENDER, SAIR = 1, -1, 2
SAIR_COMPRADO, SAIR_VENDIDO = 3, 4


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
    indicador_continuo: bool = False  # True: a noite não reinicia o aquecimento (canal de vários dias)

    def __post_init__(self):
        for nome in ("valor_ponto", "tick", "margem"):
            if not math.isfinite(getattr(self, nome)) or getattr(self, nome) <= 0:
                raise ValueError(f"{nome} precisa ser finito e positivo.")
        if self.lado not in ("comprado", "ambos"):
            raise ValueError("lado precisa ser 'comprado' ou 'ambos'")
        for nome in ("zeragem", "ultima_entrada"):
            v = getattr(self, nome)
            if not isinstance(v, int) or not 0 <= v < 24 * 60:
                raise ValueError(f"{nome} precisa ser um minuto válido do dia.")

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
    # Premissas das rodadas históricas, NÃO cotação confirmada do EA na XP.
    # A rota MT5/EA e a PTAX usada no componente B3 de WDO aguardam confirmação.
    # Mantidas sem otimização durante a auditoria; ver AUDITORIA_CODEX.md.
    custo_lado: float = 1.35     # R$ por contrato, em cada lado
    slippage_ticks: int = 1      # ticks contra você em cada execução a mercado

    def __post_init__(self):
        if not math.isfinite(self.custo_lado) or self.custo_lado < 0:
            raise ValueError("custo_lado precisa ser finito e não negativo.")
        if isinstance(self.slippage_ticks, bool) or not isinstance(self.slippage_ticks, (int, np.integer)) or self.slippage_ticks < 0:
            raise ValueError("slippage_ticks precisa ser um inteiro não negativo.")


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
    if d.empty:
        raise ValueError("CSV do MT5 sem candles.")
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
    ruim |= ~np.isfinite(df.volume.to_numpy()) | (df.volume.to_numpy() < 0)
    if ruim.any():
        i = int(np.flatnonzero(ruim)[0])
        raise ValueError(f"Candle incoerente no arquivo do MT5: {df.iloc[i].to_dict()}")
    dia = (df.ts_abertura - _BRT_MS) // _DIA_MS
    salto = df.ts_abertura.diff()
    mesmo_dia = dia == dia.shift()
    intervalos = salto[mesmo_dia]
    if intervalos.empty:
        raise ValueError("Não é possível inferir o intervalo do MT5 sem candles consecutivos no pregão.")
    passo = int(intervalos.min())
    df["ts_fechamento"] = df.ts_abertura + passo - 1
    pausa = mesmo_dia & (salto > passo)
    pausas = [(int(t), int((s - passo) // 60_000)) for t, s in zip(df.ts_abertura[pausa], salto[pausa])]
    return df, RelatorioB3(len(df), int(dia.nunique()), antes - len(df), pausas)


def vencimentos_win(inicio: int = 2021, fim: int = 2026) -> list:
    """Vencimento do WIN (B3): quarta-feira mais próxima do dia 15 dos meses pares."""
    dias = []
    for ano in range(inicio, fim + 1):
        for mes in (2, 4, 6, 8, 10, 12):
            d15 = pd.Timestamp(ano, mes, 15)
            quartas = [d15 + pd.Timedelta(days=k) for k in range(-3, 4) if (d15 + pd.Timedelta(days=k)).weekday() == 2]
            dias.append(min(quartas, key=lambda q: abs((q - d15).days)).date())
    return dias


def ajustar_vencimentos(df: pd.DataFrame, dias) -> tuple[pd.DataFrame, list]:
    """Coluna `deslocamento` (pontos a somar ao preço) que tira o salto da troca de contrato.

    Em cada dia de vencimento, o salto entre o último fechamento do pregão anterior e a
    primeira abertura do dia é somado a todos os candles anteriores. Usado só para desenhar
    indicadores de vários dias: as colunas de preço não mudam. O salto inclui o movimento real
    da noite, que fica descontado junto (erro pequeno, documentado)."""
    out = df.copy()
    dia = pd.to_datetime((out.ts_abertura - _BRT_MS), unit="ms").dt.date.to_numpy()
    deslocamento = np.zeros(len(out))
    saltos = []
    for d in sorted(set(dias)):
        idx = np.flatnonzero(dia == d)
        if not len(idx) or idx[0] == 0:
            continue
        i = int(idx[0])
        salto = float(out.abertura.iloc[i] - out.fechamento.iloc[i - 1])
        deslocamento[:i] += salto
        saltos.append((d, salto))
    out["deslocamento"] = deslocamento
    return out, saltos


def reamostrar(df: pd.DataFrame, minutos: int) -> pd.DataFrame:
    """Agrega somente blocos completos desde as 9h00. Lacunas não viram candles fictícios."""
    if isinstance(minutos, bool) or not isinstance(minutos, int) or minutos <= 0:
        raise ValueError("minutos precisa ser um inteiro positivo.")
    if df.empty:
        return df.copy()
    duracoes = df.ts_fechamento - df.ts_abertura + 1
    passo = int(duracoes.iloc[0])
    if passo <= 0 or not (duracoes == passo).all() or minutos * 60_000 % passo:
        raise ValueError("O intervalo de destino precisa ser múltiplo do intervalo de origem.")
    if df.ts_abertura.duplicated().any() or not df.ts_abertura.is_monotonic_increasing:
        raise ValueError("Candles precisam estar ordenados e sem duplicatas.")
    dia = (df.ts_abertura - _BRT_MS) // _DIA_MS
    minuto = ((df.ts_abertura - _BRT_MS) % _DIA_MS) // 60_000
    bloco = (minuto - 9 * 60) // minutos
    g = df.groupby([dia, bloco], sort=True)
    out = g.agg(abertura=("abertura", "first"), maxima=("maxima", "max"), minima=("minima", "min"),
                fechamento=("fechamento", "last"), volume=("volume", "sum"),
                inicio_real=("ts_abertura", "first"), fim_real=("ts_fechamento", "last"),
                quantidade=("ts_abertura", "size")).reset_index(names=["dia", "bloco"])
    out["ts_abertura"] = (out.dia * _DIA_MS + _BRT_MS + (9 * 60 + out.bloco * minutos) * 60_000).astype("int64")
    out["ts_fechamento"] = out.ts_abertura + minutos * 60_000 - 1
    completo = ((out.quantidade == minutos * 60_000 // passo) &
                (out.inicio_real == out.ts_abertura) & (out.fim_real == out.ts_fechamento))
    removidos = int((~completo).sum())
    out = out.loc[completo, ["ts_abertura", "abertura", "maxima", "minima", "fechamento", "volume", "ts_fechamento"]].reset_index(drop=True)
    out.attrs["blocos_incompletos_removidos"] = removidos
    return out


def executar_futuros(df: pd.DataFrame, sinais: np.ndarray | Callable[[int, int], int], risco: Risco = Risco(), custos: CustosFuturo | None = None,
                     mercado: Contrato = CONTRATOS["WIN"], aquecimento: int | np.ndarray = 0, inicio: int = 0) -> Resultado:
    """`sinais[i]`: +1 quer ficar comprado, -1 quer ficar vendido (ou sair, se só comprado).

    `risco.exposicao_max` é a fração do patrimônio que pode virar margem."""
    c_ = mercado
    custos = custos or CUSTOS.get(c_.nome, CustosFuturo())
    n = len(df)
    sinal_dinamico = callable(sinais)
    if not sinal_dinamico and len(sinais) != n:
        raise ValueError("Vetor de sinais com tamanho diferente dos candles.")
    ts_a = df.ts_abertura.to_numpy(np.int64)
    ts_f = df.ts_fechamento.to_numpy(np.int64)
    passo = int(ts_f[0] - ts_a[0] + 1) if n else 0
    dia_arr = (ts_a - _BRT_MS) // _DIA_MS
    seq = np.zeros(n, dtype=np.int64)
    for i in range(1, n):
        seguido = ts_a[i] - ts_a[i - 1] == passo or (c_.indicador_continuo and dia_arr[i] != dia_arr[i - 1])
        seq[i] = seq[i - 1] + 1 if seguido else 0
    valido = (seq >= np.maximum(np.asarray(aquecimento) - 1, 0)) & (np.arange(n) >= inicio)
    ultimo = np.append(dia_arr[1:] != dia_arr[:-1], True).tolist()
    minuto = (((ts_a - _BRT_MS) % _DIA_MS) // 60_000).tolist()
    O, H, L, C = (df[k].to_numpy(float).tolist() for k in ("abertura", "maxima", "minima", "fechamento"))
    S, V, Q, dia = None if sinal_dinamico else np.asarray(sinais).tolist(), valido.tolist(), seq.tolist(), dia_arr.tolist()

    vp, cl = c_.valor_ponto, custos.custo_lado
    usa_atr = risco.stop_atr is not None or risco.alvo_atr is not None
    ATR = (pd.Series(np.asarray(H) - np.asarray(L)).rolling(risco.atr_periodo).mean().tolist()
           if usa_atr else None)  # média da amplitude até o candle, inclusive
    slip = custos.slippage_ticks * c_.tick
    ambos = c_.lado == "ambos"
    saldo = float(risco.capital)
    pos = None
    pendente = 0
    ops, patr, patr_min = [], np.empty(n), np.empty(n)
    pico, dd_f, dd_m = saldo, 0.0, 0.0
    rejeitadas = bloqueadas = posicionado = 0
    dia_atual, base_dia, pnl_dia, entradas_dia = None, saldo, 0.0, 0
    perdas_seguidas = 0

    def fechar(bruto, motivo, ts, i, slip_saida):
        nonlocal saldo, pos, pnl_dia, perdas_seguidas
        lado, q = pos["lado"], pos["q"]
        fill = bruto - lado * slip_saida
        pnl = lado * (fill - pos["entrada"]) * vp * q - 2 * cl * q
        saldo += pnl
        pnl_dia += pnl
        perdas_seguidas = perdas_seguidas + 1 if pnl < 0 else 0
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
        if usa_atr:
            atr = ATR[i - 1] if i >= 1 else float("nan")  # conhecida no fechamento do candle do sinal
            if not math.isfinite(atr) or atr <= 0:
                rejeitadas += 1
                return
            if risco.stop_atr is not None:
                stop = c_.arredonda(entrada - lado * risco.stop_atr * atr)
            if risco.alvo_atr is not None:
                alvo = c_.arredonda(entrada + lado * risco.alvo_atr * atr)
        if (stop is not None and lado * (entrada - stop) <= 0) or \
           (alvo is not None and lado * (alvo - entrada) <= 0):
            rejeitadas += 1
            return
        q = math.floor(saldo * risco.exposicao_max / c_.margem + 1e-9)
        if risco.martingale:  # ignora o risco por operação: é exatamente o que o martingale faz
            q = min(q, 2 ** perdas_seguidas)
        elif stop is not None:
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

    def liquidacao(preco):
        if pos is None:
            return saldo
        return saldo + (pos["lado"] * (preco - pos["lado"] * slip - pos["entrada"]) * vp - 2 * cl) * pos["q"]

    for i in range(n):
        if dia[i] != dia_atual:
            dia_atual, base_dia, pnl_dia, entradas_dia = dia[i], (patr[i - 1] if i else saldo), 0.0, 0
        o, h, l, c = O[i], H[i], L[i], C[i]
        minimo_candle = liquidacao(o)
        exposto = pos is not None

        if pos is not None and minuto[i] >= c_.zeragem:
            fechar(o, "zeragem", int(ts_a[i]), i, slip)
            pendente = 0
        if pendente in (COMPRAR, VENDER):
            if pos is not None and pos["lado"] != pendente:
                fechar(o, "sinal", int(ts_a[i]), i, slip)
            if pos is None and Q[i] > 0 and minuto[i] < min(c_.ultima_entrada, c_.zeragem):
                abrir(pendente, o, i)
                exposto |= pos is not None
        elif pendente == SAIR and pos is not None:
            fechar(o, "sinal", int(ts_a[i]), i, slip)
        pendente = 0

        if pos is not None:
            lado = pos["lado"]
            if pos["stop"] is not None and (l <= pos["stop"] if lado == 1 else h >= pos["stop"]):
                bruto = min(o, pos["stop"]) if lado == 1 else max(o, pos["stop"])
                minimo_candle = min(minimo_candle, liquidacao(bruto))
                fechar(bruto, "stop", int(ts_f[i]), i, slip)
            else:
                minimo_candle = min(minimo_candle, liquidacao(l if lado == 1 else h))
                if pos["alvo"] is not None and (h >= pos["alvo"] if lado == 1 else l <= pos["alvo"]):
                    fechar(pos["alvo"], "alvo", int(ts_f[i]), i, 0.0)
        if pos is not None and ultimo[i]:
            fechar(c, "fim do dia", int(ts_f[i]), i, slip)

        if pos is not None:
            valor = liquidacao(c)
        else:
            valor = saldo
        posicionado += int(exposto)
        minimo = min(minimo_candle, valor)
        patr[i], patr_min[i] = valor, minimo
        dd_m = max(dd_m, (pico - minimo) / pico)
        pico = max(pico, valor)
        dd_f = max(dd_f, (pico - valor) / pico)

        if V[i] and not ultimo[i]:
            atual = pos["lado"] if pos is not None else 0
            s = sinais(i, atual) if sinal_dinamico else S[i]
            if s == 1 and atual != 1:
                pendente = COMPRAR
            elif s == -1 and atual != -1:
                pendente = VENDER if ambos else (SAIR if atual == 1 else 0)
            elif (s == SAIR and atual != 0) or (s == SAIR_COMPRADO and atual == 1) or \
                 (s == SAIR_VENDIDO and atual == -1):
                pendente = SAIR

    return Resultado(
        operacoes=pd.DataFrame(ops, columns=_COLS_OPS + ["lado"]),
        ts=ts_f, patrimonio=patr, patrimonio_minimo=patr_min,
        capital_inicial=float(risco.capital), capital_final=saldo,
        drawdown_fechamento=dd_f, drawdown_minimo=dd_m,
        rejeitadas_filtro=rejeitadas, bloqueadas_risco=bloqueadas,
        candles_posicionado=posicionado, candles_operaveis=int(valido.sum()),
        risco=risco, custos=custos, sinais_validos=valido,
    )
