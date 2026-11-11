//+------------------------------------------------------------------+
//| ExportarAcoes.mq5 — script do MT5                                 |
//| Exporta candles de várias ações para CSV, no mesmo formato de     |
//| "Exportar barras" (tabulação), que o tradelab-motor lê.           |
//| Só lê histórico. Não envia, altera nem cancela ordens.            |
//+------------------------------------------------------------------+
#property copyright   "TradeLab"
#property version     "1.00"
#property description "Exporta o histórico de candles de uma lista de ações para MQL5\\Files\\TradeLab."
#property description "Só lê histórico; não envia ordens."
#property script_show_inputs

input string          Ativos = "VALE3,PETR4,PETR3,ITUB4,BBDC4,B3SA3,BBAS3,ABEV3,MGLU3,ITSA4,"
                               "WEGE3,SUZB3,RENT3,GGBR4,JBSS3,LREN3,PRIO3,ELET3,CSNA3,HAPV3,"
                               "CMIG4,EQTL3,RADL3,VBBR3,UGPA3";  // 20 + 5 reservas
input ENUM_TIMEFRAMES Tempo  = PERIOD_M15;              // Tempo gráfico exportado
input datetime        Inicio = D'2015.01.01 00:00';      // Data mais antiga pedida

//+------------------------------------------------------------------+
int Copiar(const string ativo, MqlRates &r[])
  {
   // O servidor entrega o histórico aos poucos: repete até a quantidade parar de crescer.
   int anterior = -1, n = 0;
   for(int tentativa = 0; tentativa < 30; tentativa++)
     {
      n = CopyRates(ativo, Tempo, Inicio, TimeCurrent(), r);
      if(n > 0 && n == anterior && SeriesInfoInteger(ativo, Tempo, SERIES_SYNCHRONIZED))
         break;
      anterior = n;
      Sleep(1000);
     }
   return(n);
  }

//+------------------------------------------------------------------+
void OnStart()
  {
   long maxbars = TerminalInfoInteger(TERMINAL_MAXBARS);
   if(maxbars < 1000000)
      Print("ExportarAcoes: 'Máximo de barras no gráfico' está em ", maxbars,
            ". Para o histórico completo, use Ferramentas > Opções > Gráficos > Unlimited e reabra o MT5.");
   string lista[];
   int total = StringSplit(Ativos, ',', lista);
   string sufixo = StringSubstr(EnumToString(Tempo), 7);  // PERIOD_M15 -> M15
   int ok = 0;
   for(int k = 0; k < total; k++)
     {
      string ativo = lista[k];
      StringTrimLeft(ativo);
      StringTrimRight(ativo);
      if(ativo == "")
         continue;
      if(!SymbolSelect(ativo, true))
        {
         Print("ExportarAcoes: ", ativo, " NÃO existe neste servidor (código mudou?). Pulado.");
         continue;
        }
      MqlRates r[];
      int n = Copiar(ativo, r);
      if(n <= 0)
        {
         Print("ExportarAcoes: ", ativo, " sem histórico (erro ", GetLastError(), "). Pulado.");
         continue;
        }
      string nome = "TradeLab\\" + ativo + "_" + sufixo + ".csv";
      int h = FileOpen(nome, FILE_WRITE | FILE_TXT | FILE_ANSI);
      if(h == INVALID_HANDLE)
        {
         Print("ExportarAcoes: não consegui criar ", nome, " (erro ", GetLastError(), ").");
         continue;
        }
      int digitos = (int)SymbolInfoInteger(ativo, SYMBOL_DIGITS);
      FileWriteString(h, "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\r\n");
      for(int i = 0; i < n; i++)
        {
         FileWriteString(h, StringFormat("%s\t%s\t%s\t%s\t%s\t%s\t%I64d\t%I64d\t%d\r\n",
                                         TimeToString(r[i].time, TIME_DATE),
                                         TimeToString(r[i].time, TIME_SECONDS),
                                         DoubleToString(r[i].open, digitos),
                                         DoubleToString(r[i].high, digitos),
                                         DoubleToString(r[i].low, digitos),
                                         DoubleToString(r[i].close, digitos),
                                         r[i].tick_volume, r[i].real_volume, r[i].spread));
        }
      FileClose(h);
      ok++;
      Print("ExportarAcoes: ", ativo, " -> ", n, " candles, de ", TimeToString(r[0].time, TIME_DATE),
            " a ", TimeToString(r[n - 1].time, TIME_DATE), ".");
     }
   Print("ExportarAcoes: ", ok, " de ", total, " ativos exportados para a pasta MQL5\\Files\\TradeLab.");
  }
//+------------------------------------------------------------------+
