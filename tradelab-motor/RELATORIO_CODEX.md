# TradeLab — relatório de passagem (Claude → Codex), 11/11/2026

Leia este arquivo primeiro. Ele resume o que foi feito no `tradelab-motor/`, o que foi
concluído e o que **não** fazer. Os detalhes estão nos arquivos citados.

**Complemento posterior — motor 0.2.0:** leia também [AUDITORIA_CODEX.md](AUDITORIA_CODEX.md).
Foram corrigidos erros de execução e validação. Os números abaixo são registros da
versão anterior e não foram recalculados; não constituem resultado validado da versão
auditada. A auditoria não aprovou estratégias nem utilizou a reserva em execuções.

**Entrega prática posterior — 0.3.0:** `conferir-b3` verifica o CSV M5 com procedência,
hash e bloqueio de falhas antes de testes B3 no fluxo de desenvolvimento. `diario-b3`
gera fichas e comparações previsto × executado de operações encerradas no simulador,
em JSON/HTML. Os comandos novos não liberam a reserva e não conectam corretora. Veja
[b3/COLOCAR_EM_PRATICA.md](b3/COLOCAR_EM_PRATICA.md). São 128 testes passando e 4 pulados,
com dados artificiais nos casos novos. Os números históricos seguem sem recálculo.

## 1. Onde está cada coisa

| Arquivo | Conteúdo |
|---|---|
| `STATUS.md` | Situação geral e próximos passos |
| `HIPOTESES.md` | As 18 hipóteses, registradas **antes** de rodar, com os resultados |
| `criterios.toml` | A régua de aprovação e o período reservado (de 07/2026 em diante) |
| `README.md` | Como instalar, rodar e validar (Binance e B3) |
| `b3/DADOS.md` | Qualidade do histórico WIN/WDO e custo contra movimento |
| `b3/corretoras.md` | Pesquisa do Codex (custos, margens, horários, tarifas B3) |
| `b3/VERIFICACAO_PESQUISA.md` | Conferência das pesquisas do Gemini |
| `motor/` | Código: `backtest.py` (cripto), `futuros.py` (B3), `validacao.py`, `estrategias.py` |
| `tests/` | 128 casos passam e 4 são pulados (`python -m pytest`) |

Fora do Git (não estão no repositório): `dados/` (Binance e os CSVs do MT5 exportados pelo
Juares) e `resultados/` (relatórios JSON completos de cada validação). Para refazer, baixe
os dados com `python -m motor baixar ...` e peça ao Juares os CSVs de `WIN$N` e `WDO$N` (M5).

## 2. O que o motor faz

- Backtest próprio em Python; reproduz o simulador do TradeLab (PWA) até a 6ª casa decimal.
- Walk-forward (parâmetros escolhidos só com o passado), comparação com 200 rodadas de
  entradas aleatórias e com comprar e segurar, critérios fixos e período reservado que
  nenhum teste vê.
- Binance Spot: custos, filtros da corretora, ordem limitada, candles parciais.
- B3 (WIN/WDO): pontos × valor do ponto, contratos inteiros, custo por contrato e por lado,
  comprado e vendido, zeragem às 18h00, nada passa de um pregão para o outro.

## 3. Resultados (fora da amostra, depois dos custos)

| Rodada | Mercado | Hipóteses | Resultado |
|---|---|---:|---|
| 1–2 | BTC 5m/15m/1h/4h (SMA, rompimento, RSI) | 12 | Reprovadas. Day trade perde para o custo (~0,3% por operação na Binance) |
| 3–4 | BTC/ETH 4h, seguir tendência sem alvo | 3 | Positivas em BTC, reprovadas no conjunto (ETH não supera o aleatório). Comprar e segurar rendeu mais |
| 5 | B3 WIN/WDO, faixa de abertura e rompimento, comprado e vendido | 4 | **Sinal real antes dos custos** (+R$ 1,7 mil a +R$ 6,3 mil por contrato em 43 meses, supera 98–100% do aleatório), mas o custo de robô na XP é maior. Reprovadas |

**Nenhuma das 18 hipóteses foi aprovada.** O período reservado (07/2026 em diante) continua
intocado.

Capital: com R$ 1.000 e 1 minicontrato, a conta quebra (−84% a −94%). A pior queda de 1
contrato vai de R$ 4,7 mil a R$ 14,3 mil; para caber em 10% seriam R$ 47 mil a R$ 143 mil.

## 4. Decisões e regras que valem

- **Nenhuma ordem real** sem autorização escrita do Juares, com orçamento de risco e botão de
  desligar. Conta real **não** está autorizada.
- Senhas e chaves (Binance, XP, MT5) nunca no chat nem no Git.
- **A régua não muda depois de ver o resultado.** Hipótese nova é registrada em
  `HIPOTESES.md` antes de rodar.
- Corretora da B3: **XP** (MT5 e simulador grátis). A corretagem zero (RLP) da XP **exclui
  robôs**; o motor usa R$ 1,35 (WIN) e R$ 2,24 (WDO) por contrato e por lado.
- Futuros (operar vendido) não está disponível na conta Binance do Juares; não contornar.

## 5. O que não fazer

- Não rodar estratégia nova sem registrar antes em `HIPOTESES.md`.
- Não usar o período reservado (`--usar-reserva`) para ajustar nada.
- Não afrouxar `criterios.toml`.
- Não tratar resultado antes dos custos como lucro.
- Não sugerir dinheiro real com R$ 1.000 em minicontratos.

## 6. Próximos passos possíveis (decisão do Juares)

1. Robô da faixa de abertura do WIN no **simulador** do MT5 (sem dinheiro), para acompanhar
   ao vivo e comparar com o backtest.
2. Acompanhamento em papel na Binance com R$ 200 por operação.
3. Voltar ao robô só com fato novo: corretora que confirme **por escrito** custo bem menor
   para robô, e capital compatível com a queda de 1 contrato.
