# Diário automático do simulador — entrega 0.5.0

O EA `RoboSimuladorWDO.mq5`, acrescentado pelo Claude no branch, já escrevia o modelo
de 19 colunas. Esta entrega corrige sua coleta e acrescenta a comparação semanal ao
**mesmo** `diario-b3`. Não acrescenta estratégia nem recalcula o histórico de cinco anos.
O coletor desta versão acompanha as operações do **próprio EA no WDO**. Ele não coleta
automaticamente operações manuais de WIN ou de outros robôs; essas exigem integração própria.

## O que a versão 1.02 registra

- Preços de referência recebidos pela rotina antes do envio da ordem; preços de entrada
  e saída efetivamente encontrados no histórico, ponderados pelos respectivos volumes.
- As duas pontas precisam somar exatamente **um contrato**, sem reversão ou close-by,
  na direção esperada, e fechar no mesmo dia de Brasília. O lucro do MT5 precisa conferir
  com a diferença de preços × R$ 10/ponto WDO. Inconsistência suspende o registro.
- Comissão + taxa + swap vinculados à posição, com os sinais originais, sem `abs()`
  e sem substituir taxa zero pela premissa. Campo que falhou na leitura não vira zero.
- O custo previsto continua **R$ 2,24 por lado**, premissa já usada no projeto. O custo
  da rota EA na XP continua **não confirmado**. Zero observado na demo não o confirma.
- Datas exportadas com deslocamento UTC explícito; `diario-b3` converte para Brasília.
  O operador informa o fuso do servidor, que é conferido com `TimeTradeServer()` e `TimeGMT()`.
- ID formado por estratégia, símbolo e identificador da posição. Repetir o processamento
  não duplica a linha; mesmo ID com campos diferentes exige conciliação.

Se houver fechamento externo sem referência prévia, rebate que não cabe no campo de
taxa não negativa, volume divergente, leitura incompleta ou lucro incoerente, o EA
registra o motivo na aba Experts e **não emite uma operação completa inventada**.
Como no desenho anterior, enquanto o encerramento não for conciliado, novas entradas
ficam suspensas. Isso exige intervenção no simulador, não preenchimento estimado do CSV.

Os débitos sem vínculo à posição e lançamentos posteriores precisam ser conferidos no
extrato. O arquivo é uma observação do momento da coleta, não uma conciliação final da conta.
O diário não prova a equivalência completa das estratégias do EA com o backtest.

## Preparação no Windows e MT5

1. Instale as dependências do motor em uma cópia deste branch:

   ```powershell
   python -m pip install -e '.[dev]'
   ```

2. Guarde uma cópia do CSV antigo. **Não use linhas da versão 1.01 como taxa executada
   comprovada**: a versão anterior substituía zero pelo custo previsto. Reconcile essas
   linhas no extrato antes de juntá-las às novas. Comece um novo `diario_robo.csv` para a 1.02.
3. Copie `b3/mt5/RoboSimuladorWDO.mq5` para `MQL5\Experts` e compile no MetaEditor (F7).
   **A compilação não foi executada neste ambiente.** Só avance se aparecerem zero erros.
4. Use **uma única instância**, conta **DEMO**, moeda **BRL**, contrato vigente do WDO,
   seguindo [LEIA_ROBO.md](mt5/LEIA_ROBO.md). A conta fica vinculada em memória; login/senha
   não são exportados. Conta real e testador histórico são recusados.
5. Confira o relógio do servidor contra UTC e preencha `UTCServidorMinutos`.
   Exemplos de conversão, **não valores atribuídos ao servidor da XP**: UTC−3 → −180;
   UTC+2 → 120. O padrão −9999 bloqueia a inicialização. Não adivinhe o fuso.
   Mantenha o relógio do Windows sincronizado. A regra de 17h30/18h usa Brasília.
6. Compile/configure no simulador e confira a primeira operação no histórico do MT5.
   Não há instalação, conexão ou operação feita por esta entrega no seu computador.

O CSV fica em **Arquivo → Abrir pasta de dados → `MQL5\Files\TradeLab\diario_robo.csv`**.
O botão Algotrading do EA refere-se à execução no simulador já prevista no projeto;
os scripts de relatório abaixo apenas leem arquivos e não enviam ordens.

## Comparar previsto e executado

Na pasta `tradelab-motor`:

```powershell
python -m motor diario-b3 --arquivo 'C:\caminho\MQL5\Files\TradeLab\diario_robo.csv' --saida 'C:\TradeLab\relatorio'
```

Os caminhos acima são exemplos. O comando gera `diario.json` e `diario.html`, incluindo
resumo total e por **semana ISO da saída em Brasília**. O HTML abre no navegador e se
adapta à tela; não foi publicado como PWA nesta entrega.

O cálculo é o mesmo para a semana e o total:

```text
bruto executado = direção × (saída executada − entrada executada) × valor do ponto × contratos
líquido observado = bruto executado − taxas observadas
diferença = líquido observado − líquido previsto
```

O impacto do slippage já está nos preços executados: **não é descontado novamente**.
Taxa ausente bloqueia; taxa zero explicitamente observada permanece zero e aparece com
aviso sobre custo real não confirmado. Resultado positivo na demo sem cobrança não
aprova estratégia nem demonstra retorno depois dos custos reais da XP.

O bloqueio de datas continua seguindo `criterios.toml`, sem alteração nesta entrega.
O branch de base já tinha `reserva_fim = "2026-11-10"`: o diário aceita a coleta nova
posterior a essa janela e continua recusando operações dentro da reserva. Esta entrega
não abre nem lê os preços reservados. Não há opção `--usar-reserva` no diário.

Esta comparação cobre operações que estão no CSV. Não reconstrói sinais não executados,
não recalcula os candles, não identifica quem ganhou do outro lado e não treina o seletor.

## Atualização automática semanal

Primeiro execute uma vez o script, usando os caminhos reais:

```powershell
.\b3\mt5\Atualizar-Diario.ps1 -Arquivo 'C:\caminho\diario_robo.csv' -Motor 'C:\codex\tradelab-motor' -Saida 'C:\TradeLab\relatorio'
```

Depois, no mesmo Windows:

```powershell
.\b3\mt5\Instalar-TarefaDiario.ps1 -Arquivo 'C:\caminho\diario_robo.csv' -Motor 'C:\codex\tradelab-motor' -Saida 'C:\TradeLab\relatorio'
```

O instalador registra uma tarefa local para domingo às 19h, no **fuso do Windows**,
configurável por `-Dia`/`-Hora`. Precisa do usuário conectado. Não grava senha, não pede
elevação, não substitui tarefa existente e não envia mensagens. A tarefa **não foi
instalada nem executada aqui**; os scripts PowerShell também aguardam validação no Windows.

Se o motor rejeitar o CSV, o script marca `atualizacao.json` como bloqueado e move
relatórios anteriores para `.anterior`, evitando apresentá-los como atualização bem-sucedida.
O horário de geração continua visível no HTML.

## Verificação e limitações

Testes com operações artificiais conferem cálculo total/semanal, virada de ano ISO,
conversão UTC→Brasília, taxa zero, bloqueio de taxa ausente/negativa e uso do mesmo
analisador pela CLI. Nenhum relatório de resultado real do simulador foi produzido.
Os testes não substituem compilação MQL5 e validação no MT5/Windows, ainda pendentes.
Suíte completa: **200 passaram, 4 pulados**, em pandas 2.2.3 e 3.1.1. Os quatro pulados
são da amostra real que intercepta a reserva, que não foi aberta.

Fontes técnicas oficiais, consultadas em 15/11/2026:
[propriedades da conta](https://www.mql5.com/en/docs/constants/environment_state/accountinformation),
[propriedades dos negócios](https://www.mql5.com/en/docs/constants/tradingconstants/dealproperties),
[leitura de propriedades com indicação de sucesso](https://www.mql5.com/en/docs/trading/historydealgetdouble).
Agendador Windows: [principal interativo](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskprincipal),
[gatilho semanal](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasktrigger)
e [configurações da tarefa](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset).
