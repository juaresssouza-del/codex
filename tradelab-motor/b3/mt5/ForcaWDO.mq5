//+------------------------------------------------------------------+
//| ForcaWDO.mq5                                                     |
//| Alerta de candle de força: cartão b3/CARTAO_FORCA_WDO.md.        |
//| Hipótese 22 da rodada 6, NÃO aprovada: usar só no simulador.     |
//| O indicador apenas avisa. Não envia, altera nem cancela ordens.  |
//+------------------------------------------------------------------+
#property copyright   "TradeLab"
#property version     "1.00"
#property description "Alerta de candle de força no WDO (M5). Só avisa; não envia ordens."
#property description "Hipótese não aprovada: uso no simulador da XP."
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_plots   2
#property indicator_label1  "Força de alta (compra no próximo candle)"
#property indicator_type1   DRAW_ARROW
#property indicator_color1  clrLime
#property indicator_width1  2
#property indicator_label2  "Força de baixa (venda no próximo candle)"
#property indicator_type2   DRAW_ARROW
#property indicator_color2  clrRed
#property indicator_width2  2

input int    Periodo         = 20;    // Candles anteriores (seguidos, no mesmo pregão) na média
input double K               = 3.0;   // Candle de força: amplitude >= K x média
input double CorpoMin        = 0.60;  // Corpo >= esta fração da amplitude
input double StopPct         = 0.50;  // Stop sugerido, em % do preço
input int    UltimaEntradaH  = 17;    // Sem entrada a partir de (hora)
input int    UltimaEntradaM  = 30;    // Sem entrada a partir de (minuto)
input int    ZeragemH        = 18;    // Zerar até (hora)
input int    ZeragemM        = 0;     // Zerar até (minuto)
input int    AvisoZeragemMin = 10;    // Avisar N minutos antes da zeragem (0 = não avisar)
input bool   Popup           = true;  // Janela de alerta no MT5
input bool   Som             = true;  // Som
input bool   Celular         = true;  // Notificação no app MetaTrader do celular

double   BufCompra[];
double   BufVenda[];
datetime ultimoAlerta     = 0;
int      ultimoDiaZeragem = -1;

//+------------------------------------------------------------------+
int OnInit()
  {
   if(Periodo < 2 || K <= 0 || CorpoMin <= 0 || CorpoMin > 1 || StopPct <= 0)
      return(INIT_PARAMETERS_INCORRECT);
   SetIndexBuffer(0, BufCompra, INDICATOR_DATA);
   SetIndexBuffer(1, BufVenda, INDICATOR_DATA);
   PlotIndexSetInteger(0, PLOT_ARROW, 233);
   PlotIndexSetInteger(1, PLOT_ARROW, 234);
   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   PlotIndexSetDouble(1, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   IndicatorSetString(INDICATOR_SHORTNAME, StringFormat("ForcaWDO(%d; %.1f)", Periodo, K));
   if(_Period != PERIOD_M5)
      Print("ForcaWDO: o cartão foi testado em M5; este gráfico está em ", EnumToString(_Period), ".");
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
int MinutoDoDia(const datetime t)
  {
   MqlDateTime d;
   TimeToStruct(t, d);
   return(d.hour * 60 + d.min);
  }

//+------------------------------------------------------------------+
//| +1 força de alta, -1 força de baixa, 0 nada, no candle fechado i.  |
//| Os Periodo candles anteriores precisam ser seguidos: uma pausa ou |
//| a virada do dia zeram a média (igual ao motor de backtest).       |
//+------------------------------------------------------------------+
int Sinal(const int i, const datetime &time[], const double &open[], const double &high[],
          const double &low[], const double &close[])
  {
   if(i - Periodo < 0)
      return(0);
   long passo = PeriodSeconds();
   if((long)(time[i] - time[i - Periodo]) != (long)Periodo * passo)
      return(0);
   double soma = 0.0;
   for(int j = i - Periodo; j < i; j++)
      soma += high[j] - low[j];
   double media = soma / Periodo;
   double amp   = high[i] - low[i];
   double corpo = close[i] - open[i];
   if(amp <= 0.0 || amp < K * media || MathAbs(corpo) < CorpoMin * amp)
      return(0);
   return(corpo > 0.0 ? 1 : -1);
  }

//+------------------------------------------------------------------+
bool EntradaPermitida(const datetime aberturaSinal)
  {
   // A entrada seria na abertura do candle seguinte.
   int minutoEntrada = MinutoDoDia(aberturaSinal) + PeriodSeconds() / 60;
   return(minutoEntrada < MathMin(UltimaEntradaH * 60 + UltimaEntradaM, ZeragemH * 60 + ZeragemM));
  }

//+------------------------------------------------------------------+
double ArredondaTick(const double p)
  {
   double tick = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick <= 0.0)
      return(p);
   return(MathRound(p / tick) * tick);
  }

//+------------------------------------------------------------------+
void Avisar(const string msg)
  {
   if(Popup)
      Alert(msg);
   else
      Print(msg);
   if(Som && !Popup)
      PlaySound("alert.wav");
   if(Celular && !SendNotification(StringSubstr(msg, 0, 255)))
      Print("ForcaWDO: notificação não enviada. Configure o MetaQuotes ID em Ferramentas > Opções > ",
            "Notificações. Erro ", GetLastError());
  }

//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
  {
   if(rates_total < Periodo + 2)
      return(0);

   int inicio = (prev_calculated > 1) ? prev_calculated - 1 : 0;
   for(int i = inicio; i < rates_total; i++)
     {
      BufCompra[i] = EMPTY_VALUE;
      BufVenda[i]  = EMPTY_VALUE;
      if(i == rates_total - 1)
         continue;                                  // candle em formação: sem sinal
      int s = Sinal(i, time, open, high, low, close);
      if(s == 0 || !EntradaPermitida(time[i]))
         continue;
      if(s > 0)
         BufCompra[i] = low[i] - 5 * _Point;
      else
         BufVenda[i]  = high[i] + 5 * _Point;
     }

   // Alerta só para o último candle fechado, uma vez. Ao abrir o gráfico, não alerta o histórico.
   int u = rates_total - 2;
   if(prev_calculated == 0)
     {
      ultimoAlerta = time[u];
     }
   else
      if(time[u] > ultimoAlerta)
        {
         ultimoAlerta = time[u];
         int s = Sinal(u, time, open, high, low, close);
         if(s != 0)
           {
            string sentido = (s > 0) ? "ALTA" : "BAIXA";
            string hora    = TimeToString(time[u], TIME_MINUTES);
            if(EntradaPermitida(time[u]))
              {
               double stop = ArredondaTick(close[u] * (1.0 - s * StopPct / 100.0));
               Avisar(StringFormat("%s: candle de força de %s (%s). Cartão: %s 1 contrato no próximo candle. "
                                   "Stop ~%s. Zerar até %02d:%02d. SIMULADOR.",
                                   _Symbol, sentido, hora, (s > 0) ? "COMPRAR" : "VENDER",
                                   DoubleToString(stop, _Digits), ZeragemH, ZeragemM));
              }
            else
              {
               Avisar(StringFormat("%s: candle de força de %s (%s) depois do horário de entrada. "
                                   "Não abrir. Se estiver %s, zerar.",
                                   _Symbol, sentido, hora, (s > 0) ? "VENDIDO" : "COMPRADO"));
              }
           }
        }

   // Aviso de zeragem, uma vez por dia.
   if(AvisoZeragemMin > 0)
     {
      datetime agora = TimeCurrent();
      MqlDateTime d;
      TimeToStruct(agora, d);
      int minuto  = d.hour * 60 + d.min;
      int zeragem = ZeragemH * 60 + ZeragemM;
      if(minuto >= zeragem - AvisoZeragemMin && minuto < zeragem && d.day_of_year != ultimoDiaZeragem)
        {
         ultimoDiaZeragem = d.day_of_year;
         Avisar(StringFormat("%s: faltam %d min para %02d:%02d. Se estiver posicionado, ZERE.",
                             _Symbol, zeragem - minuto, ZeragemH, ZeragemM));
        }
     }
   return(rates_total);
  }
//+------------------------------------------------------------------+
