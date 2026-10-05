#property strict
#include "..\Include\LorentzianCore.mqh"

input string Fixture="LorentzianAudit\\fixture.csv";
input string Output="LorentzianAudit\\mql_parity.csv";

void OnStart() {
   int reader=FileOpen(Fixture,FILE_READ|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(reader==INVALID_HANDLE) { Print("LC_PARITY_INPUT_FAILED ",GetLastError()); return; }
   if(FileIsExist(Output,FILE_COMMON)) { Print("LC_PARITY_REFUSE_OVERWRITE"); FileClose(reader); return; }
   int output=FileOpen(Output,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(output==INVALID_HANDLE) { FileClose(reader); return; }
   LorentzianCore core; core.Init(); LCPoint p;
   FileWrite(output,"time","f1","f2","f3","f4","f5","kernel","atr","filter","prediction","direction","start","boundary_ties");
   while(!FileIsEnding(reader)) {
      string time=FileReadString(reader);
      if(time=="") break;
      double o=FileReadNumber(reader),h=FileReadNumber(reader),l=FileReadNumber(reader),c=FileReadNumber(reader);
      core.Push(o,h,l,c,p);
      FileWrite(output,time,p.f[0],p.f[1],p.f[2],p.f[3],p.f[4],p.kernel,p.atr,(int)p.filter,p.prediction,p.direction,p.start,p.boundary_ties);
   }
   FileClose(reader); FileClose(output);
   Print("LC_PARITY_COMPLETE bars=",core.Count());
}
