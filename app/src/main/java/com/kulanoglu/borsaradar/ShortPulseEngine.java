package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/**
 * BorsaPulse-2W: kısa vadeli canlı karar motoru.
 * Amaç yalnız gerçekleşmiş yükselişi kovalamak değil, kırılım hazırlığını da yakalamaktır.
 */
public final class ShortPulseEngine {
    private ShortPulseEngine() {}

    public static final class Result {
        public double price, changePct, score, confidence, relativeVolume, atrPct, stopReference;
        public double earlyBreakScore, stretchPct;
        public boolean earlyBreakout, breakout, chaseRisk;
        public String recommendation, explanation, horizonText, momentumText, flowText, trendText, phaseText;
    }

    public static Result analyze(List<MarketDataService.Candle> x) {
        if(x==null || x.size()<15) throw new IllegalArgumentException("En az 15 işlem günü gerekli");
        int end=x.size()-1;
        Result r=new Result();
        r.price=x.get(end).close;
        r.changePct=x.get(end-1).close==0?0:(x.get(end).close/x.get(end-1).close-1)*100;

        double e3=ema(x,3,end), e5=ema(x,5,end), e8=ema(x,8,end), e12=ema(x,12,end), e20=ema(x,20,end);
        double rsi7=rsi(x,7,end), roc3=roc(x,3,end), roc5=roc(x,5,end);
        double prevRoc3=end>=6?roc(x,3,end-3):0;
        double accel=roc3-prevRoc3;
        double rv=relVol(x,10,end), atr7=atr(x,7,end), atr14=atr(x,14,end);
        double eff=efficiency(x,10,end), vp=volumePressure(x,10,end), cmf=cmf(x,12,end);
        r.relativeVolume=rv; r.atrPct=r.price==0?0:atr7/r.price*100;

        double hi10=highestHigh(x,10,end-1);
        double hi20=highestHigh(x,20,end-1);
        boolean breakout=r.price>hi20;
        boolean nearBreak=hi20>0 && !breakout && (hi20-r.price)/hi20<=0.030;
        boolean emaStack=e3>e5 && e5>e8 && e8>=e12*0.995;
        boolean compression=atr14>0 && atr7/atr14<=0.92;
        boolean constructiveFlow=cmf>0.02 || vp>0.06;
        boolean acceleration=accel>0.35 && roc3>-0.5;
        boolean tightToTrend=e20>0 && r.price>=e20*0.985 && r.price<=e20*1.085;
        boolean miniBreak=hi10>0 && r.price>hi10 && !breakout;

        MarketDataService.Candle last=x.get(end);
        double range=Math.max(1e-9,last.high-last.low);
        double upperWick=last.high-Math.max(last.open,last.close);
        r.stretchPct=e20==0?0:(r.price/e20-1)*100;
        boolean stretched=r.stretchPct>10.5 || rsi7>77;
        boolean trap=(upperWick/range>0.58 && rv>1.35) || (rsi7>80 && breakout);

        double early=0;
        if(nearBreak) early+=1.25;
        if(miniBreak) early+=0.75;
        if(emaStack) early+=1.0;
        if(compression) early+=0.9;
        if(constructiveFlow) early+=0.9;
        if(acceleration) early+=0.9;
        if(rv>=1.05 && rv<=2.4) early+=0.65;
        if(tightToTrend) early+=0.65;
        if(stretched) early-=1.6;
        if(trap) early-=2.0;
        r.earlyBreakScore=early;
        r.earlyBreakout=!breakout && early>=4.0;
        r.breakout=breakout;
        r.chaseRisk=stretched || trap;

        double s=0;
        if(e3>e5)s+=0.7;else s-=0.7;
        if(e5>e8)s+=0.9;else s-=0.9;
        if(e8>e12)s+=0.7;else s-=0.7;
        if(rsi7>=48&&rsi7<=68)s+=0.8; else if(rsi7>76)s-=1.3; else if(rsi7<34)s-=0.6;
        if(roc3>0.4)s+=0.55; else if(roc3<-1.5)s-=0.7;
        if(roc5>0.8)s+=0.65; else if(roc5<-2.0)s-=0.9;
        if(rv>1.05)s+=0.65; else if(rv<0.65)s-=0.4;
        if(cmf>0.04)s+=0.75; else if(cmf<-0.08)s-=0.8;
        if(vp>0.06)s+=0.65; else if(vp<-0.10)s-=0.7;
        if(eff>0.22)s+=0.55; else if(eff<-0.25)s-=0.7;
        // Gerçekleşmiş kırılıma daha az puan; hazırlık evresine bonus.
        if(breakout && !stretched)s+=0.45;
        if(r.earlyBreakout)s+=1.35;
        else if(nearBreak)s+=0.55;
        if(acceleration)s+=0.45;
        if(stretched)s-=1.45;
        if(trap)s-=2.2;
        r.score=s;

        if(trap || (breakout && stretched)) r.recommendation="KOVALAMA / BEKLE";
        else if(r.earlyBreakout && s>=3.0) r.recommendation="ERKEN AL / KIRILIM ÖNCESİ";
        else if(s>=4.8 && !stretched) r.recommendation="AL";
        else if(s>=2.7) r.recommendation="KADEMELİ AL / İZLE";
        else if(s<=-2.8) r.recommendation="SAT / RİSKİ AZALT";
        else if(s<=-1.3) r.recommendation="ZAYIF / BEKLE";
        else r.recommendation="TUT / NÖTR";

        r.confidence=Math.max(30,Math.min(92,46+Math.abs(s)*5.4+Math.max(0,early)*3.0+(rv>1.05?3:0)-(stretched?7:0)-(trap?12:0)));
        if(r.earlyBreakout)r.horizonText="kırılım hazırlığı • 1–5 işlem günü";
        else if(s>=4.8)r.horizonText="1–3 işlem günü";
        else if(s>=2.7)r.horizonText="3–7 işlem günü";
        else r.horizonText="en fazla 10 işlem günü";
        r.stopReference=Math.max(0,r.price-1.8*atr7);
        r.momentumText=acceleration?"ivmeleniyor":roc3>0&&roc5>0?"pozitif":roc3<0&&roc5<0?"negatif":"karışık";
        r.flowText=cmf>0.04&&vp>0.05?"para/hacim girişi":cmf<-0.08&&vp<-0.08?"para/hacim çıkışı":"nötr";
        r.trendText=emaStack?"yukarı":e3<e5&&e5<e8?"aşağı":"yatay";
        r.phaseText=r.earlyBreakout?"KIRILIM HAZIRLIĞI":breakout?(stretched?"GEÇ / UZAMIŞ":"KIRILIM"):(nearBreak?"SIKIŞMA / EŞİĞE YAKIN":"NORMAL");
        r.explanation=String.format(Locale.US,
                "%s • erken %.1f/6 • EMA20 uzaklık %.1f%% • RSI7 %.1f • ROC3 %.1f%% (ivme %.1f) • RelVol x%.2f • CMF %.2f • ATR sıkışma %.2f%s",
                r.phaseText,early,r.stretchPct,rsi7,roc3,accel,rv,cmf,atr14==0?1:atr7/atr14,trap?" • TUZAK RİSKİ":"");
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
