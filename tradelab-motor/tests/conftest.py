from pathlib import Path

import pytest

from motor import dados

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def amostra():
    """499 candles reais BTCUSDT 15m que o TradeLab (PWA) usa como amostra padrão."""
    return dados.ler_tradelab_json(FIXTURES / "tradelab-amostra-btcusdt-15m.json")
