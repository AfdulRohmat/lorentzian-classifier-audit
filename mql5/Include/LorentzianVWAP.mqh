// Research-only tick-volume VWAP and explicit US Eastern clock.
#ifndef LORENTZIAN_VWAP_MQH
#define LORENTZIAN_VWAP_MQH
datetime LCMonthSunday(int year,int month,int ordinal,int utc_hour) {
   MqlDateTime d={}; d.year=year; d.mon=month; d.day=1; d.hour=utc_hour;
   datetime first=StructToTime(d); TimeToStruct(first,d);
   return first+((7-d.day_of_week)%7+7*(ordinal-1))*86400;
}
datetime LCNewYork(datetime utc) {
   MqlDateTime d; TimeToStruct(utc,d);
   bool dst=utc>=LCMonthSunday(d.year,3,2,7) && utc<LCMonthSunday(d.year,11,1,6);
   return utc-(dst ? 4 : 5)*3600;
}
int LCNYMinute(datetime utc) {
   MqlDateTime d; TimeToStruct(LCNewYork(utc),d); return d.hour*60+d.min;
}
bool LCIntradayEntry(datetime quote,datetime signal) {
   MqlDateTime d; TimeToStruct(LCNewYork(quote),d);
   int md=d.mon*100+d.day;
   // Frozen Jan-Aug 2026 NYSE full-day holidays, known before evaluation.
   if(d.year!=2026 || d.day_of_week==0 || d.day_of_week==6
      || md==101 || md==119 || md==216 || md==403 || md==525 || md==619 || md==703) return false;
   int q=LCNYMinute(quote),s=LCNYMinute(signal);
   return q>=570 && q<930 && s>=570 && (long)LCNewYork(quote)/86400==(long)LCNewYork(signal)/86400;
}
class LCVWAP {
   long day; double weight,mean,m2;
public:
   double value,sigma,z; bool valid;
   void Init() { day=-1; weight=0; mean=0; m2=0; value=0; sigma=0; z=0; valid=false; }
   void Push(const MqlRates &r) {
      long next=(long)r.time/86400;
      if(next!=day) { day=next; weight=0; mean=0; m2=0; }
      valid=false;
      if(r.tick_volume<=0) { value=mean; sigma=0; z=0; return; }
      double w=(double)r.tick_volume,x=(r.high+r.low+r.close)/3.0;
      double delta=x-mean; weight+=w; mean+=w/weight*delta; m2+=w*delta*(x-mean);
      value=mean; sigma=MathSqrt(MathMax(0,m2/weight));
      z=sigma>1e-9 ? (r.close-value)/sigma : 0;
      valid=sigma>1e-9 && MathIsValidNumber(z);
   }
   bool Allows(int side) {
      if(!valid || MathAbs(z)>3) return false;
      if(z<=-1) return side==1;
      if(z>=1) return side==-1;
      return true;
   }
};
#endif
