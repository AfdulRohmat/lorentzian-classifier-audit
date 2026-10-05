#property strict
#include "..\Include\LorentzianCore.mqh"
#include "..\Include\LorentzianExecution.mqh"
int checks=0,failures=0,report=INVALID_HANDLE;
void Check(bool condition,string name) {
   checks++; if(!condition) failures++;
   FileWrite(report,name,(int)condition);
}
void OnStart() {
   string path="LorentzianAudit\\self_test_final.csv";
   if(FileIsExist(path,FILE_COMMON)) return;
   report=FileOpen(path,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(report==INVALID_HANDLE) return;
   FileWrite(report,"check","pass");
   Check(LCRoundEven(2.5)==2 && LCRoundEven(3.5)==4 && LCRoundEven(-1.5)==-2,"bankers_rounding");
   Check(LCFloorVolume(10,1000,0.03,20,0.01)==0,"skip_below_minimum");
   Check(LCFloorVolume(30,1000,0.03,20,0.01)==0.03,"exact_minimum");
   Check(LCFloorVolume(29.99,1000,0.03,20,0.01)==0,"never_round_risk_up");
   Check(LCFloorVolume(39.99,1000,0.01,20,0.01)==0.03,"floor_step");
   Check(LCFloorVolume(1e6,10,0.01,20,0.01)==20,"maximum_volume");
   Check(LCFloorVolume(30,1000,0.01,20,0)==0,"invalid_step");
   Check(LCStopGrid(100.006,1,0.01,2)==100.00,"long_stop_outward_grid");
   Check(LCStopGrid(100.001,-1,0.01,2)==100.01,"short_stop_outward_grid");
   Check(MathAbs(LCTrailPrice(100,1,1,10.27,0.27)-100.27)<1e-12,"one_R_locks_net_breakeven_long");
   Check(MathAbs(LCTrailPrice(100,-1,1,10.27,0.27)-99.73)<1e-12,"one_R_locks_net_breakeven_short");
   LCSmoother smoother; smoother.Init(3,true);
   Check(!LCValid(smoother.Push(1)),"rma_first_missing");
   Check(!LCValid(smoother.Push(2)),"rma_second_missing");
   Check(smoother.Push(3)==2,"rma_sma_seed");
   Check(MathAbs(smoother.Push(5)-3)<1e-12,"rma_recurrence");
   LorentzianCore a,b; a.Init(); b.Init(); LCPoint p={},q={};
   bool flat_ok=true;
   for(int i=0;i<2105;i++) {
      a.Push(100,100,100,100,p);
      if(p.prediction!=0 || p.start!=0) flat_ok=false;
   }
   Check(flat_ok,"flat_prices_no_signals_and_ring_wrap");
   a.Init(); bool restart_ok=true;
   for(int i=0;i<2200;i++) {
      double c=100+MathSin(i/13.0)+i*0.01;
      a.Push(c-0.1,c+0.2,c-0.3,c,p);
      b.Push(c-0.1,c+0.2,c-0.3,c,q);
      if(p.start!=q.start || p.prediction!=q.prediction || p.atr!=q.atr) restart_ok=false;
      for(int k=0;k<5;k++) if(p.f[k]!=q.f[k]) restart_ok=false;
   }
   Check(restart_ok,"full_replay_resets_all_state");
   FileWrite(report,"total_checks",checks); FileWrite(report,"failures",failures);
   FileClose(report); Print("LC_SELF_TEST checks=",checks," failures=",failures);
}
