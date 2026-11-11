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
