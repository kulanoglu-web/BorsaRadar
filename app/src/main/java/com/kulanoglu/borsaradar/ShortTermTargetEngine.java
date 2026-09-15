package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/** Time-bound targets for short-term trades. Targets are derived from price structure and volatility. */
public final class ShortTermTargetEngine {
    public static final class Target {
        public final double entry, target1, target2, stop;
        public final int minBars, maxBars;
        public final double confidence;
        public final String horizon;
        Target(double e,double t1,double t2,double s,int min,int max,double c,String h){entry=e;target1=t1;target2=t2;stop=s;minBars=min;maxBars=max;confidence=c;horizon=h;}
        public String summary(String currency){
            double p1=entry>0?(target1/entry-1)*100:0,p2=entry>0?(target2/entry-1)*100:0;
            return String.format(Locale.US,"Hedef 1: %.2f %s (%+.1f%%) • Hedef 2: %.2f %s (%+.1f%%)\nBeklenen süre: %s • Stop/Geçersiz: %.2f %s • Güven: %.0f%%",target1,currency,p1,target2,currency,p2,horizon,stop,currency,confidence*100);
        }
    }

    public static Target calculate(List<MarketDataService.Candle> d,String interval){
        if(d==null||d.size()<12)return null;
        int n=d.size(); double last=d.get(n-1).close;
        int atrN=Math.min(14,n-1); double tr=0;
        for(int i=n-atrN;i<n;i++){
            MarketDataService.Candle c=d.get(i),p=d.get(i-1);
            tr+=Math.max(c.high-c.low,Math.max(Math.abs(c.high-p.close),Math.abs(c.low-p.close)));
        }
        double atr=Math.max(last*0.004,tr/atrN);
        int look=Math.min(40,n); double resistance=-Double.MAX_VALUE,support=Double.MAX_VALUE;
        for(int i=n-look;i<n-1;i++){MarketDataService.Candle c=d.get(i);resistance=Math.max(resistance,c.high);support=Math.min(support,c.low);}
        double momentum=(last-d.get(Math.max(0,n-6)).close)/Math.max(0.0001,d.get(Math.max(0,n-6)).close);
        double t1=Math.max(last+1.25*atr,resistance>last?resistance:last+1.25*atr);
        double t2=Math.max(t1+0.75*atr,last+2.25*atr);
        double stop=Math.max(support,last-1.35*atr);
        if(stop>=last)stop=last-1.35*atr;
        double conf=0.58+(momentum>0?0.08:-0.05)+(last>=resistance?0.07:0);
        conf=Math.max(0.35,Math.min(0.88,conf));
        String h=horizon(interval,atr/Math.max(last,0.0001));
        int[] bars=bars(interval,atr/Math.max(last,0.0001));
        return new Target(last,t1,t2,stop,bars[0],bars[1],conf,h);
    }
    private static int[] bars(String interval,double vol){int a=2,b=6;if("5m".equals(interval)){a=6;b=24;}else if("15m".equals(interval)){a=4;b=16;}else if("30m".equals(interval)){a=3;b=12;}else if("60m".equals(interval)){a=2;b=10;}else if("1d".equals(interval)){a=2;b=5;}if(vol<0.01)b+=3;return new int[]{a,b};}
    private static String horizon(String interval,double vol){if("5m".equals(interval))return vol>0.02?"30 dk–2 saat":"1–4 saat";if("15m".equals(interval))return vol>0.02?"1–4 saat":"2–8 saat";if("30m".equals(interval))return "3–12 saat";if("60m".equals(interval))return vol>0.02?"4–16 saat":"1–3 işlem günü";return vol>0.02?"1–3 işlem günü":"2–5 işlem günü";}
    private ShortTermTargetEngine(){}
}
