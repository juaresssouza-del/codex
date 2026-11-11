# Exportar o histórico das 20 ações (script ExportarAcoes)

O script só **lê** o histórico do servidor da XP e grava arquivos CSV. Não envia ordens.

1. Confira **Ferramentas → Opções → Gráficos → Máximo de barras no gráfico = Unlimited**
   (se mudar, feche e abra o MT5).
2. **Arquivo → Abrir pasta de dados** → `MQL5\Scripts` → copie `ExportarAcoes.mq5`.
3. **F4** (MetaEditor) → abra `Scripts\ExportarAcoes.mq5` → **F7** (deve dar "0 errors").
4. No MT5, abra qualquer gráfico. No Navegador (Ctrl+N) → **Scripts** → arraste
   **ExportarAcoes** para o gráfico → confira as opções (tempo **M15**, início 2015) → **OK**.
5. Espere. Ele baixa ativo por ativo; pode levar alguns minutos. Acompanhe na aba
   **Experts** (embaixo): cada ativo mostra quantos candles e de que data a que data.
   Ativo que "NÃO existe neste servidor" mudou de código: mande o print.
6. Os arquivos ficam em **Arquivo → Abrir pasta de dados → `MQL5\Files\TradeLab`**.
   Selecione todos → botão direito → **Compactar** (.zip) → envie o zip na conversa.

Mande também um print da aba **Experts** com o resumo final.
