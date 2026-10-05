#property strict
// Read-only cached/live metadata probe. No account identity and no order calls.
void OnStart() {
   string path="LorentzianAudit\\symbol_audit.csv";
   if(FileIsExist(path,FILE_COMMON)) { Print("AUDIT_REFUSE_OVERWRITE"); return; }
   int f=FileOpen(path,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(f==INVALID_HANDLE) return;
   FileWrite(f,"field","value");
   FileWrite(f,"terminal_connected",TerminalInfoInteger(TERMINAL_CONNECTED));
   FileWrite(f,"terminal_build",TerminalInfoInteger(TERMINAL_BUILD));
   FileWrite(f,"account_currency",AccountInfoString(ACCOUNT_CURRENCY));
   FileWrite(f,"account_trade_mode",AccountInfoInteger(ACCOUNT_TRADE_MODE));
   FileWrite(f,"account_leverage",AccountInfoInteger(ACCOUNT_LEVERAGE));
   string s="US500_x100";
   ResetLastError();
   bool selected=SymbolSelect(s,true);
   FileWrite(f,"exact_symbol_selected",(int)selected);
   FileWrite(f,"error",GetLastError());
   if(selected) {
      FileWrite(f,"contract_size",SymbolInfoDouble(s,SYMBOL_TRADE_CONTRACT_SIZE));
      FileWrite(f,"point",SymbolInfoDouble(s,SYMBOL_POINT));
      FileWrite(f,"tick_size",SymbolInfoDouble(s,SYMBOL_TRADE_TICK_SIZE));
      FileWrite(f,"tick_value_profit",SymbolInfoDouble(s,SYMBOL_TRADE_TICK_VALUE_PROFIT));
      FileWrite(f,"tick_value_loss",SymbolInfoDouble(s,SYMBOL_TRADE_TICK_VALUE_LOSS));
      FileWrite(f,"volume_min",SymbolInfoDouble(s,SYMBOL_VOLUME_MIN));
      FileWrite(f,"volume_max",SymbolInfoDouble(s,SYMBOL_VOLUME_MAX));
      FileWrite(f,"volume_step",SymbolInfoDouble(s,SYMBOL_VOLUME_STEP));
      FileWrite(f,"stops_level",SymbolInfoInteger(s,SYMBOL_TRADE_STOPS_LEVEL));
      FileWrite(f,"freeze_level",SymbolInfoInteger(s,SYMBOL_TRADE_FREEZE_LEVEL));
      FileWrite(f,"margin_initial",SymbolInfoDouble(s,SYMBOL_MARGIN_INITIAL));
      FileWrite(f,"margin_maintenance",SymbolInfoDouble(s,SYMBOL_MARGIN_MAINTENANCE));
      FileWrite(f,"swap_mode",SymbolInfoInteger(s,SYMBOL_SWAP_MODE));
      FileWrite(f,"swap_long",SymbolInfoDouble(s,SYMBOL_SWAP_LONG));
      FileWrite(f,"swap_short",SymbolInfoDouble(s,SYMBOL_SWAP_SHORT));
      FileWrite(f,"calc_mode",SymbolInfoInteger(s,SYMBOL_TRADE_CALC_MODE));
      for(int day=0;day<7;day++) for(uint session=0;session<10;session++) {
         datetime from,to;
         if(!SymbolInfoSessionTrade(s,(ENUM_DAY_OF_WEEK)day,session,from,to)) break;
         FileWrite(f,"session_"+IntegerToString(day)+"_"+IntegerToString(session),IntegerToString((int)from)+":"+IntegerToString((int)to));
      }
      FileFlush(f);
      MqlRates bars[]; ArraySetAsSeries(bars,false);
      ResetLastError();
      int n=CopyRates(s,PERIOD_M30,D'2022.01.01',D'2026.08.31 23:59:59',bars);
      FileWrite(f,"m30_2022_2026_count",n);
      FileWrite(f,"history_error",GetLastError());
      if(n>0) {
         FileWrite(f,"first_m30",TimeToString(bars[0].time,TIME_DATE|TIME_MINUTES));
         FileWrite(f,"last_m30",TimeToString(bars[n-1].time,TIME_DATE|TIME_MINUTES));
         int out=FileOpen("LorentzianAudit\\native_m30.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
         if(out!=INVALID_HANDLE) {
            FileWrite(out,"time","open","high","low","close","spread");
            for(int i=0;i<n;i++) FileWrite(out,(long)bars[i].time,bars[i].open,bars[i].high,bars[i].low,bars[i].close,bars[i].spread);
            FileClose(out);
         }
      }
   }
   FileClose(f); Print("LC_SYMBOL_AUDIT_COMPLETE");
}
