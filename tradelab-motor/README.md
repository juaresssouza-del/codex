# TradeLab — motor de pesquisa

**Versão 0.2.0:** leia [AUDITORIA_CODEX.md](AUDITORIA_CODEX.md) antes de interpretar os
resultados antigos. Foram corrigidos problemas de execução, drawdown, agregação e
validação. Os resultados históricos abaixo não foram recalculados com essas correções.

Motor de backtest e validação para Binance Spot (só comprado, uma posição por vez).
É a parte que faltava no TradeLab (PWA): o painel mostra, o motor decide se uma
estratégia tem vantagem **antes** de qualquer dinheiro real.

Não conecta conta, não usa chave de API e não envia ordem. Só lê histórico público.

## Instalação

Python 3.11 ou mais novo.

```sh
cd tradelab-motor
python -m pip install numpy pandas pytest
python -m pytest            # 104 passam; 4 da amostra real são pulados para proteger a reserva
```

## Uso

```sh
# 1. Histórico público, conferido por SHA-256 (cerca de 4 MB para 2 anos de BTCUSDT 15m)
python -m motor baixar --de 2024-11 --ate 2026-10 --diarios-ate 2026-11-08
python -m motor dados                       # qualidade: lacunas, candles parciais, movimento típico

# 2. Validação: é este comando que decide
python -m motor validar --estrategia sma    # sma | rompimento | rsi

# Descritivo, dentro da amostra (não valida nada)
python -m motor backtest --estrategia sma --param rapida=9 --param lenta=21

# Candles para o botão "Importar JSON" do TradeLab
python -m motor painel
```

### B3 (minicontratos WIN e WDO)

O histórico vem do MT5 da corretora (Exibir → Símbolos → Barras → `WIN$N` / `WDO$N`, M5 →
Exportar barras) e fica em `dados/B3/WIN_N_M5.csv` e `dados/B3/WDO_N_M5.csv`.

```sh
python -m motor dados --contrato WIN --intervalo 5m
python -m motor validar --contrato WIN --intervalo 15m --estrategia abertura --lado ambos \
    --capital 20000 --risco 1 --stop 0.5 --alvo 0 --exposicao 100
```

O motor de futuros (`motor/futuros.py`) opera em pontos × valor do ponto (WIN R$ 0,20;
WDO R$ 10), contratos inteiros limitados pelo risco e pela margem (`--exposicao` = % do
patrimônio que pode virar margem), custo em R$ por contrato e por lado (`--custo-lado`,
premissas WIN R$ 1,35 e WDO R$ 2,24, ainda sem confirmação da tarifa individual do EA)
e slippage em ticks. `--lado ambos` permite ficar
vendido e virar a mão. Não entra depois das 17h30, zera às 18h00 e nada passa de um
pregão para o outro. Como a noite é uma lacuna, os indicadores reaquecem a cada pregão:
o salto falso da troca de vencimento da série contínua não contamina o sinal.

Opções de risco e custo (todas em %): `--capital --risco --exposicao --stop --alvo
--perda-diaria --max-operacoes-dia --taxa --slippage`. Use `--help` em cada comando.

`dados/` e `resultados/` ficam fora do Git.

## Como o motor valida

1. **Execução honesta.** Sinal no fechamento, execução na abertura seguinte. Stop vale
   antes do alvo quando os dois cabem no mesmo candle. Gap abaixo do stop sai na
   abertura. Taxa e slippage nos dois lados. Lote, passo de preço e valor mínimo da
   Binance são respeitados.
2. **Walk-forward.** Em cada mês, os parâmetros são escolhidos só com os 6 meses
   anteriores e medidos no mês seguinte, que a escolha nunca viu. Só esse resultado conta.
3. **Linhas de base.** A estratégia precisa superar entradas aleatórias com frequência
   e duração aproximadamente calibradas, mesma elegibilidade, stop, alvo e custos
   (200 rodadas) e é comparada com comprar e
   segurar com a mesma exposição.
4. **Critérios fixados antes** em `criterios.toml`: no mínimo 200 operações, fator de
   lucro ≥ 1,3, expectativa positiva, drawdown ≤ 10% e percentil ≥ 95 contra o
   aleatório. Não afrouxe a régua depois de ver o resultado.
5. **Período reservado.** De `reserva_inicio` (em `criterios.toml`) em diante, o motor
   corta os dados sozinho. Só a estratégia que passar em tudo é rodada nele, uma vez,
   com `--usar-reserva`. Cada hipótese testada é registrada antes em `HIPOTESES.md`.
6. **Dados reais têm defeitos.** Candles parciais de paradas da Binance (fecham antes
   da hora, com volume zero) são removidos e viram lacuna. Ordem pendente não atravessa
   lacuna e o indicador precisa reaquecer depois dela.

A reprodução do simulador do TradeLab até a sexta casa decimal foi registrada antes
da auditoria. Seu teste com a amostra real fica pulado porque a amostra intercepta a
reserva. Essa paridade não foi reafirmada na versão auditada; os casos novos usam
preços sintéticos, sem consumir o histórico reservado.

## Resultado em 09/11/2026 — BTCUSDT 15m

Histórico de 01/11/2024 a 08/11/2026 (70.848 candles, sem lacunas). Fora da amostra:
05/2025 a 11/2026. Padrões: capital 1.000, exposição 10%, stop 1%, alvo 2%,
taxa 0,1% e slippage 0,05% por lado.

| Estratégia | Operações | Acerto | Fator de lucro | Resultado | Custos pagos | Supera o aleatório | Veredito |
|---|---:|---:|---:|---:|---:|---:|---|
| SMA (a do TradeLab) | 390 | 25,1% | 0,55 | −10,84% | 110,00 | 87,5% | Reprovada |
| Rompimento | 349 | 28,4% | 0,63 | −8,53% | 99,58 | 95,5% | Reprovada |
| RSI | 170 | 36,5% | 0,49 | −5,42% | 49,05 | 35,5% | Reprovada |

Comprar e segurar com a mesma exposição: −2,07% no período.

Leitura: em 15 minutos, cada operação completa custa cerca de 0,3% (taxa + slippage).
Antes dos custos, SMA e rompimento ficam perto de zero e o RSI já perde. Nenhuma
estratégia tem vantagem que pague o custo de operar nesse tempo gráfico.

Rodada 2 (5m, 1h e 4h, até 06/2026): as 9 hipóteses também foram reprovadas. O único
sinal consistente foi rompimento em 4h, positivo antes dos custos, mas abaixo do custo de
operar. Detalhes em `HIPOTESES.md`.

Rodada 3 (hipótese 13: rompimento em 4h sem alvo, saída por stop móvel): primeiro
resultado positivo, +7,07% (ordem a mercado) e +8,76% (ordem limitada + BNB) fora da
amostra, fator de lucro 1,37 e 1,47. Reprovada pela régua: 100 operações, abaixo das
200 exigidas.

Rodada 4 (hipótese 14: a mesma regra em BTC e ETH desde 2017, sem fechar a posição na
virada do mês): reprovada na avaliação conjunta. BTC foi bem (+35,6%, fator de lucro
1,84), ETH não superou o aleatório e passou do drawdown máximo. Nos dois ativos,
comprar e segurar com a mesma exposição rendeu mais. A busca em cripto foi encerrada.

## Estrutura

| Arquivo | Papel |
|---|---|
| `motor/dados.py` | Download com checksum, leitura (ms e µs), validação e lacunas |
| `motor/mercado.py` | Filtros da Binance e custos |
| `motor/backtest.py` | Execução candle a candle e limites de risco |
| `motor/estrategias.py` | Hipóteses (SMA, rompimento, RSI) e a linha de base aleatória |
| `motor/metricas.py` | Expectativa, fator de lucro, drawdown e custos |
| `motor/validacao.py` | Walk-forward, Monte Carlo aleatório, comprar e segurar, critérios |
| `motor/painel.py` | Exportação para o importador do TradeLab |
| `criterios.toml` | A régua, fixada antes dos testes |
