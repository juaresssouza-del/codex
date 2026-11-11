# Conferência dos dados e diário do simulador

Entrega 0.3.0 — 10/11/2026. Primeira etapa prática: conferir o histórico e comparar
preços previstos com execuções registradas. Não há conexão com conta ou envio de ordens.

## 1. Preparar no computador

Atualize o projeto no branch `claude/stoic-fermat-kpfnkk`. Abra o terminal na pasta
`tradelab-motor` e instale as dependências:

```powershell
py -3 -m pip install -e ".[dev]"
```

No Linux/macOS, use `python3` no lugar de `py -3`.

## 2. Conferir o histórico da B3

Coloque as exportações de **barras M5** do MT5 em `dados/B3/WIN_N_M5.csv` e
`dados/B3/WDO_N_M5.csv`. São arquivos tabulados com o cabeçalho do MT5, no horário
de Brasília. Informe a origem que realmente utilizou:

```powershell
py -3 -m motor conferir-b3 --contrato WIN --arquivo dados/B3/WIN_N_M5.csv --origem "Barras M5 exportadas do MT5 XP"
py -3 -m motor conferir-b3 --contrato WDO --arquivo dados/B3/WDO_N_M5.csv --origem "Barras M5 exportadas do MT5 XP"
```

O comando grava um manifesto JSON em `resultados/conferencia/`, com hash SHA-256,
origem declarada, cobertura observada, duplicatas e lacunas. O hash identifica os
bytes recebidos; não autentica a corretora nem prova qual contrato está no arquivo.

Opcionalmente, exija datas inicial e final, ambas inclusivas:

```powershell
py -3 -m motor conferir-b3 --contrato WIN --arquivo dados/B3/WIN_N_M5.csv --origem "Exportação MT5" --de 2025-01-06 --ate 2025-01-31
```

Essas datas são exigências suas, não um calendário de pregão inferido. Uma ponta
ausente bloqueia a conferência. Não foi implementada certificação de todos os dias
do calendário, horários oficiais ou ajustes de vencimento.

**BLOQUEADO / código de saída 2:** confira o diagnóstico e a origem. Não preencha nem
apague lacunas para passar. Uma pausa real da bolsa também exige conferência: o
verificador conservador ainda não distingue pausa de defeito da exportação. Os
comandos B3 `backtest` e `validar` passam por essa conferência antes de calcular
sinais no fluxo normal de desenvolvimento. O manifesto segue no relatório de validação.

**Reserva:** os preços de 07/2026 em diante são excluídos antes da conversão numérica
nessa conferência. O hash abrange o arquivo inteiro; o diagnóstico de preços abrange
somente o período de desenvolvimento. Os comandos novos não oferecem liberação da
reserva. O caminho explícito de confirmação final do motor anterior foi preservado e
não foi utilizado nesta entrega.

Passar na conferência só libera os dados para as verificações implementadas. Uma
hipótese continua exigindo registro prévio e aprovação nos critérios do projeto.

## 3. Preencher o diário

Faça uma cópia do modelo vazio:

```powershell
Copy-Item b3/diario-modelo.csv dados/B3/diario-simulador.csv
```

Preencha uma linha por **operação encerrada**, com separador `;`. Este é um formato
normalizado do TradeLab, não um importador automático do extrato bruto do MT5.

| Campo | Preenchimento |
|---|---|
| `id` | Identificador único, sem repetir a mesma operação |
| `ambiente` | Sempre `simulador` |
| `contrato` / `lado` / `quantidade` | `WIN` ou `WDO`; `comprado` ou `vendido`; contratos inteiros positivos |
| `entrada` / `saida` | `AAAA-MM-DD HH:MM:SS`, horário de Brasília; precisa encerrar no mesmo dia |
| `preco_entrada_previsto` / `preco_saida_previsto` | Referências documentadas antes da execução, para aquele mesmo tamanho de posição |
| `preco_entrada_executado` / `preco_saida_executado` | Preços dos fills; médias de múltiplos contratos podem ficar entre ticks |
| `taxas_previstas` / `taxas_executadas` | Totais em reais da operação completa, incluindo os dois lados; não são taxas por contrato |
| `stop` / `alvo` | Preços definidos no plano; podem ficar vazios quando não informados |
| `hipotese` | Identificação da hipótese já registrada ou identificação explícita de um teste de software |
| `motivo_entrada` / `motivo_saida` / `origem` | Explicação e origem dos registros, sem credenciais ou dados da conta |

Use números sem separador de milhares. Decimal pode usar ponto ou vírgula. Se uma
taxa não estiver disponível, não estime nem preencha zero: obtenha o dado antes de
importar. Os custos padrão do backtest não são usados como taxas observadas do diário.

Nesta primeira etapa o diário também bloqueia operações a partir de 07/2026. Ele
está preparado para conferir registros de desenvolvimento; o acompanhamento
prospectivo recente depende da definição posterior desse escopo sem consumir a reserva.

## 4. Gerar e abrir o relatório

```powershell
py -3 -m motor diario-b3 --arquivo dados/B3/diario-simulador.csv
Start-Process resultados/diario/diario.html
```

O relatório HTML se adapta a computador e celular. Abra uma operação para ver a ficha
de preços, stop, alvo, origem e motivos. O JSON completo fica em `resultados/diario/diario.json`.
Ao rodar novamente, esses dois arquivos são substituídos pelo relatório do CSV atual.

O líquido é calculado com os preços executados e as taxas informadas. A diferença de
execução já está nos preços e **não é descontada uma segunda vez**. Desvio positivo
em ticks significa execução pior que a referência; negativo significa melhora.
O relatório não demonstra que a referência seria executável, não mede risco de
posições abertas, não mede drawdown intradiário e não aprova uma estratégia.

`dados/` e `resultados/` permanecem fora do Git. Nenhuma senha, chave ou conta é necessária.

## Verificação desta entrega

- 128 testes passaram; 4 testes da amostra real continuam pulados por interceptarem a reserva.
- 24 casos novos verificam recorte da reserva, lacunas, duplicatas, custo, comprado/vendido,
  WIN/WDO, dupla contagem, dados ausentes, JSON e proteção do HTML.
- Os casos novos usam dados artificiais. Não foram rodadas hipóteses de mercado,
  recalculados os resultados antigos ou alterados os critérios de aprovação.
- Geração e escape do HTML foram testados. A revisão visual no navegador ficou
  pendente: o navegador deste ambiente não iniciou por restrição a sockets.
- A interface PWA não está neste branch; a entrega atual é o motor e seu relatório local.

## Próximo insumo necessário

Os arquivos `dados/` e `resultados/` não vieram no repositório. Para conferir os números
reais da pesquisa anterior, são necessários os CSVs de WIN/WDO e os relatórios completos.
Essa reexecução exige registro prévio da revisão, mantendo a régua e a reserva.
