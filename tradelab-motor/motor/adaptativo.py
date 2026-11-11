"""Pesquisa sequencial das hipóteses 55–57. Não conecta nem envia ordens.

Contextos e regras são congelados em HIPOTESES.md. A memória só recebe resultados
de simulações encerradas antes da decisão. Diagnósticos retrospectivos não a alimentam.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import tomllib

import numpy as np
import pandas as pd

from . import conferencia, futuros, metricas, validacao
from .backtest import Resultado, Risco, _BRT_MS, _DIA_MS
from .estrategias import ESTRATEGIAS, canal

ESPECIALISTAS = {
    "sma": {"rapida": 9, "lenta": 21},
    "rompimento_curto": {"entrada": 12, "saida": 6},
    "forca": {"periodo": 20, "k": 2.0},
    "forca_reversao": {"periodo": 20, "k": 2.0},
    "canal_suporte": {"n": 40, "r2": 0.5},
    "canal_aceleracao": {"n": 40, "r2": 0.5},
}
JANELA_CONTEXTO, MEMORIA, MIN_MEMORIA = 20, 60, 30
PF_MEMORIA = 1.3
RISCO_PESQUISA = Risco(capital=100_000, risco_por_trade=0.01, exposicao_max=1,
                       stop=0.005, alvo=None, perda_diaria_max=0.01,
                       max_operacoes_dia=10, max_contratos=1)


def _conferir_frame(df: pd.DataFrame):
    if df.empty:
        raise ValueError("Histórico vazio.")
    required = ["ts_abertura", "ts_fechamento", "abertura", "maxima", "minima", "fechamento", "volume"]
    if not set(required) <= set(df):
        raise ValueError("Faltam colunas normalizadas do histórico B3.")
    if (df.ts_abertura >= int(conferencia.inicio_reserva().timestamp() * 1000)).any():
        raise ValueError("O seletor de pesquisa não aceita preços da reserva.")
    if not np.isfinite(df[required].to_numpy(float)).all():
        raise ValueError("Histórico com valores não finitos.")
    if not df.ts_abertura.is_monotonic_increasing or df.ts_abertura.duplicated().any():
        raise ValueError("Candles precisam estar ordenados e sem duplicatas.")
    duracoes = df.ts_fechamento - df.ts_abertura + 1
    if not (duracoes == duracoes.iloc[0]).all() or duracoes.iloc[0] not in (300_000, 900_000, 1_800_000):
        raise ValueError("Use somente barras completas de 5, 15 ou 30 minutos.")
    if (df[["abertura", "maxima", "minima", "fechamento"]] <= 0).any().any() or (df.volume < 0).any():
        raise ValueError("Preço ou volume inválido.")
    if ((df.maxima < df[["abertura", "fechamento"]].max(axis=1)) |
            (df.minima > df[["abertura", "fechamento"]].min(axis=1))).any():
        raise ValueError("Candle incoerente.")


def _segmentos(df):
    ts = df.ts_abertura.to_numpy(np.int64)
    dia = (ts - _BRT_MS) // _DIA_MS
    passo = int(df.ts_fechamento.iloc[0] - ts[0] + 1)
    quebra = np.r_[True, (dia[1:] == dia[:-1]) & (np.diff(ts) != passo)]
    return np.cumsum(quebra)


def preparar(df: pd.DataFrame, contrato: str):
    """Indicadores causais entre pregões, reiniciados depois de lacunas intradiárias."""
    _conferir_frame(df)
    if contrato not in futuros.CONTRATOS:
        raise ValueError("Contrato precisa ser WIN ou WDO.")
    d = df.reset_index(drop=True).copy()
    tick = futuros.CONTRATOS[contrato].tick
    precos = d[["abertura", "maxima", "minima", "fechamento"]].to_numpy() / tick
    if not np.isclose(precos, np.round(precos), rtol=0, atol=1e-6).all():
        raise ValueError("Há preços fora do tick do contrato.")
    if contrato == "WIN":
        d, _ = futuros.ajustar_vencimentos(d, futuros.vencimentos_win())
    desloc = d.deslocamento.to_numpy() if "deslocamento" in d else np.zeros(len(d))
    ajustado = d.copy()
    for nome in ("abertura", "maxima", "minima", "fechamento"):
        ajustado[nome] = d[nome] + desloc
    # O envelope já aplica deslocamento quando a coluna existe. Remover evita ajuste duplo.
    ajustado = ajustado.drop(columns="deslocamento", errors="ignore")
    contextos = np.full(len(d), "aquecimento", dtype=object)
    sinais = {nome: np.zeros(len(d), dtype=np.int8) for nome in ESPECIALISTAS}
    for _, indices in pd.Series(np.arange(len(d))).groupby(_segmentos(d)):
        ix = indices.to_numpy()
        trecho = ajustado.iloc[ix].reset_index(drop=True)
        _, _, r2, inclinacao = canal(trecho.fechamento.to_numpy(float), JANELA_CONTEXTO)
        amplitude = (trecho.maxima - trecho.minima).to_numpy(float)
        media = pd.Series(amplitude).rolling(JANELA_CONTEXTO).mean().shift(1).to_numpy()
        pronto = np.isfinite(r2) & np.isfinite(media)
        ctx = np.where((r2 >= 0.5) & (inclinacao > 0), "alta",
                       np.where((r2 >= 0.5) & (inclinacao < 0), "baixa", "lateral"))
        ctx = np.where(amplitude > 3 * media, "choque", ctx)
        contextos[ix] = np.where(pronto, ctx, "aquecimento")
        for nome, params in ESPECIALISTAS.items():
            sinais[nome][ix] = ESTRATEGIAS[nome].sinais(trecho, **params)
    return d, contextos, sinais


def _sem_virada(sinal: int, lado: int) -> int:
    if not lado:
        return sinal if sinal in (1, -1) else 0
    if sinal in (-lado, futuros.SAIR) or (sinal == futuros.SAIR_COMPRADO and lado == 1) or \
            (sinal == futuros.SAIR_VENDIDO and lado == -1):
        return futuros.SAIR
    return 0


class Seletor:
    """Memória de resultados fechados, sem leitura de preços futuros ou diagnósticos."""

    def __init__(self, contextos, sinais, sombras: dict[str, pd.DataFrame], ts):
        self.contextos, self.sinais, self.ts = contextos, sinais, ts
        self.eventos = []
        for nome, ops in sombras.items():
            if nome not in sinais:
                raise ValueError("Especialista sem sinais.")
            for o in ops.itertuples():
                a, b, pnl = int(o.i_entrada), int(o.i_saida), float(o.pnl)
                if not 0 < a <= b < len(contextos) or not math.isfinite(pnl):
                    raise ValueError("Operação simulada inválida para a memória.")
                self.eventos.append((b, nome, str(contextos[a - 1]), pnl))
        self.eventos.sort()
        self.pos_evento = 0
        self.memoria = defaultdict(lambda: deque(maxlen=MEMORIA))
        self.dona = None
        self.ultimo_i = -1
        self.decisoes = []

    def escolher(self, i, contexto):
        if i <= self.ultimo_i:
            raise ValueError("As decisões precisam avançar em ordem cronológica.")
        self.ultimo_i = i
        while self.pos_evento < len(self.eventos) and self.eventos[self.pos_evento][0] < i:
            b, nome, ctx, pnl = self.eventos[self.pos_evento]
            self.memoria[nome, ctx].append((b, pnl))
            self.pos_evento += 1
        candidatos = []
        amostras = []
        for nome in sorted(self.sinais):
            hist = self.memoria[nome, contexto]
            amostras.append(len(hist))
            if len(hist) < MIN_MEMORIA:
                continue
            pnls = [p for _, p in hist]
            media = sum(pnls) / len(pnls)
            perdas = -sum(p for p in pnls if p < 0)
            ganhos = sum(p for p in pnls if p > 0)
            pf = ganhos / perdas if perdas else math.inf
            if media > 0 and pf >= PF_MEMORIA:
                candidatos.append((media, nome, len(hist), max(b for b, _ in hist)))
        if contexto in ("aquecimento", "choque"):
            return None, "contexto_bloqueado", 0, None, None
        if not candidatos:
            motivo = "memoria_insuficiente" if max(amostras, default=0) < MIN_MEMORIA else "sem_vantagem_na_memoria"
            return None, motivo, 0, None, None
        media, nome, n, ultimo = min(candidatos, key=lambda x: (-x[0], x[1]))
        return nome, "elegivel", n, media, ultimo

    def __call__(self, i, lado):
        nome, motivo, n, media, ultimo = self.escolher(i, str(self.contextos[i]))
        if lado:
            if self.dona is None:
                raise ValueError("Posição sem especialista responsável.")
            sinal = _sem_virada(int(self.sinais[self.dona][i]), lado)
            escolhido, motivo = self.dona, "mantem_responsavel_ate_saida"
        else:
            self.dona = None
            escolhido = nome
            sinal = _sem_virada(int(self.sinais[nome][i]), 0) if nome else 0
            proxima_abertura = int(self.ts[i]) + 1
            minuto = ((proxima_abertura - _BRT_MS) % _DIA_MS) // 60_000
            if minuto >= 17 * 60 + 30:
                sinal, motivo = 0, "fora_da_janela_de_entrada"
            elif sinal:
                self.dona = nome
            elif nome:
                motivo = "elegivel_sem_sinal_de_entrada"
        self.decisoes.append({"i": int(i), "ts_decisao": int(self.ts[i]),
                              "contexto": str(self.contextos[i]), "especialista": escolhido,
                              "avaliado_para_nova_entrada": nome,
                              "motivo": motivo, "sinal": int(sinal), "lado_antes": int(lado),
                              "amostra_escolha": n, "media_liquida_memoria": media,
                              "ultimo_i_saida_usado_na_escolha": ultimo})
        return sinal


def diagnosticar(df, ops, contextos, valor_ponto):
    """Contrafactuais dos mesmos instantes, sem sugerir fills ou causas comprovadas."""
    rows = []
    for o in ops.itertuples():
        a, b = int(o.i_entrada), int(o.i_saida)
        custo, pnl = float(o.custos), float(o.pnl)
        if not 0 <= a <= b < len(df) or not math.isfinite(custo + pnl) or custo < 0:
            raise ValueError("Operação inválida para diagnóstico.")
        lado, qtd = int(o.lado), float(o.quantidade)
        if lado not in (-1, 1) or not qtd > 0:
            raise ValueError("Lado ou quantidade inválido.")
        # Exclui a barra de saída: não sabemos se as extremas ocorreram depois do fill.
        trecho = df.iloc[a:b]
        mfe = mae = None
        if len(trecho):
            extremos = (trecho[["minima", "maxima"]].to_numpy() - float(o.preco_entrada)) * lado
            mfe = max(0.0, float(extremos.max())) * valor_ponto * qtd
            mae = min(0.0, float(extremos.min())) * valor_ponto * qtd
        rows.append({"i_entrada": a, "i_saida": b, "pnl": pnl, "custos": custo,
                     "especialista": getattr(o, "especialista", None),
                     "contexto_entrada": str(contextos[max(0, a - 1)]), "motivo_saida": o.motivo,
                     "positivo_bruto_negativo_liquido": bool(pnl < 0 < pnl + custo),
                     "inverso_mesmos_instantes_custo_simetrico": -pnl - 2 * custo,
                     "mfe_barras_anteriores_saida_reais": mfe, "mae_barras_anteriores_saida_reais": mae})
    return pd.DataFrame(rows, columns=["i_entrada", "i_saida", "pnl", "custos", "especialista", "contexto_entrada",
                                      "motivo_saida", "positivo_bruto_negativo_liquido",
                                      "inverso_mesmos_instantes_custo_simetrico",
                                      "mfe_barras_anteriores_saida_reais", "mae_barras_anteriores_saida_reais"])


def comparar_dias(df, controles, adaptativo, inicio):
    dias = pd.to_datetime(df.ts_abertura - _BRT_MS, unit="ms").dt.strftime("%Y-%m-%d")
    out = pd.DataFrame(index=pd.Index(sorted(set(dias.iloc[inicio:])), name="dia"))
    for nome, r in {**controles, "adaptativo": adaptativo}.items():
        ops = r.operacoes
        if len(ops):
            d = pd.to_datetime(ops.ts_saida - _BRT_MS, unit="ms").dt.strftime("%Y-%m-%d")
            out[nome] = ops.pnl.groupby(d).sum().reindex(out.index, fill_value=0)
        else:
            out[nome] = 0.0
    candidatos = out[list(controles)].copy()
    candidatos["ficar_de_fora"] = 0.0
    candidatos = candidatos[["ficar_de_fora", *sorted(controles)]]
    out["melhor_depois_do_fechamento"] = candidatos.idxmax(axis=1)
    out["liquido_melhor_depois_do_fechamento"] = candidatos.max(axis=1)
    out["ficar_de_fora"] = 0.0
    return out.reset_index()


def _recortar(r, inicio):
    for nome in ("ts", "patrimonio", "patrimonio_minimo", "sinais_validos"):
        setattr(r, nome, getattr(r, nome)[inicio:])
    return r


@dataclass
class Estudo:
    resultado: Resultado
    controles: dict[str, Resultado]
    decisoes: pd.DataFrame
    diagnostico: pd.DataFrame
    por_dia: pd.DataFrame
    inicio: int
    df: pd.DataFrame


def pesquisar(df: pd.DataFrame, contrato: str, progresso=None) -> Estudo:
    """Executa a política registrada, sem ajustar parâmetros ou acessar reserva."""
    d, contextos, sinais = preparar(df, contrato)
    inicio_mes = pd.Period(pd.to_datetime(int(d.ts_abertura.iloc[0]) - _BRT_MS, unit="ms"), "M") + 12
    ts_inicio = int(inicio_mes.start_time.value // 1_000_000) + _BRT_MS
    inicio = int(np.searchsorted(d.ts_abertura.to_numpy(), ts_inicio))
    if inicio >= len(d):
        raise ValueError("São necessários mais de 12 meses para separar memória e avaliação.")
    c = futuros.com_lado(futuros.CONTRATOS[contrato], "ambos")
    c = replace(c, indicador_continuo=True)
    custos = futuros.CUSTOS[contrato]
    aq = max(ESTRATEGIAS[n].aquecimento(p) for n, p in ESPECIALISTAS.items())
    sombras, controles = {}, {}
    for nome, valores in sinais.items():
        if progresso:
            progresso("Simulando especialista: " + nome)
        sinal = lambda i, lado, v=valores: _sem_virada(int(v[i]), lado)
        sombras[nome] = futuros.executar_futuros(d, sinal, RISCO_PESQUISA, custos, c, aq).operacoes
        controles[nome] = _recortar(futuros.executar_futuros(d, sinal, RISCO_PESQUISA, custos, c, aq, inicio), inicio)
        controles[nome].operacoes["especialista"] = nome
    seletor = Seletor(contextos, sinais, sombras, d.ts_fechamento.to_numpy(np.int64))
    if progresso:
        progresso("Avaliando escolhas cronológicas e possibilidade de ficar de fora")
    r = _recortar(futuros.executar_futuros(d, seletor, RISCO_PESQUISA, custos, c, aq, inicio), inicio)
    decisoes = pd.DataFrame(seletor.decisoes)
    donas = {o["i"]: o["especialista"] for o in seletor.decisoes if o["lado_antes"] == 0 and o["sinal"] in (-1, 1)}
    r.operacoes["especialista"] = [donas[int(i) - 1] for i in r.operacoes.i_entrada]
    diagnosticos = [diagnosticar(d, r.operacoes, contextos, c.valor_ponto).assign(tipo_resultado="adaptativo")]
    diagnosticos.extend(diagnosticar(d, controle.operacoes, contextos, c.valor_ponto)
                        .assign(tipo_resultado="controle_fixo") for controle in controles.values())
    nao_vazios = [f for f in diagnosticos if not f.empty]
    diagnostico = pd.concat(nao_vazios, ignore_index=True) if nao_vazios else diagnosticos[0].copy()
    return Estudo(r, controles, decisoes, diagnostico,
                  comparar_dias(d, controles, r, inicio), inicio, d)


def _json_seguro(obj):
    if isinstance(obj, dict):
        return {str(k): _json_seguro(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, np.ndarray)):
        return [_json_seguro(v) for v in obj]
    if isinstance(obj, (float, np.floating)):
        return float(obj) if math.isfinite(obj) else None
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


def executar_comando(a):
    """Única entrada CLI: conferência antes de qualquer cálculo de sinais."""
    from datetime import datetime, timezone

    df, _, manifesto = conferencia.conferir_b3(Path(a.arquivo), a.contrato, a.origem,
                                              pausas_conferidas=a.pausas_conferidas,
                                              exigir_extremos=False)
    if not manifesto["liberado_para_teste_dos_dados"]:
        raise ValueError("Histórico B3 bloqueado: " + " ".join(manifesto["erros"]))
    if a.minutos != 5:
        df = futuros.reamostrar(df, a.minutos)
    estudo = pesquisar(df, a.contrato, progresso=lambda msg: print(msg, flush=True))
    print("Comparando com as 200 referências aleatórias registradas", flush=True)
    mercado = replace(futuros.com_lado(futuros.CONTRATOS[a.contrato], "ambos"), indicador_continuo=True)
    mc = validacao.aleatorio_monte_carlo(estudo.df, estudo.resultado, 200, 42, mercado, estudo.inicio)
    medidas = metricas.calcular(estudo.resultado)
    criterios = tomllib.loads(conferencia.CRITERIOS.read_text())
    veredito = validacao.avaliar(medidas, mc.percentil, criterios)
    registro = {
        "tipo": "pesquisa_adaptativa_b3", "hipotese": {5: 55, 15: 56, 30: 57}[a.minutos],
        "gerado_em": datetime.now(timezone.utc).isoformat(), "contrato": a.contrato,
        "minutos": a.minutos, "moeda": "R$", "conferencia_dados": manifesto,
        "sha256_codigo_adaptativo": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "especialistas": ESPECIALISTAS, "risco_medicao": asdict(RISCO_PESQUISA),
        "custos_premissas": asdict(futuros.CUSTOS[a.contrato]),
        "metricas_fora_da_amostra": medidas,
        "controles_fixos": {n: metricas.calcular(r) for n, r in estudo.controles.items()},
        "aleatorias": {"n": 200, "semente": 42, "percentil": mc.percentil},
        "criterios": criterios, "veredito_criterios_deste_relatorio": asdict(veredito),
        "aprovado_para_conta_real": False,
        "limites": ["Exige o mesmo tempo aprovado nos dois mercados e confirmação prospectiva.",
                    "Histórico já pesquisado: a avaliação sequencial não elimina viés de pesquisa anterior.",
                    "O melhor do dia e o inverso são retrospectivos, nunca usados para escolher operações.",
                    "Inverso supõe mesmos instantes e custo simétrico; não reproduz outra estratégia de stop/alvo.",
                    "MFE/MAE excluem a barra de saída e não demonstram execução em extremos.",
                    "A referência aleatória aproxima frequência/duração; não replica a aprendizagem do seletor.",
                    "Candles não identificam participantes, suas intenções ou a causa de uma perda.",
                    "Custos de EA/XP são premissas ainda sujeitas a confirmação."],
    }
    destino = Path(a.saida) / f"{a.contrato}_{a.minutos}m_{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}"
    destino.mkdir(parents=True, exist_ok=False)
    controles_nao_vazios = [r.operacoes for r in estudo.controles.values() if not r.operacoes.empty]
    ops_controles = pd.concat(controles_nao_vazios, ignore_index=True) if controles_nao_vazios else \
        next(iter(estudo.controles.values())).operacoes.iloc[:0].copy()
    for nome, frame in (("decisoes", estudo.decisoes), ("operacoes", estudo.resultado.operacoes),
                        ("operacoes_controles", ops_controles),
                        ("diagnostico", estudo.diagnostico), ("por_dia", estudo.por_dia)):
        frame.to_csv(destino / f"{nome}.csv", index=False)
    (destino / "relatorio.json").write_text(json.dumps(_json_seguro(registro), ensure_ascii=False,
                                                       indent=2, allow_nan=False), encoding="utf-8")
    print(f"Pesquisa salva em {destino}. Nenhuma ordem enviada; conta real não aprovada.")
