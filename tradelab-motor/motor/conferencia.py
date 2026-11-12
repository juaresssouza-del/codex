"""Conferência M5 do MT5 com procedência e recorte anterior à reserva.

Não preenche lacunas, não testa estratégias e não comprova autenticidade da fonte.
"""
from __future__ import annotations

import csv
import hashlib
import io
import tomllib
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from . import __version__, futuros

BRT = ZoneInfo("America/Sao_Paulo")
PASSO_MS = 300_000
CRITERIOS = Path(__file__).resolve().parent.parent / "criterios.toml"


def fim_reserva(criterios: Path = CRITERIOS) -> datetime | None:
    """Fim (exclusivo) da janela reservada; depois dela, só dados ao vivo. None = sem fim."""
    dia = tomllib.loads(Path(criterios).read_text(encoding="utf-8")).get("reserva_fim")
    if not dia:
        return None
    return datetime.strptime(dia, "%Y-%m-%d").replace(tzinfo=BRT) + timedelta(days=1)


def inicio_reserva(criterios: Path = CRITERIOS) -> datetime:
    mes = tomllib.loads(Path(criterios).read_text(encoding="utf-8"))["reserva_inicio"]
    return datetime.strptime(mes, "%Y-%m").replace(tzinfo=BRT)


def ler_pausas_conferidas(caminho: Path | None, contrato: str) -> dict[tuple[int, int], dict]:
    """Pausas dentro do pregão investigadas e documentadas, por (ts em que o pregão retoma, minutos).

    Cada entrada precisa de contrato, retoma ("AAAA-MM-DD HH:MM", Brasília), minutos, causa,
    fonte e situação. Só libera a pausa idêntica; qualquer outra continua bloqueando."""
    if caminho is None:
        return {}
    pausas = {}
    for p in tomllib.loads(Path(caminho).read_text(encoding="utf-8")).get("pausa", []):
        faltando = [k for k in ("contrato", "retoma", "minutos", "causa", "fonte", "situacao")
                    if not str(p.get(k, "")).strip()]
        if faltando:
            raise ValueError("Pausa conferida sem " + ", ".join(faltando) + f": {p}")
        if p["contrato"] != contrato:
            continue
        ts = int(datetime.strptime(p["retoma"], "%Y-%m-%d %H:%M").replace(tzinfo=BRT).timestamp() * 1000)
        pausas[(ts, int(p["minutos"]))] = p
    return pausas


def conferir_b3(arquivo: Path, contrato: str, origem: str, *, criterios: Path = CRITERIOS,
                de: str | None = None, ate: str | None = None,
                exigir_extremos: bool = True,
                pausas_conferidas: Path | None = None) -> tuple[pd.DataFrame, futuros.RelatorioB3, dict]:
    """Retorna só candles de desenvolvimento. Preços da reserva não são convertidos.

    O hash cobre o arquivo inteiro como bytes; o diagnóstico de preços e lacunas
    cobre somente o recorte. Datas opcionais são inclusivas, em Brasília.
    """
    if contrato not in futuros.CONTRATOS:
        raise ValueError("Contrato precisa ser WIN ou WDO.")
    if not origem.strip():
        raise ValueError("Informe a origem do arquivo.")
    inicio = date.fromisoformat(de) if de else None
    fim = date.fromisoformat(ate) if ate else None
    reserva = inicio_reserva(criterios)
    if inicio and fim and inicio > fim:
        raise ValueError("Período invertido.")
    if any(d and d >= reserva.date() for d in (inicio, fim)):
        raise ValueError("O período pedido intercepta a reserva; use datas anteriores.")
    caminho = Path(arquivo)
    bruto = caminho.read_bytes()
    leitor = csv.DictReader(io.StringIO(bruto.decode("utf-8-sig")), delimiter="\t")
    cabecalho = leitor.fieldnames or []
    nomes = {c.strip().strip("<>").lower(): c for c in cabecalho}
    obrigatorias = {"date", "time", "open", "high", "low", "close", "vol"}
    if not obrigatorias <= nomes.keys():
        raise ValueError("CSV MT5 inválido: faltam " + ", ".join(sorted(obrigatorias - nomes.keys())))
    selecionadas, excluidas = [], 0
    for numero, linha in enumerate(leitor, 2):
        try:
            ts = datetime.strptime(linha[nomes["date"]] + " " + linha[nomes["time"]],
                                   "%Y.%m.%d %H:%M:%S").replace(tzinfo=BRT)
        except (ValueError, TypeError) as erro:
            raise ValueError(f"Data/hora inválida na linha {numero}.") from erro
        if ts >= reserva or (inicio and ts.date() < inicio) or (fim and ts.date() > fim):
            excluidas += 1
            continue
        if None in linha or any(linha.get(c) is None for c in cabecalho):
            raise ValueError(f"Quantidade de colunas inválida na linha {numero}.")
        selecionadas.append(linha)
    rel = futuros.RelatorioB3()
    df = pd.DataFrame()
    erros = []
    conferidas = ler_pausas_conferidas(pausas_conferidas, contrato)
    usadas = []
    if not selecionadas:
        erros.append("Nenhum candle de desenvolvimento no período pedido.")
    else:
        entrada = io.StringIO()
        escritor = csv.DictWriter(entrada, fieldnames=cabecalho, delimiter="\t")
        escritor.writeheader()
        escritor.writerows(selecionadas)
        entrada.seek(0)
        try:
            df, rel = futuros.carregar_mt5(entrada)
        except (ValueError, KeyError, TypeError) as erro:
            erros.append(str(erro))
    cobertura = None
    if not df.empty:
        # O intervalo é declarado M5: não inferir M10 quando faltar cada segundo candle.
        df["ts_fechamento"] = df.ts_abertura + PASSO_MS - 1
        ts = df.ts_abertura.to_numpy(np.int64)
        locais = [datetime.fromtimestamp(int(t) / 1000, tz=BRT) for t in ts]
        dias = np.array([d.date() for d in locais])
        mesmo_dia = dias[1:] == dias[:-1]
        saltos = np.diff(ts)
        if (ts % PASSO_MS != 0).any():
            erros.append("Há abertura de candle fora da grade M5.")
        falhas = np.flatnonzero(mesmo_dia & (saltos != PASSO_MS))
        rel.pausas = [(int(ts[i + 1]), int(max(0, saltos[i] - PASSO_MS) // 60_000)) for i in falhas]
        usadas = [conferidas[p] for p in rel.pausas if p in conferidas]
        if len(usadas) < len(rel.pausas):
            erros.append("Há lacunas ou intervalos irregulares dentro do pregão; conferir a origem antes de testar.")
        tick = futuros.CONTRATOS[contrato].tick
        precos = df[["abertura", "maxima", "minima", "fechamento"]].to_numpy(float) / tick
        if not np.isclose(precos, np.round(precos), rtol=0, atol=1e-6).all():
            erros.append("Há preços fora do tick do contrato declarado.")
        if exigir_extremos and inicio and locais[0].date() != inicio:
            erros.append("A primeira data solicitada não está coberta pelo arquivo.")
        if exigir_extremos and fim and locais[-1].date() != fim:
            erros.append("A última data solicitada não está coberta pelo arquivo.")
        cobertura = {"inicio": locais[0].isoformat(), "fim": locais[-1].isoformat()}
    manifesto = {
        "tipo": "conferencia_dados_b3", "versao_motor": __version__,
        "gerado_em": datetime.now(tz=BRT).isoformat(),
        "arquivo": caminho.name, "origem_declarada": origem.strip(), "contrato_declarado": contrato,
        "sha256_arquivo": hashlib.sha256(bruto).hexdigest(),
        "sha256_criterios": hashlib.sha256(Path(criterios).read_bytes()).hexdigest(),
        "intervalo_declarado": "5m", "reserva_inicio": reserva.isoformat(),
        "periodo_pedido": {"de": de, "ate": ate}, "cobertura_observada": cobertura,
        "linhas_excluidas_por_data": excluidas, "qualidade": asdict(rel),
        "pausas_conferidas": usadas,
        "liberado_para_teste_dos_dados": not erros, "erros": erros,
        "limites": ["Não comprova a origem nem o contrato apenas pelo conteúdo do CSV.",
                    "Não certifica calendário, pregões ausentes, horários oficiais ou rolagens de vencimento.",
                    "Lacunas podem ser pausas reais ou defeitos do histórico; precisam de conferência.",
                    "Conferência de dados não aprova uma estratégia."],
    }
    return df, rel, manifesto
