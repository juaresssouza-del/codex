"""Linha de comando: python -m motor <comando> --help"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import dados, metricas, painel, validacao
from .backtest import Risco, executar
from .estrategias import ESTRATEGIAS
from .mercado import SEM_FILTROS, Custos, Mercado

RAIZ = Path(__file__).resolve().parent.parent


def _data(ts: int) -> str:
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _fmt(v, casas=2) -> str:
    if v is None:
        return "—"
    if isinstance(v, (int, np.integer)):
        return f"{v:,}".replace(",", ".")
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _risco(a) -> Risco:
    return Risco(capital=a.capital, risco_por_trade=a.risco / 100, exposicao_max=a.exposicao / 100,
                 stop=a.stop / 100 or None, alvo=a.alvo / 100 or None,
                 perda_diaria_max=a.perda_diaria / 100 or None, max_operacoes_dia=a.max_operacoes_dia or None)


def _custos(a) -> Custos:
    return Custos(taxa=a.taxa / 100, slippage=a.slippage / 100)


def _mercado(a) -> Mercado:
    return SEM_FILTROS if a.sem_filtros else Mercado()


def _carregar(a):
    df, rel = dados.carregar(a.pasta, a.simbolo, a.intervalo)
    if a.de:
        df = df[df.ts_abertura >= pd.Period(a.de, "M").start_time.value // 1_000_000]
    if a.ate:
        df = df[df.ts_abertura < (pd.Period(a.ate, "M") + 1).start_time.value // 1_000_000]
    reserva = tomllib.loads(Path(a.criterios).read_text()).get("reserva_inicio")
    if a.usar_reserva:
        print(f"ATENÇÃO: usando o período reservado ({reserva} em diante). Isto é a confirmação final, uma vez só.")
    elif reserva:
        df = validacao.cortar_reserva(df, reserva)
        print(f"Período reservado ({reserva} em diante) fora do teste.")
    if df.empty:
        sys.exit("Nenhum candle no período pedido.")
    return df.reset_index(drop=True), rel


def _params(a, e) -> dict:
    p = dict(e.padrao)
    for item in a.param or []:
        k, v = item.split("=", 1)
        if k not in p:
            sys.exit(f"Parâmetro desconhecido para {e.nome}: {k}. Válidos: {', '.join(p)}")
        p[k] = type(p[k])(float(v)) if isinstance(p[k], int) else float(v)
    return p


def _tabela(titulo: str, m: dict):
    print(f"\n{titulo}")
    linhas = [
        ("Operações", _fmt(m["operacoes"])),
        ("Taxa de acerto", f"{_fmt(m['taxa_acerto_pct'], 1)} %"),
        ("Fator de lucro", _fmt(m["fator_lucro"])),
        ("Expectativa / operação", f"{_fmt(m['expectativa'], 3)} USDT ({_fmt(m['expectativa_pct'], 3)} % da posição)"),
        ("Ganho médio / perda média", f"{_fmt(m['ganho_medio'], 3)} / {_fmt(m['perda_media'], 3)} USDT"),
        ("Resultado líquido", f"{_fmt(m['resultado_liquido'])} USDT ({_fmt(m['retorno_pct'], 2)} %)"),
        ("Resultado antes dos custos", f"{_fmt(m['resultado_bruto'])} USDT"),
        ("Custos pagos (taxa + slippage)", f"{_fmt(m['custos_totais'])} USDT"),
        ("Drawdown (fechamento / intra-candle)", f"{_fmt(m['drawdown_fechamento_pct'])} % / {_fmt(m['drawdown_minimo_pct'])} %"),
        ("Tempo posicionado", f"{_fmt(m['tempo_posicionado_pct'], 1)} %"),
        ("Maior sequência de perdas", _fmt(m["maior_sequencia_perdas"])),
        ("Operações por mês", _fmt(m["operacoes_por_mes"], 1)),
        ("Saídas por motivo", ", ".join(f"{k}: {v}" for k, v in m["por_motivo"].items()) or "—"),
    ]
    if m["rejeitadas_filtro"] or m["bloqueadas_risco"]:
        linhas.append(("Entradas recusadas (filtro / risco)", f"{m['rejeitadas_filtro']} / {m['bloqueadas_risco']}"))
    largura = max(len(k) for k, _ in linhas)
    for k, v in linhas:
        print(f"  {k:<{largura}}  {v}")


def cmd_baixar(a):
    ate = date.fromisoformat(a.diarios_ate) if a.diarios_ate else None
    arquivos = dados.baixar(a.simbolo, a.intervalo, a.de, a.ate, a.pasta, diarios_ate=ate)
    print(f"{len(arquivos)} arquivos conferidos por SHA-256 em {Path(a.pasta) / a.simbolo / a.intervalo}")


def cmd_dados(a):
    df, rel = dados.carregar(a.pasta, a.simbolo, a.intervalo)
    print(f"{a.simbolo} {a.intervalo}: {_fmt(rel.candles)} candles, de {_data(df.ts_abertura.iloc[0])} "
          f"a {_data(df.ts_fechamento.iloc[-1])}")
    print(f"Duplicatas idênticas removidas: {rel.duplicatas_removidas} | candles parciais (parada da corretora) removidos: {rel.parciais_removidos}")
    print(f"Lacunas: {len(rel.lacunas)} ({_fmt(rel.candles_faltando)} candles faltando)")
    mv = dados.movimento(df)
    print(f"Candle típico: amplitude {_fmt(mv['amplitude_mediana_pct'], 3)} %, corpo {_fmt(mv['corpo_mediano_pct'], 3)} % "
          f"(uma operação completa custa ~0,3 %)")
    for l in rel.lacunas[:20]:
        print(f"  depois de {_data(l.depois_de_ts)} -> retoma {_data(l.retoma_em_ts)} ({l.candles_faltando} candles)")


def cmd_backtest(a):
    e = ESTRATEGIAS[a.estrategia]
    p = _params(a, e)
    df, _ = _carregar(a)
    r = executar(df, e.sinais(df, **p), _risco(a), _custos(a), _mercado(a), e.aquecimento(p))
    print(f"{e.descricao} {p}  |  {_data(df.ts_abertura.iloc[0])} a {_data(df.ts_fechamento.iloc[-1])}")
    _tabela("Backtest no período inteiro (DENTRO da amostra: descreve o passado, não valida nada)", metricas.calcular(r))


def cmd_validar(a):
    e = ESTRATEGIAS[a.estrategia]
    df, rel = _carregar(a)
    risco, custos, mercado = _risco(a), _custos(a), _mercado(a)
    crit = tomllib.loads(Path(a.criterios).read_text())
    print(f"{e.descricao}: {len(e.combinacoes())} combinações | treino {a.treino} meses, teste {a.teste} | "
          f"{_fmt(len(df))} candles, {len(rel.lacunas)} lacunas")
    wf = validacao.walk_forward(df, e, risco, custos, mercado, a.treino, a.teste, a.objetivo, a.min_operacoes_treino)
    inicio = int(np.searchsorted(df.ts_abertura.to_numpy(), wf.inicio_teste_ts))
    m = metricas.calcular(wf.resultado)
    mc = validacao.aleatorio_monte_carlo(df, wf.resultado, n=a.aleatorias, mercado=mercado, inicio=inicio)
    bh = metricas.calcular(validacao.comprar_e_segurar(df, risco, custos, mercado, inicio=inicio))
    print(f"\nJanelas (parâmetros escolhidos só com o treino; resultado no teste):")
    for j in wf.janelas:
        print(f"  {_data(j.teste_inicio_ts)[:7]}  {str(j.parametros or 'nenhum combo com operações suficientes'):<34}"
              f" {j.operacoes:>4} ops  {_fmt(j.capital_final - j.capital_inicial):>8} USDT")
    _tabela(f"FORA DA AMOSTRA ({_data(wf.inicio_teste_ts)[:10]} em diante) — é este que vale", m)
    print(f"\nLinhas de base no mesmo período:")
    print(f"  Comprar e segurar (mesma exposição de {_fmt(risco.exposicao_max * 100, 0)} %): {_fmt(bh['retorno_pct'])} %")
    print(f"  Entradas aleatórias ({a.aleatorias} rodadas): mediana {_fmt(float(np.median(mc.resultados)))} %, "
          f"estratégia {_fmt(mc.referencia)} % -> supera {_fmt(mc.percentil, 1)} % delas")
    v = validacao.avaliar(m, mc.percentil, crit)
    print(f"\nCritérios fixados em {Path(a.criterios).name}:")
    for i in v.itens:
        print(f"  [{'ok' if i.passou else 'X '}] {i.texto}: {_fmt(i.valor)} (exigido {_fmt(i.limite)})")
    print(f"\nVEREDITO: {'APROVADA para testar em papel ao vivo' if v.aprovado else 'REPROVADA — não use com dinheiro'}")
    saida = Path(a.saida) / f"validacao-{a.simbolo}-{a.intervalo}-{e.nome}-{datetime.now():%Y%m%d-%H%M%S}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps({
        "estrategia": e.nome, "simbolo": a.simbolo, "intervalo": a.intervalo,
        "risco": risco.__dict__, "custos": custos.__dict__, "criterios": crit,
        "janelas": [j.__dict__ for j in wf.janelas], "metricas_fora_da_amostra": m,
        "comprar_e_segurar": bh, "aleatorias": {"percentil": mc.percentil, "retornos_pct": mc.resultados.tolist()},
        "veredito": {"aprovado": v.aprovado, "itens": [i.__dict__ for i in v.itens]},
        "operacoes": wf.operacoes.to_dict(orient="records"),
    }, ensure_ascii=False, indent=1, default=float))
    print(f"Relatório completo: {saida}")


def cmd_painel(a):
    df, _ = _carregar(a)
    j = painel.para_tradelab(df, a.simbolo, a.intervalo, risco=_risco(a), custos=_custos(a))
    saida = Path(a.saida) / f"tradelab-{a.simbolo}-{a.intervalo}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(j))
    print(f"{len(j['candles'])} candles contínuos em {saida} (use 'Importar JSON' no TradeLab)")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m motor", description="Motor de pesquisa do TradeLab")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def base(p):
        p.add_argument("--simbolo", default="BTCUSDT")
        p.add_argument("--intervalo", default="15m", choices=sorted(dados.PASSO_MS))
        p.add_argument("--pasta", default=str(RAIZ / "dados"))

    def periodo(p):
        p.add_argument("--de", help="AAAA-MM (opcional)")
        p.add_argument("--ate", help="AAAA-MM (opcional)")

    def risco(p):
        p.add_argument("--criterios", default=str(RAIZ / "criterios.toml"))
        p.add_argument("--usar-reserva", action="store_true", help="inclui o período reservado (confirmação final)")
        g = p.add_argument_group("risco e custos (em %)")
        g.add_argument("--capital", type=float, default=1000)
        g.add_argument("--risco", type=float, default=0.25, help="perda no stop, %% do caixa")
        g.add_argument("--exposicao", type=float, default=10, help="tamanho máximo da posição, %% do caixa")
        g.add_argument("--stop", type=float, default=1, help="0 = sem stop")
        g.add_argument("--alvo", type=float, default=2, help="0 = sem alvo")
        g.add_argument("--perda-diaria", type=float, default=0, help="0 = sem limite")
        g.add_argument("--max-operacoes-dia", type=int, default=0, help="0 = sem limite")
        g.add_argument("--taxa", type=float, default=0.1)
        g.add_argument("--slippage", type=float, default=0.05)
        g.add_argument("--sem-filtros", action="store_true", help="ignora lote/notional mínimos (modo TradeLab)")

    p = sub.add_parser("baixar", help="baixa o histórico público e confere o SHA-256")
    base(p)
    p.add_argument("--de", required=True, help="primeiro mês, AAAA-MM")
    p.add_argument("--ate", required=True, help="último mês fechado, AAAA-MM")
    p.add_argument("--diarios-ate", help="AAAA-MM-DD: também baixa os dias do mês corrente")
    p.set_defaults(f=cmd_baixar)

    p = sub.add_parser("dados", help="relatório de qualidade do histórico")
    base(p)
    p.set_defaults(f=cmd_dados)

    for nome, f, ajuda in (("backtest", cmd_backtest, "uma rodada no período todo (descritivo)"),
                           ("validar", cmd_validar, "walk-forward + linhas de base + critérios")):
        p = sub.add_parser(nome, help=ajuda)
        base(p)
        periodo(p)
        risco(p)
        p.add_argument("--estrategia", default="sma", choices=sorted(ESTRATEGIAS))
        if nome == "backtest":
            p.add_argument("--param", action="append", help="nome=valor, ex.: --param rapida=9")
        else:
            p.add_argument("--treino", type=int, default=6, help="meses de treino por janela")
            p.add_argument("--teste", type=int, default=1, help="meses de teste por janela")
            p.add_argument("--objetivo", default="resultado_liquido", choices=["resultado_liquido", "expectativa"])
            p.add_argument("--min-operacoes-treino", type=int, default=30)
            p.add_argument("--aleatorias", type=int, default=200)
            p.add_argument("--saida", default=str(RAIZ / "resultados"))
        p.set_defaults(f=f)

    p = sub.add_parser("painel", help="exporta candles para o importador do TradeLab")
    base(p)
    periodo(p)
    risco(p)
    p.add_argument("--saida", default=str(RAIZ / "resultados"))
    p.set_defaults(f=cmd_painel)

    a = ap.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
