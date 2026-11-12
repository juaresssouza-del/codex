# TradeLab — relatório de passagem (Claude → Codex), 12/11/2026

Leia este arquivo primeiro. Ele substitui as versões anteriores (histórico no Git). Resume o
estado do `tradelab-motor/`, o que foi concluído, o que **não** fazer e as ações
recomendadas. Os detalhes estão nos arquivos citados; `HIPOTESES.md` é a fonte da verdade.

## 1. Situação em uma frase

**57 hipóteses testadas no histórico (Binance e B3), nenhuma aprovada.** O motor é confiável
(184 testes, auditado pelo Codex); o que falta é uma estratégia com vantagem maior que o custo
e capital compatível com o risco. Conta real **não** autorizada. Período reservado (07/2026
em diante, com as eleições de outubro) **intocado**.

## 2. Onde está cada coisa

| Arquivo | Conteúdo |
|---|---|
| `HIPOTESES.md` | As 57 hipóteses, registradas antes de rodar, com resultados e leituras |
| `STATUS.md` | Situação por etapa |
| `criterios.toml` | A régua (≥ 200 operações, fator de lucro ≥ 1,3, expectativa > 0, queda ≤ 10%, ≥ 95% contra o aleatório) e a reserva |
| `AUDITORIA_CODEX.md` | Correções do Codex no motor (revisadas pelo Claude) |
| `b3/DADOS.md` | Qualidade do histórico WIN/WDO, custo contra movimento, salto de vencimento do WIN |
| `b3/PAUSAS_CONFERIDAS.toml` | Duas pausas do WIN investigadas (uma é falha confirmada da B3) |
| `b3/corretoras.md` | Pesquisa do Codex: custos, margens, horários e tarifas B3 |
| `b3/CARTAO_FORCA_WDO.md` | Regra do candle de força no WDO para o simulador |
| `b3/mt5/ForcaWDO.mq5` | Indicador de alerta do MT5 para esse cartão (só avisa; não compilado aqui) |
| `b3/mt5/ExportarAcoes.mq5` | Exportador de ações (a rodada de ações foi cancelada; não usado) |
| `b3/MOTOR_ADAPTATIVO.md` | Seletor adaptativo do Codex (rodada 10) |
| `motor/` | `futuros.py` (B3), `backtest.py` (cripto), `estrategias.py`, `validacao.py`, `adaptativo.py`, `conferencia.py`, `diario.py` |

Fora do Git: `dados/` (Binance e os CSVs M5 de `WIN$N`/`WDO$N` do MT5 da XP, 11/2021–11/2026)
e `resultados/`. Os CSVs da B3 só o Juares tem; peça a ele.

## 3. Resultados por rodada (fora da amostra, depois dos custos, 1 contrato na B3)

| Rodada | O que testou | Hip. | Resultado |
|---|---|---:|---|
| 1–2 | BTC 5m–4h: SMA, rompimento, RSI | 12 | Day trade perde para o custo (~0,3% por operação) |
| 3–4 | BTC/ETH 4h seguindo tendência | 3 | Positivo em BTC, falha em ETH; comprar e segurar rendeu mais |
| 5 / 5R | WIN/WDO: faixa de abertura, rompimento | 4 (+8 medições) | Sinal antes dos custos, menor que o custo de robô na XP; R$ 1.000 quebra |
| 6 | Média móvel, candle de força a favor/contra, martingale | 7 | Martingale quebra R$ 1.000 em 3 operações; força a favor no WDO: fator 1,31 mas 166 ops e falha no WIN |
| 7 | Canal 5 min dentro do dia, sai no lateral | 4 | Filtro de canal piora o rompimento |
| 8 | Ações (swing) | — | Cancelada antes de rodar: foco em WIN/WDO |
| 9 | Canal do Juares desenhado com o passado, 15m–4h | 16 | Suporte (LTA/LTB) sem vantagem; **aceleração 15 min positiva nos dois mercados** (fator 1,17 WIN, 1,10 WDO), abaixo da régua; 30m–4h sem operações suficientes |
| 10 | Seletor adaptativo (Codex), 5/15/30 min | 3 (6 medições) | Reprovado nos 6; abaixo das melhores estratégias fixas; não há persistência de desempenho |

**Padrão que se repete (rodadas 6, 9 e 10):** só entradas **a favor de um movimento forte**
(candle de força e aceleração do canal) aparecem com fator ≥ 1 em mais de um mercado ou
rodada. Nenhuma passa na régua. Com 57 hipóteses no mesmo histórico, isso é **pista, não
evidência**.

Capital: com R$ 1.000 e 1 minicontrato, a conta quebra em todas as rodadas. A pior queda de 1
contrato vai de ~R$ 1 mil a ~R$ 17 mil conforme a estratégia; para caber em 10%, de R$ 26 mil
a R$ 170 mil.

## 4. Decisões e regras que valem

- **Nenhuma ordem real** sem autorização escrita do Juares, com orçamento de risco e botão de
  desligar.
- Senhas e chaves nunca no chat nem no Git.
- **A régua não muda depois de ver resultado.** Hipótese nova: registrar em `HIPOTESES.md`
  antes de implementar e de rodar. Reexecução técnica também é registrada antes.
- Corretora: **XP**. A corretagem zero (RLP) **exclui robôs**; motor usa R$ 1,35 (WIN) e
  R$ 2,24 (WDO) por contrato e por lado, mais 1 tick. Custo da rota EA ainda **não confirmado**.
- Foco: **WIN e WDO** (decisão do Juares). Não abrir outros mercados.
- O WIN precisa de `--pausas-conferidas b3/PAUSAS_CONFERIDAS.toml`; indicadores de vários
  dias no WIN precisam de `--ajustar-vencimento`.
- Ambiente do Claude usa pandas 3 (o do Codex, pandas 2): use `as_unit("ms")` ao converter
  datas em testes.

## 5. O que não fazer

- Não testar estratégia nova neste histórico de 5 anos sem razão forte: cada teste a mais
  aumenta a chance de um falso positivo.
- Não usar `--usar-reserva` para nada além da confirmação final de uma candidata aprovada.
- Não afrouxar `criterios.toml`, nem escolher o mercado ou o tempo gráfico que deu certo.
- Não tratar controle fixo ou diagnóstico como candidata.
- Não usar IA para ler notícia em backtest: o modelo já sabe o que aconteceu (contaminação).
- Não sugerir dinheiro real com R$ 1.000 em minicontratos, nem martingale.

## 6. Ações recomendadas (em ordem)

| # | Ação | Quem | Por quê |
|---:|---|---|---|
| 1 | **Parar de criar estratégias novas no histórico de 5 anos.** | Todos | 57 hipóteses: novos testes aqui medem mais sorte que vantagem |
| 2 | **Acompanhamento ao vivo no simulador da XP** das duas entradas a favor do movimento: candle de força no WDO (cartão e alerta prontos) e aceleração do canal em 15 min no WIN e no WDO (cartão e alerta a fazer, com a regra exata da rodada 9) | Claude faz o cartão e o alerta; Juares opera no simulador | É o único dado que nenhum teste viu |
| 3 | **Diário automático do simulador**: o MT5 grava cada operação simulada em CSV no formato de `b3/diario-modelo.csv`, e `diario-b3` compara previsto × executado toda semana | Codex | Hoje o diário é manual; sem ele não há comparação confiável |
| 4 | **Confirmar por escrito com a XP** o custo da rota de robô (EA no MT5) e se o RLP vale para ordens manuais | Juares | O custo decide se a faixa de abertura e a aceleração viram positivas |
| 5 | **Calendário oficial para a hipótese 26** (FOMC, payroll, IPCA, Copom, 11/2021–06/2026), com fonte por data | Codex (coleta), Claude (executa) | Hipótese registrada, aguarda só os dados; não rodar com datas estimadas |
| 6 | **Depois de 3 a 6 meses de simulador**: comparar o ao vivo com o teste. Se confirmar, uma única execução no período reservado (`--usar-reserva`), com as eleições de outubro/2026 como teste de estresse | Claude | Só então discutir conta real, com capital compatível (~R$ 26 mil por contrato ou mais) |

Critério de parada combinado: se o simulador contradisser o teste (resultado negativo depois
dos custos em 3 a 6 meses), encerrar a busca por robô de day trade em WIN/WDO.
