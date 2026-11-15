# Calendário oficial — hipótese 26

Coletado em **15/11/2026**. Intervalo inclusivo: **01/11/2021 a 30/06/2026**, pela
data efetiva de publicação/decisão, e não pelo mês de referência do indicador.
Nenhum preço foi carregado e a hipótese 26 **não foi executada**.

| Evento | Datas confirmadas | Fonte da data |
|---|---:|---|
| FOMC, decisões regulares de juros | 38 | [Fed, calendário 2021–2026](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) |
| Payroll, Employment Situation | 55 | [BLS, arquivo oficial](https://www.bls.gov/bls/news-release/empsit.htm); cabeçalho de cada release |
| IPCA | 56 | [IBGE, índice de releases do IPCA](https://agenciadenoticias.ibge.gov.br/busca-avancada.html?produto=9256&tipo%5B0%5D=releases), páginas 0/30/60 |
| Copom | 37 | [Banco Central, comunicados das reuniões](https://www.bcb.gov.br/api/servico/sitebcb/copom/comunicados?quantidade=100), reuniões 243–279 |
| Total | 186 | Uma linha e fonte por evento em `eventos.csv` |

## Arquivos e aplicação da regra registrada

- `eventos.csv`: evento, data efetiva, regra, data de bloqueio, fonte da data,
  documento, fonte do calendário B3 quando necessária, consulta, situação e observação.
- `bloqueios.csv`: união das datas, com eventos e fontes. **179 datas civis distintas**;
  não são 179 pregões. Um evento no feriado brasileiro continua na sua data, sem deslocamento.
- `excecoes.csv`: adiamentos, publicação cancelada e voto extraordinário do FOMC.
- `fontes_coleta.json`: método e SHA-256 dos HTML/JSON realmente baixados. Fontes lidas
  pela ferramenta web estão identificadas assim, sem inventar hash de download.
- `manifesto.json`: contagens e SHA-256 dos quatro arquivos de dados acima.

Em FOMC/payroll/IPCA, `data_bloqueio_b3` é a mesma data do anúncio. Em Copom, é o
primeiro pregão seguinte, conforme a hipótese já registrada. Foram conferidos os
calendários anuais da B3; nas 37 reuniões há três desvios em relação ao dia civil seguinte:

| Decisão Copom | Fechamento da B3 no dia seguinte | Primeiro pregão seguinte | Fonte B3 |
|---|---|---|---|
| 15/06/2022 | Corpus Christi, 16/06 | 17/06/2022 | [Comunicado 109/2021-VNC](https://www.b3.com.br/data/files/21/E1/08/FF/077CC710BD0885C7AC094EA8/EC%20109-2021-VNC%20Calendario%202022%20com%20ajustes.pdf) |
| 01/11/2023 | Finados, 02/11 | 03/11/2023 | [Ofício 151/2022-PRE](https://www.b3.com.br/data/files/29/27/8A/45/89584810A58E3348AC094EA8/OC%20151-2022%20PRE%20Calend%C3%A1rio%20de%20Feriados%20em%202023%20e%20funcionamento%20da%20B3%20em%2022.02.2023%20%28Quarta-Feira%20de%20Cinzas%29%20%28PT%29.pdf), vigente em 01–02/11; revogado em 03/11 |
| 18/06/2025 | Corpus Christi, 19/06 | 20/06/2025 | [Calendário 2025](https://www.b3.com.br/pt_br/noticias/calendario-de-feriados-2025.htm) |

Cada reunião tem sua fonte anual B3 no CSV. Os demais anos usam o
[arquivo de calendários, 2021](https://www.b3.com.br/main.jsp?lumA=1&lumII=8A80CB81633FBF0B0163402956733E3A&lumPageId=8A6882694E91F2D4014E9248DBB001C9),
[ofício 085/2024-PRE](https://www.b3.com.br/data/files/62/23/AC/05/CD630910CA8BA9F8DC0D8AA8/OC%20085-2024%20PRE%20Errata%20Retificacao%20do%20Calendario%20de%20Feriados%202024%20-%20Feriado%20Labor%20Day%20%28PT%29.pdf)
e [calendário 2026](https://www.b3.com.br/pt_br/noticias/calendario-de-negociacao-da-b3-confira-o-funcionamento-da-bolsa-em-2026.htm).
Feriado que afeta apenas liquidação em dólar não foi tratado como fechamento dos
derivativos listados WIN/WDO. Este arquivo não é um calendário universal de sessões B3.

## Exceções que impedem gerar datas por fórmula

O [BLS documenta as mudanças de agenda de 2025/2026](https://www.bls.gov/bls/2025-lapse-revised-release-dates.htm).
As datas efetivas foram também verificadas nos cabeçalhos dos releases individuais:

| Referência do payroll | Data prevista | Data efetiva |
|---|---|---|
| Setembro/2025 | 03/10/2025 | 20/11/2025 |
| Outubro/2025 | 07/11/2025 | Não publicado; não foi criada uma data de evento |
| Novembro/2025 | 05/12/2025 | 16/12/2025 |
| Janeiro/2026 | 06/02/2026 | 11/02/2026 |

Por isso há 55 releases do payroll, e não 56. O campo vazio de data efetiva na linha
cancelada de `excecoes.csv` significa ausência de publicação, não uma data a estimar.
O IPCA de maio/2023 foi publicado em **07/06/2023**, conforme a data do release no índice
do IBGE; data de modificação de arquivo no FTP não substitui a publicação.

O Fed também lista em **22/08/2025** um *notation vote* sobre estratégia monetária de
longo prazo. Ele está em `excecoes.csv`, fora das 38 decisões regulares de juros.
**Antes de executar a hipótese 26**, o Claude precisa registrar como a expressão
“decisão do FOMC” trata esse voto. Não escolher a interpretação pelo resultado do teste.
Nenhuma das interpretações foi testada nesta entrega.

## Procedência e limites

As 55 datas do payroll foram extraídas do cabeçalho “embargoed until”, conferidas com
a data do link do arquivo BLS e registradas com hash do HTML original. Releases legados
com caracteres Windows-1252 foram decodificados explicitamente, preservando o hash dos bytes.
As 56 datas IPCA vêm dos cartões do índice oficial, com link ao release correspondente;
o filtro é IPCA, não IPCA-15. As datas Copom são `dataReferencia` do JSON oficial,
com número da reunião na observação. No FOMC usa-se o último dia da reunião regular,
nunca a publicação posterior da ata.

Não foram coletadas surpresas, valores econômicos, preços ou notícias para gerar sinais.
Um calendário retrospectivo com datas efetivas não demonstra que um adiamento era conhecido
com antecedência; se o futuro uso exigir a agenda tal como conhecida em cada dia, será
necessário documentar também os avisos e horários de revisão. Não usar IA com conhecimento
do desfecho para interpretar notícias do passado.

Próximo passo do Claude: conferir o escopo do voto extraordinário, registrar a execução
da hipótese 26 antes de rodar e usar somente o recorte até junho/2026. A coleta dos dados
não autoriza mudar a régua, criar estratégias novas ou acessar a reserva.
