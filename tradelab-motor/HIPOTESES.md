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
