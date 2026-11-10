# Corretoras e dados para o TradeLab na B3

Pesquisa encerrada em **10/11/2026**. Destino: `juaresssouza-del/codex`, branch `claude/stoic-fermat-kpfnkk`. Escopo: pessoa física, WIN e WDO, day trade, robô próprio. Não houve abertura de conta, preenchimento de cadastro, envio de dados pessoais ou operação financeira.

**Decisão informada pelo titular: XP.** O objetivo imediato é testar no simulador. A mensalidade gratuita do MT5 está documentada; a corretagem específica de um EA próprio nessa conta real ainda é **não encontrado**. A tabela pública da XP exclui estratégias automatizadas da promoção de corretagem zero. Fontes: [XP custos][xp-c] e [XP plataformas][xp-p], consulta **10/11/2026**.

## 1. Tabela-resumo

Operação completa significa comprar e vender, ou vender e recomprar, a mesma quantidade no mesmo pregão. Os valores abaixo separam o **total confirmado para o robô** do cenário promocional de autoatendimento. Não incluem resultado da operação, spread, diferença entre preço esperado e executado, mensalidade rateada ou IR sobre lucro. Garantia não é despesa nem limite de perda.

**Convenções:** `C_WIN` é a tarifa B3 calculada na seção 2 para entrada e saída nas primeiras faixas; `C_WDO` depende também da conversão cambial oficial aplicável. A coluna de fontes/data cobre todos os valores numéricos da respectiva linha. “não encontrado” não significa inexistente ou gratuito.

| Corretora | MT5 para B3 | Robô próprio em conta real | Total de uma operação completa de um WIN: corretagem + ISS + B3 | Mesmo total para um WDO | Plataforma/mês | Margem day trade WIN / WDO | Anos de histórico intradiário garantidos | VPS | Fontes e consulta |
|---|---|---|---|---|---|---|---|---|---|
| XP | Sim | Sem regra escrita específica de EA próprio em conta real; oferece automação | **não encontrado para EA**; tarifa padrão e exclusão promocional na seção própria | **não encontrado para EA** | MT5 **R$ 0,00** | **R$ 155,00 / R$ 140,00**, mínimos sujeitos a aumento | não encontrado | Oferta, preço e localização: não encontrado | [Custos][xp-c], [plataformas][xp-p], [risco][xp-r], **10/11/2026** |
| Genial | Sim | Suporte escrito a robôs MQL5; menção literal ao recorte “EA próprio em conta real”: não encontrado | **não encontrado para EA**. Cenário anunciado de corretagem zero com RLP: `C_WIN`, se a conta/rota estiver elegível | **não encontrado para EA**; cenário elegível: `C_WDO` | MT5 anunciado a **R$ 0,00**; condições públicas divergentes, ver seção própria | não encontrado / não encontrado | não encontrado | Genial Cloud: **R$ 41,40**, com isenção condicionada; localização: não encontrado | [MT5][ge-m], [termos][ge-t], [Cloud preço][ge-cpreco], [Cloud isenção][ge-czero], [cálculo B3][b3-calc], **10/11/2026** |
| BTG Pactual | não encontrado em oferta oficial atual consultável | Sem regra escrita específica encontrada | **não encontrado para EA**. Autoatendimento elegível com RLP: `C_WIN` | **não encontrado para EA**; elegível com RLP: `C_WDO` | MT5 e automação própria: não encontrado | não encontrado / não encontrado | não encontrado | não encontrado | [Custos][btg-c], [tabela pública carregada pela página][btg-js], [cálculo B3][b3-calc], **10/11/2026** |
| Terra | não encontrado em oferta oficial atual consultável | Sem regra escrita específica encontrada | **não encontrado para EA**. Autoatendimento elegível com RLP: `C_WIN` | **não encontrado para EA**; elegível com RLP: `C_WDO` | MT5: não encontrado; Profit com isenção por sessões, preço cheio: não encontrado | não encontrado / não encontrado | não encontrado | não encontrado | [Corretagem][te-c], [plataformas][te-p], [cálculo B3][b3-calc], **10/11/2026** |
| CM Capital | não encontrado em oferta oficial atual consultável | Oferece robôs em Profit/Scalper; regra para EA MQL5 próprio: não encontrado | **não encontrado para EA**. Tabela geral com RLP: `C_WIN`; produtos de automação podem ter corretagem própria | **não encontrado para EA**; tabela geral com RLP: `C_WDO` | MT5: não encontrado; SmarttBot anunciado **R$ 169,90**, isenção com RLP; condições do plano próprio devem ser verificadas | **R$ 155,00–310,00 / R$ 140,00–280,00** | não encontrado | não encontrado | [Custos][cm-c], [plataformas][cm-p], [robôs][cm-robo], [cálculo B3][b3-calc], **10/11/2026** |
| Nova Futura | não encontrado em oferta oficial atual consultável | Oferece RoboTrader; regra para EA MQL5 próprio: não encontrado | **não encontrado para EA**. Clube Trader + RLP elegível: `C_WIN` | **não encontrado para EA**; Clube Trader + RLP elegível: `C_WDO` | MT5: não encontrado; Profit Pro **R$ 165,00**, isenção condicionada | **R$ 155,00 / R$ 140,00**, revisáveis | não encontrado | não encontrado | [Custos][nf-c], [Profit][nf-p], [Trader][nf-t], [cálculo B3][b3-calc], **10/11/2026** |

Para o cenário das primeiras faixas, **`C_WIN = R$ 0,50`**, sendo **R$ 0,18** de emolumentos e **R$ 0,32** de registro na ida e volta. É cálculo reproduzível, não cotação universal da conta. **`C_WDO` em reais para o mês da consulta: não encontrado**, pois a PTAX de conversão aplicável não foi obtida em fonte primária nesta pesquisa. As fórmulas e faixas estão na seção 2. Fontes: [WIN B3][b3-win-fee], [WDO B3][b3-wdo-fee] e [regras de cálculo][b3-calc], consulta **10/11/2026**.

### Critério de evidência

Foram usadas corretoras, B3, CVM e Receita para custos e regras. MetaQuotes, Nelogica e Cedro são fontes primárias de seus próprios produtos, sem provar condições de uma conta específica. Reclame Aqui aparece apenas porque o item de infraestrutura do briefing o solicita; é fonte complementar, sem valor de autorização regulatória.

Uma propaganda de plataforma que “automatiza” não confirma irrestritamente Python, alta frequência, EA próprio em conta real ou isenção de corretagem. Ausência de oferta pública de MT5 foi registrada como **não encontrado**, e não como “não oferece”.

### 1.1 Regulação — identificação usada nas seções abaixo

A consulta ao arquivo público `cad_intermed.csv`, no ZIP da CVM, foi feita por CNPJ e categoria. As linhas abaixo estão **EM FUNCIONAMENTO NORMAL**. Há também registros cancelados de outra categoria para algumas entidades; eles não foram confundidos com o registro atual de corretora.

| Entidade | CNPJ / código CVM | CVM | B3 | PQO atual | Fonte e consulta |
|---|---|---|---|---|---|
| XP Investimentos CCTVM | **02.332.886/0001-04 / 3247** | Sim | Sim, consta na relação oficial | não encontrado em registro individual legível nesta consulta | [Cadastro CVM][cvm-zip], [relação B3][b3-brokers], [ficha XP][b3-xp], **10/11/2026** |
| Genial Investimentos C. de Valores Mobiliários | **27.652.684/0001-62 / 3212** | Sim | Oferta contratada envolve também a Genial Institucional, abaixo | Ver ficha da Institucional | [Cadastro CVM][cvm-zip], [contrato MT5][ge-contrato], **10/11/2026** |
| Genial Institucional CCTVM | **05.816.451/0001-15 / 3620** | Sim | Sim, participante de negociação pleno | Sim, indicado na ficha B3 | [Cadastro CVM][cvm-zip], [ficha B3][b3-ge], **10/11/2026** |
| BTG Pactual CTVM | **43.815.158/0001-22 / 3522** | Sim | Sim, participante de negociação pleno | Sim, indicado na ficha B3 | [Cadastro CVM][cvm-zip], [ficha B3][b3-btg], **10/11/2026** |
| Terra Investimentos DTVM | **03.751.794/0001-13 / 6599** | Sim, distribuidora | Sim, consta na relação oficial | não encontrado | [Cadastro CVM][cvm-zip], [relação B3][b3-brokers], **10/11/2026** |
| CM Capital Markets CCTVM | **02.685.483/0001-30 / 3476** | Sim | Sim, participante de negociação pleno | Sim, indicado na ficha B3 | [Cadastro CVM][cvm-zip], [ficha B3][b3-cm], **10/11/2026** |
| Nova Futura CTVM | **04.257.795/0001-79 / 3697** | Sim | Sim, consta na relação oficial | não encontrado | [Cadastro CVM][cvm-zip], [relação B3][b3-brokers], **10/11/2026** |

Participação e PQO não garantem resultado do robô nem ausência de interrupções.

## XP Investimentos

### 1.1 Regulação

Sim para CVM e presença na relação B3; PQO atual: **não encontrado** em ficha individual legível. Identificação e links na tabela regulatória.

### 1.2 Robô e plataforma

- MT5 para B3: sim, **grátis**, sem quantidade mínima para isenção na linha do MT5. O comparativo é atualizado em **23/10/2026** e indica Windows, simulador e automação. Preço cheio diferente para o MT5: **não encontrado**. [Comparativo XP][xp-p], consulta **10/11/2026**.
- Regra escrita sobre algoritmos: **“Caso os clientes tenham interesse na utilização de robôs ou algoritmos específicos, deverão verificar e contratar plataformas externas.”** O documento distingue essas plataformas do Home Broker/app próprios. Autorização específica para EA próprio em conta real, Python e limites de ordens por segundo/dia ou HFT: **não encontrado**. [Procedimentos XP][xp-proc], consulta **10/11/2026**.
- Alternativas: Profit Pro **R$ 160,00/mês**, isento por **R$ 270,00** de corretagem ou **10** minicontratos com RLP; Ontick Basic grátis; SmarttBot Lite I **R$ 19,90/mês**, isenção por **20 WDO** com RLP. Disponibilidade de módulo de execução própria e eventual licença extra precisam ser conferidas no produto. [Comparativo XP][xp-p], consulta **10/11/2026**.
- Simulador: sim; duração e garantia pública de dados em tempo real especificamente no servidor demo: **não encontrado**. O [STATUS do projeto][status] informa contratação gratuita e falha de autenticação, sem acesso à conta nesta pesquisa; consulta **10/11/2026**.

### 1.3 Custos da corretora

| Item | WIN | WDO | Fonte e consulta |
|---|---|---|---|
| Padrão sem benefício, por contrato negociado/lado | **R$ 1,00** | **R$ 1,00** | [XP custos][xp-c], **10/11/2026** |
| Promoção RLP, autoatendimento elegível | **R$ 0,00** | **R$ 0,00** | [XP custos][xp-c], **10/11/2026** |
| Serviço expressamente denominado “Robôs e Estratégias Automatizadas Ontick” | **R$ 1,00 por contrato**, não extrapolar para EA do MT5 | Mesmo enquadramento; tarifa específica do EA: **não encontrado** | [XP custos][xp-c], **10/11/2026** |
| Tributos indicados sobre corretagem | **ISS 5%; PIS 0,65%; COFINS 4%**; regra exata de recomposição/arredondamento: **não encontrado** | Mesmos tributos | [XP custos][xp-c], **10/11/2026** |
| Mesa/risco, por contrato | Tabela de **R$ 16,00 a R$ 12,00**, conforme condição; valor pessoal: **não encontrado** | Mesma faixa | [XP custos][xp-c], **10/11/2026** |
| Abertura/manutenção e custódia de bolsa anunciadas | Sem cobrança | Sem cobrança | [XP custos][xp-c], **10/11/2026** |

A promoção exclui estratégias automatizadas. Na tarifa padrão, ida e volta somam **R$ 2,00 de corretagem** antes dos tributos. O total efetivo do EA é **não encontrado**; não se adotou a tarifa Ontick como se fosse a do MT5. Roteamento separado: **não encontrado**. Fonte: [XP custos][xp-c], consulta **10/11/2026**.

### 1.4 Margem e risco

O manual de risco **v67**, aprovado em **06/11/2026**, publica mínimos por contrato de **WIN R$ 155,00** e **WDO R$ 140,00**, passíveis de aumento. A transição de garantia intradiária ocorre, conforme modelo, **15 minutos** antes do encerramento sem leilão ou **10 minutos** antes com leilão. Horário fixo universal de zeragem do MT5: **não encontrado**. No modelo personalizado, consumo de **70%** da garantia pode provocar enquadramento; não é trava garantida de prejuízo. Posição remanescente pode sofrer encerramento compulsório e cobrança de mesa. Capital mínimo distinto da garantia: **não encontrado**. [Manual XP, seções de enquadramento e margem][xp-r], consulta **10/11/2026**.

### 1.5 Histórico

Anos garantidos de WIN e WDO em **1m, 5m, 15m e ticks: não encontrado**. Disponibilidade e método de ajuste de `WIN$`, `WIN$N`, `WDO$` e `WDO$N` no servidor XP: **não encontrado** em regra pública. Exportação CSV é recurso do MT5, descrito no procedimento comum abaixo; o intervalo solicitado não comprova o intervalo entregue. [XP plataformas][xp-p] e [MetaQuotes][mt-export], consulta **10/11/2026**.

### 1.6 Infraestrutura e reclamações

Para EA local, o terminal Windows precisa permanecer executando e conectado; é consequência técnica da execução no terminal, não promessa de hospedagem da XP. Oferta de VPS XP, preço e localização: **não encontrado**. [Comparativo XP][xp-p], consulta **10/11/2026**.

Reclame Aqui: **8,0/10**, período **01/05–31/10/2026**. Categorias gerais incluem atendimento e cobrança indevida. Tema predominante especificamente de instabilidade/execução do MT5: **não encontrado**. A nota geral não mede disponibilidade da plataforma. [Perfil][ra-xp] e [sobre][ra-xp-sobre], consulta **10/11/2026**.

## Genial Investimentos

### 1.1 Regulação

Sim, com distinção entre Genial Investimentos e Genial Institucional na tabela regulatória; PQO da Institucional confirmado na B3.

### 1.2 Robô e plataforma

MT5 é ofertado a custo zero. A página fala em RLP e **uma ordem mensal**; o rodapé/termos gerais exige **10 minicontratos reais por ciclo** para plataformas profissionais. A FAQ do Cloud tem condição específica diferente. Preço cheio inequívoco do MT5 fora da promoção: **não encontrado**. Não foi escolhida silenciosamente a regra mais barata. [Oferta MT5][ge-m] e [termos][ge-t], consulta **10/11/2026**.

Trecho escrito da FAQ: **“Você pode programar seu próprio robô utilizando a linguagem de programação MQL5”**. O contrato trata do envio de ordens à B3. A frase literal que autorize o recorte “EA próprio em conta real”, Python e limites numéricos de ordens/HFT: **não encontrado**. Suporte técnico a MQL5 está documentado; não foi convertido em autorização irrestrita de todas as rotas. [FAQ robôs][ge-robo] e [contrato][ge-contrato], consulta **10/11/2026**.

Alternativas: Profit Pro **R$ 140,40**, Scalper Pro **R$ 140,40**, Tryd **R$ 111,40/mês**, sujeitos às isenções/contrato. Licença adicional de automação real: **não encontrado**. Demo específica do MT5, duração e compromisso de tempo real: **não encontrado** em regra pública inequívoca. [Termos][ge-t] e [oferta MT5][ge-m], consulta **10/11/2026**.

### 1.3 Custos da corretora

WIN e WDO: corretagem anunciada **zero** em DMA com adesão e permanência no RLP, exceto operações excluídas, como zeragem compulsória. Preço cheio de cada mini sem RLP e tarifa específica do EA: **não encontrado** em tabela pública utilizável. Impostos agregados divulgados: **9,65%**; ISS isolado: **não encontrado**. Preços efetivos podem variar por escritório. Custódia, manutenção, roteamento separado e valor exato da zeragem: **não encontrado** para o escopo desta pesquisa. [Termos e aviso legal][ge-t], consulta **10/11/2026**.

### 1.4 Margem e risco

Margem atual WIN/WDO e capital mínimo: **não encontrado**. O valor ilustrativo no contrato não foi usado como margem vigente. O contrato de MT5 consultado prevê day trade e admite zeragem de posições remanescentes nos **15 minutos** anteriores ao fim do pregão; devem ser encerradas pelo cliente antes. Aceita Day/IOC/FOK e rejeita GTC/GTD/At Close nessa modalidade. Não extrapolar esse contrato a outra versão swing/netting. [Contrato MT5][ge-contrato], consulta **10/11/2026**.

### 1.5 Histórico

Anos de WIN/WDO em **1m, 5m, 15m e ticks: não encontrado**; série contínua e método de ajuste do servidor: **não encontrado**. CSV disponível tecnicamente no MT5, sem garantia de profundidade da corretora. [Oferta MT5][ge-m] e [MetaQuotes][mt-export], consulta **10/11/2026**.

### 1.6 Infraestrutura e reclamações

Genial Cloud hospeda MT5. Preço sem isenção: **R$ 41,40**. FAQ específica: **um minicontrato por ciclo**, enviado pela VM, com RLP, para manter gratuidade; termos gerais mencionam **10**, divergência a resolver no termo individual. Localização do servidor: **não encontrado**. EA local exige terminal ativo; a VM substitui esse computador enquanto estiver operacional. [Cloud][ge-cloud], [preço][ge-cpreco], [isenção][ge-czero] e [termos][ge-t], consulta **10/11/2026**.

Reclame Aqui: **9,3/10**, período disponível **01/04–30/09/2026**. Tema predominante de execução/instabilidade: **não encontrado**. [Perfil][ra-ge], consulta **10/11/2026**.

## BTG Pactual

### 1.1 Regulação

Sim, CVM e participante de negociação pleno B3; PQO indicado na ficha, conforme tabela regulatória.

### 1.2 Robô e plataforma

Oferta pública atual e preço de MT5 para B3, autorização de EA próprio em conta real, Python, limite de ordens por segundo/dia e regra de HFT: **não encontrado**. Contratação, mensalidade e licença de execução própria em alternativas profissionais: **não encontrado** nesta consulta. Demo, compromisso de tempo real e duração: **não encontrado**. A tabela citar “plataformas” não comprova autorização de um robô. Fontes examinadas: [custos][btg-c] e [regras e parâmetros][btg-r], consulta **10/11/2026**.

### 1.3 Custos da corretora

WIN e WDO por contrato negociado: autoatendimento com RLP **zero**. Sem RLP, a tabela regressiva mensal é a seguir; entrada e saída consomem contratos da tabela. As faixas são marginais, não se aplicou a última taxa retroativamente a todos os contratos. Fonte: [custos][btg-c] e [componente público da tabela][btg-js], consulta **10/11/2026**.

| Contratos no mês | R$/contrato | Fonte e consulta |
|---|---|---|
| 1–50 | 0,95 | [BTG][btg-c], [tabela][btg-js], **10/11/2026** |
| 51–100 | 0,90 | [BTG][btg-c], [tabela][btg-js], **10/11/2026** |
| 101–200 | 0,87 | [BTG][btg-c], [tabela][btg-js], **10/11/2026** |
| 201–500 | 0,76 | [BTG][btg-c], [tabela][btg-js], **10/11/2026** |
| 501–2.500 | 0,63 | [BTG][btg-c], [tabela][btg-js], **10/11/2026** |
| 2.501–5.000 | 0,33 | [BTG][btg-c], [tabela][btg-js], **10/11/2026** |
| 5.001–15.000 | 0,12 | [BTG][btg-c], [tabela][btg-js], **10/11/2026** |
| Acima de 15.000 | 0,05 | [BTG][btg-c], [tabela][btg-js], **10/11/2026** |

Mesa/liquidação compulsória: **R$ 16,00 por minicontrato**. Custódia de renda variável anunciada sem cobrança. ISS isolado, roteamento, manutenção e exceções para EA: **não encontrado**. A tabela é carregada por JavaScript público da página oficial; nenhum login foi utilizado. [Custos][btg-c] e [tabela][btg-js], consulta **10/11/2026**.

### 1.4 Margem e risco

Margem intradiária WIN/WDO, horário específico da zeragem do MT5, capital mínimo e regra individual para carregar posições: **não encontrado**. Não foi atribuída ao BTG uma margem de outra instituição. A existência de tarifa de liquidação compulsória está documentada; não se pressupõe que o robô possa carregar posição com garantia intradiária. [Custos][btg-c] e [regras][btg-r], consulta **10/11/2026**.

### 1.5 Histórico

Anos em **1m, 5m, 15m e ticks**, série contínua, ajuste de rolagem e exportação garantida pela corretora: **não encontrado**. Fonte examinada: [portal oficial de custos/plataformas][btg-c], consulta **10/11/2026**.

### 1.6 Infraestrutura e reclamações

VPS da corretora, preço, localização e exigências para terminal de EA próprio: **não encontrado**. O documento de regras prevê canais alternativos de atendimento; isso não equivale a hospedagem de robô. [Regras BTG][btg-r], consulta **10/11/2026**.

Reclame Aqui: **8,4/10**, período **01/05–31/10/2026**, obtido no comparativo do próprio RA. Tema predominante de instabilidade/execução: **não encontrado**. [Comparativo RA][ra-btg], consulta **10/11/2026**.

## Terra Investimentos

### 1.1 Regulação

Sim no cadastro CVM como distribuidora e na relação oficial B3. PQO atual: **não encontrado**, conforme tabela regulatória.

### 1.2 Robô e plataforma

MT5 para B3, preço cheio/promocional, regra escrita de EA próprio em conta real, Python e limites de ordens/HFT: **não encontrado**. Oferta oficial de Profit: One isento com RLP e operação em **quatro pregões distintos no mês**; Pro isento com RLP e operação em **dez pregões distintos no mês**. Preços cheios, módulo de automação, conta demo, tempo real e duração: **não encontrado** nas páginas públicas acessíveis. [Terra Trade][te-p], consulta **10/11/2026**.

### 1.3 Custos da corretora

WIN e WDO: **R$ 0,00 por contrato** para cliente classificado em Autoatendimento com RLP. Sem RLP, anúncio de tabela regressiva de **R$ 0,75 a R$ 0,15 por contrato**; faixas completas: **não encontrado**. ISS, custódia, manutenção, roteamento, tarifa de zeragem e corretagem específica do EA: **não encontrado**. A página completa de custos retornou acesso negado; não foi contornada. [Oferta oficial de corretagem][te-c] e [tabela completa][te-cfull], consulta **10/11/2026**.

### 1.4 Margem e risco

Margem WIN/WDO, horário de zeragem, capital mínimo e regra específica de posição no fim do dia: **não encontrado**. Fonte examinada: [tabela oficial][te-cfull], consulta **10/11/2026**.

### 1.5 Histórico

Anos garantidos em **1m, 5m, 15m e ticks**, contínua e ajuste: **não encontrado**. Exportação do Profit existe no produto Nelogica; licença e profundidade garantidas pela Terra: **não encontrado**. [Terra Trade][te-p] e [exportação Nelogica][ne-export], consulta **10/11/2026**.

### 1.6 Infraestrutura e reclamações

VPS, preço, localização e suporte a EA próprio em Windows: **não encontrado**. [Terra Trade][te-p], consulta **10/11/2026**.

Reclame Aqui: **6,8/10**, período **01/05–31/10/2026**, na listagem de reclamações. Tema predominante específico de execução/instabilidade: **não encontrado**. [RA Terra][ra-te], consulta **10/11/2026**.

## CM Capital

### 1.1 Regulação

Sim, CVM e participante de negociação pleno B3; PQO indicado na ficha, conforme tabela regulatória.

### 1.2 Robô e plataforma

MT5, EA MQL5 próprio em conta real, Python e limites de ordens/HFT de varejo: **não encontrado**. A oferta institucional de HFT não foi usada como permissão de varejo. A página oficial de robôs oferece estratégias em Profit/Scalper: **“Confira as estratégias disponíveis nas plataformas Profit e Scalper”**. Isso confirma produto de automação, sem confirmar toda estratégia própria ou sua tarifa. [Robôs CM][cm-robo], consulta **10/11/2026**.

SmarttBot é anunciado por **R$ 169,90/mês**, com isenção mediante RLP. Módulo adicional de automação própria em Profit/NTSL e seu custo: **não encontrado** de forma inequívoca. Há simulador no catálogo; compromisso de dados em tempo real e duração: **não encontrado**. [Catálogo][cm-p], consulta **10/11/2026**.

### 1.3 Custos da corretora

| Item | WIN | WDO | Fonte e consulta |
|---|---|---|---|
| Tabela geral, por contrato/lado com RLP | R$ 0,00 | R$ 0,00 | [CM custos][cm-c], **10/11/2026** |
| Sem RLP, por contrato/lado | R$ 0,99 | R$ 0,99 | [CM custos][cm-c], **10/11/2026** |
| Impostos sobre corretagem | 10,68% agregados; ISS isolado: não encontrado | Mesmo | [CM custos][cm-c], **10/11/2026** |
| Mesa/zeragem, por contrato | R$ 31,90 | R$ 31,90 | [CM custos][cm-c], [FAQ zeragem][cm-zero], **10/11/2026** |
| Abertura/manutenção/custódia de bolsa | Sem cobrança | Sem cobrança | [CM custos][cm-c], **10/11/2026** |
| Produto “Trade Certo e Gradiente Linear”, com RLP | R$ 0,49 por contrato | R$ 0,49 por contrato | [CM custos][cm-c], **10/11/2026** |
| Produto “Trade do Analista e Trade Quant”, em cada compra/venda | R$ 0,99 por contrato | R$ 1,99 por contrato | [CM custos][cm-c], **10/11/2026** |

Produtos automatizados têm preços próprios; não aplicar a tarifa geral zero a todos eles. Tarifa específica de EA MT5 e roteamento separado: **não encontrado**. [CM custos][cm-c], consulta **10/11/2026**.

### 1.4 Margem e risco

WIN **R$ 155,00–310,00**, WDO **R$ 140,00–280,00** por contrato; a corretora pode alterar a margem a qualquer momento. Critério exato para escolher cada ponta da faixa, horário fixo de zeragem, capital mínimo e tratamento específico de posição remanescente do robô: **não encontrado**. [CM custos][cm-c], consulta **10/11/2026**.

### 1.5 Histórico

Anos garantidos em **1m, 5m, 15m e ticks**, método de contínua da conta e CSV garantido pela corretora: **não encontrado**. O catálogo menciona exportação e backtest, mas não comprova a profundidade solicitada. Prazo de guarda de trilha de auditoria não foi confundido com histórico de candles. [Catálogo][cm-p], consulta **10/11/2026**.

### 1.6 Infraestrutura e reclamações

VPS da corretora, custo e localização: **não encontrado**. Exigência específica de terminal MT5 para EA próprio: **não encontrado**. A hospedagem de cada produto deve ser distinguida de um EA local. [Catálogo][cm-p], consulta **10/11/2026**.

Reclame Aqui: **9,0/10**, período disponível **01/04–30/09/2026**. Tema predominante específico de execução/instabilidade: **não encontrado**. [Perfil CM][ra-cm], consulta **10/11/2026**.

## Nova Futura

### 1.1 Regulação

Sim, CVM e relação B3. PQO atual: **não encontrado**, conforme tabela regulatória.

### 1.2 Robô e plataforma

MT5 para B3, EA MQL5 próprio em conta real, Python, limites de ordens e HFT: **não encontrado**. A página Trader oferece RoboTrader, sem regra pública suficiente para extrapolar a EA próprio. [Trader][nf-t], consulta **10/11/2026**.

Profit Max Trader **R$ 40,00**, Plus **R$ 139,00**, Pro **R$ 165,00**, Ultra **R$ 350,00/mês**. Com RLP, Max isento por **um** WIN/WDO por ciclo; Plus/Pro por **19 WDO ou 75 WIN**. Ultra sem isenção. Módulo adicional para executar estratégia própria em conta real: **não encontrado**. Há simulador e replay; duração e compromisso de tempo real da conta demo: **não encontrado**. [Profit oficial][nf-p], consulta **10/11/2026**.

### 1.3 Custos da corretora

WIN e WDO: **R$ 0,00 por contrato** no Clube Trader com RLP, **R$ 1,00** sem RLP; a ida e a volta são negócios distintos. Mesa/zeragem automática **R$ 25,00 por mini**. Abertura e manutenção sem cobrança. Tabela atualizada em **18/08/2026**. ISS, roteamento e tarifa específica do robô: **não encontrado**. [Custos Nova Futura][nf-c], consulta **10/11/2026**.

### 1.4 Margem e risco

Página pública indica **WIN R$ 155,00** e **WDO R$ 140,00**, revisáveis. Capital mínimo, garantia adicional individual, horário de zeragem e regra específica de posição deixada pelo robô: **não encontrado**. Não interpretar mínimos publicados como garantia de operação com apenas esse saldo. [Custos][nf-c], consulta **10/11/2026**.

### 1.5 Histórico

Anos garantidos em **1m, 5m, 15m e ticks**, contínua/ajuste da conta e profundidade CSV: **não encontrado**. Recursos gerais do Profit não asseguram a base contratada pela corretora. [Profit][nf-p], consulta **10/11/2026**.

### 1.6 Infraestrutura e reclamações

VPS, preço, localização e infraestrutura para EA próprio: **não encontrado**. [Trader][nf-t], consulta **10/11/2026**.

Reclame Aqui: **7,8/10**, período **01/05–31/10/2026**. Tema predominante específico de execução/instabilidade: **não encontrado**. [Perfil Nova Futura][ra-nf], consulta **10/11/2026**. As notas das corretoras têm janelas diferentes e não foram usadas como ranking de execução.

### Procedimento comum de histórico e integração

No MT5 desktop: abrir **Exibir → Símbolos → Barras/Ticks**, selecionar símbolo e período, solicitar ao servidor e exportar CSV. Configurar o máximo de barras pode ampliar o pedido; não cria dados ausentes. Conferir primeira/última data, lacunas, fuso, volume e método de rolagem de cada arquivo. Fonte técnica: [MetaQuotes, histórico de símbolos][mt-export], consulta **10/11/2026**.

O pacote Python `MetaTrader5` fornece integração técnica com o terminal. Isso não é regra de permissão de nenhuma corretora. Autorização escrita por corretora para envio real por essa integração: **não encontrado** nas fontes consultadas. [MetaQuotes, Python][mt-python], consulta **10/11/2026**.

## 2. B3 — contratos, sessão e tarifas

### Horários vigentes consultados

Horários de Brasília; calendário de feriados e alterações extraordinárias devem ser consultados antes de execução.

| Contrato/fase | Horário | Fonte e consulta |
|---|---|---|
| WIN pré-abertura | **08:55**, derivado dos **5 minutos** anteriores à abertura | [OC 055/2026-VNC][b3-055], **10/11/2026** |
| WIN negociação normal | **09:00–18:25**; call eletrônico iniciado às **18:25** | [OC 055/2026-VNC, anexo][b3-055], **10/11/2026** |
| WIN vincendo | Última sessão encerra às **18:00** | [OC 055/2026-VNC, notas do anexo][b3-055], **10/11/2026** |
| WDO pré-abertura e negociação normal | **08:55** e **09:00–18:30** | [Grade B3 câmbio][b3-h-wdo], **10/11/2026** |
| Janela de ajuste WIN / WDO | **18:00–18:15 / 15:50–16:00**; não confundir com fim da sessão | [OC 055][b3-055], [grade câmbio][b3-h-wdo], **10/11/2026** |

O **OC 055/2026-VNC, de 29/10/2026**, **revoga e substitui integralmente** o **OC 050/2026-VNC, de 13/10/2026** citado no briefing. O novo documento mantém o contexto do fim do horário de verão europeu em **25/10/2026** e americano em **01/11/2026**, com grades aplicáveis a partir de **26/10/2026** e **03/11/2026**. WDO **futuro** foi conferido na grade de câmbio, sem confundi-lo com opções WDO no anexo. Fontes: [OC 055][b3-055] e [grade de câmbio][b3-h-wdo], consulta **10/11/2026**.

A zeragem da corretora pode anteceder a grade da B3. Para o motor, calendário e encerramento da conta devem ser parâmetros separados, com tratamento do status de leilão/suspensão.

### Especificações e vencimentos

| Item | WIN | WDO | Fonte e consulta |
|---|---|---|---|
| Unidade econômica | Índice × **R$ 0,20** | **US$ 10.000** por contrato | [WIN][b3-win], [WDO][b3-wdo], **10/11/2026** |
| Cotação e valor do ponto | Pontos de índice; **R$ 0,20/ponto/contrato** | Reais por **US$ 1.000**; **R$ 10,00/ponto/contrato**, cálculo `10.000 / 1.000` | [WIN][b3-win], [WDO][b3-wdo], **10/11/2026** |
| Tick | **5 pontos = R$ 1,00** por contrato | **0,50 ponto = R$ 5,00** por contrato | [WIN][b3-win], [WDO][b3-wdo], valores monetários calculados, **10/11/2026** |
| Lote padrão | **Um contrato** | **Um contrato** | [WIN][b3-win], [WDO][b3-wdo], **10/11/2026** |
| Meses de vencimento | Meses pares | Todos os meses | [WIN][b3-win], [WDO][b3-wdo], **10/11/2026** |
| Data de vencimento | Quarta-feira mais próxima do dia **15**; sem sessão, próxima sessão | Primeiro dia de sessão do mês; último negócio na sessão anterior | [WIN][b3-win], [WDO][b3-wdo], **10/11/2026** |

A série contínua é insumo de análise; a ordem precisa apontar o vencimento negociável. Emendar contratos sem registrar o critério pode criar retornos artificiais. Rolagem não deve ser tratada como ganho/perda da estratégia sem negociação correspondente.

### Tarifas: regras de cálculo

ADV: compras/vendas ponderadas da família no mês anterior, arredondadas sem decimais; primeiro mês na faixa inicial. `Tarifa = (ADV × preço + adicional) / ADV`. Desconto progressivo usa cálculo análogo sobre ADV day trade; não aplicar a última faixa a todo o volume. [Regras B3][b3-calc], consulta **10/11/2026**.

Arredondar a centavos após cada etapa: tarifa, conversão pela **PTAX venda do último dia do mês anterior**, fator e desconto. Emolumentos: **35%**; registro: diferença, observados pisos de **R$ 0,01**. Tributos das tarifas já incluídos. [Regras B3][b3-calc], consulta **10/11/2026**.

#### WIN — tarifa única e desconto

WIN: peso ADV **0,20**, fator contratual **0,20**. Valores da tabela de tarifa única em reais, antes do fator e desconto. Fonte: [tarifas de índices][b3-win-fee], consulta **10/11/2026**.

| ADV ponderado da família | Preço da faixa (R$) | Adicional (R$) | Fonte e consulta |
|---|---|---|---|
| 1–50 | 1,97 | 0,00 | [B3 WIN][b3-win-fee], **10/11/2026** |
| 51–150 | 1,82 | 7,50 | [B3 WIN][b3-win-fee], **10/11/2026** |
| 151–500 | 1,72 | 22,50 | [B3 WIN][b3-win-fee], **10/11/2026** |
| 501–1.500 | 1,57 | 97,50 | [B3 WIN][b3-win-fee], **10/11/2026** |
| 1.501–3.500 | 1,42 | 322,50 | [B3 WIN][b3-win-fee], **10/11/2026** |
| 3.501–7.500 | 1,27 | 847,50 | [B3 WIN][b3-win-fee], **10/11/2026** |
| 7.501–15.000 | 1,17 | 1.597,50 | [B3 WIN][b3-win-fee], **10/11/2026** |
| Acima de 15.000 | 1,07 | 3.097,50 | [B3 WIN][b3-win-fee], **10/11/2026** |

| ADV day trade ponderado | Redução da faixa | Adicional do cálculo progressivo | Fonte e consulta |
|---|---|---|---|
| 1–5 | 35% | 0,00 | [B3 WIN][b3-win-fee], **10/11/2026** |
| 6–50 | 40% | -0,25 | [B3 WIN][b3-win-fee], **10/11/2026** |
| 51–150 | 55% | -7,75 | [B3 WIN][b3-win-fee], **10/11/2026** |
| 151–1.500 | 70% | -30,25 | [B3 WIN][b3-win-fee], **10/11/2026** |
| Acima de 1.500 | 75% | -105,25 | [B3 WIN][b3-win-fee], **10/11/2026** |

**Cálculo para as primeiras faixas**, por contrato em cada lado: `round(1,97 × 0,20; 2) = 0,39`; `round(0,39 × (1 − 35%); 2) = R$ 0,25`. Emolumentos `round(0,25 × 35%; 2) = R$ 0,09`; registro **R$ 0,16**. Ida e volta: **R$ 0,50**, repartidos em **R$ 0,18 + R$ 0,32**. Fontes e cálculo: [tabela WIN][b3-win-fee] e [regras][b3-calc], consulta **10/11/2026**.

#### WDO — tarifa única e desconto

WDO: peso ADV **0,20**, fator contratual **0,25**. A tabela de tarifa única é em **US$**, antes da conversão, fator e desconto. Fonte: [tarifas de dólar][b3-wdo-fee], consulta **10/11/2026**.

| ADV ponderado da família | Preço da faixa (US$) | Adicional (US$) | Fonte e consulta |
|---|---|---|---|
| 1–250 | 0,97 | 0,00 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 251–1.000 | 0,88 | 22,50 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 1.001–2.500 | 0,83 | 72,50 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 2.501–6.000 | 0,77 | 222,50 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 6.001–10.000 | 0,73 | 462,50 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 10.001–15.000 | 0,69 | 862,50 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 15.001–25.000 | 0,66 | 1.312,50 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 25.001–45.000 | 0,51 | 5.062,50 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 45.001–80.000 | 0,36 | 11.812,50 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| Acima de 80.000 | 0,33 | 14.212,50 | [B3 WDO][b3-wdo-fee], **10/11/2026** |

| ADV day trade ponderado | Redução da faixa | Adicional do cálculo progressivo | Fonte e consulta |
|---|---|---|---|
| 1–20 | 16% | 0,00 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 21–500 | 25% | -1,80 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 501–1.500 | 40% | -76,80 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 1.501–3.000 | 45% | -151,80 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 3.001–5.000 | 50% | -301,80 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 5.001–10.000 | 55% | -551,80 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 10.001–20.000 | 57,5% | -801,80 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 20.001–35.000 | 60% | -1.301,80 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| 35.001–60.000 | 62,5% | -2.176,80 | [B3 WDO][b3-wdo-fee], **10/11/2026** |
| Acima de 60.000 | 65% | -3.676,80 | [B3 WDO][b3-wdo-fee], **10/11/2026** |

Para primeiras faixas, seja `P` a PTAX aplicável: `U = round(0,97 × P; 2)`, `F = round(U × 0,25; 2)`, `T = round(F × (1 − 16%); 2)`, `C_WDO = 2 × T`; separar emolumentos/registro pela regra acima. Valor de `P` para fechar o custo em reais deste mês: **não encontrado**. Não foi estimado. Fontes: [WDO][b3-wdo-fee] e [cálculo][b3-calc], consulta **10/11/2026**.

As tabelas também publicam tarifa de liquidação no vencimento de **R$ 0,30 para WIN** e **US$ 0,12 para WDO**. Não foram acrescentadas à operação day trade encerrada antes do vencimento. Fontes: [WIN][b3-win-fee] e [WDO][b3-wdo-fee], consulta **10/11/2026**.

### Oscilação, leilões e circuit breaker

O arquivo B3 de **09/11/2026** indica limite diário ordinário de **10% para WIN** e **6% para WDO** sobre o ajuste anterior. Para o primeiro vencimento em aberto, há suspensão do limite na última sessão, segundo a nota do documento; WDO tem regras adicionais por vencimento. A B3 pode comunicar parâmetros extraordinários. [Oscilação diária, tabela e notas][b3-limite], consulta **10/11/2026**.

O circuito de proteção ligado ao Ibovespa tem estágios de queda de **10% / pausa de 30 minutos**, **15% / pausa de uma hora** e **20% / prazo decidido pela B3**. Há exceção nos **30 minutos** finais e regras de extensão de sessão. Não se deve supor que todos os derivativos cambiais parem exatamente pelos mesmos gatilhos: observar o status divulgado para cada instrumento. [Manual de negociação B3][b3-manual] e [CVM, leilões e circuit breaker][cvm-circuit], consulta **10/11/2026**.

Implicação para o motor: recusar entradas durante pré-abertura/leilão/suspensão quando a estratégia não os contempla, validar preço/tick e status, limitar repetição de ordens e reconciliar execuções antes de tentar novamente. Um stop não garante execução no preço programado durante interrupção ou falta de liquidez. São requisitos de implementação derivados das regras, não promessa de proteção da corretora.

## 3. Histórico fora da corretora

| Fonte/produto | Período, intervalos e conteúdo | Preço e formato | Contínua/rolagem | Licença pessoal para backtest | Fonte e consulta |
|---|---|---|---|---|---|
| Nelogica — Base Histórica de Dados | WINFUT/WDOFUT: disponibilidade publicada desde **01/05/2012**. Produto oferece intraday de minuto e negócio a negócio; OHLC e volumes no leiaute de barras. Confirmação de toda a janela sem lacunas: **não encontrado** | Compra avulsa; **preço não encontrado**. CSV, entrega por SFTP | Códigos contínuos publicados; método exato de ajuste aplicado ao pacote adquirido: **não encontrado**, confirmar no contrato | **não encontrado** em licença pública inequívoca do pacote | [Disponibilidade][ne-base], [introdução][ne-intro], **10/11/2026** |
| Profit desktop — exportação da plataforma | Janela publicada de **dois anos**, limitada por número de candles: **Pro 50.000, Plus 20.000, Ultra/Automação Premium 100.000**. Exporta OHLC, volume financeiro e quantidade; exportação tick WIN limitada a **oito dias** | Recurso da licença/plano; custo mensal depende da corretora. CSV pelo menu de exportação | WINFUT/WDOFUT e variantes; ver regra abaixo | Autorização contratual específica para uso externo em backtest: **não encontrado** | [Exportação Nelogica][ne-export], [séries][ne-series], **10/11/2026** |
| Cedro — Market Data Cloud / dados históricos | Oferta de histórico tick a tick, com data/hora, preço e quantidade. Anos mínimos garantidos para WIN/WDO e candles prontos de **5m/15m: não encontrado** | **Preço não encontrado**; produto histórico por FTP/API conforme contratação. Não confundir API de fim de dia com intraday | Por vencimento/contínua e ajuste: **não encontrado** | **não encontrado** | [Produtos/API Cedro][ce-api], [Market Data Cloud][ce-home], **10/11/2026** |
| B3 — histórico/UP2DATA e distribuidores | Catálogo e contratação oficial; janela pública contratável específica de WIN/WDO intraday: **não encontrado** nesta pesquisa | **Preço não encontrado**. UP2DATA documenta TXT/CSV/XML/JSON, conforme produto | Método do pacote específico: **não encontrado** | Há política/contratos de consumo; enquadramento e custo do uso pessoal não exibido em licença específica acessível: **não encontrado** | [Histórico B3][b3-hist], [UP2DATA FAQ][b3-up], [políticas vigentes][b3-policy], **10/11/2026** |
| B3 — COTAHIST público | Cotações **diárias do mercado à vista**; não atende ao histórico intradiário de WIN/WDO solicitado | Arquivos públicos ZIP/TXT; preço de pacote intraday de minis: **não encontrado** | Não aplicável ao objetivo | Não transforma acesso público em licença irrestrita de redistribuição | [Cotações históricas B3][b3-cotahist], **10/11/2026** |

**Resultado:** a oferta de Base Histórica Nelogica documenta início temporal suficiente para o horizonte do briefing, mas ainda faltam preço, licença pessoal e convenção de ajuste do pacote. Não há nesta pesquisa uma base gratuita com atendimento completo comprovado. Não se comprou pacote nem solicitou orçamento com dados pessoais.

Na exportação comum do Profit, “dois anos” não garante a entrega integral de qualquer intervalo intradiário: também vale o teto de candles do plano. Não foi calculada uma quantidade estimada de pregões para contornar esse limite. Fonte: [Nelogica exportação][ne-export], consulta **10/11/2026**.

Segundo a Nelogica, séries `FUT` consideram o contrato de maior relevância; `FUTV` mantém o vencimento até a penúltima sessão e troca no vencimento. A série histórica pode ajustar os preços passados pelo salto entre contratos, com ajuste configurável na plataforma. A convenção do arquivo comprado ou exportado deve ser registrada; não foi presumida idêntica em MT5 e Profit. [Séries históricas Nelogica][ne-series], consulta **10/11/2026**.

Candles de minuto podem ser agregados deterministicamente em intervalos maiores, desde que se preservem o calendário, o fuso, o volume e a fronteira de sessão. Isso é proposta de processamento do TradeLab, não informação de que o fornecedor já entrega todos os intervalos ou licencia qualquer uso.

## 4. Tributação — Receita Federal

| Tema | Regra confirmada | Fonte e consulta |
|---|---|---|
| IR de day trade no Brasil, incluindo futuros | **20%** sobre ganho líquido mensal; custos efetivamente pagos entram na apuração conforme regra fiscal | [Receita — Bolsa de Valores][rf-bolsa], **10/11/2026** |
| IRRF | **1%** sobre resultado líquido positivo das operações day trade do dia; antecipação dedutível do IR mensal, não soma automática para uma alíquota de **21%** | [Receita — Retenções][rf-ret], **10/11/2026** |
| Prejuízo | Compensável com ganho líquido de **day trade**, no próprio mês ou seguintes; não retroage a meses anteriores. Registrar no demonstrativo da declaração | [Receita — Compensações][rf-comp], **10/11/2026** |
| Saldo de IRRF | Compensação até dezembro do mesmo ano; remanescente pode ser objeto de restituição conforme procedimento da Receita | [Receita — Retenções][rf-ret], **10/11/2026** |
| DARF | Código **6015**, pagamento até o último dia útil do mês seguinte ao ganho | [Receita — Cálculo e pagamento][rf-pag], **10/11/2026** |

IR depende do resultado líquido e de compensações; não foi inventado um imposto fixo por operação na tabela de custos. As regras de isenção de vendas de ações não foram aplicadas ao day trade de minicontratos.

## 5. Ranking pelo custo completo de WIN

**Ranking definitivo para EA próprio em conta real: não encontrado.** Não é possível ordenar honestamente o total quando falta a tarifa do EA/rota e não há comprovação do histórico entregue. O critério solicitado foi aplicado até onde os dados permitem:

| Resultado da comparação | Corretoras | Custo de WIN no cenário anunciado | Desempate: EA próprio real / anos exportáveis | Fonte e consulta |
|---|---|---|---|---|
| Empate apenas no cenário promocional elegível, sem confirmação da tarifa do EA | Genial, BTG, Terra, CM Capital, Nova Futura | Corretagem zero; **subtotal corretagem + ISS sobre essa corretagem + B3 de R$ 0,50**, nas primeiras faixas. Taxas adicionais da conta/automação não confirmadas impedem chamá-lo de total do robô | Genial tem declaração escrita sobre MQL5; CM/Nova têm outros produtos de automação. Confirmação literal do recorte exigido e anos garantidos: **não encontrado**; sem desempate definitivo | [Genial][ge-t], [BTG][btg-c], [Terra][te-c], [CM][cm-c], [Nova][nf-c], [B3][b3-win-fee], [cálculo][b3-calc], **10/11/2026** |
| Fora do empate promocional para automação | XP | **Total do EA não encontrado**; promoção exclui automação, conforme seção de custos XP | Automação oferecida; regra específica e anos garantidos: **não encontrado** | [XP custos][xp-c], **10/11/2026** |

A escolha já feita pela XP permite continuar a preparação e o simulador, aproveitando a conta existente. **Não demonstra que a XP seja a mais barata para robô.** Obter a tarifa da rota efetiva vem antes de alimentar o motor com um custo definitivo. O resultado negativo ou reprovação de hipóteses na Binance não comprova vantagem estatística na B3.

## 6. Dados não encontrados e próximos passos concretos

| Pendência | Situação |
|---|---|
| XP: autorização de EA próprio e pacote Python em conta real | **não encontrado** por escrito com esse recorte |
| XP: corretagem da rota MT5/EA, recomposição dos tributos, roteamento e eventuais mínimos | **não encontrado**; não usar automaticamente o benefício RLP ou o preço Ontick |
| Todas: limite individual de ordens/segundo, ordens/dia e regra de HFT aplicável ao projeto | **não encontrado** |
| Todas: anos garantidos por WIN/WDO em cada intervalo e ticks, inclusive continuidade/ajuste do MT5 | **não encontrado** |
| Genial: conciliação entre oferta, termos gerais e condição específica do Cloud | **não encontrado** em termo individual; margens atuais e tarifa cheia por mini também **não encontrado** |
| BTG/Terra/CM/Nova: oferta atual oficial de MT5 e regras de EA próprio | **não encontrado**; não inferir inexistência |
| BTG/Terra: margens atuais; demais faltas de risco listadas em cada seção | **não encontrado** |
| Capitais mínimos distintos das garantias e horários individuais de zeragem | **não encontrado**, exceto referências relativas documentadas na XP/Genial |
| VPS e localização | **não encontrado** nas demais; Genial divulga preço/isenção, localização **não encontrado** |
| PQO atual XP/Terra/Nova | **não encontrado** em evidência individual atual legível nesta consulta |
| WDO: valor exato em reais aplicável ao mês desta pesquisa | **não encontrado**; falta o dado primário da conversão PTAX, não a fórmula |
| Base externa pronta para aquisição | Preço, licença pessoal e ajuste específico do pacote: **não encontrado** |
| Reclamações: tema predominante de execução/instabilidade por plataforma | **não encontrado**; notas gerais não substituem essa análise |

**Sequência para o projeto na XP:** recuperar privadamente as credenciais do simulador pelo canal oficial, confirmar conexão, exportar o histórico realmente disponível, auditar os arquivos e adaptar o motor. Não enviar senha pelo chat nem gravá-la no Git. O [STATUS][status] já registra a pendência de autenticação; consulta **10/11/2026**.

Para a resposta escrita da XP, o titular pode usar: “Pretendo executar estratégia própria em WIN/WDO via EA MQL5 no MT5 e, eventualmente, pacote Python MetaTrader5. Essa utilização é permitida na minha conta real? Qual a corretagem de cada compra e venda nessa rota, com tributos e roteamento? Qual a margem efetiva, o horário de zeragem e os limites de envio/cancelamento de ordens? Qual histórico exportável é fornecido e como a série contínua é ajustada?” Nenhum contato foi enviado nesta pesquisa.

## Fontes — links completos

Todos os links abaixo foram consultados em **10/11/2026**. Datas de atualização/validade do documento, quando disponíveis, foram separadas da data de consulta no texto. Páginas indisponíveis foram usadas apenas para registrar a limitação, não para preencher valores.

[xp-c]: https://www.xpi.com.br/custos-operacionais/
[xp-p]: https://web.xpi.com.br/xp/documentos/comparativo-de-plataformas/
[xp-r]: https://www.xpi.com.br/documentos/manual-de-risco/
[xp-proc]: https://www.xpi.com.br/documentos/procedimentos-plataforma-xp/
[ge-m]: https://www.genialinvestimentos.com.br/trader/plataformas/meta-trader/
[ge-t]: https://www.genialinvestimentos.com.br/trader/plataformas/termos-contratacao/
[ge-robo]: https://suporte.genialinvestimentos.com.br/hc/pt-br/articles/360055400032-Que-tipo-de-rob%C3%B4-eu-posso-usar-para-operar-no-MetaTrader-5
[ge-contrato]: https://genial-documents.s3.amazonaws.com/RV/Termo/Plataforma_MetaTrader.pdf
[ge-cloud]: https://suporte.genialinvestimentos.com.br/hc/pt-br/articles/4409684323860-O-que-%C3%A9-a-Genial-Cloud
[ge-cpreco]: https://suporte.genialinvestimentos.com.br/hc/pt-br/articles/4409684344212-Quais-ser%C3%A3o-os-custos-caso-eu-n%C3%A3o-cumpra-as-condi%C3%A7%C3%B5es-vigentes
[ge-czero]: https://suporte.genialinvestimentos.com.br/hc/pt-br/articles/4409692339476-Quais-s%C3%A3o-as-condi%C3%A7%C3%B5es-para-manter-a-plataforma-com-custo-zero
[btg-c]: https://investimentos.btgpactual.com/custos
[btg-js]: https://investimentos.btgpactual.com/chunk-YOPD6HGC.js
[btg-r]: https://static.btgpactual.com/media/regras-e-parametros-ctvm.pdf
[te-c]: https://vamosjuntos.terrainvestimentos.com.br/custos-de-corretagem
[te-cfull]: https://www.terrainvestimentos.com.br/custos/
[te-p]: https://vamosjuntos.terrainvestimentos.com.br/terra-trade---plataforma-gratis
[cm-c]: https://cmcapital.com.br/custos-operacionais/
[cm-p]: https://cmcapital.com.br/plataformas/
[cm-robo]: https://cmcapital.com.br/robostraders/
[cm-zero]: https://ajuda.cmcapital.com.br/hc/pt-br/articles/8180550230423-Custos-aplicados-a-Zeragem-Compuls%C3%B3ria
[nf-c]: https://www.novafutura.com.br/custos
[nf-p]: https://www.novafutura.com.br/profit
[nf-t]: https://www.novafutura.com.br/trader
[cvm-zip]: https://dados.cvm.gov.br/dados/INTERMED/CAD/DADOS/cad_intermed.zip
[b3-brokers]: https://www.b3.com.br/pt_br/solucoes/plataformas/interface-de-negociacao/trademate/top-brokers.htm
[b3-xp]: https://sistemaswebb3-listados.b3.com.br/participantsPage/detail/02332886000104?language=pt-br
[b3-ge]: https://sistemaswebb3-listados.b3.com.br/participantsPage/detail/05816451000115?language=pt-br
[b3-btg]: https://sistemaswebb3-listados.b3.com.br/participantsPage/detail/43815158000122?language=pt-br
[b3-cm]: https://sistemaswebb3-listados.b3.com.br/participantsPage/detail/02685483000130?language=pt-br
[b3-055]: https://www.b3.com.br/data/files/BE/16/C1/59/2F881A10F75B881AAC094EA8/OC%20055-2026-VNC%20NOVOS%20HORARIOS%20DE%20NEGOCIACAO_PT.pdf
[b3-h-wdo]: https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-participantes-e-traders/horario-de-negociacao/derivativos/cambio-e-dolar-pronto/
[b3-win]: https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/futuro-mini-de-ibovespa.htm
[b3-wdo]: https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/moedas/futuro-mini-de-taxa-de-cambio-de-reais-por-dolar-comercial.htm
[b3-win-fee]: https://b3.com.br/pt_br/produtos-e-servicos/tarifas/listados-a-vista-e-derivativos/renda-variavel/tarifas-de-ibovespa-e-indice-brasil-50/futuros-e-estruturadas/
[b3-wdo-fee]: https://b3.com.br/pt_br/produtos-e-servicos/tarifas/listados-a-vista-e-derivativos/moedas/tarifas-de-dolar-dos-estados-unidos/futuros-de-dolar/
[b3-calc]: https://b3.com.br/pt_br/produtos-e-servicos/tarifas/regras-de-calculo-para-derivativos-de-indices-moedas-commodities-e-divida-soberana/
[b3-limite]: https://www.b3.com.br/data/files/C3/A1/25/F4/072B1A10F75B881AAC094EA8/Oscilacao%20Maxima%20Diaria%20-%20PT%20-%2009112026.pdf
[b3-manual]: https://www.b3.com.br/data/files/C0/64/8B/70/2FE5E91064BF82E9AC094EA8/B3%20Trading%20Procedures%20Manual.pdf
[cvm-circuit]: https://www.gov.br/investidor/pt-br/investir/como-investir/como-funciona-a-bolsa/leiloes-e-circuit-braker
[mt-export]: https://www.metatrader5.com/pt/terminal/help/trading/market_watch
[mt-python]: https://www.metatrader5.com/pt/metaeditor/help/development/python
[ne-export]: https://ajuda.nelogica.com.br/hc/pt-br/articles/360044287672-Como-exportar-dados-hist%C3%B3ricos-de-ativos-para-o-Excel
[ne-base]: https://ajuda.nelogica.com.br/hc/pt-br/articles/11169188636443-Disponibilidade-de-Dados-Hist%C3%B3ricos-para-exporta%C3%A7%C3%A3o-em-CSV
[ne-intro]: https://ajuda.nelogica.com.br/hc/pt-br/articles/11169074066715-Introdu%C3%A7%C3%A3o-ao-produto-Base-Hist%C3%B3rica-de-Dados
[ne-series]: https://ajuda.nelogica.com.br/hc/pt-br/articles/360047164712-S%C3%A9ries-hist%C3%B3ricas
[ce-api]: https://ajuda.cedrotech.com/market-data/quais-sao-as-apis-do-market-data-cedro/
[ce-home]: https://www.marketdatacloud.com.br/
[b3-hist]: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/
[b3-up]: https://www.b3.com.br/main.jsp?doui_processActionId=setLocaleProcessAction&locale=pt_BR&lumA=1&lumII=2C9FBE6363B13B3A0163B28F63192B2E&lumPageId=8A6A922D600EFE0901600F1303653F46
[b3-policy]: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/politica-comercial-e-contratos/
[b3-cotahist]: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/
[rf-bolsa]: https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores/
[rf-ret]: https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/retencoes
[rf-comp]: https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/compensacoes
[rf-pag]: https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/calculo-e-pagamento-do-imposto
[ra-xp]: https://www.reclameaqui.com.br/empresa/xp-investimentos/
[ra-xp-sobre]: https://www.reclameaqui.com.br/empresa/xp-investimentos/sobre/
[ra-ge]: https://www.reclameaqui.com.br/empresa/genial-investimentos/
[ra-btg]: https://www.reclameaqui.com.br/compare/btg-pactual-digital/rico-corretora-de-investimentos/xp-investimentos/
[ra-te]: https://www.reclameaqui.com.br/empresa/terra-investimentos/lista-reclamacoes/
[ra-cm]: https://www.reclameaqui.com.br/empresa/cm-capital-e-plus/
[ra-nf]: https://www.reclameaqui.com.br/empresa/nova-futura-corretora/
[status]: https://github.com/juaresssouza-del/codex/blob/claude/stoic-fermat-kpfnkk/tradelab-motor/STATUS.md
