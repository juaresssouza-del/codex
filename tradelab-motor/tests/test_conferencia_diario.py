"""Regressões com preços artificiais; nenhum histórico de mercado é executado."""
import csv
import hashlib
import json

import pytest

from motor import conferencia, diario
from motor.__main__ import main


def mt5(tmp_path, linhas=None):
    caminho = tmp_path / "artificial-m5.csv"
    linhas = linhas or [("2025.01.06", "09:00:00"), ("2025.01.06", "09:05:00"), ("2025.01.06", "09:10:00")]
    with caminho.open("w", newline="") as arq:
        w = csv.writer(arq, delimiter="\t")
        w.writerow(["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<TICKVOL>", "<VOL>", "<SPREAD>"])
        for data, hora, *preco in linhas:
            valores = preco or [100000, 100010, 99990, 100005]
            w.writerow([data, hora, *valores, 50, 10, 5])
    return caminho


def conferir(arquivo, **kwargs):
    return conferencia.conferir_b3(arquivo, "WIN", "Teste de software: dados artificiais", **kwargs)


def operacao(**kwargs):
    return {"id": "SOFTWARE-1", "ambiente": "simulador", "contrato": "WIN", "lado": "comprado",
            "quantidade": "2", "entrada": "2025-01-06 09:30:00", "saida": "2025-01-06 09:45:00",
            "preco_entrada_previsto": "100000", "preco_saida_previsto": "100100",
            "preco_entrada_executado": "100005", "preco_saida_executado": "100095",
            "taxas_previstas": "4", "taxas_executadas": "6", "stop": "99950", "alvo": "100100",
            "hipotese": "teste unitário artificial", "motivo_entrada": "caso de software",
            "motivo_saida": "encerramento artificial", "origem": "fixture fictícia", **kwargs}


def csv_diario(tmp_path, linhas=None):
    caminho = tmp_path / "diario-artificial.csv"
    with caminho.open("w", newline="", encoding="utf-8") as arq:
        w = csv.DictWriter(arq, fieldnames=diario.COLUNAS, delimiter=";")
        w.writeheader()
        w.writerows(linhas or [operacao()])
    return caminho


def test_conferencia_hash_e_precos_da_reserva_nao_convertidos(tmp_path):
    arquivo = mt5(tmp_path, [("2025.01.06", "09:00:00"), ("2025.01.06", "09:05:00"),
                              ("2026.07.01", "09:00:00", "nao-ler", "nao-ler", "nao-ler", "nao-ler")])
    df, _, m = conferir(arquivo)
    assert m["liberado_para_teste_dos_dados"]
    assert len(df) == 2 and m["linhas_excluidas_por_data"] == 1
    assert m["sha256_arquivo"] == hashlib.sha256(arquivo.read_bytes()).hexdigest()
    assert m["cobertura_observada"]["inicio"].endswith("-03:00")


@pytest.mark.parametrize("horarios", [["09:00:00", "09:10:00"], ["09:00:00", "09:05:00", "09:15:00"]])
def test_lacuna_nao_vira_intervalo_maior_nem_candle_ficticio(tmp_path, horarios):
    arquivo = mt5(tmp_path, [("2025.01.06", h) for h in horarios])
    df, _, m = conferir(arquivo)
    assert not m["liberado_para_teste_dos_dados"]
    assert len(df) == len(horarios)
    assert (df.ts_fechamento - df.ts_abertura == 299999).all()


def test_noite_nao_vira_lacuna_intradiaria(tmp_path):
    arquivo = mt5(tmp_path, [(d, h) for d in ["2025.01.06", "2025.01.07"] for h in ["09:00:00", "09:05:00"]])
    _, rel, m = conferir(arquivo)
    assert m["liberado_para_teste_dos_dados"] and rel.pregoes == 2 and not rel.pausas


def test_duplicatas_identicas_sao_contadas_e_conflitantes_bloqueadas(tmp_path):
    arquivo = mt5(tmp_path, [("2025.01.06", "09:00:00"), ("2025.01.06", "09:00:00"), ("2025.01.06", "09:05:00")])
    _, rel, m = conferir(arquivo)
    assert m["liberado_para_teste_dos_dados"] and rel.duplicatas_removidas == 1
    arquivo = mt5(tmp_path, [("2025.01.06", "09:00:00"),
                              ("2025.01.06", "09:00:00", 100005, 100010, 99990, 100005)])
    assert not conferir(arquivo)[2]["liberado_para_teste_dos_dados"]


def test_precos_incoerentes_e_fora_do_tick_bloqueiam(tmp_path):
    arquivo = mt5(tmp_path, [("2025.01.06", "09:00:00", 100001, 100010, 99990, 100005),
                              ("2025.01.06", "09:05:00")])
    assert "tick" in " ".join(conferir(arquivo)[2]["erros"])
    arquivo.write_text(arquivo.read_text().replace("100001", "nan"))
    assert not conferir(arquivo)[2]["liberado_para_teste_dos_dados"]


def test_cobertura_pedida_nao_e_inventada(tmp_path):
    arquivo = mt5(tmp_path)
    assert not conferir(arquivo, de="2025-01-03")[2]["liberado_para_teste_dos_dados"]
    assert conferir(arquivo, de="2025-01-01", exigir_extremos=False)[2]["liberado_para_teste_dos_dados"]
    with pytest.raises(ValueError, match="reserva"):
        conferir(arquivo, ate="2026-07-01")


def test_cli_grava_diagnostico_bloqueado_sem_rodar_estrategia(tmp_path, monkeypatch):
    arquivo = mt5(tmp_path, [("2025.01.06", "09:00:00"), ("2025.01.06", "09:10:00")])
    with pytest.raises(SystemExit) as exc:
        main(["conferir-b3", "--arquivo", str(arquivo), "--contrato", "WIN", "--origem", "artificial",
              "--saida", str(tmp_path / "rel")])
    assert exc.value.code == 2
    m = json.loads(next((tmp_path / "rel").glob("*.json")).read_text())
    assert not m["liberado_para_teste_dos_dados"]
    from motor.estrategias import ESTRATEGIAS
    def proibido(*args, **kwargs):
        pytest.fail("O sinal não pode ser calculado antes da conferência de dados.")
    monkeypatch.setattr(type(ESTRATEGIAS["abertura"]), "sinais", proibido)
    with pytest.raises(SystemExit) as exc:
        main(["validar", "--arquivo", str(arquivo), "--contrato", "WIN", "--intervalo", "5m", "--estrategia", "abertura"])
    assert exc.value.code == 2


@pytest.mark.parametrize("lado,ep,sp,ee,se", [("comprado", "100000", "100100", "100005", "100095"),
                                          ("vendido", "100000", "99900", "99995", "99905")])
def test_pnl_compra_venda_e_slippage_sem_desconto_duplo(tmp_path, lado, ep, sp, ee, se):
    arquivo = csv_diario(tmp_path, [operacao(lado=lado, preco_entrada_previsto=ep, preco_saida_previsto=sp,
                                            preco_entrada_executado=ee, preco_saida_executado=se)])
    rel = diario.analisar(arquivo)
    r = rel["operacoes"][0]
    assert r["resultado_previsto"] == 36
    assert r["resultado_bruto_executado"] == 36
    assert r["resultado_liquido"] == 30  # 36 - 6 taxas; não subtrair outros 4 de slippage
    assert r["desvio_entrada_ticks"] == r["desvio_saida_ticks"] == 1
    assert r["impacto_execucao_brl"] == 4 and r["diferenca_liquido"] == -6
    assert rel["resumo"]["fator_lucro"] is None  # não gerar Infinity no JSON


def test_wdo_e_decimal_virgula(tmp_path):
    arquivo = csv_diario(tmp_path, [operacao(contrato="WDO", preco_entrada_previsto="5000", preco_saida_previsto="5005",
                       preco_entrada_executado="5000,5", preco_saida_executado="5004,5")])
    r = diario.analisar(arquivo)["operacoes"][0]
    assert r["resultado_liquido"] == 74 and r["impacto_execucao_brl"] == 20


@pytest.mark.parametrize("mudanca,erro", [({"taxas_executadas": ""}, "não foi estimado"),
                                        ({"taxas_executadas": "NaN"}, "finito"),
                                        ({"taxas_executadas": "Infinity"}, "finito"),
                                        ({"quantidade": "1.5"}, "inteira"),
                                        ({"quantidade": "0"}, "positivo"),
                                        ({"ambiente": "real"}, "simulador"),
                                        ({"entrada": "2026-07-01 09:00:00"}, "reservado"),
                                        ({"saida": "2025-01-07 09:45:00"}, "pregão"),
                                        ({"preco_entrada_previsto": "100001"}, "tick")])
def test_diario_recusa_dados_que_fabricariam_ou_distorceriam_resultado(tmp_path, mudanca, erro):
    with pytest.raises(ValueError, match=erro):
        diario.analisar(csv_diario(tmp_path, [operacao(**mudanca)]))


def test_id_duplicado_impede_contar_mesma_operacao_duas_vezes(tmp_path):
    with pytest.raises(ValueError, match="repetido"):
        diario.analisar(csv_diario(tmp_path, [operacao(), operacao()]))


def test_preco_medio_de_multiplos_fills_pode_ficar_entre_ticks(tmp_path):
    r = diario.analisar(csv_diario(tmp_path, [operacao(preco_entrada_executado="100002.5",
                                                  preco_saida_executado="100097.5")]))["operacoes"][0]
    assert r["desvio_entrada_ticks"] == r["desvio_saida_ticks"] == 0.5
    assert r["resultado_liquido"] == 32 and r["impacto_execucao_brl"] == 2


def test_resumo_ordenado_por_saida_e_fator_lucro(tmp_path):
    arquivo = csv_diario(tmp_path, [operacao(id="SOFTWARE-2", entrada="2025-01-06 10:00:00", saida="2025-01-06 10:10:00",
                                   preco_saida_executado="99995"), operacao()])
    rel = diario.analisar(arquivo)
    assert [r["id"] for r in rel["operacoes"]] == ["SOFTWARE-1", "SOFTWARE-2"]
    assert rel["resumo"]["resultado_liquido"] == 20
    assert rel["resumo"]["fator_lucro"] == 3 and rel["resumo"]["acerto_liquido_pct"] == 50


def test_cli_diario_exporta_html_seguro_e_json_reprodutivel(tmp_path):
    arquivo = csv_diario(tmp_path, [operacao(motivo_entrada='<script>alert("x")</script>')])
    pasta = tmp_path / "rel"
    main(["diario-b3", "--arquivo", str(arquivo), "--saida", str(pasta)])
    rel = json.loads((pasta / "diario.json").read_text())
    pagina = (pasta / "diario.html").read_text()
    assert rel["sha256_csv"] == hashlib.sha256(arquivo.read_bytes()).hexdigest()
    assert "<script>" not in pagina and "&lt;script&gt;" in pagina
    assert 'name="viewport"' in pagina and "SIMULADOR" in pagina
    main(["diario-b3", "--arquivo", str(arquivo), "--saida", str(pasta)])
    assert json.loads((pasta / "diario.json").read_text())["resumo"] == rel["resumo"]


# --- pausas conferidas: liberar só o que foi investigado ---------------------------------

PAUSA = [("2025.01.06", "09:00:00"), ("2025.01.06", "09:05:00"), ("2025.01.06", "09:25:00"), ("2025.01.06", "09:30:00")]


def toml_pausas(tmp_path, texto):
    caminho = tmp_path / "pausas.toml"
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def test_pausa_nao_conferida_bloqueia(tmp_path):
    _, rel, m = conferir(mt5(tmp_path, PAUSA))
    assert not m["liberado_para_teste_dos_dados"] and rel.pausas[0][1] == 15


def test_pausa_conferida_libera_e_fica_registrada(tmp_path):
    p = toml_pausas(tmp_path, '[[pausa]]\ncontrato = "WIN"\nretoma = "2025-01-06 09:25"\nminutos = 15\n'
                              'causa = "suspensão de teste"\nfonte = "teste de software"\nsituacao = "confirmada"\n')
    df, rel, m = conferir(mt5(tmp_path, PAUSA), pausas_conferidas=p)
    assert m["liberado_para_teste_dos_dados"] and len(df) == 4  # nada apagado, nada preenchido
    assert m["pausas_conferidas"][0]["causa"] == "suspensão de teste"


@pytest.mark.parametrize("entrada", [
    '[[pausa]]\ncontrato = "WIN"\nretoma = "2025-01-06 09:25"\nminutos = 10\ncausa = "x"\nfonte = "y"\nsituacao = "z"\n',
    '[[pausa]]\ncontrato = "WDO"\nretoma = "2025-01-06 09:25"\nminutos = 15\ncausa = "x"\nfonte = "y"\nsituacao = "z"\n',
    '[[pausa]]\ncontrato = "WIN"\nretoma = "2025-01-06 09:25"\nminutos = 15\ncausa = ""\nfonte = "y"\nsituacao = "z"\n',
])
def test_pausa_conferida_precisa_bater_e_ter_causa(tmp_path, entrada):
    if 'causa = ""' in entrada:
        with pytest.raises(ValueError):
            conferir(mt5(tmp_path, PAUSA), pausas_conferidas=toml_pausas(tmp_path, entrada))
    else:
        _, _, m = conferir(mt5(tmp_path, PAUSA), pausas_conferidas=toml_pausas(tmp_path, entrada))
        assert not m["liberado_para_teste_dos_dados"]


# --- diário prospectivo: depois da janela reservada, as operações ao vivo são aceitas -------

def test_diario_aceita_operacao_ao_vivo_depois_da_janela_reservada(tmp_path):
    ao_vivo = operacao(id="ROBO-1", entrada="2026-11-16 10:15:00", saida="2026-11-16 11:45:00")
    relatorio = diario.analisar(csv_diario(tmp_path, [ao_vivo]))
    assert relatorio["operacoes"][0]["id"] == "ROBO-1"


def test_diario_continua_bloqueando_a_janela_reservada(tmp_path):
    dentro = operacao(id="R-1", entrada="2026-10-26 10:00:00", saida="2026-10-26 11:00:00")
    with pytest.raises(ValueError, match="reservado"):
        diario.analisar(csv_diario(tmp_path, [dentro]))
