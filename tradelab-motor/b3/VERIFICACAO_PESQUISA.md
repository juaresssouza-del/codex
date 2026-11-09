# Verificação da pesquisa de corretoras (Gemini, 09/11/2026)

A pesquisa do Gemini foi conferida contra fontes primárias e secundárias em 09/11/2026.
Nenhum número dela entra no motor sem passar por esta tabela.

## Sinais de dado inventado

- As 6 corretoras aparecem com custos, margens e respostas idênticos.
- As fontes são páginas iniciais (ex.: xpi.com.br, rico.com.vc), sem o trecho da regra
  escrita sobre robôs que foi pedido.
- A conta não fecha: R$ 0,25 por ponta × 2 = R$ 0,50, mas a tabela diz R$ 0,55
  (e R$ 1,20 × 2 = R$ 2,40, não R$ 2,65).
- Nenhum item marcado "não encontrado", apesar de vários não estarem respondidos.

## Conferência item a item

| Item | Gemini | Verificado | Situação |
|---|---|---|---|
| Valor do ponto do WIN | R$ 1,00 | **R$ 0,20 por ponto**, tick de 5 pontos = R$ 1,00 ([B3](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/mercado-de-acoes/futuro-de-ibovespa.htm)) | **Errado (5×)** |
| Vencimento do WIN | meses pares, quarta-feira mais próxima do dia 15 | igual ([B3](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/mercado-de-acoes/futuro-de-ibovespa.htm)) | Confirmado |
| Horário WIN | 9h–18h25 | 9h–18h25 a partir de 03/11/2026 ([InfoMoney](https://www.infomoney.com.br/mercados/b3-amplia-horario-de-funcionamento-3-novembro-2026-entenda/), [ADVFN](https://br.advfn.com/jornal/2026/10/b3-muda-horarios-de-negociacao-e-amplia-sessao-de-contratos-futuros-em-novembro)) | Confirmado (fonte secundária) |
| Horário WDO | 9h–18h25 | 9h–18h30, sem alteração ([Minhas Economias](https://minhaseconomias.com.br/blog/planejamento-financeiro/mudanca-nos-horarios-de-negociacao-da-b3-a-partir-de-9-de-marco)) | Divergente; conferir no ofício da B3 |
| Margem day trade | WIN R$ 100–155; WDO R$ 150 | mínimo da B3 desde 02/02/2026: WIN R$ 155, WDO R$ 140 ([Awake Trader](https://www.awaketrader.com/pt/educacao/impostos-mini-indice-mini-dolar-b3-2026)) | Parcial; R$ 100 fica abaixo do mínimo citado |
| Emolumentos B3 | WIN R$ 0,25; WDO R$ 1,20 por ponta | fontes conflitantes: XP diz que minicontratos são isentos de emolumentos; calculadoras estimam R$ 0,25 a R$ 1,03 ([XP](https://conteudos.xpi.com.br/aprenda-a-investir/relatorios/minicontratos/), [AutoProfit](https://autoprofit.trade/calculadora-custos-b3)) | **Não confirmado**; falta a tabela oficial da B3 |
| Robô em conta real | "Sim" nas 6 | Clear: relatos conflitantes, incluindo bloqueio ("Expert not authorized") e reclamação de que não libera robôs ([MQL5](https://www.mql5.com/pt/forum/160928), [Reclame Aqui](https://www.reclameaqui.com.br/clear-corretora-de-valores/propaganda-enganosa-nao-permite-operacoes-com-robos-metatrader-5_zIM3w-zdME3gxyRn/)) | **Não confirmado** para nenhuma |
| Histórico intradiário exportável | "não nativo, via MT5" | não respondido (quantos anos de M5/M15 de WIN e WDO) | **Em aberto, é o gargalo** |
| IR day trade | 20%, IRRF 1%, DARF 6015 | igual ([Awake Trader](https://www.awaketrader.com/pt/educacao/impostos-mini-indice-mini-dolar-b3-2026), [XP](https://conteudos.xpi.com.br/aprenda-a-investir/relatorios/minicontratos/)) | Confirmado |

"RLP" (Retail Liquidity Provider): a própria corretora pode ser a contraparte da ordem do
cliente. É o que viabiliza a corretagem zero, mas há conflito de interesse e pode afetar
a execução de um robô.

## O que já dá para concluir

O custo da B3 é de outra ordem de grandeza. Estimativa para 1 WIN, entrada e saída:
emolumentos de até ~R$ 0,50, corretagem zero com RLP e ~1 tick de slippage por lado
(R$ 2,00) ≈ **R$ 2,50 por operação**. Com o índice entre 130 e 150 mil pontos, o
contrato vale ~R$ 26 a 30 mil, e o custo fica em **~0,01% do valor negociado, contra
~0,3% na Binance Spot**: cerca de 30 vezes menor. Foi o custo que derrubou o day trade
em cripto.

Contraponto: a margem de R$ 155 controla ~R$ 28 mil, uma alavancagem de ~180 vezes.
Uma variação de 1% no índice (~1.400 pontos) muda R$ 280 por contrato. Margem baixa
não é risco baixo.

## O que falta, e como conseguir

1. **Regra escrita sobre robô em conta real:** pedir ao atendimento de 2 a 3 corretoras,
   por escrito (chat ou e-mail), as perguntas abaixo.
2. **Histórico intradiário:** é o que decide se dá para testar. Caminho mais provável:
   abrir o MT5 da corretora (conta demo, se houver) e ver quantos anos de M5 de `WIN$N`
   e `WDO$N` o servidor entrega, ou usar o export do Profit (Nelogica).
3. **Tabela oficial de emolumentos da B3** para day trade de minicontratos.

### Perguntas para enviar a cada corretora

1. Robôs (Expert Advisors) no MetaTrader 5 são permitidos em conta real para WIN e WDO?
   Existe alguma regra escrita (link ou trecho do contrato)?
2. É permitido conectar o MT5 a um programa em Python (biblioteca MetaTrader5) em conta real?
3. Há limite de ordens por segundo ou por dia, ou proibição de alta frequência?
4. Qual o custo mensal do MT5 e a condição de isenção?
5. Corretagem por contrato de WIN e de WDO em day trade, com e sem RLP.
6. Margem de day trade por contrato de WIN e de WDO, e o horário da zeragem automática.
7. Quantos anos de histórico de candles de 5 e 15 minutos de WIN e WDO (série contínua)
   o servidor do MT5 fornece? Há conta demo com esses dados?

## Segunda rodada do Gemini (XP, Genial, BTG) — 09/11/2026

Mesmo padrão da primeira: nenhum link, nenhum trecho de regra, "permitido" nas três e o
histórico ("padrão via servidor MT5") de novo sem número de anos. Repete números já
contestados: margem WIN "a partir de R$ 100" na Genial, abaixo do mínimo de R$ 155
citado para a B3, e margem WDO de R$ 150 contra R$ 140.

O que as fontes mostram:

| Corretora | Evidência encontrada | Situação |
|---|---|---|
| XP | O InfoMoney (do grupo XP) orienta que na XP não se rodem dois robôs no mesmo ativo ao mesmo tempo na mesma conta, o que indica que robô é usado lá ([InfoMoney](https://www.infomoney.com.br/?p=237553)) | Indício de que permite; falta a regra escrita |
| Genial | Página do MT5: corretagem zero só com adesão ao RLP e ao menos uma ordem por mês pela plataforma; tabela de taxas datada de 24/10/2022 ([Genial](https://www.genialinvestimentos.com.br/trader/plataformas/meta-trader/)). A central de suporte tem perguntas sobre robôs, sem resposta acessível ([suporte](https://suporte.genialinvestimentos.com.br/hc/pt-br/categories/360001451071-Plataformas)) | Custo condicionado; robô não confirmado |
| BTG | Relato em fórum de que o MT5 da BTG não oferece as séries contínuas de WIN e WDO ([MQL5](https://www.mql5.com/pt/forum/stock-exchange)) | Possível problema de histórico; robô não confirmado |

Ordem provisória: XP, Genial, BTG. Só a resposta escrita das corretoras decide.
