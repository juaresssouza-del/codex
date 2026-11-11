# TradeLab — situação em 10/11/2026

## Objetivo

Robô de operações que caiba na rotina do Juares (trabalha das 8h às 18h): testar com
dados reais antes de arriscar dinheiro e só operar o que passar numa régua fixada antes.

## O que foi feito

### 1. Motor de pesquisa (`tradelab-motor/`)
- Backtest em Python, sem skills de terceiros. 51 testes passando.
- Reproduz o simulador do TradeLab (PWA) até a 6ª casa decimal.
- Dados públicos da Binance com checksum, tratamento de lacunas e de candles parciais.
- Custos, filtros da corretora, ordem limitada, limite de perda diária.
- Walk-forward (normal e contínuo), comparação com entradas aleatórias e com comprar e
  segurar, critérios fixos em `criterios.toml` e período reservado (07/2026 em diante)
  que nenhum teste vê.
- Exporta candles para o importador do TradeLab.

### 2. Cripto (Binance Spot): 15 hipóteses, todas reprovadas
Detalhes em `HIPOTESES.md`.

| Rodada | O que testou | Resultado |
|---|---|---|
| 1 | SMA, rompimento e RSI em 15m | Reprovadas; o custo (~0,3% por operação) come tudo |
| 2 | As mesmas em 5m, 1h e 4h | Reprovadas; 5m é o pior; só o rompimento em 4h teve sinal antes dos custos |
| 3 | Rompimento 4h sem alvo, com stop móvel (13a/13b) | Primeiro resultado positivo (+7% a +9%), mas só 100 operações |
| 4 | A mesma regra em BTC e ETH desde 2017 (14a/14b) | Reprovada: ETH não superou o aleatório; comprar e segurar rendeu mais nos dois |

Conclusões:
- Day trade em cripto (5m/15m) perde para o custo da Binance Spot.
- Seguir tendência em 4h tem algum sinal, mas não supera comprar e segurar.
- Futuros (operar vendido) não está disponível na conta Binance do Juares; não contornar.
- **Busca por estratégia em cripto encerrada**, como combinado antes do teste.

### 3. B3: preparação
- Briefing de pesquisa em `b3/PESQUISA_CORRETORA.md`.
- Duas pesquisas do Gemini conferidas em `b3/VERIFICACAO_PESQUISA.md`: erro grave
  (valor do ponto do WIN é R$ 0,20, não R$ 1,00) e regras de robô sem fonte.
- Na B3 o custo é ~30 vezes menor que na Binance (~0,01% contra ~0,3% por operação).
  Em compensação, a alavancagem é de ~180 vezes: margem baixa não é risco baixo.
- **Corretora escolhida: XP.** Na área "Automações" da conta: MetaTrader 5 e
  MetaTrader 5 (Simulador), ambos grátis.
- MT5 instalado no Windows do Juares. **Ainda não conecta:** o servidor XPMT5-DEMO
  responde "Invalid account". Causa provável: os dados de acesso do simulador foram
  enviados para um e-mail que estava desativado (reativado em 09/11/2026).

### 4. B3: motor adaptado (11/11/2026)
- Histórico de 5 anos de WIN e WDO exportado do MT5 da XP: íntegro (`b3/DADOS.md`).
- Pesquisa do Codex com fontes (`b3/corretoras.md`): a corretagem zero da XP exclui robôs;
  custo usado no motor: WIN R$ 1,35 e WDO R$ 2,24 por contrato e por lado, mais 1 tick.
- `motor/futuros.py`: contratos e pontos, comprado e vendido, zeragem às 18h00, nada passa
  de um dia para o outro, pausas e saltos de vencimento tratados. Estratégia nova de
  rompimento da faixa de abertura. 70 testes.
- Nenhuma estratégia foi rodada no dado real da B3: as hipóteses são registradas antes.

### 5. B3: rodada 5 (hipóteses 15 a 18), 11/11/2026
- Comprado e vendido, 1 contrato, WIN e WDO, faixa de abertura e rompimento.
- Com R$ 1.000 a conta quebra nas quatro (−84% a −94%).
- Medidas com capital que não quebra: as quatro ganham antes dos custos e superam o
  aleatório, mas o custo de robô na XP (~R$ 4,70 por operação no WIN) é maior que o ganho.
  Reprovadas. Capital para a pior queda caber em 10%: R$ 47 mil a R$ 143 mil por contrato.

### 6. Auditoria do Codex e reexecução 5R (11/11/2026)
- O Codex corrigiu medições do motor (`AUDITORIA_CODEX.md`). Revisado pelo Claude; 133 testes.
- A conferência dos CSVs bloqueou o WIN por duas pausas no pregão; documentadas em
  `b3/PAUSAS_CONFERIDAS.toml` (uma é falha confirmada da B3), sem apagar nem preencher dados.
- Reexecução das 8 medições da rodada 5: **veredito igual, todas reprovadas.** Nos testes de
  5 min o dinheiro não mudou; o aleatório corrigido ficou mais exigente, e o rompimento deixou
  de superá-lo. Só a faixa de abertura mantém sinal antes dos custos, ainda menor que o custo.

### 7. Rodada 6 (hipóteses 19 a 25), 11/11/2026
- Média móvel, candle de força (a favor e contra) e martingale, no WIN e no WDO.
- Todas reprovadas. Com R$ 1.000,90 todas quebram; o martingale quebrou em 3 operações.
- Melhor medição: candle de força a favor no WDO (fator de lucro 1,31, +R$ 3,8 mil), mas
  só 166 operações e o mesmo método perde no WIN. Não vira candidato pela regra registrada.

### 8. Rodadas 7 a 9 (11/11/2026): canal
- Rodada 8 (ações) cancelada antes de rodar: foco em WIN e WDO.
- Rodada 9: canal desenhado só com o passado, atravessando os dias, alvo na linha de retorno,
  em 15/30/60 min e 4 h. Comprar na LTA / vender na LTB não tem vantagem. A aceleração em
  15 min é positiva depois dos custos nos dois mercados (fator 1,17 e 1,10), mas abaixo da
  régua. Tempos maiores: operações de menos para validar com 5 anos.

## Próximos passos

**Atualização de auditoria (Codex, motor 0.2.0):** foram corrigidos erros reproduzíveis
de execução, drawdown, agregação e validação; veja [AUDITORIA_CODEX.md](AUDITORIA_CODEX.md).
A suíte passou em 104 casos, com 4 testes da amostra real pulados por interceptarem a
reserva. Critérios, hipóteses e regras de estratégia foram preservados. Os resultados
de mercado acima não foram recalculados e nenhuma hipótese foi aprovada. Os passos
antigos de exportação/adaptação abaixo são histórico; a próxima etapa técnica exige
conferir os dados de desenvolvimento e reexecutar as hipóteses existentes com registro
prévio da revisão, sem usar a reserva nem operar dinheiro real.

### Juares
1. **Conseguir o login e a senha do MT5 Simulador.** Conferir o e-mail reativado (e o
   spam); se não houver nada, pedir o reenvio no site (Automações) ou no chat da XP:
   > "Contratei o MetaTrader 5 Simulador, mas meu e-mail estava desativado e não recebi
   > os dados de acesso. Pode reenviar o login, a senha e o servidor? O MT5 retorna
   > 'Invalid account' no XPMT5-DEMO."
2. **Conectar o MT5** (Arquivo → Conectar-se à conta de negociação). Funcionou quando o
   canto inferior direito mostra barras verdes no lugar do ponto vermelho "0 / 0 Kb".
3. **Exportar o histórico:**
   - Ferramentas → Opções → Gráficos → "Máximo de barras no gráfico" = Unlimited;
     fechar e abrir o MT5.
   - Exibir → Símbolos (Ctrl+U) → aba Barras → `WIN$N`, M5, início 01/01/2018 →
     Solicitar → Exportar barras. Repetir para `WDO$N`.
   - Enviar os dois CSVs (ou um print com a primeira e a última data de cada um).
4. **Pedir à XP, por escrito:** robô no MT5 é permitido em conta real para WIN e WDO?
   Python? Limite de ordens? Corretagem e margem de day trade?
5. **Definir o capital** para a B3, um valor que aceite perder inteiro. Com menos de
   alguns milhares de reais, as regras de risco não deixam operar.

### Claude (quando o histórico chegar)
1. Conferir quantos anos vieram e se a série contínua tem saltos falsos na troca de
   vencimento.
2. Adaptar o motor à B3: pontos, valor do ponto (WIN R$ 0,20; WDO R$ 10), tick, custos
   por contrato, horário do pregão e zeragem no fim do dia.
3. Registrar as hipóteses da B3 em `HIPOTESES.md` **antes** de rodar, com a mesma régua.
4. Só o que passar segue para o período reservado, depois simulador ao vivo, e só então,
   com orçamento de risco autorizado por escrito pelo Juares, conta real.

## Regras que continuam valendo
- Nenhuma ordem real sem autorização do Juares. Robô só com orçamento de risco escrito
  e botão de desligar.
- Senhas e chaves nunca no chat nem no Git.
- A régua não muda depois de ver o resultado.

## Entrega prática 0.3.0 — 10/11/2026

- `conferir-b3`: manifesto com SHA-256, origem declarada e diagnóstico no recorte de
  desenvolvimento. Lacunas, conflitos, preços incoerentes ou fora do tick bloqueiam.
- A conferência foi conectada ao carregamento B3 no fluxo normal: sinais só são
  calculados depois que os dados passam nas verificações disponíveis. O comando não
  certifica todos os pregões, horários ou ajustes de vencimento.
- `diario-b3`: CSV normalizado de operações encerradas no simulador → JSON e HTML
  adaptável a celular/computador, com preços, custos e motivos. Os preços executados
  já incorporam slippage, que não é descontado novamente. Não é um robô conectado.
- Ambos os comandos novos mantêm a reserva bloqueada. A análise prospectiva recente
  e a ligação ao PWA/MT5 ficam para outra etapa definida; o PWA não está neste branch.
- 128 testes passaram; 4 da amostra real pulados. Casos novos usam preços artificiais.
  Nenhuma hipótese executada ou aprovada nesta entrega; critérios e estratégias preservados.
- Uso e modelo em [b3/COLOCAR_EM_PRATICA.md](b3/COLOCAR_EM_PRATICA.md).
- Faltam os CSVs locais e relatórios completos para a conferência/reexecução dos números antigos.

## Pesquisa adaptativa 0.4.0 — 11/11/2026

- Pedido do Juares: várias formas de operar conforme o mercado, aprendizado com perdas
  e ganhos, nos tempos de 5, 15 e 30 minutos.
- Hipóteses 55–57 registradas antes da implementação no commit `c381e37`.
- `adaptativo-b3`: seis especialistas de parâmetros fixos, contexto causal e memória
  separada por contexto; só aprende com operações simuladas encerradas em barras
  anteriores à decisão. Pode ficar de fora; responsável pela posição não muda até sair.
- Relatórios de decisões, operações, comparação diária, custos e inverso com mesmos
  instantes. A melhor escolha retrospectiva do dia é identificada e não alimenta o seletor.
- Mesma régua, custo existente como premissa, até um contrato e reserva bloqueada.
  Nenhuma integração com corretora ou alteração do PWA.
- 184 testes passaram, 4 da amostra real foram pulados. Os 27 novos casos só usaram dados
  artificiais. Nenhuma medição financeira nova com WIN/WDO real nem aprovação.
- Próximo passo: no ambiente com os CSVs M5, rodar todas as seis combinações registradas
  (WIN/WDO × 5/15/30), sem modificar parâmetros ou abrir a reserva. Depois, avaliação
  conjunta e confirmação prospectiva em simulador. Ver [b3/MOTOR_ADAPTATIVO.md](b3/MOTOR_ADAPTATIVO.md).
