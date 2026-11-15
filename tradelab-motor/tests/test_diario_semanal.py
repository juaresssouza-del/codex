"""Contabilidade com operações artificiais. Nenhum preço de mercado é carregado."""
import csv
from decimal import Decimal
import json
from pathlib import Path

import pytest

from motor import diario
from motor.__main__ import main
from tests.test_conferencia_diario import operacao


def gravar(pasta, linhas):
    arquivo=pasta/'simulador.csv'
    with arquivo.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=diario.COLUNAS,delimiter=';')
        w.writeheader();w.writerows(linhas)
    return arquivo


def test_semanas_reconciliam_com_total_sem_dobrar_slippage(tmp_path):
    linhas=[operacao(id='A', entrada='2025-01-03 10:00:00',saida='2025-01-03 10:10:00'),
            operacao(id='B', entrada='2025-01-06 10:00:00',saida='2025-01-06 10:10:00',
                     preco_saida_executado='99995')]
    r=diario.analisar(gravar(tmp_path,linhas))
    assert [s['semana_iso'] for s in r['semanas']]==['2025-W01','2025-W02']
    for campo in ['operacoes','resultado_previsto','resultado_bruto_executado',
                  'resultado_liquido','taxas_executadas','impacto_execucao_brl','diferenca_liquido']:
        assert sum(Decimal(str(s[campo])) for s in r['semanas'])==Decimal(str(r['resumo'][campo]))
    for s in r['semanas']:
        assert s['resultado_liquido']==s['resultado_bruto_executado']-s['taxas_executadas']
        assert s['diferenca_liquido']==s['resultado_liquido']-s['resultado_previsto']


def test_semana_iso_usa_ano_iso_e_brasilia(tmp_path):
    linhas=[operacao(entrada='2021-01-01 10:00:00',saida='2021-01-01 10:10:00')]
    assert diario.analisar(gravar(tmp_path,linhas))['semanas'][0]['semana_iso']=='2020-W53'
    linhas=[operacao(entrada='2025-01-06T00:00:00+00:00',saida='2025-01-06T00:10:00+00:00')]
    r=diario.analisar(gravar(tmp_path,linhas))
    assert r['semanas'][0]['semana_iso']=='2025-W01' # Domingo em Brasília.
    assert r['operacoes'][0]['saida'].endswith('-03:00')


def test_zero_observado_nao_e_substituido_por_premissa(tmp_path):
    linha=operacao(taxas_previstas='4.48',taxas_executadas='0')
    r=diario.analisar(gravar(tmp_path,[linha]))
    assert r['resumo']['taxas_executadas']==0
    assert r['resumo']['resultado_liquido']==r['resumo']['resultado_bruto_executado']
    assert any('Taxa zero observada' in l for l in r['limites'])


@pytest.mark.parametrize('taxa',['','-1'])
def test_taxa_ausente_ou_rebate_nao_vira_zero(tmp_path,taxa):
    with pytest.raises(ValueError,match='taxas_executadas'):
        diario.analisar(gravar(tmp_path,[operacao(taxas_executadas=taxa)]))


def test_comando_semanal_usa_mesmo_analisador_e_colunas(tmp_path):
    arq=gravar(tmp_path,[operacao()]);saida=tmp_path/'relatorio'
    main(['diario-b3','--arquivo',str(arq),'--saida',str(saida)])
    r=json.loads((saida/'diario.json').read_text())
    assert r['semanas'][0]['resultado_liquido']==diario.analisar(arq)['resumo']['resultado_liquido']
    assert 'Comparação semanal' in (saida/'diario.html').read_text()
    modelo=Path(__file__).resolve().parents[1]/'b3/diario-modelo.csv'
    assert modelo.read_text().strip().split(';')==diario.COLUNAS
