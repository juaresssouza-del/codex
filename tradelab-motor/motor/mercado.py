"""Regras da corretora e custos de execução."""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Mercado:
    """Filtros da Binance Spot. Os padrões são os de BTCUSDT conhecidos em 2026;
    confira em GET /api/v3/exchangeInfo (PRICE_FILTER, LOT_SIZE, NOTIONAL) antes de operar."""
    passo_preco: float = 0.01      # tickSize
    passo_qtd: float = 0.00001     # stepSize
    qtd_minima: float = 0.00001    # minQty
    notional_minimo: float = 5.0   # minNotional, em USDT

    def __post_init__(self):
        for nome in ("passo_preco", "passo_qtd", "qtd_minima", "notional_minimo"):
            v = getattr(self, nome)
            if not math.isfinite(v) or v < 0:
                raise ValueError(f"{nome} precisa ser finito e não negativo.")

    def arredonda_qtd(self, q: float) -> float:
        if self.passo_qtd <= 0:
            return q
        casas = max(0, -Decimal(str(self.passo_qtd)).normalize().as_tuple().exponent)
        return round(math.floor(q / self.passo_qtd + 1e-9) * self.passo_qtd, casas)

    def arredonda_preco(self, p: float) -> float:
        if self.passo_preco <= 0:
            return p
        casas = max(0, -Decimal(str(self.passo_preco)).normalize().as_tuple().exponent)
        return round(round(p / self.passo_preco) * self.passo_preco, casas)

    def aceita(self, qtd: float, preco: float) -> bool:
        return qtd > 0 and qtd >= self.qtd_minima and qtd * preco >= self.notional_minimo


SEM_FILTROS = Mercado(passo_preco=0, passo_qtd=0, qtd_minima=0, notional_minimo=0)


@dataclass(frozen=True)
class Custos:
    taxa: float = 0.001        # 0,1% por lado (taxa padrão Spot, sem desconto BNB)
    slippage: float = 0.0005   # 0,05% por lado, contra você
    # Entrada por ordem limitada no fechamento do candle do sinal: sem slippage, mas só executa
    # se o preço negociar abaixo do limite no candle seguinte. Saídas continuam a mercado.
    entrada_limitada: bool = False

    def __post_init__(self):
        for nome in ("taxa", "slippage"):
            v = getattr(self, nome)
            if not math.isfinite(v) or not 0 <= v < 1:
                raise ValueError(f"{nome} precisa estar entre zero (inclusive) e um (exclusive).")
