package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/**
 * BorsaPulse-2W: canlı karar motoru. En fazla son 12 işlem gününe ağırlık verir.
 * Uzun tarih telefon tarafında tekrar tekrar indirilmez.
 */
public final class ShortPulseEngine {
    private ShortPulseEngine() {}

    public static final class Result {
        public double price, changePct, score, confidence, relativeVolume, atrPct, stopReference;
        public String recommendation, explanation, horizonText, momentumText, flowText, trendText;
    }

    public static Result analyze(List<MarketDataService.Candle> x) {
        if(x==null || x.size()<10) throw new IllegalArgumentException("En az 10 işlem günü gerekli");
        int end=x.size()-1;
        Result r=new Result();
        r.price=x.get(end).close;
        r.changePct=x.get(end-1).close==0?0:(x.get(end).close/x.get(end-1).close-1)*100;

        double e3=ema(x,3,end), e5=ema(x,5,end), e8=ema(x,8,end), e12=ema(x,12,end);
        double rsi7=rsi(x,7,end), roc3=roc(x,3,end), roc5=roc(x,5,end);
        double rv=relVol(x,8,end), atr=atr(x,7,end), eff=efficiency(x,10,end), vp=volumePressure(x,10,end);
        double cmf=cmf(x,10,end);
        r.relativeVolume=rv; r.atrPct=r.price==0?0:atr/r.price*100;

        double hi=highestHigh(x,10,end-1);
        boolean breakout=r.price>hi;
        boolean nearBreak=hi>0 && !breakout && (hi-r.price)/hi<=0.018;
        MarketDataService.Candle last=x.get(end);
        double range=Math.max(1e-9,last.high-last.low);
        double upperWick=last.high-Math.max(last.open,last.close);
        boolean trap=(upperWick/range>0.58 && rv>1.35) || (rsi7>79 && breakout);

        double s=0;
        if(e3>e5)s+=1.0;else s-=0.8;
        if(e5>e8)s+=1.2;else s-=1.0;
        if(e8>e12)s+=1.0;else s-=0.8;
        if(rsi7>=52&&rsi7<=72)s+=1.0; else if(rsi7>78)s-=1.2; else if(rsi7<34)s-=0.7;
        if(roc3>1.2)s+=0.8; else if(roc3<-1.2)s-=0.8;
        if(roc5>2.0)s+=1.0; else if(roc5<-2.0)s-=1.0;
        if(rv>1.20)s+=1.0; else if(rv<0.65)s-=0.5;
        if(cmf>0.08)s+=0.9; else if(cmf<-0.08)s-=0.9;
        if(vp>0.10)s+=0.8; else if(vp<-0.10)s-=0.8;
        if(eff>0.30)s+=0.8; else if(eff<-0.25)s-=0.8;
        if(breakout)s+=1.1; else if(nearBreak)s+=0.5;
        if(last.close>last.open)s+=0.35; else s-=0.20;
        if(trap)s-=2.4;
        r.score=s;

        if(trap) r.recommendation="KOVALAMA / BEKLE";
        else if(s>=5.2) r.recommendation="AL";
        else if(s>=3.3) r.recommendation="KADEMELİ AL / İZLE";
        else if(s<=-3.0) r.recommendation="SAT / RİSKİ AZALT";
        else if(s<=-1.4) r.recommendation="ZAYIF / BEKLE";
        else r.recommendation="TUT / NÖTR";

        r.confidence=Math.max(30,Math.min(92,48+Math.abs(s)*5.8+(rv>1.2?5:0)+(Math.abs(eff)>.30?4:0)-(trap?12:0)));
        if(s>=5.2)r.horizonText="1–3 işlem günü"; else if(s>=3.3)r.horizonText="3–7 işlem günü"; else r.horizonText="en fazla 10 işlem günü";
        r.stopReference=Math.max(0,r.price-1.8*atr);
        r.momentumText=roc3>0&&roc5>0?"pozitif":roc3<0&&roc5<0?"negatif":"karışık";
        r.flowText=cmf>0.08&&vp>0.08?"para/hacim girişi":cmf<-0.08&&vp<-0.08?"para/hacim çıkışı":"nötr";
        r.trendText=e3>e5&&e5>e8?"yukarı":e3<e5&&e5<e8?"aşağı":"yatay";
        r.explanation=String.format(Locale.US,"EMA3/5/8 %s • RSI7 %.1f • ROC3 %.1f%% • ROC5 %.1f%% • RelVol x%.2f • CMF10 %.2f • hacim baskısı %.2f • trend verimi %.2f%s",
                r.trendText,rsi7,roc3,roc5,rv,cmf,vp,eff,trap?" • TUZAK RİSKİ":"");
        return r;
    }

    private static double ema(List<MarketDataService.Candle>x,int p,int end){int st=Math.max(0,end-p*3+1);double k=2.0/(p+1),e=x.get(st).close;for(int i=st+1;i<=end;i++)e=x.get(i).close*k+e*(1-k);return e;}
    private static double rsi(List<MarketDataService.Candle>x,int p,int end){if(end<p)return 50;double g=0,l=0;for(int i=end-p+1;i<=end;i++){double d=x.get(i).close-x.get(i-1).close;if(d>=0)g+=d;else l-=d;}return l==0?100:100-100/(1+(g/p)/(l/p));}
    private static double roc(List<MarketDataService.Candle>x,int p,int end){if(end<p)return 0;double a=x.get(end-p).close;return a==0?0:(x.get(end).close/a-1)*100;}
    private static double relVol(List<MarketDataService.Candle>x,int p,int end){int st=Math.max(0,end-p);double sum=0;int n=0;for(int i=st;i<end;i++){sum+=x.get(i).volume;n++;}double avg=n==0?0:sum/n;return avg<=0?1:x.get(end).volume/avg;}
    private static double atr(List<MarketDataService.Candle>x,int p,int end){int st=Math.max(1,end-p+1);double sum=0;int n=0;for(int i=st;i<=end;i++){MarketDataService.Candle c=x.get(i),pr=x.get(i-1);sum+=Math.max(c.high-c.low,Math.max(Math.abs(c.high-pr.close),Math.abs(c.low-pr.close)));n++;}return n==0?0:sum/n;}
    private static double cmf(List<MarketDataService.Candle>x,int p,int end){int st=Math.max(0,end-p+1);double mfv=0,v=0;for(int i=st;i<=end;i++){MarketDataService.Candle c=x.get(i);double den=c.high-c.low;double m=den==0?0:((c.close-c.low)-(c.high-c.close))/den;mfv+=m*c.volume;v+=c.volume;}return v==0?0:mfv/v;}
    private static double efficiency(List<MarketDataService.Candle>x,int p,int end){int st=Math.max(0,end-p);double path=0;for(int i=st+1;i<=end;i++)path+=Math.abs(x.get(i).close-x.get(i-1).close);return path==0?0:(x.get(end).close-x.get(st).close)/path;}
    private static double volumePressure(List<MarketDataService.Candle>x,int p,int end){int st=Math.max(1,end-p+1);double sig=0,tot=0;for(int i=st;i<=end;i++){double v=x.get(i).volume;sig+=Math.signum(x.get(i).close-x.get(i-1).close)*v;tot+=v;}return tot==0?0:sig/tot;}
    private static double highestHigh(List<MarketDataService.Candle>x,int p,int end){int st=Math.max(0,end-p+1);double m=-Double.MAX_VALUE;for(int i=st;i<=end;i++)m=Math.max(m,x.get(i).high);return m;}
}
