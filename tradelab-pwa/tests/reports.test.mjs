import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateReport,parseReportText,statsFor,seriesFor,money,number,cutoff} from '../dist/reports.js';
import {validation,diary,quality} from './fixtures.mjs';

for(const [kind,make] of [['validation',validation],['diary',diary],['quality',quality]])test(`recognizes ${kind}`,()=>assert.equal(validateReport(make()),kind));
test('keeps currencies distinct and never sums different files',()=>{
  const v=validation();v.moeda='USDT';const r={kind:'validation',payload:v};
  assert.equal(statsFor(r).currency,'USDT');assert.match(money(10,'USDT'),/USDT/);assert.match(money(10),/R\$/);
});
test('closed trade curve uses chronological order and capital',()=>{
  const v=validation();v.operacoes.reverse();const s=seriesFor({kind:'validation',payload:v});
  assert.deepEqual(s.map(x=>x.value),[1000,1020,1010]);
  assert.equal(statsFor({kind:'validation',payload:v}).drawdown,2);
});
test('diary curve starts at zero, with no second deduction of fees or slippage',()=>{
  const p=diary();assert.equal(validateReport(p),'diary');
  const r={kind:'diary',payload:p};assert.ok(Math.abs(seriesFor(r).at(-1).value-.6)<1e-8);assert.equal(statsFor(r).fees,5.4);
});
for(const [name,edit,message] of [
  ['reserved validation',p=>p.operacoes[0].ts_entrada=Date.parse('2026-07-01T09:00:00-03:00'),/reservado/],
  ['wrong currency',p=>p.moeda='USD',/Moeda/],
  ['missing initial capital',p=>delete p.risco.capital,/Capital/],
  ['missing net',p=>delete p.metricas_fora_da_amostra.resultado_liquido,/resultado_liquido/],
  ['inconsistent trade count',p=>p.metricas_fora_da_amostra.operacoes=3,/total/],
  ['inconsistent net',p=>p.metricas_fora_da_amostra.resultado_liquido=1000,/soma/],
  ['false approval',p=>p.veredito.aprovado=true,/contradiz/],
  ['unsupported negative factor',p=>p.metricas_fora_da_amostra.fator_lucro=-1,/fator_lucro/],
  ['NaN',p=>p.metricas_fora_da_amostra.custos_totais=NaN,/NaN/],
  ['Infinity',p=>p.metricas_fora_da_amostra.custos_totais=Infinity,/Infinity/],
])test(`rejects ${name}`,()=>{const p=validation();edit(p);assert.throws(()=>validateReport(p),message);});
for(const [name,edit,message] of [
  ['real account diary',p=>p.ambiente='real',/simulador/],
  ['duplicate IDs',p=>p.operacoes[1].id=p.operacoes[0].id,/repetidos/],
  ['missing fees',p=>delete p.operacoes[0].taxas_executadas,/taxas_executadas/],
  ['fractional contracts',p=>p.operacoes[0].quantidade=.5,/Quantidade/],
  ['altered fill math',p=>p.operacoes[0].preco_entrada_executado=100020,/diverge/],
  ['altered comparison',p=>p.operacoes[0].diferenca_liquido=100,/diverge/],
  ['reserved diary',p=>p.operacoes[0].entrada='2026-07-01T09:30:00-03:00',/reservado/],
  ['altered summary',p=>p.resumo.resultado_liquido=100,/resumo/],
])test(`rejects ${name}`,()=>{const p=diary();edit(p);assert.throws(()=>validateReport(p),message);});
test('rejects reserved quality coverage and contradictory release flag',()=>{
  const p=quality();p.cobertura_observada.fim='2026-07-01T09:30:00-03:00';assert.throws(()=>validateReport(p),/reservado/);
  const q=quality();q.erros=['falha'];assert.throws(()=>validateReport(q),/contém erros/);
});
test('blocked quality manifests are accepted as blocked, never approved',()=>{
  const p=quality();p.liberado_para_teste_dos_dados=false;p.erros=['lacuna'];assert.equal(validateReport(p),'quality');
});
test('later declared holdout cannot loosen the project reserve',()=>{
  const p=validation();p.criterios.reserva_inicio='2027-01';assert.equal(cutoff(p),Date.parse('2026-07-01T00:00:00-03:00'));
});
test('earlier declared holdout remains protected',()=>{
  const p=validation();p.criterios.reserva_inicio='2024-01';assert.throws(()=>validateReport(p),/reservado/);
});
test('missing metrics display as unavailable, not zero',()=>{assert.equal(number(null),'—');assert.equal(money(undefined),'—');});
test('recognizes BOM and rejects non-standard JSON',()=>{
  assert.equal(parseReportText('\uFEFF'+JSON.stringify(validation())).kind,'validation');
  assert.throws(()=>parseReportText('{"x": Infinity}'),/JSON inválido/);
});
test('does not accept the old candle-only export as a financial report',()=>assert.throws(()=>validateReport({candles:[]}),/arquivo de candles/));
test('plain imported text remains text in the data model',()=>{
  const p=diary();assert.equal(validateReport(p),'diary');assert.match(p.operacoes[1].motivo_entrada,/<script>/);
});
test('installable assets exist and application has a complete offline shell',()=>{
  const root=new URL('../dist/',import.meta.url);const m=JSON.parse(fs.readFileSync(new URL('manifest.webmanifest',root)));
  assert.equal(m.display,'standalone');assert.equal(m.start_url,'./#resumo');
  for(const i of m.icons)assert.ok(fs.existsSync(new URL(i.src,root)));
  assert.ok(m.icons.some(i=>i.sizes==='192x192'));assert.ok(m.icons.some(i=>i.sizes==='512x512'&&i.purpose==='maskable'));
});
test('source summary distinguishes all eight measurement accounts',()=>{
  const p=JSON.parse(fs.readFileSync(new URL('../dist/project.json',import.meta.url)));
  assert.equal(p.runs.length,8);assert.equal(p.approved,0);assert.ok(p.runs.every(r=>r.approved===false));
  assert.equal(p.runs.filter(r=>r.capital===1000).length,4);assert.equal(p.runs.filter(r=>r.capital===100000).length,4);
  assert.equal(p.runs.find(r=>r.id==='17b').net,-11910);
});
