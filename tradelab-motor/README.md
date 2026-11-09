# TradeLab — motor de pesquisa

Motor de backtest e validação para Binance Spot (só comprado, uma posição por vez).
É a parte que faltava no TradeLab (PWA): o painel mostra, o motor decide se uma
estratégia tem vantagem **antes** de qualquer dinheiro real.

Não conecta conta, não usa chave de API e não envia ordem. Só lê histórico público.

## Instalação

Python 3.11 ou mais novo.

```sh
cd tradelab-motor
python -m pip install numpy pandas pytest
python -m pytest            # 41 testes
```

## Uso

```sh
# 1. Histórico público, conferido por SHA-256 (cerca de 4 MB para 2 anos de BTCUSDT 15m)
python -m motor baixar --de 2024-11 --ate 2026-10 --diarios-ate 2026-11-08
python -m motor dados                       # qualidade: candles, duplicatas, lacunas

# 2. Validação: é este comando que decide
python -m motor validar --estrategia sma    # sma | rompimento | rsi

# Descritivo, dentro da amostra (não valida nada)
python -m motor backtest --estrategia sma --param rapida=9 --param lenta=21

# Candles para o botão "Importar JSON" do TradeLab
python -m motor painel
```

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
3. **Linhas de base.** A estratégia precisa superar entradas aleatórias com a mesma
   frequência, duração, stop, alvo e custos (200 rodadas) e é comparada com comprar e
   segurar com a mesma exposição.
4. **Critérios fixados antes** em `criterios.toml`: no mínimo 200 operações, fator de
   lucro ≥ 1,3, expectativa positiva, drawdown ≤ 10% e percentil ≥ 95 contra o
   aleatório. Não afrouxe a régua depois de ver o resultado.

O motor reproduz o simulador do TradeLab no mesmo dado (teste
`test_paridade_com_o_simulador_do_tradelab`): mesmo resultado até a 6ª casa decimal.

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
