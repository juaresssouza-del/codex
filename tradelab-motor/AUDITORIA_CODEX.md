# Auditoria do motor — versão 0.2.0

Auditoria técnica de execução, dados e validação, feita sobre o commit
`5539612ae9e1741e5b9255ce76a4798262ccd621`, no branch
`claude/stoic-fermat-kpfnkk`. Não é uma nova pesquisa de estratégia nem uma certificação
de rentabilidade. O ponto de partida foi `RELATORIO_CODEX.md`, seguido de `STATUS.md`,
`HIPOTESES.md`, código e testes.

**Conclusão:** havia erros reproduzíveis de medição e execução. As correções deixam o
simulador mais confiável, mas não aprovam nenhuma hipótese e podem tornar os resultados
anteriores piores ou diferentes. Os números históricos não foram recalculados nesta
auditoria: `dados/` e `resultados/` não estão disponíveis neste checkout.

## O que foi corrigido

| Área | Problema comprovado | Correção e efeito |
|---|---|---|
| Queda intrabar — Spot e B3 | Quando havia saída por alvo ou fim do pregão, a posição já estava fechada na hora de registrar a mínima. O movimento adverso anterior à saída desaparecia. | A mínima é registrada enquanto a posição existe. Movimento posterior a uma saída na abertura não é atribuído à posição. Stops limitam o trecho considerado ao preço de saída simulado. |
| Cronologia do drawdown | O fechamento do próprio candle podia virar um pico usado para medir uma mínima que poderia ter ocorrido antes dele. A CLI também omitia o capital inicial no cálculo da queda em reais. | A queda intrabar é comparada com os picos de **fechamentos anteriores**, incluindo o capital inicial. Mesma regra no executor, emenda das janelas e saída da CLI. Não é reconstrução de pico tick a tick. |
| Walk-forward contínuo | O aquecimento era o máximo dos parâmetros escolhidos em todas as janelas, incluindo escolhas futuras. Na B3, isso podia mudar operações de um pregão anterior. | Cada barra usa o aquecimento escolhido para sua janela. O prefixo vem da grade conhecida previamente, sem consultar escolhas futuras. Teste altera só a escolha posterior e exige passado idêntico. |
| Janelas sem configuração elegível | Eram omitidas da curva. Se nenhuma janela operasse, o resultado ficava com timestamp fictício e sem as colunas necessárias para calcular métricas. | Os meses permanecem no histórico com capital parado e sem operações; o resultado é medido e reprovado, sem exceção por esquema vazio. |
| Monte Carlo B3 | A mesma codificação aleatória de Spot era reaproveitada. Em modo comprado/vendido, `-1` podia abrir/reverter para vendido quando a referência pretendia encerrar. | Referência consulta a posição efetiva e distingue compra, venda e encerramento. Mantém custos, risco, stops e zeragens do mesmo executor. Frequência/duração continuam sendo calibrações aproximadas. |
| Elegibilidade da referência | O aleatório podia emitir sinais em barras em que a estratégia ainda estava aquecendo ou não tinha configuração elegível. | `Resultado.sinais_validos` acompanha a curva e restringe a referência às mesmas barras elegíveis. A referência precisa corresponder aos timestamps do histórico fornecido. |
| Encerramento explícito B3 | Existia a constante `SAIR`, mas o processamento dos sinais não a consumia. Uma janela contínua sem parâmetro também podia converter saída em uma nova venda. | `SAIR` encerra sem abrir posição contrária; a janela sem parâmetro não cria entradas. A abertura também respeita o menor entre o limite de entrada e a zeragem. |
| Agregação M5 para intervalos maiores | Blocos com candle faltante e blocos finais parciais recebiam a duração de um candle completo. Isso ocultava lacunas e inventava seu horário final. | Só blocos completos são agregados. Blocos removidos são contados e informados pela CLI; a lacuna permanece e provoca reaquecimento. O teste antigo que exigia incluir blocos parciais foi corrigido com justificativa explícita. |
| Entrada limitada intrabar | A máxima da barra podia acontecer antes do preenchimento da compra. Mesmo assim, o motor creditava um alvo nessa mesma barra. | Se o preenchimento foi intrabar, só credita o alvo naquela barra quando o fechamento comprova cruzamento posterior. Stop continua prioritário. É uma convenção conservadora com OHLC. |
| Preço e lote | Passos como `0,25` eram arredondados usando uma casa decimal, podendo produzir um lote inválido. Proteção arredondada para a própria entrada podia dividir por zero ou gerar saída sem distância. | Precisão vem do passo decimal; stops/alvos sem distância válida são recusados antes do dimensionamento. |
| Configuração e integridade | Custos negativos, alguns valores infinitos, limites fracionários/negativos e volumes MT5 inválidos podiam passar. Uma métrica infinita podia ser aprovada. | Validação de valores finitos, domínios e inteiros. Dados inválidos não viram ganho artificial. MT5 sem intervalo inferível recebe erro explícito. |
| Moeda e API de custos | Agregação podia somar BRL com USDT. A API B3 sem argumento de custos recebia o objeto de custos de Spot e falhava. | Agregação rejeita moedas distintas. Na ausência de custos explícitos, a API escolhe as premissas do mercado correto. |
| Rastreabilidade | Relatório JSON não identificava a revisão do motor. | Relatórios novos incluem `versao_motor = "0.2.0"`. Não misturar seus números com os relatórios anteriores sem revisão. |

## Evidência e verificações

Foi executada a suíte anterior **antes das alterações**: **70 testes passaram**; os
**4 testes dependentes da amostra real do PWA foram desmarcados**, para proteger a reserva.

Foram acrescentados **34 casos de regressão**, todos com preços inventados ou exemplos
curtos controlados. Os defeitos principais foram reproduzidos antes de suas correções.
Exemplos independentes de resultado esperado:

- B3, um contrato de WIN, capital fictício de R$ 10.000, preço de entrada de 100.000,
  mínima de 99.000 e fechamento no mesmo preço de entrada: a queda observada antes
  da saída de fim de dia é R$ 200, e não zero.
- Candle de alvo, com preço menor antes da saída em cenário OHLC conservador: o lucro
  realizado não apaga a mínima anterior.
- Limitada em 100, abertura 101, máxima 103, mínima 99,5 e fechamento 100: a máxima
  não comprova que o alvo 102 foi negociado **depois** da compra.
- Um bloco de quinze minutos que perdeu um de seus candles de cinco minutos não pode
  ser tratado como um candle completo.
- Mudar apenas o aquecimento escolhido numa janela futura não pode mudar as operações
  da janela anterior.

Resultado da suíte da versão auditada: **104 passaram e 4 foram pulados**, de **108
casos coletados**. Os quatro pulos são explicados abaixo, não falhas silenciosamente
ignoradas. Ambiente utilizado: Python 3.12, NumPy 2.3.5, pandas 2.2.3 e pytest 9.2.0.

Reprodução da verificação, com as dependências instaladas:

```sh
cd tradelab-motor
python -m pytest -q
```

`tests/test_auditoria.py` concentra as regressões novas. Também foram verificados o
comando `--help`, a compilação dos módulos e o diff. Não foram executados comandos
`baixar`, `backtest`, `validar`, `agregar` ou `--usar-reserva` sobre dados reais.

## Reserva, estratégias e critérios preservados

`criterios.toml`, `HIPOTESES.md` e `motor/estrategias.py` não foram alterados. Nenhuma
hipótese nova foi executada; nenhum parâmetro de estratégia foi otimizado. Os custos
numéricos e os horários escolhidos pelas rodadas anteriores também foram mantidos.

Blobs da base preservados:

| Arquivo | SHA do blob |
|---|---|
| `criterios.toml` | `611b30fd5645fdd963507957f0a925fb6963dc52` |
| `HIPOTESES.md` | `42bc7a372fe7f15046ee148ddb9419b2902b9f7e` |
| `motor/estrategias.py` | `944d0c530c4f10c2a88c5c3ec48f69688618ef7b` |

A fixture real `tests/fixtures/tradelab-amostra-btcusdt-15m.json` tem timestamps de
**04/11/2026 a 09/11/2026**, dentro da reserva definida a partir de **07/2026**.
Sua execução foi excluída já na verificação inicial. A fixture `amostra` agora confere
os timestamps antes de carregar preços para execução e pula seus quatro testes
dependentes quando houver interseção com a reserva. O arquivo de preços não foi
editado. Casos com datas futuras geradas artificialmente continuam sendo dados
sintéticos, não uso do histórico reservado.

Há exposição prévia documentada: a primeira rodada de `HIPOTESES.md` informa ter visto
julho–novembro/2026 antes da criação da reserva; `b3/DADOS.md` já descreve eventos de
outubro/2026. Não é correto declarar retrospectivamente esses dados totalmente
desconhecidos. Esta auditoria não usou seus preços em execuções, nem mudou a data da
reserva para contornar o problema.

## Premissas e divergências que não viraram novos parâmetros

- **Custos XP:** WIN R$ 1,35 e WDO R$ 2,24 por contrato/lado são premissas das rodadas,
  não confirmação da tarifa individual do EA. A pesquisa `b3/corretoras.md` registra
  que a rota MT5/EA não foi confirmada e que falta a conversão oficial para fechar o
  componente B3 de WDO. Os comentários foram corrigidos; os números não foram
  reduzidos para tentar fazer uma hipótese passar.
- **Sessão, margem e execução:** zeragem fixa às 18h00, garantia, tick e slippage são
  parâmetros do modelo. Não comprovam execução por esse preço/horário na conta real
  nem reconstituem todas as alterações históricas de calendário e margem.
- **Grade registrada:** `HIPOTESES.md` descreve seis combinações de
  `rompimento_curto`, mas a grade atual gera oito. Sem os relatórios JSON originais,
  não se pode afirmar qual revisão/grade produziu cada número. Não se alterou a grade.
- **Stop móvel:** a descrição antiga de uma mínima móvel que “nunca desce” não
  corresponde a um stop monotônico implementado no executor. O código usa sinal
  pela mínima de uma janela e stop percentual configurado. Implementar um trailing
  stop diferente exigiria uma hipótese própria registrada antes, e não uma correção
  disfarçada dos testes anteriores.
- **Métricas informativas:** Sharpe continua com a convenção legada de anualização em
  365 períodos. Não foi usado como critério de aprovação; não deve ser apresentado
  como Sharpe anual por pregão B3 sem definir e adaptar essa convenção.

## Limites desta auditoria e sequência

OHLC não revela a ordem exata de todos os preços dentro de uma barra, fila, liquidez,
preenchimento parcial, spread variável ou latência. As convenções conservadoras
documentadas não substituem ticks e execução observada. A referência aleatória tem
calibração aproximada; seu percentil não representa probabilidade de lucro futuro
nem uma correção estatística completa para todas as hipóteses já tentadas.

Não foram auditados os CSVs completos, o ajuste da série contínua, os relatórios JSON
antigos, o terminal do titular ou uma conexão de ordens. Não há execução real neste
motor. Os testes de código não demonstram vantagem econômica.

Antes de reaproveitar os números anteriores: obter apenas os dados de desenvolvimento
autorizados, conferir a revisão/configuração original e registrar em `HIPOTESES.md`
a reexecução técnica das hipóteses existentes com a versão auditada, preservando os
critérios e excluindo a reserva. Reconferir resultado líquido, queda e comparação
aleatória. **Nenhuma das hipóteses foi promovida a aprovada nesta auditoria.**
