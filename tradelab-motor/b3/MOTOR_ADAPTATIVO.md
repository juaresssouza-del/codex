# Motor adaptativo de pesquisa — 11/11/2026

O pedido do Juares é reconhecer condições diferentes do mercado, escolher entre várias
formas de operar e aprender com os resultados. A versão 0.4.0 implementa uma primeira
política de seleção para pesquisa em WIN e WDO, nos tempos de 5, 15 e 30 minutos.
**Código implementado não demonstra rentabilidade. Não há ligação com conta real.**

## O que já foi testado na B3

Fonte: [HIPOTESES.md](../HIPOTESES.md), estado anterior a esta entrega, consultado em
11/11/2026. A contagem é de identificadores de hipóteses por ativo/tempo, não de técnicas
distintas nem de todas as configurações exploradas.

| Rodada | Identificadores B3 | Quantidade | Situação registrada |
|---|---|---:|---|
| 5 e reexecução 5R | 15–18 | 4 | Faixa de abertura e rompimento; reprovadas |
| 6 | 19–25 | 7 | Médias, força, força contrária e martingale; reprovadas |
| 7 | 27–30 | 4 | Canal com rompimento ou recuo; reprovadas |
| 9 | 39–54 | 16 | Suporte e aceleração; 8 inconclusivas por falta de operações; nenhuma candidata |

Total: **31 identificadores nas rodadas realizadas**, com reexecuções e variações de
capital que não foram contadas como técnicas novas. A hipótese 26 aguarda calendário;
31–38 foram canceladas antes de rodar. As novas 55–57 estão registradas e ainda não
foram executadas com o histórico real nesta entrega.

Existem medições positivas, incluindo força a favor no WDO e aceleração em 15 minutos
nos dois contratos. Elas falharam em outros requisitos da régua. Resultado positivo
isolado e estratégia aprovada são estados diferentes.

## O que podemos descobrir olhando para trás

Os candles permitem comparar regras reproduzíveis e suas oportunidades. Não identificam
quem lucrou, suas posições em outros mercados, seu risco ou suas intenções. Também não
permitem concluir que determinada estratégia de outra pessoa foi a contraparte de uma
operação nossa.

A nova saída diária compara os especialistas fixos, o seletor e ficar de fora. Uma
coluna adicional mostra qual especialista teria sido melhor **depois de conhecer o
fechamento**. Esse é um diagnóstico do conjunto testado, não previsão nem recomendação
de que poderíamos ter escolhido o vencedor antecipadamente. O seletor não lê essa coluna.

O inverso usa uma conta explícita: mantendo os mesmos instantes e supondo custos
simétricos, resultado inverso = −resultado líquido − 2 × custos. Assim, duas direções
podem perder depois dos custos. Alterar também stop, alvo ou tempo de saída produz
outra estratégia e exige outro teste registrado.

## Como a seleção funciona

A política completa foi registrada em [HIPOTESES.md](../HIPOTESES.md), hipóteses 55–57,
antes da implementação e de qualquer teste de mercado desta entrega.

| Parte | Comportamento |
|---|---|
| Biblioteca | SMA, rompimento curto, força, força contrária, suporte e aceleração em canal; parâmetros congelados |
| Contexto | Alta, baixa, lateral, choque ou aquecimento, calculados só até o fechamento atual |
| Memória | Por especialista e contexto da entrada; últimos 60 resultados líquidos simulados, já encerrados |
| Escolha | Exige 30 registros, média positiva e fator de lucro ≥ 1,3; escolhe a maior média líquida |
| Abstenção | Sem vantagem na memória, sem amostra ou em choque: nenhuma nova entrada |
| Atualização | Só incorpora uma operação em decisões de candles posteriores ao encerramento |
| Posição aberta | Mantém o responsável até a saída; sinal oposto encerra sem virar a mão na mesma abertura |
| Avaliação | Primeiros 12 meses só alimentam simulações; desempenho medido depois, em sequência cronológica |

É uma memória estatística de resultados, não uma IA que inventa regras após cada perda.
Os especialistas continuam em simulação mesmo quando não são escolhidos. O aprendizado
não exige abrir posições reais para experimentar.

Indicadores podem atravessar pregões, mas posições são zeradas diariamente. O ajuste de
vencimento WIN só altera indicadores; o preço de execução permanece original. Lacunas
intradiárias reiniciam o aquecimento. Foi mantido o executor B3 existente, com custos e
restrições; nenhum aumento de posição após perder foi acrescentado.

O capital de R$100 mil usado na pesquisa é uma escala de medição, não proposta para
aplicação do Juares. Orçamento pessoal, margem e autorização de conta real são outros
controles. As premissas de custo do EA na XP ainda dependem de confirmação.

## Como executar com os dados locais

Na pasta `tradelab-motor`, com as dependências do projeto instaladas:

```bash
python -m motor adaptativo-b3 --arquivo dados/B3/WIN_N_M5.csv --contrato WIN --origem "MT5 XP, exportação do histórico" --minutos 5 --pausas-conferidas b3/PAUSAS_CONFERIDAS.toml
```

Os nomes são os convencionais do projeto; use o caminho efetivo dos CSVs. Não informe
login, senha ou chave na origem. Repetir para 15 e 30 minutos, e depois para WDO nos três
tempos, sem omitir resultados ruins ou sem operações. A hipótese de cada tempo só pode
ser candidata se passar no WIN e WDO com a mesma política.

A conferência do M5 acontece antes dos sinais. A agregação mantém apenas barras
completas. Os critérios vêm do arquivo existente; o comando não oferece
`--usar-reserva`, troca de parâmetros ou redução de custos para fazê-lo passar.

Cada execução cria uma pasta própria em `resultados/adaptativo/`:

| Saída | Uso |
|---|---|
| `relatorio.json` | Procedência, hashes, parâmetros, métricas, controles, 200 aleatórias e avaliação da régua |
| `decisoes.csv` | Contexto, responsável, motivo da escolha/abstenção e último encerramento conhecido usado |
| `operacoes.csv` | Operações do seletor com o especialista responsável |
| `operacoes_controles.csv` | Operações de cada especialista fixo no período de avaliação |
| `diagnostico.csv` | Custos, motivo de saída, contexto, inverso e excursões dos controles e do seletor |
| `por_dia.csv` | Resultado diário de cada alternativa e melhor escolha retrospectiva, incluindo ficar de fora |

O diagnóstico marca ganho antes dos custos que virou prejuízo líquido. MFE/MAE usam
apenas barras anteriores à saída para não aproveitar extremos ocorridos depois do
encerramento. São descrições parciais do percurso, não alvos que se consiga executar
nesses preços nem prova da causa da perda.

## Como julgar o resultado

Os controles são executados novamente com os parâmetros e riscos comuns deste estudo;
não reproduzem necessariamente as grades walk-forward das rodadas antigas. Compare o
seletor com eles, com ficar de fora e com a referência aleatória, sempre depois de custos.
As 200 aleatórias usam o procedimento existente, aproximando frequência e duração;
não refazem a aprendizagem do seletor em cada permutação.

Os critérios de aprovação continuam os mesmos. A pontuação usada na memória é apenas
uma condição de seleção, não certificação de uma estratégia. Um relatório individual
não libera negociação: é preciso o resultado dos dois mercados e confirmação
prospectiva em simulador. A reserva de julho/2026 em diante continua bloqueada.

Escolher muitas regras depois de ver seus resultados aumenta o risco de ajustar a
história. Esta nova seleção também pode perder, inclusive mais que um especialista
fixo. A avaliação sequencial evita usar fechamentos futuros na escolha, mas não elimina
o viés acumulado de pesquisas anteriores no mesmo histórico.

Referências consultadas em 11/11/2026:

- [CVM — material sobre day trade, custos e riscos](https://www.gov.br/cvm/pt-br/assuntos/noticias/2020/educacao-financeira-em-pauta--cvm-lanca-materiais-educativos-sobre-day-trade-e-funcionamento-da-bolsa-de-valores-5221f3b6650040a084fd7e3554ad9807/).
- [Bailey e colaboradores — The Probability of Backtest Overfitting](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253).

## Estado desta entrega

O módulo e o comando estão implementados. Verificação com preços artificiais cobre
causalidade, aprendizado com resultados fechados, abstenção, responsável pela posição,
custos, inversão e exportação. **Os CSVs reais e relatórios completos não estão neste
checkout; nenhum resultado financeiro novo foi produzido.** A interface PWA não foi
alterada nem conectada ao seletor. O próximo passo é a execução das seis medições no
ambiente que contém os CSVs, respeitando o registro prévio e sem abrir a reserva.
