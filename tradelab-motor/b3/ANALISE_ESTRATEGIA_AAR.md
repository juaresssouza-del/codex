# Estratégia do vídeo da Academia Alta Renda — análise para o TradeLab

Data da análise e das consultas: **11/11/2026**.
Código e histórico de decisões consultados no branch `claude/stoic-fermat-kpfnkk`, commit `b9598bad6125badaafcc1d75858bfc79f423c6e6`.

**Parecer: vale formalizar como hipótese; rentabilidade em WIN/WDO não demonstrada.**
A descrição ainda deixa escolhas discricionárias que impedem reproduzir um robô único.
Esta entrega é uma análise documental: nenhuma estratégia nova foi executada, nenhum
critério foi modificado e nenhum preço do período reservado foi utilizado.

## Fonte e limite da análise

- [Vídeo original — A ÚNICA Estratégia de DayTrading que Você Vai PRECISAR! 🤯, Academia Alta Renda](https://www.youtube.com/watch?v=uoSLafTWnY4).
- [Transcrição republicada associada ao mesmo título e canal, Readray](https://readray.ai/pt/notes/day-trading-strategy-20251030/the-only-day-trading-strategy-you-need).

O título e o canal foram conferidos no YouTube. A reprodução não avançou e o painel de
transcrição oficial permaneceu vazio neste acesso. A extração das regras abaixo usa a
transcrição republicada, com marcações de tempo; não constitui conferência audiovisual
integral. Ela apresenta aparentes erros de transcrição, portanto números falados
incoerentes não foram tratados como instruções. Alegações de lucro do apresentador não
foram verificadas.

## Método descrito na transcrição

| Trecho aproximado | Regra extraída |
|---|---|
| 00:24–03:24 | Tendência por estrutura. Na alta, um fundo só ganha validade estrutural depois de o avanço subsequente romper o topo anterior; perder esse fundo muda o viés. |
| 03:35–05:45 | Buscar demanda na alta e oferta na baixa. Zona: mínima à máxima do candle anterior ao impulso, junto à consolidação; esperar retorno. |
| 05:45–07:27 | Compra: stop abaixo da zona e alvo no topo recente. Venda: stop acima e alvo no fundo recente. |
| 07:46–08:59 | Filtrar operações por recompensa/risco superior a 2,5:1. |

Essas são regras descritivas da fonte, não especificação de execução já implementada.

## O que muda em relação ao nosso motor

O código inspecionado em [motor/estrategias.py](../motor/estrategias.py) usa regressão
linear, R² e limites paralelos para os sinais de canal. A descrição acima usa estrutura
de pivôs e zonas horizontais. Há parentesco na ideia de seguir tendência, mas os sinais
não são equivalentes. Reprovar os canais não prova que esta alternativa perde; também
não fornece evidência a favor dela.

Em [HIPOTESES.md](../HIPOTESES.md), a rodada 9 registra aceleração em 15 minutos com
resultado líquido positivo: WIN +R$ 856, fator de lucro 1,17, 101 operações; WDO
+R$ 1.090, fator 1,10, 145 operações. Fonte: registro desse commit, consultado em
11/11/2026, sem reexecução independente nesta análise. Nenhuma passou a régua. Assim,
“nenhuma aprovada” é a descrição correta do projeto, mesmo havendo medições positivas.

## O que precisa ser decidido antes de implementar e testar

São escolhas da nossa futura adaptação; não devem ser atribuídas ao apresentador.

| Decisão pendente | Por que altera o resultado |
|---|---|
| Tempo gráfico e algoritmo de pivôs, incluindo confirmação | Diferentes definições mudam a tendência e o momento em que o robô pode conhecê-la. |
| Rompimento por máxima/mínima ou por fechamento | Um pavio pode inverter o viés numa versão e ser ignorado na outra. |
| Critério quantitativo de impulso e consolidação | Sem ele, selecionar zonas a olho depois de ver o desfecho permite escolher os acertos. |
| Zona elegível, prioridade entre zonas, validade e número de retornos | Evita escolher retrospectivamente a região que funcionou. |
| Preço de entrada, tipo de ordem e expiração | Tocar a zona não demonstra execução da ordem naquele preço. |
| Distância adicional do stop, alvo congelado e cálculo do retorno/risco | Preço efetivo, arredondamento e custos podem descaracterizar uma oportunidade aparente. |
| Reinício diário ou estrutura entre pregões e tratamento de vencimentos | A série contínua e lacunas podem criar estrutura artificial. |

**Risco principal de medição: usar informação futura.** Um pivô reconhecido após novos
candles só pode produzir decisões depois da confirmação. Uma zona identificada após
o impulso não pode gerar uma entrada retroativa. A validade do fundo não pode ser
antecipada ao rompimento que o confirma.

Uma entrada após confirmação no fechamento, executada na abertura seguinte, seria uma
adaptação nossa. Não deve ser apresentada como reprodução fiel de uma entrada limitada
no retorno à zona.

## Adaptação necessária na execução B3

Em [motor/futuros.py](../motor/futuros.py), `executar_futuros` recebe sinais de direção/
saída. Sua função interna `abrir` calcula stop e alvo a partir de percentuais
`risco.stop` e `risco.alvo` aplicados ao preço de entrada. Para representar a proposta
com fidelidade, será necessário transmitir e armazenar níveis de stop e alvo próprios
de cada operação e, se escolhida entrada limitada, modelar também preço e validade da
ordem. Acrescentar somente uma função de sinais não resolve essa diferença.

A especificação deve preservar execução causal, compra e venda, zeragem diária, custos
e proteção de risco. Se só houver barras OHLC, a sequência intrabar não é conhecida:
conflitos entre entrada, stop e alvo precisam de tratamento conservador ou dados mais
granulares. Encostar no limite não deve garantir uma execução perfeita.

Os níveis precisam respeitar os contratos: WIN varia em passos de 5 pontos; WDO em
0,5 ponto. Fontes oficiais, consultadas em 11/11/2026:
[B3 — WIN](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/mercado-de-acoes/futuro-de-ibovespa.htm)
e [B3 — WDO](https://b3.com.br/pt_br/produtos-e-servicos/negociacao/moedas/futuro-mini-de-taxa-de-cambio-de-reais-por-dolar-comercial.htm).
As tarifas em `CUSTOS` são premissas históricas do projeto; a rota e o custo efetivo do
EA na XP continuam sujeitos à confirmação documentada.

## Por que o filtro de retorno/risco não comprova vantagem

Exemplo matemático, não resultado observado: se cada vitória entregar exatamente
+2,5R e cada derrota −1R, a taxa de equilíbrio antes de custos é
1 / (1 + 2,5) = 28,57%. Taxas, diferença de execução e encerramentos antecipados
alteram esse equilíbrio. Um alvo distante também pode ser atingido menos vezes.

A transcrição não fornece uma série completa reproduzível de operações, com perdas,
custos, queda máxima e validação fora da amostra. Portanto, não há taxa de acerto
auditada para importar para o TradeLab nem promessa de renda que possamos adotar.

## Continuação concreta

1. Fechar uma única especificação mecânica e marcar explicitamente todas as adaptações
   nossas. Evitar uma busca ampla de configurações até aparecer um resultado favorável.
2. Registrar a hipótese completa em [HIPOTESES.md](../HIPOTESES.md) **antes** de qualquer
   teste de mercado, incluindo WIN e WDO, execução, custos, parâmetros e validação.
3. Implementar níveis por operação e conferir causalidade e execução com cenários
   artificiais, antes de usar o histórico.
4. Com os CSVs locais disponíveis, executar a validação de desenvolvimento com os
   critérios existentes, registrar também as tentativas que falharem e manter a mesma
   regra nos dois mercados.
5. Preservar [criterios.toml](../criterios.toml) e excluir julho/2026 em diante.
   Esta análise não autoriza abrir a reserva. Eventual avanço depende do processo de
   validação do projeto e, depois, de simulação prospectiva antes de dinheiro real.

Os diretórios `dados/` e `resultados/` não estão neste snapshot do Git. Sem esses CSVs
não foi realizado backtest novo, nem auditado o resultado financeiro completo das
rodadas anteriores.

**Estado final: análise concluída; especificação automática pendente; hipótese ainda
não registrada nem testada; nenhuma aprovação para operação real.**
