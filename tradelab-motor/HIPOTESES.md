# Registro de hipóteses

Toda hipótese testada entra aqui **antes** de rodar, com a configuração fixada. Quanto
mais hipóteses testadas, maior a chance de uma passar por sorte: este registro é o que
permite descontar isso. Hipótese reprovada não volta com parâmetro "ajustado".

Padrões, salvo indicação: capital 1.000 USDT, exposição 10%, risco 0,25%, stop 1%,
alvo 2%, taxa 0,1% e slippage 0,05% por lado, filtros da Binance, critérios de
`criterios.toml`, 200 rodadas aleatórias, objetivo do treino = resultado líquido.

**Período reservado:** de 2026-07 em diante (`reserva_inicio`). Só a estratégia que passar
em tudo é rodada nele, uma vez.

## Rodada 1 — 09/11/2026 — BTCUSDT 15m

Dados 2024-11 a 2026-11-08. Treino 6 meses, teste 1, mínimo de 30 operações no treino.
Feita antes de existir a reserva: estes testes **viram** jul-nov/2026.

| # | Estratégia | Grade | Resultado |
|---|---|---|---|
| 1 | SMA | 16 combinações | Reprovada (FL 0,55; −10,84%) |
| 2 | Rompimento | 10 combinações | Reprovada (FL 0,63; −8,53%) |
| 3 | RSI | 27 combinações | Reprovada (FL 0,49; −5,42%) |

## Rodada 2 — 09/11/2026 — BTCUSDT 5m, 1h e 4h

Hipótese: o custo fixo de ~0,3% por operação pesa menos em tempos gráficos maiores.
As mesmas três estratégias e grades da rodada 1 (a grade é em candles, então o
horizonte em horas muda com o tempo gráfico). Tudo até 2026-06.

| # | Tempo | Dados | Treino / teste | Mín. ops treino |
|---|---|---|---|---:|
| 4–6 | 5m | 2024-11 a 2026-06 | 6 / 1 meses | 30 |
| 7–9 | 1h | 2021-01 a 2026-06 | 6 / 1 meses | 20 |
| 10–12 | 4h | 2021-01 a 2026-06 | 12 / 1 meses | 15 |

Resultados (fora da amostra; "bruto" = antes de taxa e slippage; "aleatório" = % das
200 rodadas aleatórias que a estratégia superou):

| # | Tempo | Estratégia | Ops | Fator de lucro | Líquido | Bruto (USDT) | Aleatório | Veredito |
|---|---|---|---:|---:|---:|---:|---:|---|
| 4 | 5m | SMA | 879 | 0,42 | −23,99% | −5,86 | 94,5% | Reprovada |
| 5 | 5m | Rompimento | 598 | 0,45 | −17,65% | −13,07 | 72,5% | Reprovada |
| 6 | 5m | RSI | 327 | 0,31 | −10,13% | −9,34 | 24,0% | Reprovada |
| 7 | 1h | SMA | 481 | 0,67 | −11,43% | +20,20 | 91,0% | Reprovada |
| 8 | 1h | Rompimento | 529 | 0,66 | −13,63% | +13,12 | 82,5% | Reprovada |
| 9 | 1h | RSI | 458 | 0,48 | −18,35% | −60,66 | 0,5% | Reprovada |
| 10 | 4h | SMA | 127 | 0,49 | −5,59% | −18,99 | 9,5% | Reprovada |
| 11 | 4h | Rompimento | 229 | 0,81 | −3,32% | +33,90 | 100% | Reprovada |
| 12 | 4h | RSI | 215 | 0,50 | −9,17% | −30,57 | 5,0% | Reprovada |

Comprar e segurar com a mesma exposição: 5m −3,76% (05/2025–06/2026); 1h +6,82%
(07/2021–06/2026); 4h +2,48% (01/2022–06/2026).

Leitura:
- 5m é o pior tempo gráfico: o maior volume de operações paga o maior custo, e nenhuma
  estratégia tem resultado positivo nem antes dos custos.
- Reversão por RSI perde antes dos custos em todos os tempos gráficos: comprar queda
  em BTC, com este stop e alvo, é pior que entrar ao acaso.
- O único sinal consistente é seguir tendência em tempo gráfico maior. Rompimento 4h
  superou 100% das rodadas aleatórias e ganhou 0,15% por operação antes dos custos,
  mas cada operação custa ~0,29%. Não paga.
- Nenhuma das 12 hipóteses chegou perto do critério. Variações de parâmetro destas três
  estratégias não devem ser testadas de novo.

## Rodada 3 — 09/11/2026 — BTCUSDT 4h, seguir tendência sem alvo fixo

Registrada antes de rodar. Hipótese: o único sinal das rodadas 1–2 (rompimento em 4h,
positivo antes dos custos) era cortado por um desenho de day trade: alvo fixo de 2% e
stop de 1%, menor que um candle típico de 4h (1,31%). Seguir tendência ganha deixando a
operação correr e saindo só quando a tendência vira.

Desenho comum aos dois cenários:
- Estratégia `rompimento`, mesma grade (entrada 20/40/60/96, saída 10/20/48 candles).
  A saída pela mínima de M candles é o stop móvel: sobe com o preço, nunca desce.
- Sem alvo. Stop de emergência de 5%, fixo, não otimizado.
- Risco por operação 0,5%: com stop de 5%, a posição fica em 10% do caixa, como nas
  rodadas anteriores.
- 4h, 2021-01 a 2026-06, treino 12 meses, teste 1, mínimo de 15 operações no treino.

| # | Cenário de custo | Parâmetros |
|---|---|---|
| 13a | Hoje: ordem a mercado, sem BNB | taxa 0,1%, slippage 0,05% por lado |
| 13b | Ordem limitada na entrada + BNB | taxa 0,075%; entrada sem slippage, só executa se o preço voltar ao fechamento do sinal; saída a mercado com slippage 0,05% |

Regra de parada combinada: se 13a e 13b forem reprovadas, encerra a busca por estratégia
em BTC. Se uma passar, roda uma vez no período reservado antes de qualquer outro passo.

Resultados (fora da amostra, 01/2022 a 06/2026):

| # | Ops | Acerto | Fator de lucro | Líquido | Bruto (USDT) | Aleatório | Critérios | Veredito |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 13a | 100 | 37,0% | 1,37 | +7,07% | +100,59 | 93,5% | falha em operações e aleatório | Reprovada |
| 13b | 100 | 37,0% | 1,47 | +8,76% | +107,94 | 96,0% | falha só em operações (100 < 200) | Reprovada |

Comprar e segurar com a mesma exposição: +2,48%. Drawdown máximo 3,0%.

Correção feita durante a rodada, antes de aceitar o resultado: a 1ª execução da 13b
considerava executada a ordem limitada quando a abertura era **igual** ao limite, o que
acontece em 48% dos candles de 4h e é otimista (tocar o preço não garante a vez na fila).
A regra passou a exigir que o preço negocie abaixo do limite. Efeito: 2 ordens não
executadas; fator de lucro de 1,48 para 1,47. O número da tabela é o corrigido.

Leitura:
- Primeiro resultado positivo do projeto, e coerente com a hipótese: tirar o alvo e o stop
  curtos transformou o rompimento em 4h de −3,32% (rodada 2) em +7,07% com o mesmo custo.
  Ganho médio 2,3–2,5 vezes a perda média; o lucro vem de poucas operações longas.
- Pela régua fixada, as duas são **reprovadas**: 100 operações em 4,5 anos não bastam
  para separar vantagem de sorte. A régua não muda.
- Limitação conhecida: o walk-forward encerra a posição no fim de cada mês de teste
  (18 saídas "fim"). Para quem segue tendência isso corta operações vencedoras e paga
  custo a mais. Um robô real não fecharia a posição na virada do mês.
- O período reservado (07/2026 em diante) continua intocado.

## Rodada 4 — 09/11/2026 — hipótese 14: mais evidência para a 13

Registrada antes de rodar. Mesma regra da 13, sem reotimizar nada à mão. Muda só o que
pode trazer mais evidência e o que tornava o teste irreal:

- **Modo contínuo** (`--continuo`): a posição atravessa a virada de mês. Os parâmetros
  continuam escolhidos todo mês só com os 12 meses anteriores.
- **Mais histórico:** 2017-08 a 2026-06 (fora da amostra a partir de 2018-08).
- **Segundo ativo:** ETHUSDT, mesma regra e mesma grade.

Fixo: `rompimento`, grade da rodada 1, 4h, stop de emergência 5%, sem alvo, risco 0,5%
(posição de 10% do caixa), treino 12 meses, teste 1, mínimo de 15 operações no treino.

| # | Ativos | Custo |
|---|---|---|
| 14a | BTCUSDT + ETHUSDT | a mercado, sem BNB (taxa 0,1%, slippage 0,05%) |
| 14b | BTCUSDT + ETHUSDT | ordem limitada na entrada + BNB (taxa 0,075%) |

Regra de aprovação, fixada agora: a **14b conjunta** (`python -m motor agregar`, operações
somadas, pior drawdown e pior percentil entre os ativos) passa em todos os critérios de
`criterios.toml` **e** a **14a conjunta** tem expectativa positiva. BTC sozinho é
reportado, mas não decide.

Se aprovada: roda uma vez no período reservado (07/2026 em diante), 14b, nos dois ativos.
Se reprovada: encerra a busca por estratégia em cripto e o projeto segue para a B3.

Resultados (fora da amostra, 08/2018 a 06/2026, modo contínuo):

| | BTC 14a | BTC 14b | ETH 14a | ETH 14b |
|---|---:|---:|---:|---:|
| Operações | 168 | 168 | 181 | 182 |
| Acerto | 33,9% | 33,9% | 28,2% | 27,5% |
| Fator de lucro | 1,74 | 1,84 | 1,28 | 1,27 |
| Resultado | +31,89% | +35,63% | +16,44% | +15,64% |
| Drawdown | 8,98% | 8,43% | 12,28% | 11,40% |
| Supera o aleatório | 100% | 100% | 88,5% | 81,0% |
| Comprar e segurar (mesma exposição de 10%) | +67,50% | +67,58% | +27,54% | +27,58% |

Avaliação conjunta (`agregar`, regra fixada antes):

| | Operações | Fator de lucro | Pior drawdown | Pior percentil | Veredito |
|---|---:|---:|---:|---:|---|
| 14b (decide) | 350 | 1,51 | 11,40% (ETH) | 81,0% (ETH) | **Reprovada** |
| 14a | 349 | 1,48 | 12,28% (ETH) | 88,5% (ETH) | Reprovada |

Leitura:
- Pela regra registrada, a hipótese 14 está **reprovada**: em ETH a mesma regra não supera
  o aleatório e passa do drawdown máximo. A regra não muda depois do resultado.
- BTC sozinho passa em tudo menos no número de operações (168 < 200), mas não decide:
  escolher o ativo que deu certo depois de ver o resultado é o erro que a régua evita.
- **Contraponto decisivo:** com a mesma exposição de 10%, comprar e segurar rendeu mais
  que a estratégia nos dois ativos (BTC +67,5% contra +35,6%; ETH +27,6% contra +15,6%).
  Em 8 anos de alta do cripto, operar não superou ficar parado.
- Conforme combinado: **fim da busca por estratégia em cripto.** O período reservado
  (07/2026 em diante) não foi usado. O projeto segue para a B3.

## Rodada 5 — 11/11/2026 — B3: WIN e WDO, comprado e vendido

Registrada antes de rodar. Primeira rodada na B3, com o histórico de 5 anos do MT5 da XP
(`b3/DADOS.md`). Decisões do Juares: operar **comprado e vendido** e começar com
**R$ 1.000**, com a menor alavancagem possível, que é **1 contrato** por operação.

Desenho comum:
- `--lado ambos`, **1 contrato fixo** (`--max-contratos 1`), capital R$ 1.000.
- Stop 0,5%, sem alvo; saída pelo sinal contrário, pelo stop ou pela zeragem às 18h00.
  Sem entrada depois das 17h30; nada passa de um pregão para o outro.
- Custo de robô na XP: WIN R$ 1,35 e WDO R$ 2,24 por contrato e por lado, mais 1 tick
  de slippage em cada execução a mercado.
- Dados de 11/2021 a 06/2026 (o período reservado, de 07/2026 em diante, fica de fora).
  Treino 12 meses, teste 1, mínimo de 30 operações no treino, 200 rodadas aleatórias.
- Mesma régua de `criterios.toml`. A queda máxima é medida sobre os R$ 1.000.

| # | Contrato | Tempo | Estratégia | Grade |
|---|---|---|---|---|
| 15 | WIN | 5 min | `abertura` (faixa dos primeiros 15/30/60 min) | 3 combinações |
| 16 | WIN | 15 min | `rompimento_curto` (máx./mín. de 6/12/20 candles; saída 3/6/12) | 6 combinações |
| 17 | WDO | 5 min | `abertura` | 3 combinações |
| 18 | WDO | 15 min | `rompimento_curto` | 6 combinações |

Leitura combinada antes do teste:
- Com R$ 1.000, 1 contrato já é alavancagem de ~35× (WIN) e ~56× (WDO): um stop de 0,5%
  custa ~18% (WIN) e ~28% (WDO) do capital. **O critério de queda máxima de 10% deve
  falhar mesmo que a estratégia tenha vantagem.** Por isso o relatório também mostra o
  capital necessário para a pior queda caber em 10%.
- Leitura: se uma hipótese passar em operações, fator de lucro, expectativa e percentil, e
  falhar só na queda máxima, a conclusão é "vantagem, mas capital insuficiente": segue
  para o período reservado e para o simulador, e não para dinheiro real com R$ 1.000.
- Se falhar em vantagem, está reprovada como as anteriores.

Resultado com R$ 1.000 (fora da amostra a partir de 11/2022): **as quatro quebram a conta.**

| # | Resultado | Pior queda | Capital para a pior queda caber em 10% | Operações até parar |
|---|---:|---:|---:|---:|
| 15 WIN abertura 5m | −86,0% | R$ 1.313 | R$ 13.130 | 60 |
| 16 WIN rompimento 15m | −88,6% | R$ 1.068 | R$ 10.684 | 118 |
| 17 WDO abertura 5m | −84,0% | R$ 1.166 | R$ 11.658 | 9 |
| 18 WDO rompimento 15m | −93,5% | R$ 1.200 | R$ 12.003 | 19 |

Depois da queda, o saldo fica abaixo da margem e o robô para de operar (dezenas de milhares
de entradas recusadas). **Conclusão sobre o capital: R$ 1.000 não sustenta 1 minicontrato.**

A quebra encurtou a amostra e impediu julgar a vantagem. Correção de medição, registrada
antes de rodar: **15b a 18b**, as mesmas quatro hipóteses, mesma regra, 1 contrato, com
capital de medição de **R$ 100.000** só para a conta não quebrar no meio. O resultado em
reais por operação é o mesmo; muda só o tamanho da amostra. O critério de queda máxima
perde sentido nessa medição (é % de R$ 100 mil); valem operações, fator de lucro,
expectativa e percentil contra o aleatório.

Resultado da medição 15b–18b (1 contrato, R$ 100 mil só para não quebrar; 11/2022 a 06/2026):

| # | Ops | Acerto | Fator de lucro | Antes dos custos | Custos | Líquido | Supera o aleatório | Pior queda (R$) | Veredito |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 15b WIN abertura 5m | 1.459 | 40,6% | 0,99 | **+6.255** | 6.857 | −602 | 99,0% | 7.796 | Reprovada |
| 16b WIN rompimento 15m | 975 | 42,4% | 0,93 | **+1.727** | 4.583 | −2.856 | 98,5% | 4.668 | Reprovada |
| 17b WDO abertura 5m | 1.164 | 43,9% | 0,90 | **+4.945** | 16.855 | −11.910 | 100% | 14.306 | Reprovada |
| 18b WDO rompimento 15m | 688 | 42,0% | 0,81 | **+1.715** | 9.962 | −8.247 | 100% | 9.344 | Reprovada |

Leitura:
- **Há sinal real na B3:** as quatro ganham antes dos custos e superam quase todas as rodadas
  aleatórias, comprado e vendido. É o padrão mais consistente do projeto.
- **O sinal é menor que o custo.** No melhor caso (15b, WIN abertura), o ganho antes dos
  custos é ~R$ 4,29 por operação e o custo, ~R$ 4,70. Com corretagem zero para robô (a XP
  não dá), sobraria ~R$ 1,80 por operação: fator de lucro perto de 1,04, ainda longe de 1,3.
- **Capital:** a pior queda de 1 contrato vai de R$ 4,7 mil a R$ 14,3 mil. Para caber em 10%,
  seriam necessários de R$ 47 mil a R$ 143 mil. R$ 1.000 quebra (rodada 5 original).
- 18 hipóteses testadas no projeto; nenhuma aprovada. O período reservado continua intocado.

## Rodada 5R — 11/11/2026 — reexecução técnica das hipóteses 15–18 e 15b–18b

Registrada antes de rodar. **Não é hipótese nova.** Mesmas estratégias, grades, parâmetros,
custos, horários e critérios; muda só a versão do motor, corrigida pela auditoria do Codex
(`AUDITORIA_CODEX.md`, commits `a21d4ce` e `cfde595`): queda medida dentro do candle antes
da saída, pico anterior ao candle, saída explícita na B3, agregação de 15 min só com blocos
completos, entrada bloqueada perto da zeragem. Objetivo: saber como as correções mudam os
números e se o veredito se mantém.

Correções do próprio registro, apontadas pela auditoria:
- O `rompimento_curto` tem **8 combinações**, não 6 como escrito na rodada 5 (saída ≤
  entrada em entrada 6/12/20 × saída 3/6/12). O código não mudou: as rodadas 5 e 5R usam 8.
- A "saída pela mínima de M candles" das hipóteses 13 e 14 é saída **por sinal**, não um
  stop móvel que só sobe.

Dados: os mesmos CSVs do MT5 (WIN SHA-256 `651f10d4…44f6`, WDO `5b8167f4…2a26`), sem a
reserva (07/2026 em diante). A conferência (`conferir-b3`) bloqueou o WIN por duas pausas
dentro do pregão; foram investigadas e documentadas em `b3/PAUSAS_CONFERIDAS.toml`, sem
apagar nem preencher candles: 21/08/2025 (falha da B3, confirmada por resposta da B3 no
Reclame Aqui) e 03/06/2025 (causa não encontrada; afeta um pregão).

Configurações (iguais às da rodada 5):
- 15–18: `--capital 1000 --risco 100 --exposicao 100 --max-contratos 1 --stop 0.5 --alvo 0
  --lado ambos --treino 12 --min-operacoes-treino 30`.
- 15b–18b: as mesmas, com `--capital 100000`.
- 15/15b WIN 5m `abertura`; 16/16b WIN 15m `rompimento_curto`; 17/17b WDO 5m `abertura`;
  18/18b WDO 15m `rompimento_curto`. WIN com `--pausas-conferidas b3/PAUSAS_CONFERIDAS.toml`.

Comparação a reportar, antigo contra novo: resultado líquido, custos, fator de lucro,
número de operações e maior queda do saldo.

Resultados da 5R (motor 0.3.0), antigo → novo. Fora da amostra, 11/2022 a 06/2026.

Com R$ 1.000 (15–18):

| # | Operações | Fator de lucro | Líquido (R$) | Custos (R$) | Pior queda (R$) | Supera o aleatório | Veredito |
|---|---|---|---|---|---|---|---|
| 15 WIN abertura 5m | 60 → 60 | 0,82 → 0,82 | −860 → −860 | 282 → 282 | 1.313 → 1.313 | 80,0% → 23,5% | Reprovada |
| 16 WIN rompimento 15m | 118 → 682 | 0,84 → 0,96 | −886 → −984 | 555 → 3.205 | 1.068 → 2.264 | 55,5% → 0,0% | Reprovada |
| 17 WDO abertura 5m | 9 → 9 | 0,48 → 0,48 | −840 → −840 | 130 → 130 | 1.166 → 1.166 | 45,0% → 3,5% | Reprovada |
| 18 WDO rompimento 15m | 19 → 19 | 0,64 → 0,64 | −935 → −935 | 275 → 275 | 1.200 → 1.200 | 17,0% → 0,0% | Reprovada |

Com R$ 100 mil, 1 contrato (15b–18b):

| # | Operações | Fator de lucro | Antes dos custos (R$) | Custos (R$) | Líquido (R$) | Pior queda (R$) | Supera o aleatório | Veredito |
|---|---|---|---|---|---|---|---|---|
| 15b WIN abertura 5m | 1.459 → 1.459 | 0,99 → 0,99 | +6.255 → +6.255 | 6.857 → 6.857 | −602 → −602 | 7.796 → 7.796 | 99,0% → 96,5% | Reprovada |
| 16b WIN rompimento 15m | 975 → 956 | 0,93 → 0,95 | +1.727 → +2.478 | 4.583 → 4.493 | −2.856 → −2.015 | 4.668 → 3.916 | 98,5% → 86,0% | Reprovada |
| 17b WDO abertura 5m | 1.164 → 1.164 | 0,90 → 0,90 | +4.945 → +4.945 | 16.855 → 16.855 | −11.910 → −11.910 | 14.306 → 14.306 | 100% → 96,0% | Reprovada |
| 18b WDO rompimento 15m | 688 → 687 | 0,81 → 0,82 | +1.715 → +2.010 | 9.962 → 9.948 | −8.247 → −7.938 | 9.344 → 9.034 | 100% → 78,5% | Reprovada |

Leitura:
- **Veredito igual: as 8 reprovadas.** Nenhuma correção virou um resultado negativo em positivo.
- **5 minutos (15, 17): operações e dinheiro idênticos.** As correções de execução não
  alteraram nenhuma operação; mudou só a comparação com o aleatório.
- **15 minutos (16, 18): pequenas mudanças.** A agregação agora descarta blocos incompletos
  (no WIN, o bloco das 18h15 de cada pregão, que tem só 2 candles e fica depois da zeragem
  das 18h00). Em 16 com R$ 1.000, isso mudou o caminho da conta: ela quebra mais devagar
  (682 operações em vez de 118), mas quebra igual (−98%).
- **A comparação com o aleatório caiu em todas.** O aleatório corrigido sabe encerrar a
  posição em vez de virar a mão, e por isso ficou melhor. Com isso o rompimento (16b,
  18b) deixou de superar 95% do aleatório. Só a faixa de abertura (15b, 17b) ainda supera.
  **O "sinal real" da rodada 5 encolheu:** vale para a faixa de abertura, não para o
  rompimento, e continua menor que o custo.
- A queda máxima em reais não mudou nos testes de 5 min. A medição corrigida da queda
  dentro do candle só fez diferença nos de 15 min.

## Rodada 6 — 11/11/2026 — B3: média móvel, candle de força e martingale

Registrada antes de rodar. Pedido do Juares: testar métodos que gerem lucro com
**R$ 1.000,90**, podendo usar média móvel, candle de força e martingale.

Já são 18 hipóteses (26 medições contando a 5R). Com mais 7, uma delas pode superar 95%
do aleatório só por sorte. **Regra mais dura, fixada agora:** um método só vira candidato
se, na medição com capital que não quebra (R$ 100 mil, 1 contrato), passar em todos os
critérios de `criterios.toml` **no WIN e no WDO ao mesmo tempo**. Só então vai ao período
reservado, uma vez.

Desenho comum (igual ao da rodada 5): 5 min, comprado e vendido, stop 0,5%, sem alvo,
zeragem 18h00, sem entrada depois das 17h30, custo de robô XP (WIN R$ 1,35 e WDO R$ 2,24
por contrato e lado) mais 1 tick, treino 12 meses, teste 1, mínimo de 30 operações no
treino, dados de 11/2021 a 06/2026, WIN com `b3/PAUSAS_CONFERIDAS.toml`. Cada hipótese
roda duas vezes: com **R$ 1.000,90** (o capital real) e com **R$ 100 mil** (medição).

| # | Contrato | Estratégia | Grade |
|---|---|---|---|
| 19 / 20 | WIN / WDO | `sma`: cruzamento de médias, dentro do pregão | 16 combinações |
| 21 / 22 | WIN / WDO | `forca`: entra a favor de candle de força (amplitude ≥ k × média dos N anteriores, corpo ≥ 60%) | N 10/20 × k 1,5/2/3 |
| 23 / 24 | WIN / WDO | `forca_reversao`: o mesmo candle, entrando contra (exaustão) | idem |
| 25 | WIN | `abertura` (a melhor da rodada 5) com **martingale**: dobra os contratos após cada perda, volta a 1 após um ganho, até a margem e no máximo 16 | 3 combinações |

Martingale, leitura combinada antes: ele não muda o resultado médio por contrato; só
redistribui o risco. É avaliado no capital real (R$ 1.000,90) e também em R$ 100 mil para
mostrar o tamanho das perdas. Só seria aceito se passasse em todos os critérios com o
capital real.

Resultados da rodada 6 (fora da amostra, 11/2022 a 06/2026):

Medição com R$ 100 mil e 1 contrato (decide pela regra registrada):

| # | Ops | Acerto | Fator de lucro | Antes dos custos (R$) | Custos (R$) | Líquido (R$) | Pior queda (R$) | Supera o aleatório | Veredito |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 19b WIN média móvel | 1.710 | 39,5% | 0,86 | +256 | 8.037 | −7.781 | 9.855 | 62,0% | Reprovada |
| 20b WDO média móvel | 1.142 | 36,1% | 0,71 | −250 | 16.536 | −16.786 | 17.117 | 41,0% | Reprovada |
| 21b WIN força a favor | 789 | 38,9% | 0,84 | −2.547 | 3.708 | −6.255 | 7.524 | 17,0% | Reprovada |
| 22b WDO força a favor | 166 | 44,6% | **1,31** | +6.245 | 2.404 | **+3.841** | 2.617 | **100%** | Reprovada (166 < 200 ops; WIN falha) |
| 23b WIN força contra | 232 | 48,3% | 0,83 | −1.289 | 1.090 | −2.379 | 2.959 | 10,5% | Reprovada |
| 24b WDO força contra | 293 | 46,1% | 0,68 | −4.065 | 4.243 | −8.308 | 8.728 | 3,5% | Reprovada |
| 25b WIN abertura + martingale | 1.430 | 41,5% | 0,95 | +10.273 | 26.611 | −16.338 | **46.261** | 67,5% | Reprovada |

Com o capital real, R$ 1.000,90: **as 7 quebram a conta** (−78% a −90%). O martingale (25)
quebrou nas **3 primeiras operações**: 3 perdas seguidas (1, 2 e 4 contratos) levaram
R$ 855, e o saldo restante não cobria mais a margem.

Leitura:
- **Média móvel e candle de força contra o movimento: sem sinal.** Perdem antes dos custos
  ou ficam em zero, e não superam o aleatório.
- **Martingale:** dobrar a posição multiplicou os custos (R$ 26,6 mil contra R$ 6,9 mil da
  mesma estratégia com 1 contrato) e a pior queda (R$ 46 mil contra R$ 7,8 mil). Não mudou o
  resultado médio por contrato. Confirmado com os dados: martingale acelera a quebra.
- **22b (WDO, candle de força a favor) é a melhor medição do projeto na B3:** fator de lucro
  1,31, +R$ 3.841, supera 100% do aleatório, queda de 2,6%. **Não vira candidato** pela regra
  fixada antes: falha no número de operações (166 < 200) e o mesmo método perde no WIN (21b,
  fator 0,84). Com 33 medições feitas, um resultado assim em um único mercado é exatamente o
  falso positivo que a regra existe para barrar. Fica registrado como observação; só pode
  voltar como hipótese nova, registrada antes, com dados que ele ainda não viu.
- 25 hipóteses testadas no projeto; nenhuma aprovada. O período reservado continua intocado.

## Rodada 7 — 11/11/2026 — filtro de agenda e operação só em canal

Registrada antes de implementar e de rodar.

### Hipótese 26 — filtro de agenda econômica (aguarda dados)

A observação da rodada 6 (candle de força a favor no WDO, `forca`, média de 20 candles,
k = 3) **com filtro de agenda**: nenhuma entrada nos dias de **decisão do FOMC** (Fed),
**payroll** americano e **IPCA**, nem no pregão seguinte a uma **decisão do Copom** (anunciada
depois do fechamento). Mesmo stop, zeragem e custos da rodada 6; 1 contrato; R$ 100 mil de
medição; mesma régua.

Hipótese: o candle de força em dia de notícia é ruído de evento, não movimento que continua.
Dados necessários antes de rodar: o calendário oficial dessas datas de 11/2021 a 06/2026
(Fed, BLS, IBGE, Banco Central), com fonte. **Não roda com datas estimadas.** Como é uma
hipótese num só mercado (WDO), só vira candidato se também passar no WIN com o mesmo filtro.

### Hipóteses 27 a 30 — o método do Juares: operar só em canal, nunca no lateral

Descrição do Juares: operava sempre dentro de um canal de alta ou de baixa, comprando ou
vendendo no rompimento do canal ou na média dentro do canal, e não operava em mercado lateral.

Regra (5 minutos, dentro do pregão; o canal recomeça a cada dia, como os outros indicadores):
- **Canal:** regressão linear dos últimos N fechamentos. Inclinação > 0 e R² ≥ r → canal de
  alta; inclinação < 0 e R² ≥ r → canal de baixa; R² < r → **lateral**.
- **Lateral:** não abre posição; se estiver posicionado, **sai** no candle seguinte.
- `canal_rompimento`: em canal de alta, compra quando fecha acima da máxima dos 12 candles
  anteriores; em canal de baixa, vende quando fecha abaixo da mínima.
- `canal_media`: em canal de alta, compra quando o candle toca a linha média do canal e fecha
  acima dela; em canal de baixa, vende quando toca e fecha abaixo.
- Grade: N = 24 ou 36 candles (2 h ou 3 h); r = 0,5 ou 0,7 → 4 combinações.
- Comum: comprado e vendido, 1 contrato, stop 0,5%, sem alvo, zeragem 18h00, sem entrada
  depois das 17h30, custo de robô XP mais 1 tick, treino 12 meses, teste 1, mínimo de 30
  operações no treino, dados 11/2021 a 06/2026, WIN com `b3/PAUSAS_CONFERIDAS.toml`.
  Medição com R$ 100 mil. A conta de R$ 1.000,90 já se mostrou insuficiente para 1 contrato
  em todas as rodadas anteriores e não é rodada de novo.

| # | Contrato | Estratégia |
|---|---|---|
| 27 | WIN | `canal_rompimento` |
| 28 | WDO | `canal_rompimento` |
| 29 | WIN | `canal_media` |
| 30 | WDO | `canal_media` |

Regra de aprovação, a mesma da rodada 6: candidato só se passar em todos os critérios no
**WIN e no WDO** com a mesma estratégia. Referência para saber se o filtro de canal ajuda: o
rompimento sem filtro (`rompimento_curto`, rodada 5R: WIN fator 0,95, WDO 0,82).

Resultados das hipóteses 27 a 30 (1 contrato, R$ 100 mil; 11/2022 a 06/2026):

| # | Ops | Acerto | Fator de lucro | Antes dos custos (R$) | Custos (R$) | Líquido (R$) | Pior queda (R$) | Supera o aleatório | Veredito |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 27 WIN canal + rompimento | 766 | 36,8% | 0,88 | +915 | 3.600 | −2.685 | 3.904 | 67,0% | Reprovada |
| 28 WDO canal + rompimento | 529 | 33,3% | 0,77 | +1.350 | 7.660 | −6.310 | 6.330 | 55,5% | Reprovada |
| 29 WIN canal + média | 1.044 | 33,1% | 0,75 | −2.514 | 4.907 | −7.421 | 8.055 | 8,5% | Reprovada |
| 30 WDO canal + média | 750 | 32,3% | 0,69 | −110 | 10.860 | −10.970 | 10.970 | 30,5% | Reprovada |

Leitura:
- **O filtro de canal não melhorou o rompimento; piorou.** Sem filtro (5R), o fator de lucro
  era 0,95 (WIN) e 0,82 (WDO); com filtro, 0,88 e 0,77.
- **Entrar no recuo à média perde antes dos custos** nos dois mercados.
- **A saída por "virou lateral" dominou:** 658 de 766 saídas no WIN e 872 de 1.044 em 29 foram
  por sinal, quase todas porque o R² caiu abaixo do limite. A posição sai cedo e paga custo.
  Esta é uma tradução possível do método; a forma como o Juares saía das operações (e em que
  tempo gráfico ele desenhava o canal) não foi informada e pode ser diferente. Testar outra
  forma é hipótese nova, registrada antes.
- 30 hipóteses no projeto; nenhuma aprovada. A hipótese 26 (agenda) aguarda o calendário oficial.

## Rodada 8 — 11/11/2026 — swing trade em canal, 20 ações (registrada antes dos dados)

Decisões do Juares: as **20 ações mais negociadas**, **swing trade** (a posição pode durar
dias), canais em **15 min, 30 min, 60 min e 4 h**. As imagens enviadas eram exemplos da
internet; a regra segue o texto de canais de alta e baixa que ele mandou.

**Universo fixado agora, por liquidez no início do histórico (2021), não pela de hoje** (a
lista de hoje favoreceria quem subiu): VALE3, PETR4, PETR3, ITUB4, BBDC4, B3SA3, BBAS3,
ABEV3, MGLU3, ITSA4, WEGE3, SUZB3, RENT3, GGBR4, JBSS3, LREN3, PRIO3, ELET3, CSNA3, HAPV3.
Reservas, na ordem, para código que não existir mais no servidor: CMIG4, EQTL3, RADL3,
VBBR3, UGPA3.

**Dados:** M15 do MT5 da XP (script `b3/mt5/ExportarAcoes.mq5`); 30 min, 60 min e 4 h por
agregação. **Ajuste por proventos é obrigatório**: sem ele, cada data-ex de dividendo vira
uma queda falsa que quebra o canal. Não roda com preço sem ajuste.

**Regra (só comprado: com R$ 1.000,90, vender a descoberto exige aluguel de ações e fica fora).**
O canal é redesenhado a cada candle **só com os N candles anteriores**: reta de regressão dos
fechamentos; linha de cima paralela pelo topo mais alto acima da reta, linha de baixo
paralela pelo fundo mais baixo (o canal "desenhado à mão", sem olhar o futuro). Canal de alta:
inclinação > 0 e R² ≥ r. A noite **não** reinicia o canal (swing trade).
- `canal_suporte` (texto: "comprar quando o preço toca a linha inferior"): em canal de alta,
  o candle toca a LTA e fecha acima dela → compra na abertura seguinte. **Sai** quando a
  máxima toca a linha de retorno (alvo) ou quando fecha abaixo da LTA (rompimento contra).
- `canal_aceleracao` (texto: "rompimento a favor sinaliza aceleração"; alvo = largura
  projetada): em canal de alta, fecha acima da linha de retorno → compra. **Sai** no alvo
  (linha de retorno + largura do canal) ou se fechar de volta abaixo da linha média.
- Canal de baixa ou lateral: não abre posição.
- Grade: N = 40 ou 80 candles; r = 0,5 ou 0,7 → 4 combinações.
- Stop de emergência 10%; saída na abertura se houver salto além do stop. Posição de 100% do
  capital (R$ 1.000,90): um salto de 5% contra custa ~R$ 50.
- Custos (operação manual): corretagem R$ 0 com RLP **a confirmar na XP**; tarifa B3 0,03% e
  slippage 0,05% por lado.
- Walk-forward por ação: treino 12 meses, teste 1, mínimo de 10 operações no treino.
  Reserva (07/2026 em diante) fora.

| # | Estratégia | Tempo |
|---|---|---|
| 31 / 32 / 33 / 34 | `canal_suporte` | 15 min / 30 min / 60 min / 4 h |
| 35 / 36 / 37 / 38 | `canal_aceleracao` | 15 min / 30 min / 60 min / 4 h |

**Avaliação, fixada agora:** cada hipótese junta as 20 ações (operações somadas; o percentil
contra o aleatório soma as rodadas aleatórias das 20). Critérios de `criterios.toml`. Por
serem 8 hipóteses, **uma estratégia só vira candidata se passar em pelo menos 2 dos 4 tempos
gráficos**. Comparação obrigatória: comprar e segurar as mesmas ações no mesmo período.

**Rodada 8 cancelada antes de rodar (11/11/2026),** por decisão do Juares: foco no WIN e no
WDO até esgotar esses dois mercados, em vez de abrir outro. Nenhum dado de ações foi pedido
ou usado; as hipóteses 31–38 não existem como teste.

## Rodada 9 — 11/11/2026 — o método de canal do Juares no WIN e no WDO

Registrada antes de implementar e de rodar. Difere da rodada 7 (5 min, canal só dentro do
dia, saída por "virou lateral", sem alvo) em tudo o que o texto do Juares descreve:

- **Canal desenhado só com o passado, atravessando os dias:** a cada candle, regressão dos N
  fechamentos anteriores; linha de cima paralela pelo topo mais alto acima da reta, linha de
  baixo paralela pelo fundo mais baixo. Canal de alta: inclinação > 0 e R² ≥ r; de baixa:
  inclinação < 0 e R² ≥ r.
- **WIN ajustado só para desenhar o canal:** nos 27 vencimentos do período há um salto médio
  de +1,84% na abertura (dia comum: 0,35%), que é a troca de contrato, não movimento. O
  salto do dia de vencimento é descontado de todos os candles anteriores, só no cálculo do
  canal; a execução usa o preço real. Como nada passa de um dia para o outro, o resultado em
  pontos de cada operação não muda. WDO não precisa: no vencimento, salto igual ao de um dia
  comum (0,32% contra 0,26%).
- `canal_suporte`: canal de alta, toca a LTA e fecha acima → compra; sai na linha de retorno
  (alvo) ou se fechar abaixo da LTA. Canal de baixa, toca a LTB e fecha abaixo → vende; sai na
  linha de retorno de baixo ou se fechar acima da LTB.
- `canal_aceleracao`: fecha acima da linha de retorno de um canal de alta → compra; alvo =
  linha de retorno + largura do canal; sai se voltar abaixo da linha média. Simétrico na
  baixa.
- Grade: N = 40 ou 80 candles, r = 0,5 ou 0,7 → 4 combinações.
- **Execução day trade:** 1 contrato, comprado e vendido, stop de emergência 2% (proteção
  contra salto; a saída normal é a da regra), sem entrada depois das 17h30, zeragem 18h00,
  custo de robô XP mais 1 tick, treino 12 meses, teste 1, mínimo de 30 operações no treino,
  11/2021 a 06/2026, WIN com `b3/PAUSAS_CONFERIDAS.toml`, medição com R$ 100 mil.
- Tempos: 15 min, 30 min, 60 min e 4 h (em 4 h o pregão tem dois candles completos, 9h–13h e
  13h–17h; o de 17h é incompleto e é descartado).

| | 15 min | 30 min | 60 min | 4 h |
|---|---|---|---|---|
| `canal_suporte` WIN / WDO | 39 / 40 | 41 / 42 | 43 / 44 | 45 / 46 |
| `canal_aceleracao` WIN / WDO | 47 / 48 | 49 / 50 | 51 / 52 | 53 / 54 |

**Regra de aprovação, fixada agora:** são 16 medições; um resultado bom isolado é esperado
por sorte. Candidato só se a **mesma estratégia, no mesmo tempo gráfico, passar em todos os
critérios no WIN e no WDO**. Só então vai ao período reservado, que contém as eleições de
outubro/2026.

Resultados da rodada 9 (1 contrato, R$ 100 mil; 11/2022 a 06/2026):

| Estratégia, tempo | Mercado | Ops | Acerto | Fator de lucro | Antes dos custos (R$) | Custos (R$) | Líquido (R$) | Pior queda (R$) | Supera o aleatório |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| aceleração 15 min (47/48) | WIN | 101 | 41,6% | 1,17 | +1.331 | 475 | **+856** | 939 | 88,5% |
| | WDO | 145 | 45,5% | 1,10 | +3.190 | 2.100 | **+1.090** | 2.094 | 94,5% |
| suporte 15 min (39/40) | WIN | 372 | 30,4% | 0,81 | −1.511 | 1.748 | −3.259 | 6.566 | 22,0% |
| | WDO | 310 | 29,4% | 0,80 | +20 | 4.489 | −4.469 | 4.623 | 41,0% |
| suporte 30 min (41/42) | WIN | 245 | 41,6% | 1,00 | +1.097 | 1.152 | −55 | 2.322 | 67,5% |
| | WDO | 188 | 31,4% | 0,87 | +640 | 2.722 | −2.082 | 4.442 | 56,5% |
| suporte 60 min (43/44) | WIN | 146 | 45,2% | 0,98 | +527 | 686 | −159 | 1.822 | 57,0% |
| | WDO | 140 | 37,9% | 0,63 | −3.370 | 2.027 | −5.397 | 6.521 | 4,5% |

**Inconclusivas por falta de operações (zero operações no teste):** suporte 4 h (45/46) e
aceleração 30 min, 60 min e 4 h (49–54). Nenhuma janela de treino chegou às 30 operações
exigidas: o canal nesses tempos gera, no máximo, 39, 16, 13 e 2 sinais de entrada por ano
(frequência medida sem resultado financeiro). Mesmo sem o mínimo do treino, não chegariam
às 200 operações da régua em 43 meses. A régua não foi alterada.

Leitura:
- **Nenhuma candidata:** nenhuma passou em todos os critérios em um mercado, muito menos nos dois.
- **Comprar na LTA / vender na LTB (suporte) não tem vantagem** em nenhum tempo gráfico: perde
  ou empata nos dois mercados e não supera o aleatório.
- **A aceleração em 15 min é a primeira estratégia do projeto com resultado positivo depois
  dos custos nos dois mercados ao mesmo tempo** (fator 1,17 no WIN e 1,10 no WDO). Mas fica
  abaixo da régua em três pontos nos dois: fator de lucro < 1,3, menos de 200 operações e não
  supera 95% do aleatório. Com 54 hipóteses no projeto, não basta. Junto com o candle de força
  a favor no WDO (22b), forma um padrão: **entrar a favor de um movimento forte** é o único tipo
  de entrada que aparece positivo. Registrado como observação; só volta como hipótese nova,
  com dados que não viu (simulador ao vivo).
- 54 hipóteses no projeto; nenhuma aprovada. Reserva intocada.
