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

from . import conferencia, dados, diario, futuros, metricas, painel, validacao
from .backtest import Risco, executar
from .estrategias import ESTRATEGIAS
from .mercado import SEM_FILTROS, Custos, Mercado
from . import __version__

RAIZ = Path(__file__).resolve().parent.parent


def _data(ts: int, brt: bool = False) -> str:
    if brt:
        return datetime.fromtimestamp(ts / 1000 - 3 * 3600, tz=timezone.utc).strftime("%Y-%m-%d %H:%M (Brasília)")
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
                 perda_diaria_max=a.perda_diaria / 100 or None, max_operacoes_dia=a.max_operacoes_dia or None,
                 max_contratos=a.max_contratos or None)


def _custos(a):
    if a.contrato:
        padrao = futuros.CUSTOS[a.contrato]
        return futuros.CustosFuturo(padrao.custo_lado if a.custo_lado is None else a.custo_lado, a.slippage_ticks)
    return Custos(taxa=a.taxa / 100, slippage=a.slippage / 100, entrada_limitada=a.entrada_limitada)


def _mercado(a):
    if a.contrato:
        return futuros.com_lado(futuros.CONTRATOS[a.contrato], a.lado)
    return SEM_FILTROS if a.sem_filtros else Mercado()


def _nome(a) -> str:
    return a.contrato or a.simbolo


def _moeda(a) -> str:
    return "R$" if a.contrato else "USDT"


def _carregar_b3(a):
    arquivo = Path(a.arquivo) if a.arquivo else Path(a.pasta) / "B3" / f"{a.contrato}_N_M5.csv"
    conf = None
    if getattr(a, "usar_reserva", False):
        # Caminho explícito de confirmação final já existente; não usado no desenvolvimento.
        df, rel = futuros.carregar_mt5(arquivo)
    else:
        df, rel, conf = conferencia.conferir_b3(
            arquivo, a.contrato, getattr(a, "origem", "MT5 (origem não verificada)"),
            criterios=getattr(a, "criterios", conferencia.CRITERIOS),
            de=f"{a.de}-01" if getattr(a, "de", None) else None,
            ate=str(pd.Period(a.ate, "M").end_time.date()) if getattr(a, "ate", None) else None,
            exigir_extremos=False)
        if not conf["liberado_para_teste_dos_dados"]:
            raise ValueError("Histórico B3 bloqueado: " + " ".join(conf["erros"]) +
                             " Use conferir-b3 para gravar o diagnóstico.")
    minutos = dados.PASSO_MS[a.intervalo] // 60_000
    if minutos < 5:
        sys.exit("O histórico da B3 está em candles de 5 minutos; use --intervalo 5m ou maior.")
    if minutos > 5:
        df = futuros.reamostrar(df, minutos)
        removidos = df.attrs.get("blocos_incompletos_removidos", 0)
        if removidos:
            print(f"B3: {removidos} blocos incompletos removidos na agregação; lacunas preservadas.")
    if conf is not None:
        df.attrs["conferencia_dados"] = conf
    return df, rel


def _carregar(a):
    df, rel = _carregar_b3(a) if a.contrato else dados.carregar(a.pasta, a.simbolo, a.intervalo)
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


def _tabela(titulo: str, m: dict, moeda: str = "USDT"):
    print(f"\n{titulo}")
    linhas = [
        ("Operações", _fmt(m["operacoes"])),
        ("Taxa de acerto", f"{_fmt(m['taxa_acerto_pct'], 1)} %"),
        ("Fator de lucro", _fmt(m["fator_lucro"])),
        ("Expectativa / operação", f"{_fmt(m['expectativa'], 3)} {moeda} ({_fmt(m['expectativa_pct'], 3)} % {'do patrimônio' if moeda == 'R$' else 'da posição'})"),
        ("Ganho médio / perda média", f"{_fmt(m['ganho_medio'], 3)} / {_fmt(m['perda_media'], 3)} {moeda}"),
        ("Resultado líquido", f"{_fmt(m['resultado_liquido'])} {moeda} ({_fmt(m['retorno_pct'], 2)} %)"),
        ("Resultado antes dos custos", f"{_fmt(m['resultado_bruto'])} {moeda}"),
        ("Custos pagos (taxa + slippage)", f"{_fmt(m['custos_totais'])} {moeda}"),
        ("Drawdown (fechamento / intra-candle)", f"{_fmt(m['drawdown_fechamento_pct'])} % / {_fmt(m['drawdown_minimo_pct'])} %"),
        ("Tempo posicionado", f"{_fmt(m['tempo_posicionado_pct'], 1)} %"),
        ("Maior sequência de perdas", _fmt(m["maior_sequencia_perdas"])),
        ("Operações por mês", _fmt(m["operacoes_por_mes"], 1)),
        ("Saídas por motivo", ", ".join(f"{k}: {v}" for k, v in m["por_motivo"].items()) or "—"),
    ]
    if m["nao_executadas"]:
        linhas.append(("Ordens limitadas não executadas", _fmt(m["nao_executadas"])))
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
    if a.contrato:
        df, rel = _carregar_b3(a)
        print(f"{a.contrato} {a.intervalo}: {_fmt(len(df))} candles em {rel.pregoes} pregões, de "
              f"{_data(df.ts_abertura.iloc[0], True)} a {_data(df.ts_fechamento.iloc[-1], True)}")
        print(f"Duplicatas idênticas removidas: {rel.duplicatas_removidas} | pausas dentro do pregão: {len(rel.pausas)}")
        for ts, minutos in rel.pausas[:20]:
            print(f"  retoma em {_data(ts, True)} depois de {minutos} min sem negócio")
        return
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
    mercado = _mercado(a)
    r = validacao._exec(mercado)(df, e.sinais(df, **p), _risco(a), _custos(a), mercado, e.aquecimento(p))
    print(f"{e.descricao} {p}  |  {_data(df.ts_abertura.iloc[0])} a {_data(df.ts_fechamento.iloc[-1])}")
    _tabela("Backtest no período inteiro (DENTRO da amostra: descreve o passado, não valida nada)", metricas.calcular(r),
           _moeda(a))


def cmd_validar(a):
    e = ESTRATEGIAS[a.estrategia]
    df, rel = _carregar(a)
    risco, custos, mercado = _risco(a), _custos(a), _mercado(a)
    crit = tomllib.loads(Path(a.criterios).read_text())
    print(f"{e.descricao}: {len(e.combinacoes())} combinações | treino {a.treino} meses, teste {a.teste} | "
          f"{_fmt(len(df))} candles, {len(getattr(rel, 'lacunas', getattr(rel, 'pausas', [])))} lacunas")
    wf = validacao.walk_forward(df, e, risco, custos, mercado, a.treino, a.teste, a.objetivo, a.min_operacoes_treino,
                                continuo=a.continuo)
    inicio = int(np.searchsorted(df.ts_abertura.to_numpy(), wf.inicio_teste_ts))
    m = metricas.calcular(wf.resultado)
    mc = validacao.aleatorio_monte_carlo(df, wf.resultado, n=a.aleatorias, mercado=mercado, inicio=inicio)
    bh = metricas.calcular(validacao.comprar_e_segurar(df, risco, custos, mercado, inicio=inicio))
    print(f"\nJanelas (parâmetros escolhidos só com o treino; resultado no teste):")
    for j in wf.janelas:
        print(f"  {_data(j.teste_inicio_ts)[:7]}  {str(j.parametros or 'nenhum combo com operações suficientes'):<34}"
              f" {j.operacoes:>4} ops  {_fmt(j.capital_final - j.capital_inicial):>8} {_moeda(a)}")
    _tabela(f"FORA DA AMOSTRA ({_data(wf.inicio_teste_ts)[:10]} em diante) — é este que vale", m, _moeda(a))
    print(f"\nLinhas de base no mesmo período:")
    if a.contrato:
        print(f"  Comprar na abertura e zerar no fim (mesmo stop e risco): {_fmt(bh['retorno_pct'])} %")
    else:
        print(f"  Comprar e segurar (mesma exposição de {_fmt(risco.exposicao_max * 100, 0)} %): {_fmt(bh['retorno_pct'])} %")
    print(f"  Entradas aleatórias ({a.aleatorias} rodadas): mediana {_fmt(float(np.median(mc.resultados)))} %, "
          f"estratégia {_fmt(mc.referencia)} % -> supera {_fmt(mc.percentil, 1)} % delas")
    if a.contrato:
        pico_anterior = np.maximum.accumulate(np.r_[wf.resultado.capital_inicial, wf.resultado.patrimonio])[:-1]
        pior = float(np.max(pico_anterior - wf.resultado.patrimonio_minimo, initial=0))
        print(f"  Pior queda em reais: R$ {_fmt(pior)} -> capital para ela caber em "
              f"{_fmt(crit.get('drawdown_max_pct', 10), 0)} %: R$ {_fmt(pior / crit.get('drawdown_max_pct', 10) * 100)}")
    v = validacao.avaliar(m, mc.percentil, crit)
    print(f"\nCritérios fixados em {Path(a.criterios).name}:")
    for i in v.itens:
        print(f"  [{'ok' if i.passou else 'X '}] {i.texto}: {_fmt(i.valor)} (exigido {_fmt(i.limite)})")
    print(f"\nVEREDITO: {'APROVADA para testar em papel ao vivo' if v.aprovado else 'REPROVADA — não use com dinheiro'}")
    saida = Path(a.saida) / f"validacao-{_nome(a)}-{a.intervalo}-{e.nome}{'-' + a.lado if a.contrato else ''}{'-limitada' if getattr(custos, 'entrada_limitada', False) else ''}-{datetime.now():%Y%m%d-%H%M%S-%f}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps({
        "versao_motor": __version__,
        "conferencia_dados": df.attrs.get("conferencia_dados"),
        "estrategia": e.nome, "simbolo": _nome(a), "intervalo": a.intervalo, "continuo": a.continuo,
        "moeda": _moeda(a), "lado": a.lado if a.contrato else "comprado",
        "risco": risco.__dict__, "custos": custos.__dict__, "criterios": crit,
        "janelas": [j.__dict__ for j in wf.janelas], "metricas_fora_da_amostra": m,
        "comprar_e_segurar": bh, "aleatorias": {"percentil": mc.percentil, "retornos_pct": mc.resultados.tolist()},
        "veredito": {"aprovado": v.aprovado, "itens": [i.__dict__ for i in v.itens]},
        "operacoes": wf.operacoes.to_dict(orient="records"),
    }, ensure_ascii=False, indent=1, default=float))
    print(f"Relatório completo: {saida}")


def cmd_agregar(a):
    rels = [json.loads(Path(f).read_text()) for f in a.relatorios]
    crit = tomllib.loads(Path(a.criterios).read_text())
    m, v = validacao.agregar(rels, crit)
    print("Ativos: " + ", ".join(f"{r['simbolo']} {r['intervalo']} ({len(r['operacoes'])} ops)" for r in rels))
    print(f"Operações somadas: {m['operacoes']} | fator de lucro {_fmt(m['fator_lucro'])} | "
          f"expectativa {_fmt(m['expectativa'], 3)} {rels[0].get('moeda', 'USDT')} | "
          f"resultado {_fmt(m['resultado_liquido'])} {rels[0].get('moeda', 'USDT')}")
    print(f"Pior drawdown {_fmt(m['drawdown_minimo_pct'])} % | pior percentil contra o aleatório {_fmt(m['percentil'], 1)} %")
    for i in v.itens:
        print(f"  [{'ok' if i.passou else 'X '}] {i.texto}: {_fmt(i.valor)} (exigido {_fmt(i.limite)})")
    print(f"\nVEREDITO CONJUNTO: {'APROVADA para o período reservado' if v.aprovado else 'REPROVADA — não use com dinheiro'}")


def cmd_painel(a):
    if a.contrato:
        sys.exit("A exportação para o painel do TradeLab só vale para a Binance.")
    df, _ = _carregar(a)
    j = painel.para_tradelab(df, a.simbolo, a.intervalo, risco=_risco(a), custos=_custos(a))
    saida = Path(a.saida) / f"tradelab-{a.simbolo}-{a.intervalo}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(j))
    print(f"{len(j['candles'])} candles contínuos em {saida} (use 'Importar JSON' no TradeLab)")


def cmd_conferir_b3(a):
    _, _, conf = conferencia.conferir_b3(Path(a.arquivo), a.contrato, a.origem,
                                        criterios=Path(a.criterios), de=a.de, ate=a.ate)
    destino = Path(a.saida) / f"conferencia-{a.contrato}-{datetime.now(conferencia.BRT):%Y%m%d-%H%M%S-%f}.json"
    diario.salvar_json(destino, conf)
    print(f"Conferência: {destino}")
    print(f"SHA-256: {conf['sha256_arquivo']}")
    print(f"Candles de desenvolvimento: {conf['qualidade']['candles']}; reserva excluída.")
    if not conf["liberado_para_teste_dos_dados"]:
        print("BLOQUEADO: " + " ".join(conf["erros"]))
        raise SystemExit(2)
    print("Dados passaram nas verificações disponíveis; isso não aprova uma estratégia.")


def cmd_diario_b3(a):
    rel = diario.analisar(Path(a.arquivo), criterios=Path(a.criterios))
    pasta = Path(a.saida)
    diario.salvar_json(pasta / "diario.json", rel)
    diario.salvar_html(pasta / "diario.html", rel)
    print(f"{rel['resumo']['operacoes']} operações encerradas no simulador.")
    print(f"Resultado líquido: R$ {_fmt(rel['resumo']['resultado_liquido'])}")
    print(f"Relatório para abrir no navegador: {pasta / 'diario.html'}")
    print(f"Registro completo: {pasta / 'diario.json'}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m motor", description="Motor de pesquisa do TradeLab")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def base(p):
        p.add_argument("--simbolo", default="BTCUSDT")
        p.add_argument("--intervalo", default="15m", choices=sorted(dados.PASSO_MS))
        p.add_argument("--pasta", default=str(RAIZ / "dados"))
        p.add_argument("--contrato", choices=sorted(futuros.CONTRATOS), help="minicontrato da B3 (usa o CSV do MT5)")
        p.add_argument("--arquivo", help="CSV do MT5 (padrão: dados/B3/<CONTRATO>_N_M5.csv)")

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
        g.add_argument("--entrada-limitada", action="store_true",
                       help="entra por ordem limitada no fechamento do sinal (sem slippage, pode não executar)")
        g.add_argument("--lado", default="comprado", choices=["comprado", "ambos"], help="B3: só comprado ou também vendido")
        g.add_argument("--custo-lado", type=float, default=None, help="B3: R$ por contrato em cada lado (padrão do contrato)")
        g.add_argument("--max-contratos", type=int, default=0, help="B3: teto de contratos por operação (0 = sem teto)")
        g.add_argument("--slippage-ticks", type=int, default=1, help="B3: ticks contra você em cada execução a mercado")
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

    p = sub.add_parser("conferir-b3", help="conferência M5 com SHA-256 e bloqueio da reserva")
    p.add_argument("--arquivo", required=True, help="CSV tabulado de barras M5 exportado pelo MT5")
    p.add_argument("--contrato", required=True, choices=sorted(futuros.CONTRATOS))
    p.add_argument("--origem", required=True, help="origem declarada do arquivo; não informe credenciais")
    p.add_argument("--criterios", default=str(conferencia.CRITERIOS))
    p.add_argument("--de", help="primeira data exigida no arquivo, AAAA-MM-DD")
    p.add_argument("--ate", help="última data exigida no arquivo, AAAA-MM-DD")
    p.add_argument("--saida", default=str(RAIZ / "resultados" / "conferencia"))
    p.set_defaults(f=cmd_conferir_b3)

    p = sub.add_parser("diario-b3", help="CSV normalizado do simulador → JSON e relatório HTML")
    p.add_argument("--arquivo", required=True, help="CSV separado por ;, no modelo b3/diario-modelo.csv")
    p.add_argument("--criterios", default=str(conferencia.CRITERIOS))
    p.add_argument("--saida", default=str(RAIZ / "resultados" / "diario"))
    p.set_defaults(f=cmd_diario_b3)

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
            p.add_argument("--continuo", action="store_true",
                           help="a posição atravessa a virada de mês (robô real), em vez de fechar no fim de cada janela")
            p.add_argument("--aleatorias", type=int, default=200)
            p.add_argument("--saida", default=str(RAIZ / "resultados"))
        p.set_defaults(f=f)

    p = sub.add_parser("agregar", help="avaliação conjunta de relatórios de vários ativos")
    p.add_argument("relatorios", nargs="+", help="arquivos JSON gerados por 'validar'")
    p.add_argument("--criterios", default=str(RAIZ / "criterios.toml"))
    p.set_defaults(f=cmd_agregar)

    p = sub.add_parser("painel", help="exporta candles para o importador do TradeLab")
    base(p)
    periodo(p)
    risco(p)
    p.add_argument("--saida", default=str(RAIZ / "resultados"))
    p.set_defaults(f=cmd_painel)

    a = ap.parse_args(argv)
    try:
        a.f(a)
    except (ValueError, OSError) as erro:
        ap.exit(2, f"Erro: {erro}\n")


if __name__ == "__main__":
    main()
