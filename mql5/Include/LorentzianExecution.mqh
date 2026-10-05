#ifndef LORENTZIAN_EXECUTION_MQH
#define LORENTZIAN_EXECUTION_MQH
double LCFloorVolume(double budget,double loss_per_lot,double minimum,double maximum,double step) {
   if(budget<=0 || loss_per_lot<=0 || minimum<=0 || step<=0 || maximum<minimum) return 0;
   double volume=NormalizeDouble(MathFloor(MathMin(budget/loss_per_lot,maximum)/step+1e-12)*step,8);
   if(volume<minimum-1e-12 || volume*loss_per_lot>budget+1e-8) return 0;
   return volume;
}
double LCStopGrid(double price,int side,double tick,int digits) {
   if(tick<=0 || (side!=1 && side!=-1)) return 0;
   return NormalizeDouble((side==1 ? MathFloor(price/tick+1e-10) : MathCeil(price/tick-1e-10))*tick,digits);
}
double LCTrailPrice(double entry,int side,double peak_r,double risk,double friction) {
   return entry+side*((peak_r-1.0)*risk+friction);
}
#endif
