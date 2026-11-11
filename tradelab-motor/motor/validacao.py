"""Validação: walk-forward, linhas de base e critérios fixados antes do teste.

Walk-forward: em cada janela, escolhe os parâmetros só com o passado (treino) e mede
no período seguinte, que a escolha nunca viu (teste). O resultado que vale é a soma
dos testes. Otimizar e medir no mesmo período é como a estratégia "funciona" no
histórico e quebra no dinheiro real.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import metricas
from .backtest import Resultado, Risco, executar
from .estrategias import Estrategia, aleatoria
from .futuros import CUSTOS, SAIR, Contrato, CustosFuturo, executar_futuros
from .mercado import Custos, Mercado


def _exec(mercado):
    """Futuros da B3 usam o motor por pregão; o resto, o motor de cripto."""
    return executar_futuros if isinstance(mercado, Contrato) else executar


def _custos_padrao(mercado, custos):
    if custos is not None:
        return custos
    return CUSTOS[mercado.nome] if isinstance(mercado, Contrato) else Custos()


@dataclass
class Janela:
    indice: int
    treino_inicio_ts: int
    treino_fim_ts: int
    teste_inicio_ts: int
    teste_fim_ts: int
    parametros: dict | None
    metricas_treino: dict | None
    capital_inicial: float
    capital_final: float
    operacoes: int


@dataclass
class ResultadoWF:
    estrategia: str
    janelas: list[Janela]
    resultado: Resultado  # só os períodos de teste, emendados
    operacoes: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.operacoes = self.resultado.operacoes

    @property
    def capital_final(self) -> float:
        return self.resultado.capital_final

    @property
    def inicio_teste_ts(self) -> int:
        return self.janelas[0].teste_inicio_ts


def cortar_reserva(df: pd.DataFrame, reserva: str | None) -> pd.DataFrame:
    """Tira o período reservado (do mês `reserva`, AAAA-MM, em diante). Ele só é olhado uma
    vez, no fim, para confirmar a estratégia que sobreviver; antes disso, nenhum teste o vê."""
    if not reserva:
        return df
    limite = pd.Period(reserva, "M").start_time.value // 1_000_000
    return df[df.ts_abertura < limite].reset_index(drop=True)


def _inicios_de_mes(ts: np.ndarray) -> list[int]:
    meses = pd.to_datetime(ts, unit="ms").to_period("M")
    primeiro, ultimo = meses.min(), meses.max()
    return [int(p.start_time.value // 1_000_000) for p in pd.period_range(primeiro, ultimo + 1, freq="M")]


def _emendar(partes: list[Resultado], capital_inicial: float, risco: Risco, custos: Custos) -> Resultado:
    ops = pd.concat([p.operacoes.assign(janela=k) for k, p in enumerate(partes)], ignore_index=True) \
        if partes else pd.DataFrame(columns=["janela"])
    patr = np.concatenate([p.patrimonio for p in partes]) if partes else np.array([capital_inicial])
    pmin = np.concatenate([p.patrimonio_minimo for p in partes]) if partes else patr
    pico = np.maximum.accumulate(np.concatenate([[capital_inicial], patr]))[1:]
    pico_anterior = np.maximum.accumulate(np.concatenate([[capital_inicial], patr]))[:-1]
    return Resultado(
        operacoes=ops, ts=np.concatenate([p.ts for p in partes]) if partes else np.array([0]),
        patrimonio=patr, patrimonio_minimo=pmin, capital_inicial=capital_inicial,
        capital_final=partes[-1].capital_final if partes else capital_inicial,
        drawdown_fechamento=float(np.max((pico - patr) / pico, initial=0)),
        drawdown_minimo=float(np.max((pico_anterior - pmin) / pico_anterior, initial=0)),
        rejeitadas_filtro=sum(p.rejeitadas_filtro for p in partes),
        nao_executadas=sum(p.nao_executadas for p in partes),
        bloqueadas_risco=sum(p.bloqueadas_risco for p in partes),
        candles_posicionado=sum(p.candles_posicionado for p in partes),
        candles_operaveis=sum(p.candles_operaveis for p in partes),
        risco=risco, custos=custos,
        sinais_validos=np.concatenate([p.sinais_validos for p in partes]) if partes else np.array([False]))


def walk_forward(df: pd.DataFrame, estrategia: Estrategia, risco: Risco = Risco(), custos: Custos | CustosFuturo | None = None,
                 mercado: Mercado = Mercado(), treino_meses: int = 6, teste_meses: int = 1,
                 objetivo: str = "resultado_liquido", min_operacoes_treino: int = 30,
                 continuo: bool = False) -> ResultadoWF:
    """`continuo=False`: cada mês de teste é uma rodada separada e a posição fecha no fim dele.
    `continuo=True`: uma rodada só, trocando os parâmetros a cada mês; a posição atravessa
    a virada, como faria um robô real que se reotimiza todo mês."""
    for nome, v in (("treino_meses", treino_meses), ("teste_meses", teste_meses)):
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            raise ValueError(f"{nome} precisa ser um inteiro positivo.")
    if df.empty:
        raise ValueError("Histórico vazio para walk-forward.")
    custos = _custos_padrao(mercado, custos)
    ts = df.ts_abertura.to_numpy(np.int64)
    marcos = _inicios_de_mes(ts)
    pos = lambda t: int(np.searchsorted(ts, t))
    combinacoes = estrategia.combinacoes()
    sinais_cache: dict[tuple, np.ndarray] = {}

    def sinais(params):  # sinais dependem só do passado, então calcular uma vez no histórico todo é seguro
        k = tuple(sorted(params.items()))
        if k not in sinais_cache:
            sinais_cache[k] = estrategia.sinais(df, **params)
        return sinais_cache[k]

    escolhas = []  # (t0, t1, t2, b, c, parametros, metricas do treino)
    k = 0
    while k + treino_meses < len(marcos) - 1:
        t0, t1 = marcos[k], marcos[k + treino_meses]
        t2 = marcos[min(k + treino_meses + teste_meses, len(marcos) - 1)]
        a, b, c = pos(t0), pos(t1), pos(t2)
        if c <= b:
            break
        melhor, melhor_m = None, None
        for params in combinacoes:
            r = _exec(mercado)(df.iloc[a:b], sinais(params)[a:b], risco, custos, mercado, estrategia.aquecimento(params))
            m = metricas.calcular(r)
            if m[objetivo] is None or m["operacoes"] < min_operacoes_treino:
                continue
            if melhor_m is None or m[objetivo] > melhor_m[objetivo]:
                melhor, melhor_m = params, m
        escolhas.append((t0, t1, t2, b, c, melhor, melhor_m))
        k += teste_meses
    if not escolhas:
        raise ValueError(f"Histórico curto: são necessários mais de {treino_meses + teste_meses} meses.")
    if continuo:
        return _walk_forward_continuo(df, estrategia, escolhas, sinais, risco, custos, mercado)

    janelas, partes, capital = [], [], risco.capital
    for t0, t1, t2, b, c, melhor, melhor_m in escolhas:
        inicial = capital
        if melhor is not None:
            aq = estrategia.aquecimento(melhor)
            ini = max(b - aq, 0)
            r = _exec(mercado)(df.iloc[ini:c], sinais(melhor)[ini:c], Risco(**{**risco.__dict__, "capital": capital}),
                         custos, mercado, aq, inicio=b - ini)
            corte = b - ini  # o aquecimento entra só para os indicadores, não no resultado
            r.patrimonio, r.patrimonio_minimo, r.ts = r.patrimonio[corte:], r.patrimonio_minimo[corte:], r.ts[corte:]
            r.sinais_validos = r.sinais_validos[corte:]
            partes.append(r)
            capital = r.capital_final
        else:
            # Mês sem configuração elegível é caixa parado, não um buraco no histórico.
            # O resultado vazio também precisa manter o esquema das operações.
            r = _exec(mercado)(df.iloc[b:c], np.zeros(c - b, dtype=np.int8),
                               Risco(**{**risco.__dict__, "capital": capital}), custos, mercado)
            r.sinais_validos[:] = False
            r.candles_operaveis = 0
            partes.append(r)
        janelas.append(Janela(len(janelas), t0, t1, t1, t2, melhor, melhor_m, inicial, capital,
                              len(partes[-1].operacoes) if melhor is not None else 0))
    resultado = _emendar(partes, risco.capital, risco, custos)
    return ResultadoWF(estrategia.nome, janelas, resultado)


def _walk_forward_continuo(df, estrategia, escolhas, sinais, risco, custos, mercado) -> ResultadoWF:
    b0, c_fim = escolhas[0][3], escolhas[-1][4]
    composto = np.zeros(len(df), dtype=np.int8)
    aquecimentos = np.zeros(len(df), dtype=np.int64)
    anterior = None
    for _, _, _, b, c, params, _ in escolhas:
        if params is not None:
            composto[b:c] = sinais(params)[b:c]
            aquecimentos[b:c] = estrategia.aquecimento(params)
            anterior = params
        elif anterior is not None:  # mês sem parâmetro aprovado: não entra, mas ainda sabe sair
            if isinstance(mercado, Contrato):
                composto[b:c] = SAIR  # não converter "sair" em uma nova venda a descoberto
            else:
                composto[b:c] = np.where(sinais(anterior)[b:c] == -1, -1, 0)
                aquecimentos[b:c] = estrategia.aquecimento(anterior)
    # O tamanho do prefixo vem da grade conhecida antes dos testes; cada barra usa
    # só o aquecimento escolhido naquele momento. Escolha futura não altera o passado.
    aq = max((estrategia.aquecimento(p) for p in estrategia.combinacoes()), default=0)
    ini = max(b0 - aq, 0)
    r = _exec(mercado)(df.iloc[ini:c_fim], composto[ini:c_fim], risco, custos, mercado,
                       aquecimentos[ini:c_fim], inicio=b0 - ini)
    corte = b0 - ini
    r.patrimonio, r.patrimonio_minimo, r.ts = r.patrimonio[corte:], r.patrimonio_minimo[corte:], r.ts[corte:]
    r.sinais_validos = r.sinais_validos[corte:]
    inicios = np.array([e[1] for e in escolhas], dtype=np.int64)
    r.operacoes["janela"] = np.searchsorted(inicios, r.operacoes.ts_entrada.to_numpy(np.int64), side="right") - 1
    janelas, capital = [], risco.capital
    for j, (t0, t1, t2, b, c, params, m) in enumerate(escolhas):
        final = float(r.patrimonio[c - b0 - 1])  # marcado a mercado no último candle do mês
        janelas.append(Janela(j, t0, t1, t1, t2, params, m, capital, final, int((r.operacoes.janela == j).sum())))
        capital = final
    return ResultadoWF(estrategia.nome, janelas, r)


@dataclass
class ResultadoMC:
    resultados: np.ndarray   # retorno % de cada rodada aleatória
    referencia: float        # retorno % da estratégia
    percentil: float         # % das rodadas aleatórias que a estratégia superou


def _aleatoria_futuros(n, prob_entrada, prob_saida, proporcao_comprada, semente):
    """Referência nula: entrada e encerramento distintos, consultando a posição efetiva.

    Frequência e duração são calibradas aproximadamente, não condicionadas ao lucro.
    Uma saída não vira reversão de mão; stops e zeragens continuam no mesmo executor.
    """
    u = np.random.default_rng(semente).random((n, 3))
    def sinal(i, lado):
        if lado:
            return SAIR if u[i, 1] < prob_saida else 0
        if u[i, 0] < prob_entrada:
            return 1 if u[i, 2] < proporcao_comprada else -1
        return 0
    return sinal


def aleatorio_monte_carlo(df: pd.DataFrame, ref: Resultado, n: int = 200, semente: int = 7,
                          mercado: Mercado = Mercado(), inicio: int = 0) -> ResultadoMC:
    """Entradas e saídas ao acaso, calibradas para a mesma frequência e duração média das
    operações da estratégia, com o mesmo stop, alvo, risco e custos."""
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("n precisa ser um inteiro positivo.")
    ops = ref.operacoes
    livres = max(ref.candles_operaveis - ref.candles_posicionado, 1)
    p_ent = min(max(len(ops), 1) / livres, 0.5)
    dur = float((ops.i_saida - ops.i_entrada + 1).mean()) if len(ops) else 10.0
    p_sai = min(1 / max(dur, 1), 0.5)
    elegivel = np.ones(len(df), dtype=bool)
    if ref.sinais_validos is not None:
        elegivel[:] = False
        ts_df = df.ts_fechamento.to_numpy(np.int64)
        indices = np.searchsorted(ts_df, ref.ts)
        if (indices >= len(df)).any() or not np.array_equal(ts_df[indices], ref.ts):
            raise ValueError("A referência aleatória precisa do mesmo histórico da estratégia.")
        elegivel[indices] = ref.sinais_validos
    def gerar(k):
        if isinstance(mercado, Contrato):
            prop = float((ops.lado == 1).mean()) if len(ops) else .5
            if mercado.lado == "comprado":
                prop = 1.0
            sinal = _aleatoria_futuros(len(df), p_ent, p_sai, prop, semente + k)
            return lambda i, lado: sinal(i, lado) if elegivel[i] else 0
        return np.where(elegivel, aleatoria(len(df), p_ent, p_sai, semente + k), 0)
    rodadas = np.array([
        (_exec(mercado)(df, gerar(k), ref.risco, ref.custos, mercado,
                  inicio=inicio).capital_final / ref.risco.capital - 1) * 100
        for k in range(n)])
    alvo = (ref.capital_final / ref.capital_inicial - 1) * 100
    percentil = float(((rodadas < alvo).sum() + 0.5 * (rodadas == alvo).sum()) / n * 100)
    return ResultadoMC(rodadas, alvo, percentil)


def comprar_e_segurar(df: pd.DataFrame, risco: Risco = Risco(), custos: Custos | CustosFuturo | None = None,
                      mercado: Mercado = Mercado(), inicio: int = 0) -> Resultado:
    """Compra no começo e segura até o fim, com a mesma exposição máxima e sem stop."""
    custos = _custos_padrao(mercado, custos)
    s = np.zeros(len(df), dtype=np.int8)
    if isinstance(mercado, Contrato):
        # B3: compra na abertura de cada pregão com o mesmo stop e risco, sem alvo, e zera no fim.
        # Sem stop, a margem inteira viraria posição e a linha de base mediria alavancagem, não sinal.
        dia = (df.ts_abertura.to_numpy(np.int64) - 3 * 3_600_000) // 86_400_000
        primeiro = np.append(True, dia[1:] != dia[:-1])
        s[primeiro & (np.arange(len(df)) >= inicio)] = 1
        return executar_futuros(df, s, Risco(**{**risco.__dict__, "alvo": None}), custos, mercado, inicio=inicio)
    sem_stop = Risco(**{**risco.__dict__, "stop": None, "alvo": None})
    s[inicio] = 1
    return executar(df, s, sem_stop, custos, mercado, inicio=inicio)


@dataclass(frozen=True)
class Item:
    nome: str
    valor: float | None
    limite: float
    passou: bool
    texto: str


@dataclass(frozen=True)
class Veredito:
    aprovado: bool
    itens: list[Item]


def avaliar(m: dict, percentil: float, crit: dict) -> Veredito:
    regras = [
        ("min_operacoes", m.get("operacoes"), lambda v, x: v >= x, "operações fora da amostra"),
        ("fator_lucro_min", m.get("fator_lucro"), lambda v, x: v >= x, "fator de lucro depois dos custos"),
        ("expectativa_min", m.get("expectativa"), lambda v, x: v > x, "expectativa por operação (na moeda do teste)"),
        ("drawdown_max_pct", m.get("drawdown_minimo_pct"), lambda v, x: v <= x, "drawdown máximo (%)"),
        ("percentil_aleatorio_min", percentil, lambda v, x: v >= x, "percentil contra entradas aleatórias"),
    ]
    itens = []
    for nome, valor, ok, texto in regras:
        if nome not in crit:
            continue
        passou = valor is not None and bool(np.isfinite(valor)) and bool(ok(valor, crit[nome]))
        itens.append(Item(nome, valor, crit[nome], passou, texto))
    return Veredito(all(i.passou for i in itens) and bool(itens), itens)


def agregar(relatorios: list[dict], crit: dict) -> tuple[dict, Veredito]:
    """Junta os relatórios JSON de vários ativos: soma as operações, e para drawdown e
    percentil contra o aleatório vale o pior ativo."""
    if not relatorios:
        raise ValueError("Nenhum relatório para agregar.")
    moedas = {r.get("moeda", "USDT") for r in relatorios}
    if len(moedas) != 1:
        raise ValueError("Não é possível agregar resultados de moedas diferentes.")
    pnl = np.array([o["pnl"] for r in relatorios for o in r["operacoes"]], dtype=float)
    ganho, perda = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    m = {
        "operacoes": len(pnl),
        "fator_lucro": ganho / perda if perda > 0 else None,
        "expectativa": float(pnl.mean()) if len(pnl) else None,
        "resultado_liquido": float(pnl.sum()),
        "drawdown_minimo_pct": max(r["metricas_fora_da_amostra"]["drawdown_minimo_pct"] for r in relatorios),
        "percentil": min(r["aleatorias"]["percentil"] for r in relatorios),
    }
    return m, avaliar(m, m["percentil"], crit)
