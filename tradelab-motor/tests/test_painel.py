from motor import painel

from .util import PASSO_15M, serie


def test_exporta_ultimo_trecho_continuo_no_formato_do_importador():
    df = serie(300)
    depois = df.index >= 200
    df.loc[depois, "ts_abertura"] += 4 * PASSO_15M
    df.loc[depois, "ts_fechamento"] += 4 * PASSO_15M
    j = painel.para_tradelab(df, "BTCUSDT", "15m", limite=60)
    assert j["symbol"] == "BTCUSDT" and j["interval"] == "15m" and j["mode"] == "historico"
    c = j["candles"]
    assert len(c) == 60 and c[-1]["opened"] == int(df.ts_abertura.iloc[-1])
    assert all(b["opened"] == a["opened"] + PASSO_15M for a, b in zip(c, c[1:]))
    assert set(c[0]) == {"opened", "closed", "open", "high", "low", "close", "volume"}
    assert set(j["config"]) == {"capital", "fee", "slip", "stop", "target"}
    curto = painel.para_tradelab(df, "BTCUSDT", "15m", limite=20_000)
    assert len(curto["candles"]) == 100  # só o trecho depois da lacuna
