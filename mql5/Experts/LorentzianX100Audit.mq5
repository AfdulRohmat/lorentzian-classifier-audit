#property strict
#property version "1.20"
#property description "Tester-only causal Lorentzian M30 runner. Not approved for forward/live use."
#include "..\Include\LorentzianCore.mqh"
#include "..\Include\LorentzianExecution.mqh"

input datetime HistoryAnchor=D'2025.06.15 00:00';
input datetime EvaluationStart=D'2026.01.01 00:00';
input datetime EvaluationEnd=D'2026.09.01 00:00';
input double RiskPercent=1.0;
// Explicitly authorized sensitivity only: may exceed nominal risk. Default off.
input bool AllowMinimumLotFallback=false;
// Frozen at entry. The same risk distance drives trail activation and width.
input int StopATRMultiplier=1;
// Zero means no time exit. Legacy default retained for regression controls.
input int MaxHoldingHours=24;
// Legacy modeling reserves, NOT a verified statement of broker fees.
input double ExitSlippageReserve=0.02;
input double RoundTripCommissionPrice=0.25;
input ulong Magic=51001030;
input string RunTag="native_smoke";

LorentzianCore classifier;
datetime last_bar=0,entry_time=0;
double entry_fill=0,risk_price=0,best_r=-DBL_MAX;
double last_bid=0,last_ask=0;
datetime last_quote_time=0;
int journal=INVALID_HANDLE,signals=INVALID_HANDLE;
bool ready=false,failed=false;
datetime first_tick=0,last_tick=0;
long tick_count=0;
string pending_close="";
datetime next_close_attempt=0;

void Log(string event,string detail,double value=0) {
   if(journal!=INVALID_HANDLE) {
      FileWrite(journal,(long)TimeCurrent(),event,detail,value);
      FileFlush(journal);
   }
   if(event=="FAIL") Print("LC_FAIL ",detail);
}
void Fail(string detail) { failed=true; Log("FAIL",detail); }
bool OwnPosition() {
   if(!PositionSelect(_Symbol)) return false;
   if((ulong)PositionGetInteger(POSITION_MAGIC)!=Magic) { Fail("foreign_position"); return false; }
   return true;
}
ENUM_ORDER_TYPE_FILLING Filling() {
   long flags=SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);
   if((flags&SYMBOL_FILLING_FOK)!=0) return ORDER_FILLING_FOK;
   if((flags&SYMBOL_FILLING_IOC)!=0) return ORDER_FILLING_IOC;
   return ORDER_FILLING_RETURN;
}
bool Send(MqlTradeRequest &request,MqlTradeResult &result) {
   // Defense in depth: every order path has the same non-bypassable guard.
   if(!MQLInfoInteger(MQL_TESTER)) { Fail("not_strategy_tester"); return false; }
   request.magic=Magic;
   request.deviation=10;
   bool ok=OrderSend(request,result);
   Log("ORDER_RESULT",IntegerToString((int)result.retcode),result.price);
   if(!ok || (result.retcode!=TRADE_RETCODE_DONE && result.retcode!=TRADE_RETCODE_DONE_PARTIAL)) return false;
   return true;
}
bool Close(string reason) {
   if(!OwnPosition()) { pending_close=""; return !failed; }
   if(TimeCurrent()<next_close_attempt) return false;
   MqlTick tick; if(!SymbolInfoTick(_Symbol,tick)) return false;
   MqlTradeRequest request={}; MqlTradeResult result={};
   request.action=TRADE_ACTION_DEAL; request.symbol=_Symbol;
   request.position=(ulong)PositionGetInteger(POSITION_TICKET);
   request.volume=PositionGetDouble(POSITION_VOLUME);
   bool is_long=PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY;
   request.type=is_long ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price=is_long ? tick.bid : tick.ask;
   request.type_filling=Filling(); request.comment=reason;
   if(!Send(request,result)) {
      if(result.retcode==TRADE_RETCODE_MARKET_CLOSED) {
         pending_close=reason; next_close_attempt=TimeCurrent()+60;
         Log("CLOSE_DEFERRED","market_closed"); return false;
      }
      Fail("close_rejected_"+reason); return false;
   }
   if(PositionSelect(_Symbol)) { Fail("partial_close_unresolved"); return false; }
   pending_close=""; next_close_attempt=0;
   Log("EXIT",reason,result.price); return true;
}
double QuantStop(double price,int side) {
   double tick=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   return LCStopGrid(price,side,tick,_Digits);
}
bool ValidStop(double stop,int side,const MqlTick &tick,bool modifying=false) {
   long level=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   if(modifying) level=MathMax(level,SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL));
   return stop>0 && (side==1 ? tick.bid-stop : stop-tick.ask)>=level*_Point;
}
void Enter(int side,double atr) {
   if(failed || OwnPosition() || !LCValid(atr) || atr<=0) return;
   if(failed) return; // OwnPosition may have detected a foreign position.
   MqlTick tick; if(!SymbolInfoTick(_Symbol,tick)) { Fail("no_quote"); return; }
   double intended=side==1 ? tick.ask : tick.bid;
   double stop=QuantStop(intended-side*atr*StopATRMultiplier,side);
   if(!ValidStop(stop,side,tick)) { Log("SKIP","invalid_initial_stop",stop); return; }
   double friction=ExitSlippageReserve+RoundTripCommissionPrice;
   double per_lot=0;
   ENUM_ORDER_TYPE type=side==1 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!OrderCalcProfit(type,_Symbol,1.0,intended,stop-side*friction,per_lot) || per_lot>=0) {
      Fail("risk_conversion_failed"); return;
   }
   double budget=AccountInfoDouble(ACCOUNT_BALANCE)*RiskPercent/100;
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP),minimum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maximum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   if(step<=0 || minimum<=0 || maximum<minimum || budget<=0) { Fail("invalid_sizing_spec"); return; }
   double volume=LCFloorVolume(budget,-per_lot,minimum,maximum,step);
   bool used_minimum=false;
   if(volume<minimum-1e-12 && AllowMinimumLotFallback) {
      volume=minimum; used_minimum=true;
   }
   if(volume<minimum-1e-12) { Log("SKIP","below_minimum",volume); return; }
   double planned_loss=volume*(-per_lot);
   double allowed_budget=used_minimum ? planned_loss : budget;
   if(planned_loss>allowed_budget+1e-8) { Fail("risk_rounding_breach"); return; }
   double margin=0;
   if(!OrderCalcMargin(type,_Symbol,volume,intended,margin)) { Fail("margin_conversion_failed"); return; }
   if(margin>AccountInfoDouble(ACCOUNT_MARGIN_FREE)) { Log("SKIP","insufficient_margin",margin); return; }
   MqlTradeRequest request={}; MqlTradeResult result={}; MqlTradeCheckResult check={};
   request.action=TRADE_ACTION_DEAL; request.symbol=_Symbol; request.magic=Magic;
   request.type=type; request.volume=volume; request.price=intended; request.sl=stop;
   request.tp=0; request.type_filling=Filling(); request.comment="LC_X100_AUDIT";
   if(!OrderCheck(request,check)) { Log("SKIP","order_check_"+IntegerToString((int)check.retcode)); return; }
   if(!Send(request,result)) {
      if(result.retcode==TRADE_RETCODE_MARKET_CLOSED || result.retcode==TRADE_RETCODE_NO_MONEY) {
         Log("SKIP","entry_rejected_"+IntegerToString((int)result.retcode)); return;
      }
      Fail("entry_rejected"); return;
   }
   if(!OwnPosition()) { Fail("entry_position_missing"); return; }
   entry_fill=PositionGetDouble(POSITION_PRICE_OPEN);
   entry_time=(datetime)PositionGetInteger(POSITION_TIME);
   risk_price=MathAbs(entry_fill-stop)+friction;
   best_r=-DBL_MAX;
   Log("ENTRY",IntegerToString(side),PositionGetDouble(POSITION_VOLUME));
   Log("ENTRY_BUDGET","usd",budget);
   Log("ENTRY_PLANNED_RISK","usd",planned_loss);
   if(used_minimum) Log("ENTRY_MINIMUM_FALLBACK","actual_risk_percent",planned_loss/budget*RiskPercent);
   Log("ENTRY_INITIAL_STOP","price",stop);
   Log("ENTRY_ATR","points",atr);
   Log("ENTRY_RISK_PRICE","points",risk_price);
   double actual_risk=0;
   if(!OrderCalcProfit(type,_Symbol,PositionGetDouble(POSITION_VOLUME),entry_fill,stop-side*friction,actual_risk)) {
      Close("risk_calc_failed"); Fail("post_fill_risk_calculation"); return;
   }
   // OrderCalcProfit reports USD to cents; permit only half-cent conversion rounding.
   if(-actual_risk>allowed_budget+0.005001) { Close("risk_overshoot"); Fail("post_fill_risk_overshoot"); }
}
void Trail(datetime closed_bar) {
   if(!OwnPosition() || failed || risk_price<=0) return;
   // Only quotes from the completed bar; never the first quote of the new bar.
   if(last_quote_time<closed_bar || last_quote_time>=closed_bar+1800) {
      Log("TRAIL_SKIP","missing_completed_quote"); return;
   }
   if(entry_time>=closed_bar+1800) return;
   int side=PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY ? 1 : -1;
   double mark=(side==1 ? last_bid : last_ask);
   double friction=ExitSlippageReserve+RoundTripCommissionPrice;
   double current_r=(side*(mark-entry_fill)-friction)/risk_price;
   Log("MARK_R","completed_m30_quote",current_r);
   best_r=MathMax(best_r,current_r);
   if(best_r<1.0) return;
   double stop=QuantStop(LCTrailPrice(entry_fill,side,best_r,risk_price,friction),side);
   double existing=PositionGetDouble(POSITION_SL);
   if(side*(stop-existing)<=0) return;
   MqlTick tick; if(!SymbolInfoTick(_Symbol,tick)) return;
   if((side==1 && tick.bid<=stop) || (side==-1 && tick.ask>=stop)) { Close("trail_gap"); return; }
   if(!ValidStop(stop,side,tick,true)) { Log("TRAIL_SKIP","stops_or_freeze_limit",stop); return; }
   MqlTradeRequest request={}; MqlTradeResult result={};
   request.action=TRADE_ACTION_SLTP; request.symbol=_Symbol;
   request.position=(ulong)PositionGetInteger(POSITION_TICKET); request.sl=stop; request.tp=0;
   if(!Send(request,result)) {
      if(result.retcode==TRADE_RETCODE_MARKET_CLOSED || result.retcode==TRADE_RETCODE_NO_CHANGES) {
         Log("TRAIL_SKIP","modify_"+IntegerToString((int)result.retcode)); return;
      }
      Fail("trail_modify_rejected"); return;
   }
   Log("TRAIL","tighten",stop);
}
void RecordSignal(datetime stamp,const LCPoint &p) {
   if(signals!=INVALID_HANDLE)
      FileWrite(signals,(long)stamp,p.f[0],p.f[1],p.f[2],p.f[3],p.f[4],p.kernel,p.atr,(int)p.filter,p.prediction,p.direction,p.start,p.boundary_ties);
}
int OnInit() {
   if(!MQLInfoInteger(MQL_TESTER)) { Print("Tester only: no account trading permitted"); return INIT_FAILED; }
   if((_Symbol!="US500_x100" && _Symbol!="US500") || _Period!=PERIOD_M30 || AccountInfoString(ACCOUNT_CURRENCY)!="USD") return INIT_PARAMETERS_INCORRECT;
   if(RiskPercent<=0 || RiskPercent>5 || HistoryAnchor>=EvaluationStart || EvaluationStart>=EvaluationEnd
      || ExitSlippageReserve<0 || RoundTripCommissionPrice<0
      || StopATRMultiplier<1 || StopATRMultiplier>10
      || (MaxHoldingHours!=0 && MaxHoldingHours!=24)) return INIT_PARAMETERS_INCORRECT;
   if(AllowMinimumLotFallback && RiskPercent!=1.0) return INIT_PARAMETERS_INCORRECT;
   if(StringFind(RunTag,"\\")>=0 || StringFind(RunTag,"/")>=0 || StringFind(RunTag,"..")>=0) return INIT_PARAMETERS_INCORRECT;
   string base="LorentzianAudit\\"+RunTag;
   if(FileIsExist(base+"_events.csv",FILE_COMMON)||FileIsExist(base+"_signals.csv",FILE_COMMON)) return INIT_FAILED;
   journal=FileOpen(base+"_events.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   signals=FileOpen(base+"_signals.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(journal==INVALID_HANDLE || signals==INVALID_HANDLE) return INIT_FAILED;
   FileWrite(journal,"time","event","detail","value");
   FileWrite(signals,"time","f1","f2","f3","f4","f5","kernel","atr","filter","prediction","direction","start","boundary_ties");
   classifier.Init(); Log("INIT","tester_only");
   Log("SPEC","contract_size",SymbolInfoDouble(_Symbol,SYMBOL_TRADE_CONTRACT_SIZE));
   Log("SPEC","volume_min",SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN));
   Log("SPEC","volume_step",SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP));
   Log("SPEC","volume_max",SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX));
   Log("SPEC","swap_long",SymbolInfoDouble(_Symbol,SYMBOL_SWAP_LONG));
   return INIT_SUCCEEDED;
}
void OnTick() {
   if(first_tick==0) first_tick=TimeCurrent();
   last_tick=TimeCurrent(); tick_count++;
   if(!MQLInfoInteger(MQL_TESTER) || failed) return;
   datetime now=TimeCurrent();
   // Continue processing closed bars while waiting for a tradable exit quote.
   // Otherwise a session closure could silently interrupt the feature history.
   if(pending_close!="") Close(pending_close);
   if(now>=EvaluationEnd) { Close("evaluation_end"); return; }
   if(MaxHoldingHours>0 && OwnPosition() && now>=entry_time+MaxHoldingHours*3600) Close("time_24h");
   datetime completed=iTime(_Symbol,PERIOD_M30,1);
   if(completed<=0) { Fail("no_closed_bar"); return; }
   if(completed!=last_bar) {
      MqlRates rates[]; ArraySetAsSeries(rates,false);
      datetime first=ready ? last_bar+1800 : HistoryAnchor;
      int n=CopyRates(_Symbol,PERIOD_M30,first,completed,rates);
      if(n<=0 || (!ready && (rates[0].time>HistoryAnchor+7*86400 || n<2000))) {
         Fail("anchored_history_unavailable"); return;
      }
      if(rates[n-1].time!=completed) { Fail("history_not_synchronized"); return; }
      if(ready && n!=1) { Fail("unexpected_closed_bar_gap"); return; }
      LCPoint p={};
      for(int i=0;i<n;i++) {
         if(rates[i].time>=iTime(_Symbol,PERIOD_M30,0)) { Fail("incomplete_bar"); return; }
         classifier.Push(rates[i].open,rates[i].high,rates[i].low,rates[i].close,p);
         RecordSignal(rates[i].time,p);
         if(p.boundary_ties>0) { Fail("neighbor_boundary_tie_requires_review"); return; }
      }
      last_bar=completed; ready=true;
      Trail(completed);
      if(now>=EvaluationStart && p.start!=0 && !failed && pending_close=="") {
         if(OwnPosition()) {
            int side=PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY ? 1 : -1;
            if(side!=p.start && !Close("opposite")) return;
         }
         if(!OwnPosition()) Enter(p.start,p.atr);
      }
   }
   MqlTick tick;
   if(SymbolInfoTick(_Symbol,tick)) { last_bid=tick.bid; last_ask=tick.ask; last_quote_time=tick.time; }
}
double OnTester() {
   if(!MQLInfoInteger(MQL_TESTER)) return 0;
   string base="LorentzianAudit\\"+RunTag;
   int stats=FileOpen(base+"_stats.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(stats!=INVALID_HANDLE) {
      FileWrite(stats,"field","value");
      FileWrite(stats,"failed",(int)failed);
      FileWrite(stats,"ready",(int)ready);
      FileWrite(stats,"first_tick",(long)first_tick);
      FileWrite(stats,"last_tick",(long)last_tick);
      FileWrite(stats,"tick_count",tick_count);
      FileWrite(stats,"classifier_bars",classifier.Count());
      FileWrite(stats,"risk_percent",RiskPercent);
      FileWrite(stats,"minimum_lot_fallback",(int)AllowMinimumLotFallback);
      FileWrite(stats,"stop_atr_multiplier",StopATRMultiplier);
      FileWrite(stats,"max_holding_hours",MaxHoldingHours);
      FileWrite(stats,"deposit",TesterStatistics(STAT_INITIAL_DEPOSIT));
      FileWrite(stats,"net_profit",TesterStatistics(STAT_PROFIT));
      FileWrite(stats,"final_balance",AccountInfoDouble(ACCOUNT_BALANCE));
      FileWrite(stats,"final_equity",AccountInfoDouble(ACCOUNT_EQUITY));
      FileWrite(stats,"trades",TesterStatistics(STAT_TRADES));
      FileWrite(stats,"winners",TesterStatistics(STAT_PROFIT_TRADES));
      FileWrite(stats,"profit_factor",TesterStatistics(STAT_PROFIT_FACTOR));
      FileWrite(stats,"balance_dd_percent",TesterStatistics(STAT_BALANCE_DDREL_PERCENT));
      FileWrite(stats,"equity_dd_percent",TesterStatistics(STAT_EQUITY_DDREL_PERCENT));
      FileWrite(stats,"max_loss_trade",TesterStatistics(STAT_MAX_LOSSTRADE));
      FileWrite(stats,"max_win_trade",TesterStatistics(STAT_MAX_PROFITTRADE));
      FileWrite(stats,"max_consecutive_losses",TesterStatistics(STAT_MAX_CONLOSS_TRADES));
      FileWrite(stats,"min_margin_level",TesterStatistics(STAT_MIN_MARGINLEVEL));
      FileClose(stats);
   }
   if(HistorySelect(0,TimeCurrent())) {
      int out=FileOpen(base+"_deals.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
      if(out!=INVALID_HANDLE) {
         FileWrite(out,"ticket","position_id","time","entry","type","reason","volume","price","profit","commission","fee","swap");
         for(int i=0;i<HistoryDealsTotal();i++) {
            ulong id=HistoryDealGetTicket(i);
            if(HistoryDealGetString(id,DEAL_SYMBOL)!=_Symbol) continue;
            FileWrite(out,id,HistoryDealGetInteger(id,DEAL_POSITION_ID),HistoryDealGetInteger(id,DEAL_TIME),
               HistoryDealGetInteger(id,DEAL_ENTRY),HistoryDealGetInteger(id,DEAL_TYPE),HistoryDealGetInteger(id,DEAL_REASON),
               HistoryDealGetDouble(id,DEAL_VOLUME),HistoryDealGetDouble(id,DEAL_PRICE),HistoryDealGetDouble(id,DEAL_PROFIT),
               HistoryDealGetDouble(id,DEAL_COMMISSION),HistoryDealGetDouble(id,DEAL_FEE),HistoryDealGetDouble(id,DEAL_SWAP));
         }
         FileClose(out);
      }
   }
   return failed ? -DBL_MAX : TesterStatistics(STAT_PROFIT);
}
void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &request,const MqlTradeResult &result) {
   if(!MQLInfoInteger(MQL_TESTER) || trans.type!=TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetString(trans.deal,DEAL_SYMBOL)!=_Symbol || (ulong)HistoryDealGetInteger(trans.deal,DEAL_MAGIC)!=Magic) return;
   Log("DEAL_PROFIT",IntegerToString((int)HistoryDealGetInteger(trans.deal,DEAL_ENTRY)),HistoryDealGetDouble(trans.deal,DEAL_PROFIT));
   Log("DEAL_COMMISSION","actual_tester",HistoryDealGetDouble(trans.deal,DEAL_COMMISSION));
   Log("DEAL_SWAP","actual_tester",HistoryDealGetDouble(trans.deal,DEAL_SWAP));
}
void OnDeinit(const int reason) {
   Log("DEINIT",IntegerToString(reason));
   if(journal!=INVALID_HANDLE) FileClose(journal);
   if(signals!=INVALID_HANDLE) FileClose(signals);
}
