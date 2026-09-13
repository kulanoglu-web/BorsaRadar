package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/** İlave teknik teyitler: MFI, OBV eğimi, Williams %R, Donchian konumu ve Ichimoku bulutu. */
public final class AdvancedIndicatorEngine {
    private AdvancedIndicatorEngine(){}
    public static final class Result {
        public double mfi14,obvSlope,williamsR14,donchianPosition,tenkan,kijun,cloudTop,cloudBottom;
        public boolean ichimokuBull;
        public String summary;
    }
    public static Result analyze(List<MarketDataService.Candle>x){
        if(x==null||x.size()<30)throw new IllegalArgumentException("Gelişmiş indikatörler için en az 30 gün gerekli");
        Result r=new Result(); int e=x.size()-1;
        r.mfi14=mfi(x,14,e); r.obvSlope=obvSlope(x,20,e); r.williamsR14=williamsR(x,14,e); r.donchianPosition=donchian(x,20,e);
        r.tenkan=(highest(x,9,e)+lowest(x,9,e))/2.0; r.kijun=(highest(x,26,e)+lowest(x,26,e))/2.0;
        double spanA=(r.tenkan+r.kijun)/2.0, spanB=(highest(x,52,e)+lowest(x,52,e))/2.0;
        r.cloudTop=Math.max(spanA,spanB); r.cloudBottom=Math.min(spanA,spanB); r.ichimokuBull=x.get(e).close>r.cloudTop&&r.tenkan>=r.kijun;
        r.summary=String.format(Locale.US,"MFI %.1f • OBV eğim %.2f • W%%R %.1f • Donchian %.0f%% • Ichimoku %s",r.mfi14,r.obvSlope,r.williamsR14,r.donchianPosition*100,r.ichimokuBull?"+":"-");
        return r;
    }
    private static double mfi(List<MarketDataService.Candle>x,int p,int e){double pos=0,neg=0;int st=Math.max(1,e-p+1);for(int i=st;i<=e;i++){double tp=(x.get(i).high+x.get(i).low+x.get(i).close)/3.0,pt=(x.get(i-1).high+x.get(i-1).low+x.get(i-1).close)/3.0,flow=tp*x.get(i).volume;if(tp>=pt)pos+=flow;else neg+=flow;}return neg==0?100:100-100/(1+pos/neg);}
    private static double obvSlope(List<MarketDataService.Candle>x,int p,int e){int st=Math.max(1,e-p+1);double obv=0,first=0;boolean set=false;for(int i=st;i<=e;i++){obv+=Math.signum(x.get(i).close-x.get(i-1).close)*x.get(i).volume;if(!set){first=obv;set=true;}}double avgVol=0;for(int i=st;i<=e;i++)avgVol+=x.get(i).volume;avgVol/=Math.max(1,e-st+1);return avgVol==0?0:(obv-first)/(avgVol*Math.max(1,e-st));}
    private static double williamsR(List<MarketDataService.Candle>x,int p,int e){double h=highest(x,p,e),l=lowest(x,p,e);return h==l?-50:-100*(h-x.get(e).close)/(h-l);}
    private static double donchian(List<MarketDataService.Candle>x,int p,int e){double h=highest(x,p,e),l=lowest(x,p,e);return h==l?.5:(x.get(e).close-l)/(h-l);}
    private static double highest(List<MarketDataService.Candle>x,int p,int e){int st=Math.max(0,e-p+1);double v=-Double.MAX_VALUE;for(int i=st;i<=e;i++)v=Math.max(v,x.get(i).high);return v;}
    private static double lowest(List<MarketDataService.Candle>x,int p,int e){int st=Math.max(0,e-p+1);double v=Double.MAX_VALUE;for(int i=st;i<=e;i++)v=Math.min(v,x.get(i).low);return v;}
}
