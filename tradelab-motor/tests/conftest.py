from pathlib import Path
import json
import tomllib

import pandas as pd

import pytest

from motor import dados

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def amostra():
    """499 candles reais BTCUSDT 15m que o TradeLab (PWA) usa como amostra padrão."""
    arquivo = FIXTURES / "tradelab-amostra-btcusdt-15m.json"
    reserva = tomllib.loads((FIXTURES.parent.parent / "criterios.toml").read_text()).get("reserva_inicio")
    if reserva:
        limite = pd.Period(reserva, "M").start_time.value // 1_000_000
        # Inspeciona só os timestamps. Não executa estratégia em preços da reserva.
        timestamps = [c["opened"] for c in json.loads(arquivo.read_text())["candles"]]
        if any(ts >= limite for ts in timestamps):
            pytest.skip("A amostra real do PWA intercepta o período reservado; usar regressões sintéticas.")
    return dados.ler_tradelab_json(arquivo)
