import {MAX_BYTES, parseReportText, labelReport, statsFor, seriesFor, finite, number, integer, money, percent, dateTime} from './reports.js';

const icons = {
  grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  flask:'<path d="M9 3h6M10 3v7l-5.5 9a1.4 1.4 0 0 0 1.2 2h12.6a1.4 1.4 0 0 0 1.2-2L14 10V3M8 15h8"/>',
  book:'<path d="M5 3h14v18H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2ZM5 17h14M8 7h7M8 10h5"/>',
  data:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 4 16 4 16 0V5M4 12v7c0 4 16 4 16 0v-7"/>',
  upload:'<path d="M12 16V3m-5 5 5-5 5 5M4 15v5h16v-5"/>',
  download:'<path d="M12 3v13m-5-5 5 5 5-5M4 15v5h16v-5"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  arrow:'<path d="m9 5 7 7-7 7"/>',
  external:'<path d="M14 3h7v7M21 3l-9 9M10 3H4v17h17v-6"/>',
  shield:'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
  check:'<path d="m5 12 4 4L19 6"/>',
  close:'<path d="m6 6 12 12M18 6 6 18"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
  file:'<path d="M14 2H5v20h14V7l-5-5ZM14 2v6h5M8 12h8M8 16h6"/>',
  trash:'<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>',
  trend:'<path d="m3 17 6-6 4 4L21 5M15 5h6v6"/>',
  wallet:'<path d="M20 7H4V3h14v4M4 7H2v14h18V7ZM20 11h-6v6h6M16 14h.01"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  minus:'<path d="M5 12h14"/>',
};
function icon(name, size=18) {
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  for(const [k,v] of Object.entries({width:size,height:size,viewBox:'0 0 24 24',fill:'none',stroke:'currentColor','stroke-width':1.5,'stroke-linecap':'round','stroke-linejoin':'round','aria-hidden':'true'}))svg.setAttribute(k,v);
  svg.innerHTML=icons[name]||icons.file; // only the constant icon dictionary is inserted as markup
  return svg;
}
function el(tag, attrs={}, ...children) {
  const node=document.createElement(tag);
  for(const [key,value] of Object.entries(attrs)){
    if(value===null||value===undefined||value===false)continue;
    if(key.startsWith('on')&&typeof value==='function')node.addEventListener(key.slice(2),value);
    else if(key==='class')node.className=value;
    else if(key==='value')node.value=value;
    else node.setAttribute(key,value===true?'':String(value));
  }
  for(const child of children.flat(Infinity))if(child!==null&&child!==undefined&&child!==false)node.append(child instanceof Node?child:document.createTextNode(String(child)));
  return node;
}
const $=selector=>document.querySelector(selector);
const views={resumo:{label:'Resumo',icon:'grid'},testes:{label:'Testes',icon:'flask'},diario:{label:'Diário',icon:'book'},dados:{label:'Dados',icon:'data'}};
const state={project:null,reports:[],db:null,view:'resumo',summaryId:'project',validationId:null,diaryId:null,qualityId:null,capital:100000,query:'',tradeLimit:50,deferredInstall:null};
let toastTimer;
function toast(message){clearTimeout(toastTimer);$('#toast').textContent=message;$('#toast').hidden=false;toastTimer=setTimeout(()=>$('#toast').hidden=true,5500);}
function button(label, name, onClick, cls='ghost'){return el('button',{class:`button ${cls}`,onclick:onClick},name?icon(name,14):null,label);}
function badge(label, cls=''){return el('span',{class:`chip ${cls}`},label);}
function notice(text, tone='neutral'){return el('div',{class:`notice ${tone}`},icon(tone==='green'?'shield':'info',17),el('div',{},text));}
function external(label,url){return el('a',{href:url,target:'_blank',rel:'noopener noreferrer'},label,' ',icon('external',11));}
function pageHeading(eyebrow,title,desc,tag){return el('div',{class:'page-heading'},el('div',{},el('p',{class:'eyebrow'},eyebrow),el('h1',{},title),el('p',{class:'description'},desc)),tag?el('div',{class:'heading-aside'},tag):null);}
function metric(label,value,note,name='trend',tone=''){return el('article',{class:'metric'},el('div',{class:'metric-label'},label),el('span',{class:'corner'},icon(name,16)),el('div',{class:`metric-value ${tone}`},value),el('p',{class:'metric-note'},note));}
function panel(title,subtitle,body,action=null,foot=null){return el('section',{class:'panel'},el('div',{class:'panel-head'},el('div',{},el('h2',{},title),subtitle?el('p',{},subtitle):null),action),body,foot?el('div',{class:'panel-foot'},foot):null);}
function sourceLink(){return state.project?external('Ver registro da pesquisa',state.project.source_url):null;}
function openImport(){const d=$('#import-dialog');if(!d.open)d.showModal();}
function empty(title,desc,name='file'){return el('div',{class:'empty'},el('div',{class:'empty-icon'},icon(name,24)),el('h2',{},title),el('p',{},desc),button('Importar relatório','upload',openImport,'primary'));}
function kindList(kind){return state.reports.filter(r=>r.kind===kind).sort((a,b)=>b.importedAt.localeCompare(a.importedAt));}
function findReport(id){return state.reports.find(r=>r.id===id);}
function picker(list, selected, onChange, allowProject=false){
  const select=el('select',{'aria-label':'Selecionar relatório',onchange:e=>onChange(e.target.value)});
  if(allowProject)select.append(el('option',{value:'project'},'Resumo do projeto · rodada 5R'));
  for(const r of list)select.append(el('option',{value:r.id},`${labelReport(r)} · ${r.name}`));
  if(!list.length&&!allowProject)select.append(el('option',{value:''},'Nenhum arquivo importado'));
  select.value=selected||(list[0]?.id??'');
  return el('div',{class:'source-select'},el('label',{},'RELATÓRIO ATIVO'),select);
}
function renderNav(){
  const nav=$('#navigation');nav.replaceChildren();
  for(const [key,v] of Object.entries(views)){
    const count=key==='testes'?kindList('validation').length:key==='diario'?kindList('diary').length:key==='dados'?state.reports.length:null;
    nav.append(el('button',{class:`nav-button ${state.view===key?'active':''}`,'aria-current':state.view===key?'page':null,onclick:()=>{location.hash=key;}},icon(v.icon,19),el('span',{},v.label),count!==null?el('span',{class:'nav-count'},String(count)):null));
  }
}
function capitalToggle(){return el('div',{class:'segmented','aria-label':'Capital da medição'},...[100000,1000].map(c=>el('button',{class:state.capital===c?'active':'','aria-pressed':state.capital===c,onclick:()=>{state.capital=c;render();}},c===100000?'R$ 100 mil':'R$ 1 mil')));}
function runBars(){
  const runs=state.project.runs.filter(r=>r.capital===state.capital);
  const max=Math.max(...runs.map(r=>Math.abs(r.net)),1);
  const body=el('div',{class:'panel-body'});
  for(const r of runs){const fill=el('div',{class:'bar-fill'});fill.style.width=`${Math.max(2,100*Math.abs(r.net)/max)}%`;body.append(el('div',{class:'bar-row'},el('div',{class:'bar-label'},el('b',{},r.symbol),el('small',{},`#${r.id} · ${r.interval}`)),el('div',{class:'bar-track'},fill),el('div',{class:'bar-amount'},money(r.net))));}
  body.append(el('div',{class:'bar-caption'},el('i'),`Resultado líquido · 1 contrato por operação · ${state.project.period}`));
  return panel('Resultado por medição','Depois dos custos informados no registro',body,capitalToggle(),[el('span',{},'Medições separadas; valores arredondados.'),sourceLink()]);
}
function projectOutcome(){return el('section',{class:'panel outcome'},badge('RODADA 5R','amber'),el('div',{class:'outcome-value'},'0',el('span',{},' / 8')),el('h2',{},'Medições aprovadas'),el('div',{class:'outcome-rule','aria-label':'As oito medições foram reprovadas'},...Array.from({length:8},()=>el('i'))),el('p',{},'A reexecução manteve os oito resultados reprovados. Os custos seguem maiores que a vantagem observada.'),el('div',{class:'outcome-bottom'},el('span',{},'Motor ',state.project.engine_version),el('span',{},'Reserva preservada')));}
function runTable(runs,withOld=false){
  const headings=['Medição','Estratégia','Operações','Fator de lucro',...(withOld?['Líquido anterior']:[]),'Líquido 5R','Maior queda','Veredito'];
  const body=el('tbody');
  for(const r of runs)body.append(el('tr',{},el('td',{},el('span',{class:'table-title'},`${r.symbol} #${r.id}`),el('small',{class:'mono'},`${r.interval} · capital ${money(r.capital, 'BRL')}`)),el('td',{},r.strategy),el('td',{class:'mono'},integer(r.operations)),el('td',{class:'mono'},number(r.profit_factor)),...(withOld?[el('td',{class:'mono muted'},money(r.old_net))]:[]),el('td',{class:'mono negative'},money(r.net)),el('td',{class:'mono'},money(r.drawdown_brl)),el('td',{},badge('Reprovada','red'))));
  return el('div',{class:'table-wrap',tabindex:'0','aria-label':'Resultados documentados da rodada 5R'},el('table',{},el('thead',{},el('tr',{},...headings.map(h=>el('th',{scope:'col'},h)))),body));
}
function renderProject(){
  const p=state.project;
  if(!p)return empty('Traga seu primeiro resultado','Importe um JSON de validação para acompanhar as métricas do motor.');
  return el('div',{},el('div',{class:'metrics'},metric('Hipóteses registradas',integer(p.hypotheses),'Registro acumulado do projeto','flask'),metric('Estratégias aprovadas',integer(p.approved),'Pela régua fixada antes dos testes','shield','amber'),metric('Medições reexecutadas','08','Rodada 5R · WIN e WDO','trend'),metric('Limite do histórico','JUN/26','A partir de julho: reserva','clock')),
    el('div',{class:'grid'},runBars(),projectOutcome()),
    notice('Este é o resumo documentado da pesquisa. Para ver a curva de saldo e os critérios completos de uma medição, importe o JSON gerado pelo motor.'),
    el('div',{class:'mini-grid'},el('article',{class:'mini-card'},icon('flask',20),el('div',{},el('h3',{},'Testes com contexto'),el('p',{},'Versão do motor, custos e veredito no mesmo lugar.'),button('Ver testes','arrow',()=>location.hash='testes','text'))),el('article',{class:'mini-card'},icon('book',20),el('div',{},el('h3',{},'Diário de execução'),el('p',{},'Compare referências, fills e taxas do simulador.'),button('Abrir diário','arrow',()=>location.hash='diario','text'))),el('article',{class:'mini-card'},icon('data',20),el('div',{},el('h3',{},'Origem dos dados'),el('p',{},'Conferências, cobertura e arquivos importados.'),button('Conferir dados','arrow',()=>location.hash='dados','text')))),
    panel('Última reexecução','Capital de medição de R$ 100 mil, mantendo 1 contrato. Não é recomendação de capital.',runTable(p.runs.filter(r=>r.capital===100000)),badge('4 MEDIÇÕES'),[el('span',{},p.note),sourceLink()]));
}
function makeChart(r){
  const points=seriesFor(r);
  if(points.length<2)return empty('Ainda sem operações nesta curva','O relatório importado não contém operações encerradas suficientes.');
  const s=statsFor(r), width=660,height=215,pad={l:67,r:18,t:17,b:27};
  let min=Infinity,max=-Infinity;for(const p of points){min=Math.min(min,p.value);max=Math.max(max,p.value);}
  const span=max-min||Math.max(Math.abs(max)*.01,1);min-=span*.12;max+=span*.12;
  const x=i=>pad.l+i/(points.length-1)*(width-pad.l-pad.r),y=v=>pad.t+(max-v)/(max-min)*(height-pad.t-pad.b);
  const path=points.map((p,i)=>`${i?'L':'M'}${x(i).toFixed(2)},${y(p.value).toFixed(2)}`).join(' ');
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.setAttribute('class','chart');svg.setAttribute('role','img');svg.setAttribute('aria-label',r.kind==='diary'?'Resultado acumulado das operações encerradas':'Saldo após cada operação encerrada');
  const ns=(tag,attrs,text)=>{const n=document.createElementNS(svg.namespaceURI,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;};
  for(let i=0;i<4;i++){const v=min+i*(max-min)/3,Y=y(v);svg.append(ns('line',{x1:pad.l,x2:width-pad.r,y1:Y,y2:Y,class:'chart-grid'}),ns('text',{x:pad.l-10,y:Y+3,'text-anchor':'end',class:'chart-axis'},number(v,0)));}
  for(const i of [...new Set([0,Math.floor((points.length-1)/2),points.length-1])])svg.append(ns('text',{x:x(i),y:height-3,'text-anchor':i===0?'start':i===points.length-1?'end':'middle',class:'chart-axis'},dateTime(points[i].ts,true)));
  const color=s.net>=0?'#b5df86':'#ec968b';
  svg.append(ns('path',{d:path+` L${x(points.length-1)},${height-pad.b} L${pad.l},${height-pad.b}Z`,fill:color,'fill-opacity':'.035'}),ns('path',{d:path,fill:'none',stroke:color,'stroke-width':1.7,'stroke-linejoin':'round','stroke-linecap':'round'}),ns('circle',{cx:x(points.length-1),cy:y(points.at(-1).value),r:3,fill:color}));
  return el('div',{},el('div',{class:'chart-balance'},el('div',{},r.kind==='diary'?'Acumulado líquido':'Saldo final do teste',el('b',{},money(points.at(-1).value,s.currency))),el('span',{},`${integer(s.operations)} operações`)),el('div',{class:'chart-area'},svg));
}
function criteriaPanel(r){
  const p=r.payload,items=p.veredito?.itens||[];
  const content=el('div');
  for(const i of items)content.append(el('div',{class:`criterion ${i.passou?'ok':''}`},el('span',{class:'criterion-icon'},icon(i.passou?'check':'close',16)),el('div',{},el('b',{},i.texto),el('p',{},`Limite informado: ${number(i.limite,2)}`)),el('strong',{},number(i.valor,2))));
  if(!items.length)content.append(el('div',{class:'panel-body muted small'},'Critérios completos não informados neste arquivo.'));
  const verdict=p.veredito?badge(p.veredito.aprovado?'Aprovada no teste':'Reprovada',p.veredito.aprovado?'green':'red'):badge('Sem veredito');
  return panel('Critérios do relatório','Limites e resultado informados pelo motor',content,verdict);
}
function importedSummary(r){
  const s=statsFor(r),p=r.payload,diary=r.kind==='diary';
  return el('div',{},el('div',{class:'metrics'},metric('Resultado líquido',money(s.net,s.currency),'Depois dos custos informados','wallet',s.net>=0?'positive':'negative'),metric(diary?'Taxas executadas':'Custos totais',money(s.fees,s.currency),diary?'Taxas totais das operações':'Taxas e impacto da execução','minus'),metric(diary?'Diferença do previsto':'Maior queda intradiária',diary?money(s.delta):percent(s.drawdown),diary?'Executado menos referência':'Valor informado no relatório original','trend',diary?(s.delta>=0?'positive':'negative'):''),metric('Fator de lucro',number(s.factor),'Líquido ganho ÷ líquido perdido','flask')),
    el('div',{class:'grid'},panel(diary?'Resultado acumulado':'Curva do saldo','Após operações encerradas; não representa o caminho intradiário',makeChart(r),badge(diary?'SIMULADOR':'FORA DA AMOSTRA'),[el('span',{},`Motor ${p.versao_motor||'não informado'} · ${r.name}`)]),diary?panel('Referência e execução','O slippage já está nos preços executados.',el('div',{class:'panel-body'},el('p',{class:'small muted'},'Resultado previsto'),el('h2',{class:'mono section-gap'},money(s.planned)),el('p',{class:'small muted section-gap'},'Acerto líquido'),el('h2',{class:'mono section-gap'},percent(s.winRate)),el('p',{class:'small muted section-gap'},'O diário descreve operações encerradas. Não aprova estratégias.'))):criteriaPanel(r)),
    notice(diary?'Este é um diário do simulador, com valores informados no arquivo. A diferença de execução não é descontada novamente do resultado líquido.':'O capital é simulado. Uma aprovação no relatório não autoriza operar uma conta real.'),
    el('div',{class:'source-note'},`Arquivo: ${r.name} · importado em ${dateTime(r.importedAt)}. ${diary?'Resultado acumulado a partir de zero.':`Capital inicial simulado: ${money(p.risco.capital,s.currency)}.`}`));
}
function summaryView(){
  const list=state.reports.filter(r=>r.kind==='validation'||r.kind==='diary');
  if(state.summaryId!=='project'&&!findReport(state.summaryId))state.summaryId='project';
  const r=findReport(state.summaryId);
  return [pageHeading('CENTRAL DE PESQUISA','Visão geral','Resultados do motor. Decisões com contexto.',badge('PESQUISA B3','green')),el('div',{class:'toolbar'},picker(list,state.summaryId,id=>{state.summaryId=id;render();},true),el('span',{class:'file-meta'},r?'Arquivo local do dispositivo':'Fonte: registro do projeto')),r?importedSummary(r):renderProject()];
}
function validationDetail(r){
  const p=r.payload,s=statsFor(r);
  return el('div',{class:'section-gap'},el('div',{class:'metrics'},metric('Líquido fora da amostra',money(s.net,s.currency),'Relatório importado','wallet',s.net>=0?'positive':'negative'),metric('Operações',integer(s.operations),`${p.simbolo} · ${p.intervalo}`,'book'),metric('Taxa de acerto',percent(s.winRate),'Operações com líquido positivo','trend'),metric('Maior queda intradiária',percent(s.drawdown),'Não é queda só no fechamento','shield')),criteriaPanel(r),el('p',{class:'source-note'},`Arquivo ${r.name} · motor ${p.versao_motor||'não informado'} · capital simulado ${money(p.risco.capital,s.currency)}.`));
}
function testsView(){
  const list=kindList('validation');const selected=findReport(state.validationId)||list[0];
  return [pageHeading('MÉTODO E VALIDAÇÃO','Testes e hipóteses','Cada medição mantém seus custos, capital e critérios.',badge('RESERVA 07/2026','amber')),
    state.project?panel('Reexecução registrada · rodada 5R','Valores arredondados do registro. Não são saldos de uma conta real.',runTable(state.project.runs,true),badge('8 REPROVADAS','red'),[el('span',{},'R$ 100 mil é o capital usado para medir a estratégia com 1 contrato.'),sourceLink()]):null,
    el('div',{class:'section-gap'},panel('Relatórios completos importados','Selecione um JSON para conferir as métricas e cada critério.',list.length?el('div',{class:'panel-body'},picker(list,selected?.id,id=>{state.validationId=id;render();}),selected?validationDetail(selected):null):empty('Veja o teste completo','Importe o JSON produzido por python -m motor validar. O resumo da rodada já está disponível acima.','flask'),list.length?badge(`${list.length} ARQUIVOS`):null)),
    el('p',{class:'source-note'},'Os vereditos vêm dos arquivos. O painel não ajusta critérios nem executa novas estratégias.')];
}
function field(label,value,cls=''){return el('div',{},el('dt',{},label),el('dd',{class:cls},value??'Não informado'));}
function tradeCard(op){return el('details',{class:'trade'},el('summary',{},el('span',{class:'trade-symbol'},op.contrato),el('div',{class:'trade-main'},el('b',{},`${op.lado==='comprado'?'Compra':'Venda'} · ${integer(op.quantidade)} ${op.quantidade===1?'contrato':'contratos'}`),el('small',{},`${dateTime(op.entrada)} · ${op.id}`)),el('div',{class:`trade-pnl ${op.resultado_liquido>=0?'positive':'negative'}`},money(op.resultado_liquido)),el('span',{class:'trade-arrow'},icon('arrow',14))),el('dl',{},field('Entrada prevista / executada',`${number(op.preco_entrada_previsto)} / ${number(op.preco_entrada_executado)}`,'mono'),field('Saída prevista / executada',`${number(op.preco_saida_previsto)} / ${number(op.preco_saida_executado)}`,'mono'),field('Taxas previstas / executadas',`${money(op.taxas_previstas)} / ${money(op.taxas_executadas)}`,'mono'),field('Stop / alvo',`${op.stop===null?'Não informado':number(op.stop)} / ${op.alvo===null?'Não informado':number(op.alvo)}`,'mono'),field('Líquido previsto',money(op.resultado_previsto),'mono'),field('Diferença do previsto',money(op.diferenca_liquido),'mono'),field('Desvio entrada / saída (ticks)',`${number(op.desvio_entrada_ticks)} / ${number(op.desvio_saida_ticks)}`,'mono'),field('Hipótese',op.hipotese),field('Saída (Brasília)',dateTime(op.saida)),field('Motivo da entrada',op.motivo_entrada),field('Motivo da saída',op.motivo_saida),field('Origem',op.origem)),el('p',{class:'trade-note'},'Desvio positivo em ticks indica execução pior que a referência. O slippage já está nos preços.'));}
function diaryView(){
  const list=kindList('diary'),r=findReport(state.diaryId)||list[0];
  const top=pageHeading('REFERÊNCIA × EXECUÇÃO','Diário do simulador','Entenda o que aconteceu em cada operação.',badge('SIMULADOR','green'));
  if(!r)return [top,panel('Operações encerradas','Entradas, saídas, custos e motivos.',empty('Seu diário começa com os registros','Importe o diario.json gerado pelo motor. Cada operação mostrará o previsto, o executado e o resultado depois das taxas.','book')),notice('Nesta fase, o diário respeita o período de desenvolvimento anterior a julho de 2026. Nenhuma operação recente é importada automaticamente.')];
  const s=statsFor(r),search=el('input',{class:'search',type:'search',placeholder:'Buscar contrato, ID ou motivo…','aria-label':'Buscar operações',value:state.query,oninput:e=>{state.query=e.target.value;state.tradeLimit=50;renderTrades(r);}});
  return [top,el('div',{class:'toolbar'},picker(list,r.id,id=>{state.diaryId=id;state.query='';render();}),search),el('div',{class:'metrics'},metric('Líquido executado',money(s.net),'Operações encerradas','wallet',s.net>=0?'positive':'negative'),metric('Resultado previsto',money(s.planned),'Referências informadas no diário','trend'),metric('Taxas executadas',money(s.fees),'Total da entrada e da saída','minus'),metric('Diferença do previsto',money(s.delta),'Executado menos referência','flask',s.delta>=0?'positive':'negative')),el('div',{class:'toolbar'},el('span',{class:'small muted'},`${integer(s.operations)} operações · acerto líquido ${percent(s.winRate)}`),button('Exportar JSON','download',()=>exportRecord(r),'text')),el('div',{id:'trade-results',class:'trade-list'}),notice('O relatório não mede posições abertas nem drawdown intradiário. Valores ausentes permanecem sem informação.','neutral')];
}
function renderTrades(r){
  const target=$('#trade-results');if(!target)return;
  const q=state.query.trim().toLocaleLowerCase('pt-BR');
  const ops=r.payload.operacoes.filter(o=>[o.id,o.contrato,o.lado,o.motivo_entrada,o.motivo_saida,o.hipotese].some(v=>v.toLocaleLowerCase('pt-BR').includes(q))).sort((a,b)=>Date.parse(b.saida)-Date.parse(a.saida));
  target.replaceChildren(...ops.slice(0,state.tradeLimit).map(tradeCard));
  if(!ops.length)target.append(el('p',{class:'status-line'},'Nenhuma operação corresponde à busca.'));
  if(ops.length>state.tradeLimit)target.append(button(`Mostrar mais · ${state.tradeLimit} de ${ops.length}`,'plus',()=>{state.tradeLimit+=50;renderTrades(r);}));
  target.classList.add('section-gap');
}
function qualityDetails(r){
  const p=r.payload,q=p.qualidade;
  const body=el('div',{},el('dl',{class:'data-fields'},field('Contrato declarado',p.contrato_declarado),field('Candles verificados',integer(q.candles),'mono'),field('Pregões observados',integer(q.pregoes),'mono'),field('Cobertura inicial',p.cobertura_observada?dateTime(p.cobertura_observada.inicio):'Não disponível'),field('Cobertura final',p.cobertura_observada?dateTime(p.cobertura_observada.fim):'Não disponível'),field('Duplicatas idênticas removidas',integer(q.duplicatas_removidas),'mono'),field('Pausas registradas',integer(q.pausas.length),'mono'),field('Linhas excluídas por data',integer(p.linhas_excluidas_por_data),'mono'),field('Origem declarada',p.origem_declarada),field('SHA-256 do arquivo',p.sha256_arquivo,'mono long-code')));
  if(p.erros.length)body.append(el('div',{class:'data-errors'},el('b',{},'Pontos que bloqueiam o histórico'),el('ul',{},...p.erros.map(e=>el('li',{},String(e))))));
  if(p.pausas_conferidas?.length)body.append(el('div',{class:'data-errors'},`${p.pausas_conferidas.length} pausa(s) com conferência registrada. Veja as evidências no manifesto exportado.`));
  return panel('Conferência do histórico','Identidade do arquivo e verificações informadas pelo motor.',body,badge(p.liberado_para_teste_dos_dados?'Conferência passou':'Dados bloqueados',p.liberado_para_teste_dos_dados?'green':'red'),[el('span',{},'Passar na conferência não certifica a origem e não aprova uma estratégia.')]);
}
function recordRow(r){return el('article',{class:'record'},el('span',{class:'record-kind'},icon(r.kind==='validation'?'flask':r.kind==='diary'?'book':'data',19)),el('div',{class:'record-info'},el('b',{},r.name),el('small',{},`${labelReport(r)} · ${dateTime(r.importedAt)}`)),el('div',{class:'record-actions'},el('button',{class:'icon-button','aria-label':`Exportar ${r.name}`,title:'Exportar JSON',onclick:()=>exportRecord(r)},icon('download',16)),el('button',{class:'icon-button','aria-label':`Remover ${r.name}`,title:'Remover deste navegador',onclick:()=>removeRecord(r)},icon('trash',15))));}
function dataView(){
  const qualities=kindList('quality'),r=findReport(state.qualityId)||qualities[0];
  return [pageHeading('PROCEDÊNCIA E ORGANIZAÇÃO','Seus dados','Arquivos identificados, resultados rastreáveis.',badge('ARMAZENAMENTO LOCAL')),
    el('div',{class:'metrics'},metric('Arquivos importados',integer(state.reports.length),'Guardados neste navegador','file'),metric('Validações',integer(kindList('validation').length),'Relatórios completos do motor','flask'),metric('Diários',integer(kindList('diary').length),'Operações encerradas no simulador','book'),metric('Conferências',integer(qualities.length),'Manifestos de qualidade do histórico','shield')),
    qualities.length?el('div',{},el('div',{class:'toolbar'},picker(qualities,r.id,id=>{state.qualityId=id;render();})),qualityDetails(r)):panel('Qualidade do histórico','Origem, hash, cobertura e pausas.',empty('Traga a conferência do MT5','Importe o JSON gerado por conferir-b3 para revisar o histórico que sustenta seus testes.','data')),
    el('div',{class:'section-gap'},panel('Arquivos neste navegador','Use exportar para transferir uma cópia a outro aparelho.',el('div',{class:'panel-body'},state.reports.length?el('div',{class:'record-list'},...state.reports.map(recordRow)):el('p',{class:'small muted'},'Nenhum arquivo importado. O resumo inicial vem do registro do projeto.'),el('p',{class:'source-note'},'Não há sincronização automática entre aparelhos. Seus relatórios não são enviados ao servidor do painel.')),button('Importar JSON','upload',openImport,'small-button ghost'))),
    el('p',{class:'privacy-note section-gap'},'O resumo da rodada 5R vem do repositório. Ele não inclui histórico de preços nem curvas inventadas. Os arquivos completos continuam no computador até você importá-los aqui.'),
    button('Como instalar e usar no celular','info',()=>$('#about-dialog').showModal(),'text')];
}
function render(){
  const hash=location.hash.slice(1);state.view=views[hash]?hash:'resumo';renderNav();
  const content=state.view==='resumo'?summaryView():state.view==='testes'?testsView():state.view==='diario'?diaryView():dataView();
  $('#main').replaceChildren(...content.filter(Boolean));
  if(state.view==='diario'){const r=findReport(state.diaryId)||kindList('diary')[0];if(r)renderTrades(r);}
  document.title=`${views[state.view].label} · TradeLab B3`;
}
function openDb(){return new Promise((resolve,reject)=>{if(!('indexedDB'in window)){reject(new Error('Armazenamento local indisponível neste navegador.'));return;}const request=indexedDB.open('tradelab-b3',1);request.onupgradeneeded=()=>request.result.createObjectStore('reports',{keyPath:'id'});request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);request.onblocked=()=>reject(new Error('Feche outras abas antigas do TradeLab e tente novamente.'));});}
function dbAction(mode,action){return new Promise((resolve,reject)=>{if(!state.db){reject(new Error('Não foi possível acessar o armazenamento local. Verifique as permissões do navegador.'));return;}const tx=state.db.transaction('reports',mode);const request=action(tx.objectStore('reports'));let result;request.onsuccess=()=>result=request.result;tx.oncomplete=()=>resolve(result);tx.onerror=()=>reject(tx.error||request.error);tx.onabort=()=>reject(tx.error||new Error('A gravação foi interrompida.'));});}
async function importFiles(files){
  if(!files?.length)return;
  if(state.importing){toast('Aguarde a importação em andamento.');return;}
  state.importing=true;
  openImport();const status=$('#import-status');status.replaceChildren();
  $('#choose-files').disabled=true;$('#choose-files').textContent='Conferindo arquivos…';
  let accepted=0;
  for(const file of [...files]){
    const row=el('div',{class:'import-result'},`${file.name}: conferindo…`);status.append(row);
    try{
      if(file.size>MAX_BYTES)throw new Error('Arquivo maior que 25 MB.');
      const raw=await file.text();const parsed=parseReportText(raw);
      const bytes=new TextEncoder().encode(raw);const hash=await crypto.subtle.digest('SHA-256',bytes);const id=[...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,'0')).join('');
      if(state.reports.some(r=>r.id===id)){row.classList.add('success');row.textContent=`${file.name}: já estava importado. Nenhuma duplicação.`;continue;}
      const r={id,name:file.name,importedAt:new Date().toISOString(),size:file.size,...parsed};
      await dbAction('readwrite',store=>store.put(r));state.reports.unshift(r);accepted++;
      if(r.kind==='validation'){state.validationId=id;state.summaryId=id;}else if(r.kind==='diary'){state.diaryId=id;if(!kindList('validation').length)state.summaryId=id;}else state.qualityId=id;
      row.classList.add('success');row.textContent=`${file.name}: importado e salvo neste navegador.`;
    }catch(error){row.classList.add('error');row.textContent=`${file.name}: ${error.message||'Não foi possível importar o arquivo.'}`;}
  }
  state.importing=false;$('#choose-files').disabled=false;$('#choose-files').textContent='Selecionar JSONs';$('#file-input').value='';render();
  if(accepted)toast(`${accepted} ${accepted===1?'arquivo importado':'arquivos importados'}.`);
}
function exportRecord(r){const blob=new Blob([JSON.stringify(r.payload,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=el('a',{href:url,download:r.name.replace(/[^\p{L}\p{N}._-]/gu,'_')||'tradelab.json'});document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function removeRecord(r){if(!confirm(`Remover "${r.name}" deste navegador? O arquivo original no seu computador não será alterado.`))return;try{await dbAction('readwrite',store=>store.delete(r.id));state.reports=state.reports.filter(x=>x.id!==r.id);for(const k of ['validationId','diaryId','qualityId'])if(state[k]===r.id)state[k]=null;if(state.summaryId===r.id)state.summaryId='project';render();toast('Registro removido deste navegador.');}catch(e){toast(e.message);}}
function connection(){const c=$('#connection');c.classList.toggle('offline',!navigator.onLine);c.lastElementChild.textContent=navigator.onLine?'Online':'Modo offline';}
function installButton(){const b=$('#install-button');b.replaceChildren(icon('download',15),el('span',{class:'install-label'},'Instalar'));b.hidden=window.matchMedia('(display-mode: standalone)').matches;b.onclick=async()=>{if(!state.deferredInstall){$('#about-dialog').showModal();return;}const prompt=state.deferredInstall;state.deferredInstall=null;await prompt.prompt();await prompt.userChoice;};}
async function boot(){
  $('#import-button').replaceChildren(icon('plus',14),'Importar JSON');$('#import-button').addEventListener('click',openImport);
  $('#upload-symbol').replaceChildren(icon('upload',22));
  for(const b of document.querySelectorAll('.icon-button.close-dialog'))b.replaceChildren(icon('close',18));
  for(const b of document.querySelectorAll('.close-dialog'))b.addEventListener('click',()=>b.closest('dialog').close());
  $('#about-button').addEventListener('click',()=>$('#about-dialog').showModal());
  $('#choose-files').addEventListener('click',()=>$('#file-input').click());
  $('#dropzone').addEventListener('click',()=>$('#file-input').click());
  $('#dropzone').addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();$('#file-input').click();}});
  $('#file-input').addEventListener('change',e=>importFiles(e.target.files));
  for(const type of ['dragenter','dragover'])$('#dropzone').addEventListener(type,e=>{e.preventDefault();$('#dropzone').classList.add('dragging');});
  for(const type of ['dragleave','drop'])$('#dropzone').addEventListener(type,e=>{e.preventDefault();$('#dropzone').classList.remove('dragging');});
  $('#dropzone').addEventListener('drop',e=>importFiles(e.dataTransfer.files));
  window.addEventListener('hashchange',()=>{render();window.scrollTo({top:0,behavior:'instant'});});
  window.addEventListener('online',connection);window.addEventListener('offline',connection);connection();installButton();
  window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();state.deferredInstall=e;});window.addEventListener('appinstalled',()=>{$('#install-button').hidden=true;toast('TradeLab instalado.');});
  const loaded=await Promise.allSettled([fetch('./project.json').then(r=>{if(!r.ok)throw new Error('Resumo indisponível');return r.json();}),openDb()]);
  if(loaded[0].status==='fulfilled')state.project=loaded[0].value;
  if(loaded[1].status==='fulfilled'){state.db=loaded[1].value;state.reports=await dbAction('readonly',store=>store.getAll());}
  else toast('O resumo está disponível, mas o armazenamento local não pôde ser aberto.');
  render();
  if('serviceWorker'in navigator)navigator.serviceWorker.register('./sw.js').catch(()=>toast('O painel abriu. O modo offline não pôde ser preparado neste navegador.'));
}
boot().catch(error=>{$('#main').replaceChildren(pageHeading('TRADELAB','Não foi possível abrir','Atualize a página para tentar novamente.'),notice(error.message));});
