# Pesquisa para a B3 — briefing para o Codex

Objetivo: escolher a corretora e a fonte de dados para testar e, se aprovado, operar um
robô em **mini-índice (WIN)** e **mini-dólar (WDO)** na B3. O robô roda sozinho durante o
pregão, porque o dono trabalha das 8h às 18h. Prioridade: **menor custo total por
operação**, **robô permitido em conta real** e **histórico intradiário confiável**.

Este arquivo é a lista do que o motor de backtest (`tradelab-motor/`) precisa. A resposta
vai em `tradelab-motor/b3/corretoras.md`, no formato da seção "Formato da resposta".

## Regras da pesquisa

- **Fonte primária primeiro:** site da corretora (página de custos, contrato, FAQ), site da
  B3, CVM. Blog, vídeo, comparador ou página com link de afiliado só como apoio, e
  marcado como tal.
- **Cada número com o link e a data da consulta.** Se não achar, escreva "não encontrado".
  Não estime e não preencha com valor de outra corretora.
- **Preço promocional** ("corretagem zero", "primeiro mês grátis"): registre o preço
  promocional, o preço cheio e a condição para manter o desconto.
- Não abra conta, não preencha cadastro e não informe dados pessoais em nenhum site.

## 1. Corretoras

Inclua as que oferecem MetaTrader 5 para B3 e as conhecidas por day trade em minicontratos.
No mínimo 6. Para cada uma:

### 1.1 Regulação
- Participante autorizado da B3 e registro na CVM (sim/não, com link).
- Selo PQO da B3, se houver.

### 1.2 Robô e plataforma
- Oferece **MetaTrader 5** para B3? Custo mensal da plataforma e condição para isenção.
- **Robôs (Expert Advisors) permitidos em conta real?** Há regra escrita? Copie o trecho.
- Permite conectar **Python** ao MT5 (pacote `MetaTrader5`) em conta real?
- Limites: ordens por segundo, proibição de alta frequência, ordens máximas por dia.
- Outras plataformas com automação (ProfitChart/NTSL, Tryd, API própria) e custo.
- **Conta demo / simulador:** existe? Dados em tempo real? Duração?

### 1.3 Custos por contrato (day trade)
Para **WIN** e **WDO**, separadamente:
- Corretagem por contrato ou por ordem, e se é cobrada na entrada e na saída.
- ISS sobre a corretagem.
- Taxa de custódia, manutenção de conta, roteamento e "zeragem compulsória".
- Qualquer outra taxa da corretora.
- Os emolumentos da B3 vão na seção 2, não repita aqui.

### 1.4 Margem e risco
- Margem (garantia) para day trade por contrato de **WIN** e de **WDO**.
- Horário da zeragem automática pela corretora.
- Capital mínimo para abrir conta ou operar minicontratos.
- O que acontece se o robô deixar posição aberta no fim do dia.

### 1.5 Dados históricos pela corretora
- O MT5 (ou outra plataforma) da corretora dá quantos anos de candles de **1, 5 e 15
  minutos** de WIN e WDO? E de tick?
- Tem série **contínua** (por exemplo `WIN$` / `WIN$N`)? Como ela emenda os vencimentos?
- Dá para **exportar em CSV**? Como?

### 1.6 Infraestrutura
- O robô exige computador ligado com Windows? A corretora oferece **VPS**? Custo e
  localização do servidor.
- Reclamações sobre instabilidade ou execução no Reclame Aqui (nota e tema principal,
  com link).

## 2. B3 (fonte oficial)

- **Horário de negociação** atual de WIN e WDO, incluindo a abertura e o fechamento, e o
  efeito do horário de verão americano. Há ofícios recentes, como o OC 050/2026-VNC
  (vigente a partir de 26/10/2026 e 03/11/2026).
- **Especificação do contrato:** valor do ponto, tamanho do tick e multiplicador de WIN e WDO.
- **Vencimentos e rolagem:** meses de vencimento e regra da data de cada um.
- **Emolumentos e taxa de registro** para day trade de minicontratos, com a tabela por
  faixa de volume, se houver.
- Limites de oscilação e regras de leilão ou circuit breaker que afetem um robô.

## 3. Fontes de dados históricos fora da corretora

O teste precisa de **pelo menos 2 anos** de candles de 5 ou 15 minutos (ideal: 5 anos ou
mais) de WIN e WDO, com OHLC e volume. Para cada fonte (pacote de market data da B3,
Nelogica/Profit, fornecedores pagos, bases públicas):
- Custo, período disponível, intervalos (tick, 1m, 5m, 15m) e formato (CSV, API).
- Série por vencimento, contínua, ou ambas. Se for contínua, como ajusta a rolagem.
- Licença: permite uso pessoal em backtest?

## 4. Tributação (só para confirmar, com fonte da Receita Federal)

- Alíquota de IR em day trade de minicontratos e o IRRF de 1%.
- Compensação de prejuízo e prazo do DARF.

## Formato da resposta

Arquivo `tradelab-motor/b3/corretoras.md` com:

1. **Tabela-resumo**, uma linha por corretora: MT5 (sim/não), robô em conta real
   (sim/não/sem regra escrita), custo total de **uma operação completa** de 1 WIN (entrada
   + saída: corretagem + ISS + emolumentos B3) e o mesmo para 1 WDO, plataforma por mês,
   margem day trade WIN/WDO, anos de histórico intradiário e VPS.
2. Uma seção por corretora com os itens 1.1 a 1.6, cada número com link e data.
3. Seções 2, 3 e 4 com os dados oficiais.
4. **Ranking final** pelo custo total de uma operação completa de WIN, desempatado por
   (a) robô explicitamente permitido em conta real e (b) anos de histórico exportável.
5. Lista do que não foi encontrado.
