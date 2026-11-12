"""Diário passivo de operações encerradas no simulador. Não envia ordens.

Os preços executados já incluem o efeito do slippage: não descontá-lo duas vezes.
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import math
import os
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from . import __version__, futuros
from .conferencia import BRT, CRITERIOS, fim_reserva, inicio_reserva

COLUNAS = ["id", "ambiente", "contrato", "lado", "quantidade", "entrada", "saida",
           "preco_entrada_previsto", "preco_saida_previsto", "preco_entrada_executado",
           "preco_saida_executado", "taxas_previstas", "taxas_executadas", "stop", "alvo",
           "hipotese", "motivo_entrada", "motivo_saida", "origem"]


def _numero(texto: str, campo: str, *, positivo: bool = False) -> Decimal:
    try:
        n = Decimal(texto.strip().replace(",", "."))
    except (InvalidOperation, AttributeError) as erro:
        raise ValueError(f"{campo}: número ausente ou inválido; não foi estimado.") from erro
    if not n.is_finite() or n < 0 or (positivo and n == 0):
        raise ValueError(f"{campo}: número precisa ser finito e {'positivo' if positivo else 'não negativo'}.")
    return n


def _hora(texto: str) -> datetime:
    try:
        d = datetime.fromisoformat(texto)
    except (ValueError, TypeError) as erro:
        raise ValueError("Data/hora inválida; use AAAA-MM-DD HH:MM:SS, horário de Brasília.") from erro
    return d.replace(tzinfo=BRT) if d.tzinfo is None else d.astimezone(BRT)


def _brl(n: Decimal) -> float:
    valor = float(n.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    if not math.isfinite(valor):
        raise ValueError("Valor monetário fora do intervalo suportado.")
    return valor


def analisar(arquivo: Path, *, criterios: Path = CRITERIOS) -> dict:
    """Lê o CSV normalizado de operações completas, sem integração com corretora.

    Cada id é único. Campos ausentes geram erro; taxas não são presumidas zero.
    Nesta etapa o diário também se restringe às datas anteriores à reserva.
    """
    reserva = inicio_reserva(criterios)
    fim = fim_reserva(criterios)
    na_reserva = lambda h: h >= reserva and (fim is None or h < fim)
    registros, vistos = [], set()
    bruto = Path(arquivo).read_bytes()
    with io.StringIO(bruto.decode("utf-8-sig"), newline="") as arq:
        leitor = csv.DictReader(arq, delimiter=";")
        if not set(COLUNAS) <= set(leitor.fieldnames or []):
            raise ValueError("CSV do diário inválido; use o modelo separado por ponto e vírgula.")
        for numero, linha in enumerate(leitor, 2):
            try:
                if None in linha or any(linha.get(c) is None for c in COLUNAS):
                    raise ValueError("Quantidade de colunas inválida.")
                identificador = linha["id"].strip()
                if not identificador or identificador in vistos:
                    raise ValueError("id ausente ou repetido; operação não pode ser contada duas vezes.")
                if linha["ambiente"].strip().lower() != "simulador":
                    raise ValueError("Este diário aceita somente ambiente=simulador.")
                contrato = linha["contrato"].strip().upper()
                if contrato not in futuros.CONTRATOS:
                    raise ValueError("Contrato precisa ser WIN ou WDO.")
                lado = linha["lado"].strip().lower()
                if lado not in ("comprado", "vendido"):
                    raise ValueError("Lado precisa ser comprado ou vendido.")
                q = _numero(linha["quantidade"], "quantidade", positivo=True)
                if q != q.to_integral_value():
                    raise ValueError("Quantidade de contratos precisa ser inteira.")
                entrada, saida = _hora(linha["entrada"]), _hora(linha["saida"])
                if na_reserva(entrada) or na_reserva(saida):
                    raise ValueError("Operação intercepta o período reservado; importação bloqueada.")
                if saida < entrada or saida.date() != entrada.date():
                    raise ValueError("Saída precisa ocorrer após a entrada e no mesmo pregão.")
                for campo in ("hipotese", "motivo_entrada", "motivo_saida", "origem"):
                    if not linha[campo].strip():
                        raise ValueError(f"{campo} precisa ser informado.")
                c = futuros.CONTRATOS[contrato]
                vp, tick = Decimal(str(c.valor_ponto)), Decimal(str(c.tick))
                precos = {}
                for campo in ("preco_entrada_previsto", "preco_saida_previsto", "preco_entrada_executado",
                              "preco_saida_executado", "stop", "alvo"):
                    p = _numero(linha[campo], campo, positivo=True) if linha[campo].strip() else None
                    if p is None and campo.startswith("preco_"):
                        raise ValueError(f"{campo} ausente; não foi estimado.")
                    # Fills agregados podem ter preço médio entre ticks (ex.: 2 contratos).
                    media_executada = campo.endswith("_executado") and q > 1
                    if p is not None and not media_executada and p % tick:
                        raise ValueError(f"{campo}: preço fora do tick de {contrato}.")
                    precos[campo] = p
                taxas_p = _numero(linha["taxas_previstas"], "taxas_previstas")
                taxas_e = _numero(linha["taxas_executadas"], "taxas_executadas")
                sinal = 1 if lado == "comprado" else -1
                ep, sp = precos["preco_entrada_previsto"], precos["preco_saida_previsto"]
                ee, se = precos["preco_entrada_executado"], precos["preco_saida_executado"]
                bruto_p, bruto_e = sinal * (sp - ep) * vp * q, sinal * (se - ee) * vp * q
                desvio_entrada, desvio_saida = sinal * (ee - ep) / tick, sinal * (sp - se) / tick
                registros.append({
                    **{k: linha[k].strip() for k in ("hipotese", "motivo_entrada", "motivo_saida", "origem")},
                    "id": identificador, "contrato": contrato, "lado": lado, "quantidade": int(q),
                    "entrada": entrada.isoformat(), "saida": saida.isoformat(),
                    **{k: float(v) if v is not None else None for k, v in precos.items()},
                    "taxas_previstas": _brl(taxas_p), "taxas_executadas": _brl(taxas_e),
                    "resultado_previsto": _brl(bruto_p - taxas_p), "resultado_bruto_executado": _brl(bruto_e),
                    "resultado_liquido": _brl(bruto_e - taxas_e),
                    "desvio_entrada_ticks": float(desvio_entrada), "desvio_saida_ticks": float(desvio_saida),
                    "impacto_execucao_brl": _brl(bruto_p - bruto_e),
                    "diferenca_liquido": _brl((bruto_e - taxas_e) - (bruto_p - taxas_p)),
                })
                vistos.add(identificador)
            except (ValueError, InvalidOperation, OverflowError) as erro:
                raise ValueError(f"Linha {numero}: {erro}") from erro
    if not registros:
        raise ValueError("Diário sem operações encerradas.")
    registros.sort(key=lambda r: (_hora(r["saida"]), _hora(r["entrada"]), r["id"]))
    ganhos = sum(Decimal(str(r["resultado_liquido"])) for r in registros if r["resultado_liquido"] > 0)
    perdas = -sum(Decimal(str(r["resultado_liquido"])) for r in registros if r["resultado_liquido"] < 0)
    def soma(campo):
        return _brl(sum((Decimal(str(r[campo])) for r in registros), Decimal(0)))
    return {
        "tipo": "diario_simulador_b3", "versao_motor": __version__, "ambiente": "simulador", "moeda": "BRL",
        "arquivo": Path(arquivo).name, "sha256_csv": hashlib.sha256(bruto).hexdigest(),
        "gerado_em": datetime.now(tz=BRT).isoformat(),
        "reserva_inicio": reserva.isoformat(), "operacoes": registros,
        "resumo": {"operacoes": len(registros), "resultado_previsto": soma("resultado_previsto"),
                   "resultado_bruto_executado": soma("resultado_bruto_executado"),
                   "resultado_liquido": soma("resultado_liquido"), "taxas_executadas": soma("taxas_executadas"),
                   "impacto_execucao_brl": soma("impacto_execucao_brl"), "diferenca_liquido": soma("diferenca_liquido"),
                   "acerto_liquido_pct": round(100 * sum(r["resultado_liquido"] > 0 for r in registros) / len(registros), 2),
                   "fator_lucro": float(ganhos / perdas) if perdas else None},
        "limites": ["Relatório descritivo de operações encerradas: não aprova estratégias.",
                    "O diário não calcula risco de posições abertas nem drawdown intradiário.",
                    "Preços previstos devem ser referências anteriores ao fill, não ajustados depois.",
                    "Taxas são totais da operação e precisam ser informadas; ausentes não viram zero.",
                    "O impacto da execução já está nos preços; não é descontado novamente do líquido."],
    }


def salvar_json(caminho: Path, conteudo: dict) -> None:
    """Grava substituindo atomicamente; JSON financeiro nunca contém NaN/Infinity."""
    _salvar(caminho, json.dumps(conteudo, ensure_ascii=False, indent=2, allow_nan=False))


def _salvar(caminho: Path, conteudo: str) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    nome = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=caminho.parent, delete=False) as arq:
            nome = arq.name
            arq.write(conteudo)
        os.replace(nome, caminho)
    finally:
        if nome and Path(nome).exists():
            Path(nome).unlink()


def salvar_html(caminho: Path, relatorio: dict) -> None:
    def escapar(v):
        return html.escape(str(v))
    def dinheiro(v):
        return (f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    s = relatorio["resumo"]
    cards = "".join(f'<article><span>{escapar(t)}</span><strong>{escapar(v)}</strong></article>' for t, v in [
        ("Líquido no simulador", dinheiro(s["resultado_liquido"])),
        ("Referência prevista", dinheiro(s["resultado_previsto"])),
        ("Taxas informadas", dinheiro(s["taxas_executadas"])),
        ("Diferença do previsto", dinheiro(s["diferenca_liquido"]))])
    linhas = []
    for r in relatorio["operacoes"]:
        campos = [("ID", r["id"]), ("Hipótese", r["hipotese"]), ("Quantidade", r["quantidade"]),
                  ("Entrada (Brasília)", r["entrada"]), ("Saída (Brasília)", r["saida"]),
                  ("Entrada prevista / executada", f'{r["preco_entrada_previsto"]:g} / {r["preco_entrada_executado"]:g}'),
                  ("Saída prevista / executada", f'{r["preco_saida_previsto"]:g} / {r["preco_saida_executado"]:g}'),
                  ("Stop", r["stop"] if r["stop"] is not None else "não informado"),
                  ("Alvo", r["alvo"] if r["alvo"] is not None else "não informado"),
                  ("Líquido previsto", dinheiro(r["resultado_previsto"])),
                  ("Diferença do previsto", dinheiro(r["diferenca_liquido"])),
                  ("Taxas previstas / executadas", f'{dinheiro(r["taxas_previstas"])} / {dinheiro(r["taxas_executadas"])}'),
                  ("Desvio entrada / saída (ticks)", f'{r["desvio_entrada_ticks"]:g} / {r["desvio_saida_ticks"]:g}'),
                  ("Motivo da entrada", r["motivo_entrada"]), ("Motivo da saída", r["motivo_saida"]), ("Origem", r["origem"])]
        ficha = "".join(f'<div><dt>{escapar(k)}</dt><dd>{escapar(v)}</dd></div>' for k, v in campos)
        linhas.append(f'<details><summary><span>{escapar(r["contrato"])} · {escapar(r["lado"])} · {escapar(r["id"])}</span><b>{escapar(dinheiro(r["resultado_liquido"]))}</b></summary><dl>{ficha}</dl></details>')
    operacoes = "".join(linhas)
    limites = "".join(f"<li>{escapar(x)}</li>" for x in relatorio["limites"])
    _salvar(caminho, f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>TradeLab · Diário do simulador</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#101519;color:#e6ecef;font:15px system-ui,sans-serif}}main{{max-width:1200px;margin:auto;padding:28px}}header{{border-bottom:1px solid #34414a;padding-bottom:20px}}h1{{font-size:26px;margin:12px 0}}p,li{{color:#b4c2ca;line-height:1.6}}.tag{{color:#9fe1bd;font-size:12px;letter-spacing:.12em}}.cards{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:24px 0}}article{{padding:18px;background:#1a2329;border:1px solid #34414a;border-radius:8px}}article span{{display:block;color:#b4c2ca;font-size:13px}}strong{{display:block;font-size:24px;margin-top:10px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}}details{{border:1px solid #34414a;border-radius:8px;margin:10px 0;background:#151e24}}summary{{cursor:pointer;padding:18px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}}summary:hover{{background:#1a272f}}summary span,dd{{overflow-wrap:anywhere}}dl{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;margin:0;padding:20px;border-top:1px solid #34414a}}dt{{font-size:12px;color:#b4c2ca}}dd{{margin:6px 0 0}}@media(max-width:800px){{.cards{{grid-template-columns:repeat(2,minmax(0,1fr))}}main{{padding:16px}}strong{{font-size:20px}}dl{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}@media(max-width:440px){{.cards,dl{{grid-template-columns:1fr}}}}</style></head>
<body><main><header><span class="tag">TRADELAB / SIMULADOR / BRL</span><h1>Diário de operações</h1>
<p>{s["operacoes"]} operações encerradas · {s["acerto_liquido_pct"]:g}% com líquido positivo.
Conferência descritiva; nenhuma aprovação de estratégia é emitida.</p>
<p>Gerado em {escapar(relatorio["gerado_em"])} · arquivo {escapar(relatorio["arquivo"])}</p></header><section class="cards">{cards}</section>
<h2>Previsto e executado</h2><p>Abra cada operação para conferir preços, stop, alvo e motivos. No desvio em ticks, valor positivo indica execução pior que a referência; negativo indica melhora.</p>
<section>{operacoes}</section>
<h2>Como interpretar</h2><ul>{limites}</ul></main></body></html>''')
