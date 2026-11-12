# Robô do simulador — RoboSimuladorWDO (MT5)

Executa sozinho, **só na conta simulador**, as regras testadas no mini-dólar e grava cada
operação encerrada no diário. **Recusa conta real**: confere o tipo de conta ao iniciar e a
cada tick; se não for simulador, não abre e se desliga.

| Estratégia (escolha uma por gráfico) | Tempo | Regra (congelada no código) |
|---|---|---|
| Aceleração do canal | 15 min | Rodada 9, hipótese 48: canal dos 40 candles anteriores, R² ≥ 0,5; entra quando fecha além da linha de retorno, sai no alvo (largura projetada) ou se voltar para o lado errado da linha média; stop de emergência 2% |
| Candle de força | 5 min | Rodada 6, hipótese 22: amplitude ≥ 3 × a média dos 20 anteriores e corpo ≥ 60%; vira a mão no sinal contrário; stop 0,5% |

Comum: 1 contrato, comprado e vendido, sem entrada depois das 17h30, zeragem às 18h00.
Nenhuma das duas foi aprovada no histórico: o simulador é o teste com dados novos.

## Instalar

1. Copie `RoboSimuladorWDO.mq5` para **Arquivo → Abrir pasta de dados → `MQL5\Experts`**.
2. **F4** (MetaEditor) → abra o arquivo → **F7**. Deve aparecer **"0 errors"**. Se aparecer
   erro, mande o print da aba Erros (o código não pôde ser compilado no servidor do Claude).
3. No MT5 conectado ao **simulador**, ligue o botão **Algotrading** (barra de cima, fica verde).
4. Abra um gráfico do **WDO$N** (M15 para a aceleração, M5 para o candle de força).
5. Arraste **RoboSimuladorWDO** do Navegador (Ctrl+N → Consultor Expert) para o gráfico. Na
   janela de opções:
   - **Comum:** marque "Permitir Algo Trading".
   - **Parâmetros de entrada:** escolha a **Estratégia** e preencha **SimboloOrdem** com o
     contrato vigente do mini-dólar (veja na Observação do Mercado, ex.: `WDOZ26`).
6. OK. No canto do gráfico aparece o chapéu do robô; na aba **Experts** aparece
   "RoboSimuladorWDO pronto".

Para rodar as duas estratégias ao mesmo tempo, use **dois gráficos** e um **Magico diferente**
em cada um. Na conta Netting da B3 só existe uma posição por contrato: se as duas entrarem
juntas, as ordens se somam. Por isso a recomendação é **começar só pela aceleração**.

## Rotina

- O computador fica **ligado com o MT5 aberto** durante o pregão (9h às 18h). Se desligar, o
  robô para; ao religar, ele retoma a posição aberta que for dele.
- Todo **primeiro dia útil do mês** o WDO vence: troque **SimboloOrdem** para o contrato novo
  (o robô avisa 3 dias antes).
- Notificações chegam no celular a cada entrada e saída (configure o MetaQuotes ID em
  Ferramentas → Opções → Notificações).

## Diário e revisão

Cada operação encerrada vai para `MQL5\Files\TradeLab\diario_robo.csv`, no formato do
`b3/diario-modelo.csv`. Para revisar (à noite ou no fim de semana), envie esse arquivo na
conversa, ou rode:

```sh
python -m motor diario-b3 --arquivo diario_robo.csv
```

Toda semana, com um CSV M5 novo do WDO$N, o motor recalcula as mesmas regras nos mesmos dias
e compara com o que o robô fez: sinais que deveriam ter ocorrido, atraso e preço de execução.
