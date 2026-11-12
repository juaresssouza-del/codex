//+------------------------------------------------------------------+
//| RoboSimuladorWDO.mq5 — Expert Advisor do TradeLab                |
//| SÓ SIMULADOR: recusa conta real (confere o tipo de conta).       |
//| Executa no mini-dólar as regras testadas, sem alteração:         |
//|  - aceleração do canal, 15 min (rodada 9, hipótese 48)           |
//|  - candle de força, 5 min (rodada 6, hipótese 22)                |
//| Grava cada operação encerrada no formato do diario-b3.           |
//+------------------------------------------------------------------+
#property copyright   "TradeLab"
#property version     "1.00"
#property description "Robô de SIMULADOR para o WDO. Recusa conta real."
#property description "Regras das hipóteses testadas, congeladas no código."

#include <Trade\Trade.mqh>

enum ENUM_ESTRATEGIA
  {
   ACELERACAO_CANAL_M15 = 0,   // Aceleração do canal (15 min)
   CANDLE_FORCA_M5      = 1    // Candle de força (5 min)
  };

input ENUM_ESTRATEGIA Estrategia   = ACELERACAO_CANAL_M15; // Estratégia (uma por gráfico)
input string          SimboloSinal = "WDO$N";               // Série contínua usada para o sinal
input string          SimboloOrdem = "";                    // Contrato vigente para as ordens (ex.: WDOZ26)
input long            Magico       = 20261112;              // Identificador das ordens do robô
input bool            Notificar    = true;                  // Notificação no celular a cada entrada e saída

// Regras congeladas: são as do teste. Mudar qualquer valor é outra hipótese.
#define CANAL_N         40
#define CANAL_R2        0.5
#define CANAL_STOP      0.02
#define FORCA_N         20
#define FORCA_K         3.0
#define FORCA_CORPO     0.6
#define FORCA_STOP      0.005
#define ULTIMA_ENTRADA  (17 * 60 + 30)
#define ZERAGEM         (18 * 60)
#define CUSTO_LADO      2.24     // R$ por contrato e por lado (premissa do teste, WDO)
#define ARQUIVO_DIARIO  "TradeLab\\diario_robo.csv"

CTrade          trade;
string          ativoOrdem;
ENUM_TIMEFRAMES tempo;
datetime        ultimoCandle = 0;

// Posição aberta pelo robô
bool     aberta = false;
int      ladoAberto = 0;
long     idPosicao = 0;
datetime horaEntrada = 0;
double   previstoEntrada = 0, executadoEntrada = 0, stopEntrada = 0;
string   motivoEntrada = "";

//+------------------------------------------------------------------+
bool ContaPermitida()
  {
   if(MQLInfoInteger(MQL_TESTER))
      return(true);   // Testador de estratégia do MT5
   return(AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_DEMO);
  }

int MinutoDoDia(const datetime t)
  {
   MqlDateTime d;
   TimeToStruct(t, d);
   return(d.hour * 60 + d.min);
  }

bool MesmoDia(const datetime a, const datetime b)
  {
   MqlDateTime x, y;
   TimeToStruct(a, x);
   TimeToStruct(b, y);
   return(x.year == y.year && x.mon == y.mon && x.day == y.day);
  }

double Arredonda(const double p)
  {
   double tick = SymbolInfoDouble(ativoOrdem, SYMBOL_TRADE_TICK_SIZE);
   if(tick <= 0.0)
      return(p);
   return(MathRound(p / tick) * tick);
  }

string Data(const datetime t)
  {
   string s = TimeToString(t, TIME_DATE | TIME_SECONDS);   // AAAA.MM.DD HH:MM:SS
   StringReplace(s, ".", "-");
   return(s);
  }

string NomeEstrategia()
  {
   return(Estrategia == ACELERACAO_CANAL_M15 ? "aceleracao_canal_15m" : "candle_forca_5m");
  }

void Avisar(const string msg)
  {
   Print(msg);
   if(Notificar && !MQLInfoInteger(MQL_TESTER))
      SendNotification(StringSubstr(msg, 0, 255));
  }

//+------------------------------------------------------------------+
//| Sinal da aceleração do canal no candle r[0] (r[1..40] = os 40     |
//| anteriores; r[40] o mais antigo). Mesmo cálculo de                |
//| motor/estrategias.py: canal_envelope + sinais_canal_aceleracao.   |
//| Retorna 1 compra, -1 venda, 2 sair, 3 sair se comprado,           |
//| 4 sair se vendido, 0 nada.                                        |
//+------------------------------------------------------------------+
int SinalCanal(const MqlRates &r[])
  {
   double sx = 0, sy = 0;
   for(int j = 0; j < CANAL_N; j++)
     {
      sx += j;
      sy += r[CANAL_N - j].close;
     }
   double mx = sx / CANAL_N, my = sy / CANAL_N, sxy = 0, sxx = 0;
   for(int j = 0; j < CANAL_N; j++)
     {
      sxy += (j - mx) * (r[CANAL_N - j].close - my);
      sxx += (j - mx) * (j - mx);
     }
   double b = sxy / sxx, a = my - b * mx;
   double offU = -DBL_MAX, offL = DBL_MAX, sse = 0, sst = 0;
   for(int j = 0; j < CANAL_N; j++)
     {
      double linha = a + b * j;
      int k = CANAL_N - j;
      offU = MathMax(offU, r[k].high - linha);
      offL = MathMin(offL, r[k].low - linha);
      sse += (r[k].close - linha) * (r[k].close - linha);
      sst += (r[k].close - my) * (r[k].close - my);
     }
   double proj = a + b * CANAL_N;
   double sup = proj + offU, inf = proj + offL, med = (sup + inf) / 2.0, larg = sup - inf;
   double r2 = (sst > 0) ? 1.0 - sse / sst : 0.0;
   bool alta = b > 0 && r2 >= CANAL_R2, baixa = b < 0 && r2 >= CANAL_R2;
   double c = r[0].close, h = r[0].high, l = r[0].low;
   if(alta && c > sup)
      return(1);
   if(baixa && c < inf)
      return(-1);
   bool saiC = (h >= sup + larg) || (c < med);
   bool saiV = (l <= inf - larg) || (c > med);
   if(saiC && saiV)
      return(2);
   if(saiC)
      return(3);
   if(saiV)
      return(4);
   return(0);
  }

//+------------------------------------------------------------------+
//| Candle de força no candle r[0] (r[1..20] = os 20 anteriores).     |
//+------------------------------------------------------------------+
int SinalForca(const MqlRates &r[])
  {
   double soma = 0;
   for(int k = 1; k <= FORCA_N; k++)
      soma += r[k].high - r[k].low;
   double media = soma / FORCA_N;
   double amp = r[0].high - r[0].low, corpo = r[0].close - r[0].open;
   if(amp <= 0 || amp < FORCA_K * media || MathAbs(corpo) < FORCA_CORPO * amp)
      return(0);
   return(corpo > 0 ? 1 : -1);
  }

//+------------------------------------------------------------------+
//| Os candles exigidos estão seguidos? Pausa dentro do pregão sempre |
//| interrompe. A virada do dia só é aceita na aceleração (o canal     |
//| atravessa a noite no teste); no candle de força, não.             |
//+------------------------------------------------------------------+
bool Seguidos(const MqlRates &r[], const int quantos)
  {
   long passo = PeriodSeconds(tempo);
   for(int k = 0; k < quantos - 1; k++)
     {
      bool mesmo = MesmoDia(r[k].time, r[k + 1].time);
      if(!mesmo && Estrategia == CANDLE_FORCA_M5)
         return(false);
      if(mesmo && (long)(r[k].time - r[k + 1].time) != passo)
         return(false);
     }
   return(true);
  }

//+------------------------------------------------------------------+
void Registrar(const string motivoSaida, const double previstoSaida)
  {
   double precoSaida = 0, taxas = 0;
   if(HistorySelectByPosition(idPosicao))
     {
      for(int i = 0; i < HistoryDealsTotal(); i++)
        {
         ulong t = HistoryDealGetTicket(i);
         taxas += MathAbs(HistoryDealGetDouble(t, DEAL_COMMISSION)) + MathAbs(HistoryDealGetDouble(t, DEAL_FEE));
         if((ENUM_DEAL_ENTRY)HistoryDealGetInteger(t, DEAL_ENTRY) == DEAL_ENTRY_OUT)
            precoSaida = HistoryDealGetDouble(t, DEAL_PRICE);
        }
     }
   if(precoSaida <= 0)
      precoSaida = previstoSaida;
   string origem = "RoboSimuladorWDO v1.00, conta simulador";
   double taxasPrevistas = 2 * CUSTO_LADO;
   if(taxas <= 0)
     {
      taxas = taxasPrevistas;
      origem += "; simulador sem cobranca: taxas executadas = previstas";
     }
   int digitos = (int)SymbolInfoInteger(ativoOrdem, SYMBOL_DIGITS);
   string hipotese = (Estrategia == ACELERACAO_CANAL_M15) ?
                     "rodada 9 h48: canal_aceleracao WDO 15m n=40 R2=0,5 stop 2%" :
                     "rodada 6 h22: forca WDO 5m N=20 k=3 corpo 60% stop 0,5%";
   string linha = StringFormat("%s-%I64d;simulador;WDO;%s;1;%s;%s;%s;%s;%s;%s;%.2f;%.2f;%s;;%s;%s;%s;%s",
                               NomeEstrategia(), (long)horaEntrada,
                               ladoAberto > 0 ? "comprado" : "vendido",
                               Data(horaEntrada), Data(TimeCurrent()),
                               DoubleToString(previstoEntrada, digitos), DoubleToString(Arredonda(previstoSaida), digitos),
                               DoubleToString(executadoEntrada, digitos), DoubleToString(precoSaida, digitos),
                               taxasPrevistas, taxas, DoubleToString(stopEntrada, digitos),
                               hipotese, motivoEntrada, motivoSaida, origem);
   int h = FileOpen(ARQUIVO_DIARIO, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI);
   if(h == INVALID_HANDLE)
     {
      Print("RoboSimuladorWDO: não consegui abrir o diário (erro ", GetLastError(), "). Linha: ", linha);
      return;
     }
   if(FileSize(h) == 0)
      FileWriteString(h, "id;ambiente;contrato;lado;quantidade;entrada;saida;preco_entrada_previsto;"
                      "preco_saida_previsto;preco_entrada_executado;preco_saida_executado;taxas_previstas;"
                      "taxas_executadas;stop;alvo;hipotese;motivo_entrada;motivo_saida;origem\r\n");
   FileSeek(h, 0, SEEK_END);
   FileWriteString(h, linha + "\r\n");
   FileClose(h);
  }

//+------------------------------------------------------------------+
void Fechar(const string motivo, const double previsto)
  {
   if(!aberta)
      return;
   if(!trade.PositionClose(ativoOrdem))
     {
      Avisar(StringFormat("WDO robô: FALHA ao zerar (%s), retcode %d. Zere manualmente no simulador.",
                          motivo, trade.ResultRetcode()));
      return;
     }
   Registrar(motivo, previsto);
   Avisar(StringFormat("WDO robô (%s): ZEROU %s. Motivo: %s.", NomeEstrategia(),
                       ladoAberto > 0 ? "compra" : "venda", motivo));
   aberta = false;
   ladoAberto = 0;
  }

//+------------------------------------------------------------------+
void Abrir(const int lado, const double previsto, const string motivo)
  {
   double preco = lado > 0 ? SymbolInfoDouble(ativoOrdem, SYMBOL_ASK) : SymbolInfoDouble(ativoOrdem, SYMBOL_BID);
   double pct = (Estrategia == ACELERACAO_CANAL_M15) ? CANAL_STOP : FORCA_STOP;
   double sl = Arredonda(preco * (1.0 - lado * pct));
   bool ok = lado > 0 ? trade.Buy(1, ativoOrdem, 0.0, sl, 0.0, NomeEstrategia())
                      : trade.Sell(1, ativoOrdem, 0.0, sl, 0.0, NomeEstrategia());
   if(!ok || (trade.ResultRetcode() != TRADE_RETCODE_DONE && trade.ResultRetcode() != TRADE_RETCODE_PLACED))
     {
      Avisar(StringFormat("WDO robô: ordem RECUSADA (%s), retcode %d.", lado > 0 ? "compra" : "venda",
                          trade.ResultRetcode()));
      return;
     }
   if(!PositionSelect(ativoOrdem))
     {
      Avisar("WDO robô: ordem enviada, mas a posição não apareceu. Confira o simulador.");
      return;
     }
   aberta = true;
   ladoAberto = lado;
   idPosicao = PositionGetInteger(POSITION_IDENTIFIER);
   horaEntrada = TimeCurrent();
   previstoEntrada = Arredonda(previsto);
   executadoEntrada = PositionGetDouble(POSITION_PRICE_OPEN);
   stopEntrada = sl;
   motivoEntrada = motivo;
   Avisar(StringFormat("WDO robô (%s): %s 1 contrato a %s. Stop %s. %s",
                       NomeEstrategia(), lado > 0 ? "COMPROU" : "VENDEU",
                       DoubleToString(executadoEntrada, _Digits), DoubleToString(sl, _Digits), motivo));
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   if(!ContaPermitida())
     {
      Alert("RoboSimuladorWDO: esta NÃO é uma conta de simulador. O robô não roda em conta real.");
      return(INIT_FAILED);
     }
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_NETTING)
     {
      Alert("RoboSimuladorWDO: a conta precisa ser Netting (como a da B3).");
      return(INIT_FAILED);
     }
   ativoOrdem = (SimboloOrdem == "") ? _Symbol : SimboloOrdem;
   if(StringFind(ativoOrdem, "$") >= 0)
     {
      Alert("RoboSimuladorWDO: informe em SimboloOrdem o contrato vigente (ex.: WDOZ26); ", ativoOrdem,
            " é só a série histórica e não recebe ordens.");
      return(INIT_PARAMETERS_INCORRECT);
     }
   if(!SymbolSelect(ativoOrdem, true) || !SymbolSelect(SimboloSinal, true))
     {
      Alert("RoboSimuladorWDO: símbolo não encontrado (", ativoOrdem, " ou ", SimboloSinal, ").");
      return(INIT_PARAMETERS_INCORRECT);
     }
   tempo = (Estrategia == ACELERACAO_CANAL_M15) ? PERIOD_M15 : PERIOD_M5;
   trade.SetExpertMagicNumber((ulong)Magico);
   trade.SetTypeFillingBySymbol(ativoOrdem);
   ultimoCandle = iTime(SimboloSinal, tempo, 0);   // não age sobre o candle já em andamento
   if(PositionSelect(ativoOrdem) && PositionGetInteger(POSITION_MAGIC) == Magico)
     {
      aberta = true;
      ladoAberto = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 1 : -1;
      idPosicao = PositionGetInteger(POSITION_IDENTIFIER);
      horaEntrada = (datetime)PositionGetInteger(POSITION_TIME);
      executadoEntrada = PositionGetDouble(POSITION_PRICE_OPEN);
      previstoEntrada = executadoEntrada;
      stopEntrada = PositionGetDouble(POSITION_SL);
      motivoEntrada = "posição retomada após reiniciar o robô";
     }
   datetime venc = (datetime)SymbolInfoInteger(ativoOrdem, SYMBOL_EXPIRATION_TIME);
   if(venc > 0 && venc - TimeCurrent() < 3 * 86400)
      Alert("RoboSimuladorWDO: ", ativoOrdem, " vence em menos de 3 dias. Troque SimboloOrdem pelo próximo contrato.");
   EventSetTimer(15);
   Print("RoboSimuladorWDO pronto: ", NomeEstrategia(), ", sinal em ", SimboloSinal, ", ordens em ", ativoOrdem, ".");
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
  }

//+------------------------------------------------------------------+
void Processar()
  {
   if(!ContaPermitida())
     {
      Alert("RoboSimuladorWDO: conta não é de simulador. Robô desligado.");
      ExpertRemove();
      return;
     }
   // Stop executado pelo servidor
   if(aberta && !PositionSelect(ativoOrdem))
     {
      Registrar("stop", stopEntrada);
      Avisar(StringFormat("WDO robô (%s): saiu no STOP.", NomeEstrategia()));
      aberta = false;
      ladoAberto = 0;
     }
   // Zeragem às 18h00
   if(aberta && MinutoDoDia(TimeCurrent()) >= ZERAGEM)
      Fechar("zeragem 18h00", iOpen(SimboloSinal, tempo, 0));

   datetime t0 = iTime(SimboloSinal, tempo, 0);
   if(t0 == 0 || t0 == ultimoCandle)
      return;
   ultimoCandle = t0;

   int quantos = (Estrategia == ACELERACAO_CANAL_M15) ? CANAL_N + 1 : FORCA_N + 1;
   MqlRates r[];
   ArraySetAsSeries(r, true);
   if(CopyRates(SimboloSinal, tempo, 1, quantos, r) != quantos)
      return;
   if(!MesmoDia(r[0].time, t0))
      return;                                   // sinal do último candle do dia não vale no dia seguinte
   if(!Seguidos(r, quantos))
      return;                                   // indicador ainda "frio" depois de pausa
   int s = (Estrategia == ACELERACAO_CANAL_M15) ? SinalCanal(r) : SinalForca(r);
   double abertura = iOpen(SimboloSinal, tempo, 0);
   bool podeEntrar = MinutoDoDia(t0) < MathMin(ULTIMA_ENTRADA, ZERAGEM) &&
                     (long)(t0 - r[0].time) == PeriodSeconds(tempo);
   string quando = TimeToString(r[0].time, TIME_MINUTES);
   int atual = aberta ? ladoAberto : 0;

   if(s == 1 && atual != 1)
     {
      if(atual == -1)
         Fechar("sinal contrário (" + quando + ")", abertura);
      if(podeEntrar)
         Abrir(1, abertura, (Estrategia == ACELERACAO_CANAL_M15 ? "aceleração de alta " : "candle de força de alta ") + quando);
     }
   else
      if(s == -1 && atual != -1)
        {
         if(atual == 1)
            Fechar("sinal contrário (" + quando + ")", abertura);
         if(podeEntrar)
            Abrir(-1, abertura, (Estrategia == ACELERACAO_CANAL_M15 ? "aceleração de baixa " : "candle de força de baixa ") + quando);
        }
      else
         if((s == 2 && atual != 0) || (s == 3 && atual == 1) || (s == 4 && atual == -1))
            Fechar("regra de saída do canal (" + quando + ")", abertura);
  }

void OnTick()  { Processar(); }
void OnTimer() { Processar(); }
//+------------------------------------------------------------------+
