package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/** Eksik kalan klasik teknik katmani: MOST, QQE-benzeri filtre, Fibonacci ve pivot seviyeleri. */
public final class AdditionalIndicatorEngine {
    private AdditionalIndicatorEngine(){}
    public static final class Result {
        public double most,qqe,fib382,fib50,fib618,pivot,r1,s1,r2,s2;
        public boolean mostBull,qqeBull,abovePivot;
        public String summary;
    }
    public static Result analyze(List<MarketDataService.Candle>x){
        if(x==null||x.size()<20)throw new IllegalArgumentException("Ek indikatörler için en az 20 gün gerekli");
        Result r=new Result(); int e=x.size()-1;
        double ema=IndicatorEngine.ema(x,10,e), atr=IndicatorEngine.atr(x,10,e), close=x.get(e).close;
        r.most=ema-2.0*atr; r.mostBull=close>r.most;
        double rsi=IndicatorEngine.rsi(x,14,e); double smooth=emaRsi(x,14,5,e); double delta=Math.abs(rsi-smooth);
        r.qqe=smooth-0.45*delta; r.qqeBull=rsi>r.qqe;
        int st=Math.max(0,e-59); double hi=-Double.MAX_VALUE,lo=Double.MAX_VALUE;
        for(int i=st;i<=e;i++){hi=Math.max(hi,x.get(i).high);lo=Math.min(lo,x.get(i).low);}
        double range=Math.max(1e-9,hi-lo); r.fib382=hi-range*.382; r.fib50=hi-range*.5; r.fib618=hi-range*.618;
        MarketDataService.Candle p=x.get(Math.max(0,e-1)); r.pivot=(p.high+p.low+p.close)/3.0;
        r.r1=2*r.pivot-p.low; r.s1=2*r.pivot-p.high; r.r2=r.pivot+(p.high-p.low); r.s2=r.pivot-(p.high-p.low); r.abovePivot=close>=r.pivot;
        r.summary=String.format(Locale.US,"MOST %.2f %s • QQE %.1f %s • Pivot %.2f • Fib 38/50/61 %.2f/%.2f/%.2f",r.most,r.mostBull?"+":"-",r.qqe,r.qqeBull?"+":"-",r.pivot,r.fib382,r.fib50,r.fib618);
        return r;
    }
    private static double emaRsi(List<MarketDataService.Candle>x,int rsiPeriod,int emaPeriod,int end){int start=Math.max(rsiPeriod,end-emaPeriod*4);double k=2.0/(emaPeriod+1),v=IndicatorEngine.rsi(x,rsiPeriod,start);for(int i=start+1;i<=end;i++)v=IndicatorEngine.rsi(x,rsiPeriod,i)*k+v*(1-k);return v;}
}
