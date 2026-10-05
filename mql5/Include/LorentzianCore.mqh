// Independent streaming implementation of the frozen causal Python variant.
// Not the original author's ANN. No trading or terminal dependencies here.
#ifndef LORENTZIAN_CORE_MQH
#define LORENTZIAN_CORE_MQH
#define LC_MISSING EMPTY_VALUE

bool LCValid(double x) { return x!=LC_MISSING && MathIsValidNumber(x); }
double LCRoundEven(double x) {
   double lo=MathFloor(x), f=x-lo;
   if(f<0.5) return lo;
   if(f>0.5) return lo+1.0;
   return ((long)lo%2==0) ? lo : lo+1.0;
}
double LCQuant(double a,double b) { return (LCRoundEven(a*100.0)-LCRoundEven(b*100.0))/100.0; }

class LCSmoother {
   int n, count;
   double alpha, total, value;
public:
   void Init(int period,bool rma=false) {
      n=period; count=0; alpha=(rma ? 1.0/period : 2.0/(period+1));
      total=0; value=LC_MISSING;
   }
   double Push(double x) {
      if(!LCValid(x)) { count=0; total=0; value=LC_MISSING; return value; }
      if(LCValid(value)) value=alpha*x+(1-alpha)*value;
      else { total+=x; count++; if(count>=n) value=total/n; }
      return value;
   }
};

class LCNormalizer {
   double lo,hi;
public:
   void Init() { lo=1e11; hi=-1e11; }
   double Push(double x) {
      if(!LCValid(x)) return LC_MISSING;
      lo=MathMin(lo,x); hi=MathMax(hi,x);
      return (x-lo)/MathMax(hi-lo,1e-9);
   }
};

struct LCPoint {
   double close, f[5], kernel, atr;
   int prediction, direction, start, boundary_ties;
   bool filter, finite;
};

class LorentzianCore {
   LCPoint ring[2048];
   int count, state;
   double prev_high,prev_low,prev_close,prev_ohlc4,prev_kernel;
   double smooth_tr,smooth_plus,smooth_minus;
   double regime_v1,regime_v2,regime_klmf,regime_ema;
   double wt_ring[4];
   LCSmoother gain14,loss14,gain9,loss9,wt_ema1,wt_ema2,wt_ema3,adx,atr14,atr10;
   LCNormalizer wt_norm,cci_norm;
   double RSI(double gain,double loss) {
      if(!LCValid(gain)||!LCValid(loss)) return LC_MISSING;
      return (loss==0 ? 100.0 : 100.0-100.0/(1+gain/loss))/100.0;
   }
public:
   void Init() {
      count=0; state=0; prev_high=0; prev_low=0; prev_close=0; prev_ohlc4=0; prev_kernel=0;
      smooth_tr=0; smooth_plus=0; smooth_minus=0;
      regime_v1=0; regime_v2=0; regime_klmf=0; regime_ema=0;
      gain14.Init(14,true); loss14.Init(14,true); gain9.Init(9,true); loss9.Init(9,true);
      wt_ema1.Init(10); wt_ema2.Init(10); wt_ema3.Init(11);
      adx.Init(20,true); atr14.Init(14,true); atr10.Init(10,true);
      wt_norm.Init(); cci_norm.Init();
      for(int k=0;k<4;k++) wt_ring[k]=LC_MISSING;
   }
   int Count() { return count; }
   void Push(double open,double high,double low,double close,LCPoint &p) {
      int i=count;
      p.close=close;
      double change=close-prev_close;
      double gain=(i>0 ? MathMax(change,0) : LC_MISSING);
      double loss=(i>0 ? MathMax(-change,0) : LC_MISSING);
      p.f[0]=RSI(gain14.Push(gain),loss14.Push(loss));
      p.f[4]=RSI(gain9.Push(gain),loss9.Push(loss));

      double hlc3=(high+low+close)/3;
      double e1=wt_ema1.Push(hlc3);
      double e2=wt_ema2.Push(LCValid(e1)? MathAbs(hlc3-e1) : LC_MISSING);
      double ci=LC_MISSING;
      if(LCValid(e1)&&LCValid(e2)) ci=(e2!=0 ? (hlc3-e1)/(0.015*e2) : 0);
      double wt=wt_ema3.Push(ci), wt_sum=0;
      wt_ring[i%4]=wt;
      bool wt_ok=true;
      // Chronological summation, like the reference SMA.
      for(int k=3;k>=0;k--) {
         if(i-k<0 || !LCValid(wt_ring[(i-k)%4])) { wt_ok=false; break; }
         wt_sum+=wt_ring[(i-k)%4];
      }
      p.f[1]=wt_norm.Push(wt_ok ? wt-wt_sum/4 : LC_MISSING);

      double cci=LC_MISSING;
      if(i>=19) {
         double avg=0,dev=0;
         for(int k=19;k>=0;k--) avg+=(k==0 ? close : ring[(i-k)%2048].close);
         avg/=20;
         for(int k=19;k>=0;k--) dev+=MathAbs((k==0 ? close : ring[(i-k)%2048].close)-avg);
         dev/=20;
         cci=(dev!=0 ? (close-avg)/(0.015*dev) : 0);
      }
      p.f[2]=cci_norm.Push(cci);

      double tr=MathMax(high-low,MathMax(MathAbs(high-prev_close),MathAbs(low-prev_close)));
      p.atr=atr14.Push(tr);
      double a10=atr10.Push(tr);
      double qtr=MathMax(LCQuant(high,low),MathMax(MathAbs(LCQuant(high,prev_close)),MathAbs(LCQuant(low,prev_close))));
      double up=LCQuant(high,prev_high),down=LCQuant(prev_low,low);
      double plus=(up>down && up>0 ? up : 0),minus=(down>up && down>0 ? down : 0);
      if(i==0) { smooth_tr=qtr; smooth_plus=plus; smooth_minus=minus; }
      else {
         smooth_tr=smooth_tr-smooth_tr/20+qtr;
         smooth_plus=smooth_plus-smooth_plus/20+plus;
         smooth_minus=smooth_minus-smooth_minus/20+minus;
      }
      double dp=(smooth_tr!=0 ? smooth_plus/smooth_tr*100 : 0);
      double dm=(smooth_tr!=0 ? smooth_minus/smooth_tr*100 : 0);
      double dx=(dp+dm!=0 ? MathAbs(dp-dm)/(dp+dm)*100 : 0);
      double adx_value=adx.Push(dx);
      p.f[3]=LCValid(adx_value)? adx_value/100 : LC_MISSING;

      double ohlc4=(open+high+low+close)/4, slope=0;
      if(i==0) { regime_v2=high-low; regime_klmf=ohlc4; }
      else {
         regime_v1=0.2*(ohlc4-prev_ohlc4)+0.8*regime_v1;
         regime_v2=0.1*(high-low)+0.8*regime_v2;
         double omega=(regime_v2!=0 ? MathAbs(regime_v1/regime_v2) : 0);
         double alpha=(-MathPow(omega,2)+MathSqrt(MathPow(omega,4)+16*MathPow(omega,2)))/8;
         double current=alpha*ohlc4+(1-alpha)*regime_klmf;
         slope=MathAbs(current-regime_klmf); regime_klmf=current;
         regime_ema=(regime_ema==0 && i<200 ? slope : (2.0/201)*slope+(1-2.0/201)*regime_ema);
      }
      p.filter=(!LCValid(a10)||tr>a10) && (regime_ema==0 || (slope-regime_ema)/regime_ema>=-0.1);
      double weighted=0,weights=0;
      for(int k=0;k<=MathMin(26,i);k++) {
         double w=MathPow(1+k*k/1024.0,-8);
         weighted+=(k==0 ? close : ring[(i-k)%2048].close)*w;
         weights+=w;
      }
      p.kernel=weighted/weights;
      p.finite=true;
      for(int f=0;f<5;f++) if(!LCValid(p.f[f])) p.finite=false;
      ring[i%2048]=p;

      double best[9]; int labels[9],indices[9],found=0;
      for(int n=0;n<9;n++) { best[n]=DBL_MAX; labels[n]=0; indices[n]=-1; }
      if(p.finite) for(int j=i-4;j>=MathMax(0,i-2000);j--) {
         if(j%4==0 || !ring[j%2048].finite) continue;
         double d=0;
         for(int f=0;f<5;f++) d+=MathLog(1+MathAbs(ring[j%2048].f[f]-p.f[f]));
         // Stable ascending index on ties. Audit the boundary: numpy argpartition
         // has no stable tie policy. Any prediction mismatch blocks parity.
         int pos=8;
         if(d>best[pos] || (d==best[pos] && j>indices[pos])) continue;
         while(pos>0 && (d<best[pos-1] || (d==best[pos-1] && j<indices[pos-1]))) {
            best[pos]=best[pos-1]; labels[pos]=labels[pos-1]; indices[pos]=indices[pos-1]; pos--;
         }
         double move=ring[(j+4)%2048].close-ring[j%2048].close;
         best[pos]=d; labels[pos]=(move>0 ? 1 : move<0 ? -1 : 0); indices[pos]=j;
         found++;
      }
      p.prediction=0; p.boundary_ties=0;
      if(found>=8) {
         for(int n=0;n<8;n++) p.prediction+=labels[n];
         if(best[8]!=DBL_MAX && MathAbs(best[8]-best[7])<=1e-12) p.boundary_ties=1;
      }
      int previous=state;
      if(p.filter && p.prediction>0) state=1;
      if(p.filter && p.prediction<0) state=-1;
      p.direction=state; p.start=0;
      if(i>0 && state!=previous) {
         if(state==1 && p.kernel>prev_kernel) p.start=1;
         if(state==-1 && p.kernel<prev_kernel) p.start=-1;
      }
      ring[i%2048]=p;
      prev_high=high; prev_low=low; prev_close=close; prev_ohlc4=ohlc4; prev_kernel=p.kernel;
      count++;
   }
};
#endif
