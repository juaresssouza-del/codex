"""Integridade do calendário factual; não há execução da hipótese 26."""
import csv
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

PASTA=Path(__file__).resolve().parents[1]/'b3/calendario_h26'


def linhas(nome):
    with (PASTA/nome).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f,delimiter=';'))


def test_contagem_intervalo_e_fontes_por_data():
    rows=linhas('eventos.csv')
    assert Counter(r['evento'] for r in rows)=={'FOMC':38,'PAYROLL':55,'IPCA':56,'COPOM':37}
    assert len({(r['evento'],r['data_evento']) for r in rows})==186
    for r in rows:
        assert date(2021,11,1)<=date.fromisoformat(r['data_evento'])<=date(2026,6,30)
        for campo in ['fonte_data','fonte_documento']+(['fonte_calendario_b3'] if r['evento']=='COPOM' else []):
            assert urlparse(r[campo]).hostname in {'www.federalreserve.gov','www.bls.gov',
               'agenciadenoticias.ibge.gov.br','www.bcb.gov.br','www.b3.com.br'}
        assert r['status']=='confirmado' and r['consultado_em']=='2026-11-15'


def test_datas_efetivas_e_feriados():
    rows=linhas('eventos.csv')
    payroll={r['data_evento'] for r in rows if r['evento']=='PAYROLL'}
    assert {'2025-11-20','2025-12-16','2026-02-11'}<=payroll
    assert not {'2025-10-03','2025-11-07','2025-12-05','2026-02-06'}&payroll
    copom={r['data_evento']:r['data_bloqueio_b3'] for r in rows if r['evento']=='COPOM'}
    assert copom['2022-06-15']=='2022-06-17'
    assert copom['2023-11-01']=='2023-11-03'
    assert copom['2025-06-18']=='2025-06-20'
    assert '2023-06-07' in {r['data_evento'] for r in rows if r['evento']=='IPCA'}


def test_uniao_bloqueios_e_excecao_fomc_explicitada():
    rows=linhas('eventos.csv');blocks=linhas('bloqueios.csv')
    assert {r['data_bloqueio_b3'] for r in blocks}=={r['data_bloqueio_b3'] for r in rows}
    assert len(blocks)==179 # Datas civis, não contagem de pregões.
    assert any(r['evento']=='FOMC' and r['data_efetiva']=='2025-08-22' for r in linhas('excecoes.csv'))


def test_hashes_manifesto_e_cabecalhos():
    manifest=json.loads((PASTA/'manifesto.json').read_text())
    assert manifest['hipotese_executada'] is False and manifest['criterios_alterados'] is False
    for nome,sha in manifest['arquivos'].items():
        assert hashlib.sha256((PASTA/nome).read_bytes()).hexdigest()==sha
    meta=json.loads((PASTA/'fontes_coleta.json').read_text())
    releases=[s for s in meta if s.get('data_publicacao')]
    assert len(releases)==55 and all(s['sha256_html'] for s in releases)
