// Parsing and presentation helpers only. No strategy, broker or order execution.
export const DEFAULT_RESERVE = '2026-07';
export const MAX_BYTES = 25 * 1024 * 1024;
const MAX_TRADES = 100000;
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
export const finite = v => typeof v === 'number' && Number.isFinite(v);
export const number = (v, digits = 2) => finite(v) ? new Intl.NumberFormat('pt-BR', { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(v) : '—';
export const integer = v => finite(v) ? new Intl.NumberFormat('pt-BR', {maximumFractionDigits: 0}).format(v) : '—';
export const money = (v, currency = 'BRL') => finite(v) ? (currency === 'USDT' ? `${number(v)} USDT` : new Intl.NumberFormat('pt-BR', { style:'currency', currency:'BRL' }).format(v)) : '—';
export const percent = v => finite(v) ? `${number(v, 1)}%` : '—';
export function dateTime(v, short = false) {
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? '—' : new Intl.DateTimeFormat('pt-BR', {timeZone:'America/Sao_Paulo', day:'2-digit', month:'2-digit', ...(short ? {} : {year:'numeric', hour:'2-digit', minute:'2-digit'})}).format(d);
}
function fail(message) { throw new Error(message); }
function requireNumber(v, label, {nullable = false, min = -Infinity, max = Infinity, whole = false} = {}) {
  if (nullable && (v === null || v === undefined)) return;
  if (!finite(v) || v < min || v > max || (whole && !Number.isInteger(v))) fail(`${label}: valor inválido ou ausente.`);
}
function text(v, label) { if (typeof v !== 'string' || !v.trim() || v.length > 20000) fail(`${label}: texto inválido ou ausente.`); }
export function cutoff(payload = {}) {
  if (payload.reserva_inicio !== undefined && typeof payload.reserva_inicio !== 'string') fail('Início da reserva inválido.');
  const declared = payload.criterios?.reserva_inicio || payload.reserva_inicio?.slice(0, 7) || DEFAULT_RESERVE;
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(declared)) fail('Início da reserva inválido.');
  const month = declared < DEFAULT_RESERVE ? declared : DEFAULT_RESERVE;
  return Date.parse(`${month}-01T00:00:00-03:00`);
}
function checkTime(v, label, limit) {
  const ts = typeof v === 'number' ? v : (typeof v === 'string' && /T.*(?:Z|[+-]\d\d:\d\d)$/.test(v) ? Date.parse(v) : NaN);
  if (!finite(ts) || ts < 0) fail(`${label}: data/hora inválida.`);
  if (ts >= limit) fail('Este arquivo contém operações ou preços no período reservado (07/2026 em diante). Importe o recorte de desenvolvimento.');
  return ts;
}
function checkTrades(ops) { if (!Array.isArray(ops) || ops.length > MAX_TRADES) fail('Lista de operações inválida ou muito grande.'); }
function numbersIn(v, depth = 0) {
  if (depth > 60) fail('Arquivo com estrutura excessivamente profunda.');
  if (typeof v === 'number' && !Number.isFinite(v)) fail('O arquivo contém NaN ou Infinity.');
  if (v && typeof v === 'object') for (const x of Object.values(v)) numbersIn(x, depth + 1);
}
export function validateReport(p) {
  if (!object(p)) fail('Selecione um objeto JSON gerado pelo motor TradeLab.');
  numbersIn(p);
  const limit = cutoff(p);
  if (p.tipo === 'diario_simulador_b3') {
    if (p.ambiente !== 'simulador' || p.moeda !== 'BRL') fail('O diário precisa ser do simulador B3, em BRL.');
    checkTrades(p.operacoes);
    if (!object(p.resumo)) fail('Resumo do diário ausente.');
    const ids = new Set();
    for (const op of p.operacoes) {
      if (!object(op)) fail('Operação inválida.');
      text(op.id, 'ID'); if (ids.has(op.id)) fail('Há IDs de operação repetidos.'); ids.add(op.id);
      if (!['WIN','WDO'].includes(op.contrato) || !['comprado','vendido'].includes(op.lado)) fail('Contrato ou lado inválido.');
      requireNumber(op.quantidade, 'Quantidade', {min:1, whole:true});
      const e = checkTime(op.entrada, 'Entrada', limit), s = checkTime(op.saida, 'Saída', limit);
      if (s < e) fail('Há uma saída anterior à entrada.');
      for (const k of ['preco_entrada_previsto','preco_saida_previsto','preco_entrada_executado','preco_saida_executado']) requireNumber(op[k], k, {min:Number.MIN_VALUE});
      for (const k of ['taxas_previstas','taxas_executadas']) requireNumber(op[k], k, {min:0});
      for (const k of ['resultado_previsto','resultado_liquido','resultado_bruto_executado','diferenca_liquido','impacto_execucao_brl','desvio_entrada_ticks','desvio_saida_ticks']) requireNumber(op[k], k);
      for (const k of ['stop','alvo']) requireNumber(op[k], k, {nullable:true, min:Number.MIN_VALUE});
      for (const k of ['hipotese','motivo_entrada','motivo_saida','origem']) text(op[k], k);
      const vp = op.contrato === 'WIN' ? 0.2 : 10;
      const sign = op.lado === 'comprado' ? 1 : -1;
      const actual = sign * (op.preco_saida_executado - op.preco_entrada_executado) * op.quantidade * vp - op.taxas_executadas;
      const planned = sign * (op.preco_saida_previsto - op.preco_entrada_previsto) * op.quantidade * vp - op.taxas_previstas;
      if (Math.abs(actual - op.resultado_liquido) > 0.011 || Math.abs(planned - op.resultado_previsto) > 0.011) fail('O líquido informado diverge dos preços e taxas. Confira o arquivo no motor.');
      if (Math.abs((actual-planned)-op.diferenca_liquido)>0.011 || Math.abs(actual+op.taxas_executadas-op.resultado_bruto_executado)>0.011) fail('A comparação de execução diverge dos preços e taxas.');
    }
    requireNumber(p.resumo.operacoes, 'Total de operações', {min:0,whole:true});
    if (p.resumo.operacoes !== p.operacoes.length) fail('O total do diário diverge da lista de operações.');
    for (const k of ['resultado_liquido','resultado_previsto','taxas_executadas','diferenca_liquido','impacto_execucao_brl']) {
      requireNumber(p.resumo[k], k);
      if (Math.abs(p.operacoes.reduce((s,o)=>s+o[k],0) - p.resumo[k]) > 0.011) fail(`O resumo diverge das operações: ${k}.`);
    }
    requireNumber(p.resumo.acerto_liquido_pct, 'Acerto', {min:0,max:100});
    requireNumber(p.resumo.fator_lucro, 'Fator de lucro', {nullable:true,min:0});
    return 'diary';
  }
  if (p.tipo === 'conferencia_dados_b3') {
    if (!['WIN','WDO'].includes(p.contrato_declarado)) fail('Contrato da conferência inválido.');
    if (typeof p.liberado_para_teste_dos_dados !== 'boolean' || !object(p.qualidade)) fail('Conferência incompleta.');
    if (p.cobertura_observada) {
      checkTime(p.cobertura_observada.inicio, 'Cobertura inicial', limit);
      checkTime(p.cobertura_observada.fim, 'Cobertura final', limit);
    }
    for (const k of ['candles','pregoes','duplicatas_removidas']) requireNumber(p.qualidade[k], k, {min:0,whole:true});
    if (!Array.isArray(p.qualidade.pausas) || !Array.isArray(p.erros)) fail('Diagnóstico da conferência incompleto.');
    text(p.origem_declarada, 'Origem');
    if (typeof p.sha256_arquivo !== 'string' || !/^[a-f0-9]{64}$/i.test(p.sha256_arquivo)) fail('SHA-256 inválido.');
    if (p.liberado_para_teste_dos_dados && p.erros.length) fail('Conferência marcada como liberada contém erros.');
    return 'quality';
  }
  if (object(p.metricas_fora_da_amostra) && Array.isArray(p.operacoes)) {
    text(p.estrategia, 'Estratégia'); text(p.simbolo, 'Símbolo'); text(p.intervalo, 'Intervalo');
    if (!['R$','BRL','USDT'].includes(p.moeda)) fail('Moeda ausente ou não reconhecida. Valores não serão convertidos.');
    const m = p.metricas_fora_da_amostra;
    checkTrades(p.operacoes);
    for (const op of p.operacoes) {
      if (!object(op)) fail('Operação inválida.');
      const e=checkTime(op.ts_entrada,'Entrada',limit), s=checkTime(op.ts_saida,'Saída',limit);
      if (s < e) fail('Há uma saída anterior à entrada.');
      requireNumber(op.pnl, 'Líquido da operação');
    }
    requireNumber(m.operacoes, 'Operações', {min:0,whole:true});
    if (m.operacoes !== p.operacoes.length) fail('O total informado diverge das operações do relatório.');
    for (const k of ['resultado_liquido','custos_totais','resultado_bruto','retorno_pct']) requireNumber(m[k],k);
    for (const k of ['taxa_acerto_pct','drawdown_minimo_pct','drawdown_fechamento_pct']) requireNumber(m[k],k,{nullable:true,min:0});
    requireNumber(m.fator_lucro,'fator_lucro',{nullable:true,min:0});
    requireNumber(m.expectativa,'expectativa',{nullable:true});
    requireNumber(m.taxa_acerto_pct,'taxa_acerto_pct',{nullable:true,min:0,max:100});
    if (Math.abs(p.operacoes.reduce((s,o)=>s+o.pnl,0) - m.resultado_liquido) > 0.02) fail('O líquido do relatório diverge da soma das operações.');
    if (!object(p.risco) || !finite(p.risco.capital) || p.risco.capital<=0) fail('Capital inicial do teste ausente ou inválido.');
    if (p.veredito && (typeof p.veredito.aprovado !== 'boolean' || !Array.isArray(p.veredito.itens))) fail('Veredito inválido.');
    if (p.veredito?.itens.some(i=>!object(i)||typeof i.passou!=='boolean'||typeof i.texto!=='string'||!finite(i.limite)||!(finite(i.valor)||i.valor===null))) fail('Critérios informados inválidos.');
    if (p.veredito?.aprovado && (!p.veredito.itens.length || p.veredito.itens.some(i=>!i.passou))) fail('O veredito de aprovação contradiz os critérios.');
    return 'validation';
  }
  if (Array.isArray(p.candles)) fail('Este é um arquivo de candles. Importe o JSON de validar, diario-b3 ou conferir-b3.');
  fail('Formato não reconhecido. Use um relatório de validação, diário ou conferência do motor.');
}
export function parseReportText(raw) {
  if (new TextEncoder().encode(raw).byteLength > MAX_BYTES) fail('Arquivo maior que 25 MB.');
  let p; try { p = JSON.parse(raw.replace(/^\uFEFF/,'')); } catch { fail('JSON inválido. NaN e Infinity não são aceitos; exporte novamente pelo motor.'); }
  return {kind:validateReport(p), payload:p};
}
export function labelReport(r) {
  const p = r.payload;
  if (r.kind === 'validation') return `${p.simbolo} · ${p.estrategia.replaceAll('_',' ')} · ${p.intervalo}`;
  if (r.kind === 'diary') return `Diário B3 · ${p.resumo.operacoes} operações`;
  return `${p.contrato_declarado} · conferência M5`;
}
export function seriesFor(r) {
  const p=r.payload;
  if (r.kind !== 'validation' && r.kind !== 'diary') return [];
  const diary = r.kind === 'diary';
  const sorted=[...p.operacoes].sort((a,b)=> diary ? Date.parse(a.saida)-Date.parse(b.saida) : a.ts_saida-b.ts_saida);
  let balance = diary ? 0 : p.risco.capital;
  const out = [{value:balance, ts:sorted.length ? (diary ? Date.parse(sorted[0].entrada) : sorted[0].ts_entrada) : null}];
  for (const op of sorted) {balance+=diary?op.resultado_liquido:op.pnl;out.push({value:balance,ts:diary?Date.parse(op.saida):op.ts_saida});}
  return out;
}
export function statsFor(r) {
  const p=r.payload;
  if (r.kind==='validation') return {currency:p.moeda==='USDT'?'USDT':'BRL',net:p.metricas_fora_da_amostra.resultado_liquido,fees:p.metricas_fora_da_amostra.custos_totais,gross:p.metricas_fora_da_amostra.resultado_bruto,operations:p.metricas_fora_da_amostra.operacoes,drawdown:p.metricas_fora_da_amostra.drawdown_minimo_pct,factor:p.metricas_fora_da_amostra.fator_lucro,winRate:p.metricas_fora_da_amostra.taxa_acerto_pct};
  if (r.kind==='diary') return {currency:'BRL',net:p.resumo.resultado_liquido,fees:p.resumo.taxas_executadas,planned:p.resumo.resultado_previsto,delta:p.resumo.diferenca_liquido,operations:p.resumo.operacoes,factor:p.resumo.fator_lucro,winRate:p.resumo.acerto_liquido_pct};
  return null;
}
export function csvEscape(value) {return '"'+String(value??'').replaceAll('"','""')+'"';}
