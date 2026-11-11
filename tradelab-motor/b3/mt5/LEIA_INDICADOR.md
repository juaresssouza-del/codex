# Indicador de alerta ForcaWDO (MT5)

Avisa quando aparece um candle de força no mini-dólar, pela regra de
`b3/CARTAO_FORCA_WDO.md`. **Só avisa: não envia, altera nem cancela ordens.** Hipótese não
aprovada: use no **simulador** da XP.

## Instalar

1. No MT5: **Arquivo → Abrir pasta de dados** → entre em `MQL5\Indicators`.
2. Copie para lá o arquivo `ForcaWDO.mq5`.
3. No MT5, aperte **F4** (abre o MetaEditor). No Navegador do MetaEditor, abra
   `Indicators\ForcaWDO.mq5` e aperte **F7** (Compilar). Embaixo deve aparecer
   **"0 errors"**. Se aparecer erro, mande um print da aba **Erros**.
4. Volte ao MT5. Abra o gráfico do **WDO$N** em **M5**. No Navegador (Ctrl+N) →
   **Indicadores** → arraste **ForcaWDO** para o gráfico → OK.

## Notificação no celular

1. Instale o app **MetaTrader 5** no celular → **Configurações** (ou Mensagens) e copie o
   **MetaQuotes ID**.
2. No MT5 do computador: **Ferramentas → Opções → Notificações** → marque "Ativar
   notificações push" → cole o MetaQuotes ID → **Testar**. A mensagem de teste deve chegar.
3. O computador precisa ficar **ligado com o MT5 aberto** durante o pregão: o alerta sai
   dele, não da XP.

## O que o alerta diz

- **Candle de força dentro do horário:** "COMPRAR" ou "VENDER" 1 contrato no próximo
  candle, com o stop sugerido (0,5% do fechamento do candle de sinal).
- **Candle de força depois das 17h30:** não abrir; se você estiver na mão contrária, zerar.
- **17h50:** aviso para zerar até 18h00.

A ordem vai no **contrato vigente** (ex.: `WDOZ26`), não no `WDO$N`, que é só a série
contínua. Confira o código vigente na Observação do Mercado.

## Conferir que o indicador faz o mesmo que o motor

No gráfico **WDO$N M5**, as setas de **junho/2026** têm de bater com os sinais do motor
(setas só aparecem quando a entrada é permitida):

| Candle (abertura, Brasília) | Sentido | Entrada permitida? |
|---|---|---|
| 01/06/2026 14:40 | BAIXA (venda) | sim |
| 03/06/2026 18:15 | BAIXA (venda) | não (depois das 17h30) |
| 08/06/2026 18:05 | ALTA (compra) | não (depois das 17h30) |
| 11/06/2026 14:25 | BAIXA (venda) | sim |
| 11/06/2026 14:30 | BAIXA (venda) | sim |
| 17/06/2026 15:00 | ALTA (compra) | sim |
| 19/06/2026 16:00 | ALTA (compra) | sim |
| 19/06/2026 17:10 | BAIXA (venda) | sim |
| 29/06/2026 16:45 | ALTA (compra) | sim |

Se houver seta a mais ou a menos, mande um print do dia: a diferença precisa ser
explicada antes de usar o alerta.
