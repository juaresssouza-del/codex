# Histórico da B3 — qualidade dos dados (10/11/2026)

Exportado pelo Juares do MT5 do simulador da XP (servidor XPMT5-DEMO), série contínua,
candles de 5 minutos. Arquivos em `dados/B3/` (fora do Git).

| | WIN$N (mini-índice) | WDO$N (mini-dólar) |
|---|---|---|
| Período | 10/11/2021 a 10/11/2026 | 10/11/2021 a 10/11/2026 |
| Candles / pregões | 138.756 / 1.248 | 140.008 / 1.248 |
| Candles por pregão (mediana) | 113 (9h00 a 18h20) | 114 (9h00 a 18h25) |
| Duplicatas / OHLC incoerente | 0 / 0 | 0 / 0 |
| Pausas dentro do dia | 4 (máx. 70 min) | 1 (15 min) |
| Preço mediano | 127.425 pontos | 5.237,5 pontos |
| Candle típico (máx − mín) | 150 pontos = 0,117% | 4,5 pontos = 0,089% |

Formato do arquivo: separado por tabulação, cabeçalho `<DATE> <TIME> <OPEN> <HIGH> <LOW>
<CLOSE> <TICKVOL> <VOL> <SPREAD>`, horário de Brasília. A coluna SPREAD está em pontos do
MT5 (WIN: 5 = 1 tick; WDO: 500 = 0,5 ponto).

## Custo contra movimento

Estimativa por operação completa (entrada + saída, 1 contrato): emolumentos ainda não
confirmados (fontes falam em ~R$ 0,25 por ponta no WIN e ~R$ 1,20 no WDO) e 1 tick de
slippage por lado.

| | Custo estimado | Em pontos | Candle típico de 5 min | Candle / custo |
|---|---:|---:|---:|---:|
| WIN | ~R$ 2,50 | ~12,5 pontos | 150 pontos | **~12 vezes** |
| WDO | ~R$ 12,40 | ~1,2 ponto | 4,5 pontos | **~3,6 vezes** |
| BTC na Binance (15 min, para comparar) | ~0,30% | | 0,231% | 0,8 vez |

Na Binance, uma operação custava mais que um candle inteiro de 15 minutos. No WIN, o
custo é cerca de 1/12 de um candle de 5 minutos.

## O que os dados mostram e o motor precisa tratar

1. **Troca de vencimento.** Há saltos de ~2,4% a 2,7% na abertura de quartas-feiras de
   vencimento do WIN (15/06/2022, 15/10/2025, 17/12/2025, 08/04/2026). Indica que a série
   `$N` emenda os contratos **sem ajuste**: o salto é a diferença entre o contrato velho
   e o novo, não movimento real. Em day trade (zerado no fim do dia) isso não afeta o
   resultado, mas distorce indicador que olha para dias anteriores. Solução: indicadores
   calculados dentro do dia, ou série ajustada só para os indicadores.
2. **Eventos extremos reais.** Eleições: 03/10/2022, 31/10/2022, 05/10/2026 (WIN +9,2%)
   e **26/10/2026: WIN −14,9% na abertura, com pausa de 10 minutos às 9h35** (provável
   circuit breaker); dólar +9,2%. Também 05/08/2024 (crise global) e 06/11/2024 (eleição
   nos EUA). Uma posição levada de um dia para o outro em 26/10/2026 perderia ~31 mil
   pontos (R$ 6,2 mil por contrato de WIN). **Zerar no fim do dia é obrigatório.**
3. **Pausas no pregão.** O backtest não pode assumir que o stop executa durante uma pausa:
   ele executa na reabertura, ao preço que vier.
4. **Período reservado.** Com a mesma regra da cripto, de 07/2026 em diante fica fora dos
   testes. Os eventos de outubro/2026 caem nesse período: servirão de teste de estresse
   final, não de ajuste.
