# Cartão — candle de força no mini-dólar (WDO), só no simulador

**Situação:** hipótese 22 da rodada 6, **não aprovada** (166 operações, abaixo das 200
exigidas, e o mesmo método perde no WIN). Uso: acompanhamento no **simulador da XP**, para
coletar dados que o teste ainda não viu. Não é recomendação de investimento.

Configuração escolhida pelo walk-forward em todas as 44 janelas mensais do teste:
média dos **20** candles anteriores, candle de força com **3×** essa média.

## Regra (WDO, gráfico de 5 minutos, 1 contrato)

| Passo | Regra |
|---|---|
| 1. Média | A cada candle fechado, calcule a amplitude média (máxima − mínima) dos **20 candles anteriores do mesmo pregão**. Antes de haver 20 candles no dia (por volta das 10h40), não há sinal |
| 2. Candle de força | Amplitude do candle ≥ **3 × a média** **e** corpo (fechamento − abertura, sem sinal) ≥ **60%** da amplitude |
| 3. Entrada | Candle de força **de alta** (fechou acima da abertura): **compra** 1 WDO a mercado na abertura do candle seguinte. **De baixa:** **vende** 1 WDO |
| 4. Stop | Junto com a entrada, stop a **0,5%** do preço (WDO a 5.600 ≈ 28 pontos ≈ **R$ 280**, mais custos) |
| 5. Saída | Pelo stop; ou por um candle de força **no sentido contrário** (zera e vira a mão); ou **zerar até 18h00** |
| 6. Horários | **Nenhuma entrada depois das 17h30.** Nunca levar posição para o dia seguinte |
| 7. Limites | Um stop por dia: tomou, encerra o dia. Perdeu mais de R$ 600 no mês (cerca de 2 stops), para o mês |
| 8. Diário | Registre cada operação em `b3/diario-modelo.csv`: horário do sinal, da ordem, preço previsto e executado |

## O que esperar, pelo teste (11/2022 a 06/2026)

- ~4 operações por mês; acerto de 44,6%.
- Ganho médio ~R$ 218; perda média ~R$ 134 por operação.
- A maioria das operações (115 de 166) ficou aberta até a zeragem das 18h00.
- Pior sequência: 5 perdas seguidas. Pior queda: R$ 2.617.
- Resultado: +R$ 3.841 em 43 meses (~R$ 90/mês por contrato), **antes do IR de 20%**.

## Quando avaliar

Depois de **20 operações** no simulador (cerca de 5 meses), compare o diário com o que o
motor teria feito nos mesmos dias. Só se a execução manual reproduzir o teste vale discutir
conta real, e com o capital da seção abaixo.

## Capital para 1 contrato

| Referência | Valor |
|---|---:|
| Margem exigida pela XP | R$ 140 |
| Um stop (~28 pontos + custos e slippage) | ~R$ 295 |
| Pior queda medida no teste | R$ 2.617 |
| Pior queda = 10% do capital | **~R$ 26 mil** |
| Com folga de 2× para quedas maiores que as do teste | **~R$ 50 mil** |
