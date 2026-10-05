package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/**
 * Kırılma zinciri: hem yukarı kırılımı hem aşağı kırılımı (düşüş) aşamalı olarak öngörmeye çalışır.
 *
 *  1. SIKIŞMA    : Bollinger bant genişliği yüzdeliği, ATR(5)/ATR(20) daralması, 10/40 bar aralık oranı
 *  2. AKIŞ       : CMF(20), OBV eğimi, yükselen/düşen gün hacim dengesi  (para girişi mi çıkışı mı)
 *  3. YÖN        : EMA20 eğimi, fiyatın EMA50'ye uzaklığı, RSI, MACD histogramı, RSI ıraksaması
 *  4. TEYİT/TUZAK: 20 barlık kutunun dışında hacimli kapanış; kutu dışına taşıp içeri dönen mum tuzaktır
 *
 * Aşamalar: 0 SAKİN • 1 SIKIŞMA • 2 HAZIRLIK (yön belli) • 3 TETİK YAKIN / hacimsiz deneme • 4 KIRILDI (hacim teyitli).
 * backtest(): aynı kuralı hissenin KENDİ geçmişinde sınar ve rastgele bir günün başarı oranıyla kıyaslar;
 * böylece göstergenin o hissede gerçekten bir üstünlüğü olup olmadığı görünür. Eşikler genel kabul görmüş
 * değerlerdir, BIST verisine göre optimize EDİLMEDİ. Tek başına AL/SAT üretmez.
 */
public final class BreakoutChain {
    private BreakoutChain(){}

    public static final int MIN_BARS=70;

    public static final class Result {
        public final int stage; public final String stageName, dir;
        public final double squeeze, flow, direction, combined, readiness, triggerUp, triggerDown, stopRef, targetRef, relVol, atrPct;
        public final boolean confirmed, trap;
        Result(int st,String name,String dir,double sq,double fl,double di,double comb,double rd,double tu,double td,double stop,double tgt,double rv,double atrPct,boolean conf,boolean trap){
            stage=st;stageName=name;this.dir=dir;squeeze=sq;flow=fl;direction=di;combined=comb;readiness=rd;triggerUp=tu;triggerDown=td;stopRef=stop;targetRef=tgt;relVol=rv;this.atrPct=atrPct;confirmed=conf;this.trap=trap;
        }
        public String summary(){ return String.format(Locale.US,"Kırılma zinciri: %s • sıkışma %.0f • akış %+.0f • yön %+.0f • hazırlık %.0f • tetik ▲%.2f / ▼%.2f",stageName,squeeze,flow,direction,readiness,triggerUp,triggerDown); }
        public String levels(){ if(Double.isNaN(stopRef))return ""; return String.format(Locale.US,"Seviye: stop %.2f • ölçülü hedef %.2f (kutu yüksekliği kadar)",stopRef,targetRef); }
    }

    public static final class Backtest {
        public int signals,hits,upSignals,upHits,downSignals,downHits,bars;
        public double hitRate=Double.NaN,baselineRate=Double.NaN,edge=Double.NaN;
        public String summary(){
            if(signals==0)return "Geçmiş sınama: bu hissede tetik aşamasına ulaşan sinyal yok.";
            String s=String.format(Locale.GERMANY,"Geçmiş sınama (bu hisse, %d gün): %d sinyal • 5 günde 1×ATR yönde gitti: %%%.0f • rastgele gün: %%%.0f • fark %+.0f puan",bars,signals,hitRate*100,baselineRate*100,edge*100);
            return signals<8?s+" • örnek az, güvenilmez":s;
        }
    }
    private static final class S { int n; double[] atr5,atr14,atr20,bbw,cmf20,obv,ema20,ema50,hist,rsi,volAvgPrev20,upVolP,dnVolP,volP; }
    private static S prep(List<MarketDataService.Candle> x){
        int n=x.size();S s=new S();s.n=n; double[] tr=new double[n],trp=new double[n+1];
        s.bbw=new double[n];s.cmf20=new double[n];s.obv=new double[n];s.ema20=new double[n];s.ema50=new double[n];s.hist=new double[n];s.rsi=new double[n];
        s.volAvgPrev20=new double[n];s.upVolP=new double[n+1];s.dnVolP=new double[n+1];s.volP=new double[n+1]; double[] mfvP=new double[n+1];
        for(int i=0;i<n;i++){ MarketDataService.Candle c=x.get(i); tr[i]=i==0?c.high-c.low:Math.max(c.high-c.low,Math.max(Math.abs(c.high-x.get(i-1).close),Math.abs(c.low-x.get(i-1).close))); trp[i+1]=trp[i]+tr[i]; double den=c.high-c.low,mfm=den>0?((c.close-c.low)-(c.high-c.close))/den:0; mfvP[i+1]=mfvP[i]+mfm*c.volume;s.volP[i+1]=s.volP[i]+c.volume; boolean up=i>0&&c.close>x.get(i-1).close,dn=i>0&&c.close<x.get(i-1).close; s.upVolP[i+1]=s.upVolP[i]+(up?c.volume:0);s.dnVolP[i+1]=s.dnVolP[i]+(dn?c.volume:0);s.obv[i]=i==0?0:s.obv[i-1]+(up?c.volume:(dn?-c.volume:0)); }
        s.atr5=new double[n];s.atr14=new double[n];s.atr20=new double[n]; for(int i=0;i<n;i++){s.atr5[i]=avgTr(trp,i,5);s.atr14[i]=avgTr(trp,i,14);s.atr20[i]=avgTr(trp,i,20);}
        for(int i=0;i<n;i++){ if(i>=19){double m=0;for(int k=i-19;k<=i;k++)m+=x.get(k).close;m/=20;double v=0;for(int k=i-19;k<=i;k++){double d=x.get(k).close-m;v+=d*d;}s.bbw[i]=m>0?4d*Math.sqrt(v/20)/m:Double.NaN;}else s.bbw[i]=Double.NaN; int a=Math.max(0,i-19);double vv=s.volP[i+1]-s.volP[a];s.cmf20[i]=vv>0?(mfvP[i+1]-mfvP[a])/vv:0; if(i>=20)s.volAvgPrev20[i]=(s.volP[i]-s.volP[i-20])/20d;else s.volAvgPrev20[i]=Double.NaN; }
        double e12=x.get(0).close,e26=e12,sig=0;s.ema20[0]=e12;s.ema50[0]=e12;
        for(int i=0;i<n;i++){ double c=x.get(i).close; if(i>0){e12=c*(2d/13)+e12*(1-2d/13);e26=c*(2d/27)+e26*(1-2d/27);s.ema20[i]=c*(2d/21)+s.ema20[i-1]*(1-2d/21);s.ema50[i]=c*(2d/51)+s.ema50[i-1]*(1-2d/51);} double macd=e12-e26;sig=i==0?macd:macd*(2d/10)+sig*(1-2d/10);s.hist[i]=macd-sig; }
        double ag=0,al=0;s.rsi[0]=50; for(int i=1;i<n;i++){double ch=x.get(i).close-x.get(i-1).close,g=Math.max(ch,0),l=Math.max(-ch,0);if(i<=14){ag+=g/14;al+=l/14;}else{ag=(ag*13+g)/14;al=(al*13+l)/14;}s.rsi[i]=i<14?50:(al==0?100:100-100/(1+ag/al));} return s;
    }
    private static double avgTr(double[] trp,int i,int p){int a=Math.max(0,i-p+1);return (trp[i+1]-trp[a])/(i-a+1);}
    private static double clamp(double v,double lo,double hi){return Math.max(lo,Math.min(hi,v));}
    private static double maxHigh(List<MarketDataService.Candle> x,int a,int b){double m=-Double.MAX_VALUE;for(int i=Math.max(0,a);i<=b;i++)m=Math.max(m,x.get(i).high);return m;}
    private static double minLow(List<MarketDataService.Candle> x,int a,int b){double m=Double.MAX_VALUE;for(int i=Math.max(0,a);i<=b;i++)m=Math.min(m,x.get(i).low);return m;}
    public static Result analyze(List<MarketDataService.Candle> x){if(x==null||x.size()<MIN_BARS)return null;return at(x,prep(x),x.size()-1);}
    private static Result at(List<MarketDataService.Candle> x,S s,int e){
        if(e<60)return null; MarketDataService.Candle c=x.get(e);double close=c.close;if(!(close>0))return null; double atr=Math.max(s.atr14[e],close*0.001);
        int from=Math.max(19,e-119),cnt=0,le=0;for(int k=from;k<=e;k++){if(!Double.isNaN(s.bbw[k])){cnt++;if(s.bbw[k]<=s.bbw[e])le++;}} double bbScore=cnt>0?100d*(1d-(double)le/cnt)+100d/Math.max(cnt,1):0;bbScore=clamp(bbScore,0,100); double atrRatio=s.atr20[e]>0?s.atr5[e]/s.atr20[e]:1d,atrScore=clamp((1d-atrRatio)/0.4d,0,1)*100d; double r10=maxHigh(x,e-9,e)-minLow(x,e-9,e),r40=maxHigh(x,e-39,e)-minLow(x,e-39,e); double rangeScore=r40>0?clamp((1d-r10/r40)/0.6d,0,1)*100d:0; double squeeze=0.5*bbScore+0.3*atrScore+0.2*rangeScore;
        double cmfS=clamp(s.cmf20[e]*250d,-100,100);double v20=s.volP[e+1]-s.volP[e-19];double obvS=v20>0?clamp((s.obv[e]-s.obv[e-20])/v20*100d,-100,100):0;double up=s.upVolP[e+1]-s.upVolP[e-19],dn=s.dnVolP[e+1]-s.dnVolP[e-19];double udS=(up+dn)>0?(up-dn)/(up+dn)*100d:0;double flow=(cmfS+obvS+udS)/3d;
        double slope=clamp((s.ema20[e]-s.ema20[e-5])/atr*60d,-100,100);double pos=clamp((close-s.ema50[e])/atr*25d,-100,100);double rsiS=clamp((s.rsi[e]-50d)*2d,-100,100);double macdS=(s.hist[e]>0?30:-30)+(s.hist[e]>s.hist[e-3]?30:-30);double div=0; double lowNew=minLow(x,e-19,e),lowOld=minLow(x,e-39,e-20),hiNew=maxHigh(x,e-19,e),hiOld=maxHigh(x,e-39,e-20);double rMinNew=100,rMinOld=100,rMaxNew=0,rMaxOld=0;for(int k=e-19;k<=e;k++){rMinNew=Math.min(rMinNew,s.rsi[k]);rMaxNew=Math.max(rMaxNew,s.rsi[k]);}for(int k=e-39;k<=e-20;k++){rMinOld=Math.min(rMinOld,s.rsi[k]);rMaxOld=Math.max(rMaxOld,s.rsi[k]);}if(lowNew<lowOld*0.998&&rMinNew>rMinOld+3)div=30;else if(hiNew>hiOld*1.002&&rMaxNew<rMaxOld-3)div=-30;double direction=clamp((slope+pos+rsiS+macdS)/4d+div,-100,100);double combined=0.5*flow+0.5*direction;
        double hiN=maxHigh(x,e-20,e-1),loN=minLow(x,e-20,e-1),boxH=hiN-loN;double vAvg=s.volAvgPrev20[e];double rv=vAvg>0?c.volume/vAvg:Double.NaN;boolean volOk=!Double.isNaN(rv)&&rv>=1.3d;double rng=c.high-c.low,barPos=rng>0?(close-c.low)/rng:0.5;boolean confUp=close>hiN&&volOk&&barPos>=0.6,confDn=close<loN&&volOk&&barPos<=0.4;boolean weakUp=close>hiN&&!confUp,weakDn=close<loN&&!confDn;boolean trapUp=c.high>hiN&&close<=hiN&&rng>0&&(c.high-close)/rng>=0.5;boolean trapDn=c.low<loN&&close>=loN&&rng>0&&(close-c.low)/rng>=0.5;
        String dir=combined>=20?"YUKARI":(combined<=-20?"AŞAĞI":"NÖTR");int stage;String name;boolean conf=false,trap=false;if(confUp){stage=4;dir="YUKARI";name="KIRILDI ▲ (hacim teyitli)";conf=true;}else if(confDn){stage=4;dir="AŞAĞI";name="KIRILDI ▼ (hacim teyitli)";conf=true;}else if(weakUp){stage=3;dir="YUKARI";name="KIRILIM DENEMESİ ▲ (hacimsiz, zayıf)";}else if(weakDn){stage=3;dir="AŞAĞI";name="KIRILIM DENEMESİ ▼ (hacimsiz, zayıf)";}else if(trapUp){stage=0;name="TUZAK ▲ (başarısız yukarı kırılım)";trap=true;}else if(trapDn){stage=0;name="TUZAK ▼ (başarısız aşağı kırılım)";trap=true;}else if(squeeze>=60&&!dir.equals("NÖTR")&&Math.abs(flow)>=20&&Math.signum(flow)==Math.signum(direction)){double dist=(dir.equals("YUKARI")?hiN-close:close-loN)/atr;if(dist<=1d){stage=3;name="TETİK YAKIN "+(dir.equals("YUKARI")?"▲":"▼");}else{stage=2;name="HAZIRLIK "+(dir.equals("YUKARI")?"▲":"▼");}}else if(squeeze>=60){stage=1;name="SIKIŞMA (yön belirsiz)";}else{stage=0;name="SAKİN";}
        double prox=0;if(!dir.equals("NÖTR")){double dist=stage==4?0:Math.max(0,(dir.equals("YUKARI")?hiN-close:close-loN)/atr);prox=100d*clamp(1d-dist/2d,0,1);}double readiness=trap?Math.min(20,0.3*squeeze):clamp(0.45*squeeze+0.35*Math.abs(combined)+0.20*prox,0,100);double stop=Double.NaN,tgt=Double.NaN;if(dir.equals("YUKARI")){stop=Math.max(loN,hiN-2d*atr);tgt=hiN+boxH;}else if(dir.equals("AŞAĞI")){stop=Math.min(hiN,loN+2d*atr);tgt=loN-boxH;}return new Result(stage,name,dir,squeeze,flow,direction,combined,readiness,hiN,loN,stop,tgt,rv,atr/close*100d,conf,trap);
    }
    private static final int HORIZON=5;
    private static boolean reaches(List<MarketDataService.Candle> x,int e,double thr,boolean up){double base=x.get(e).close;double hi=base+thr,lo=base-thr;for(int j=e+1;j<=e+HORIZON&&j<x.size();j++){MarketDataService.Candle k=x.get(j);boolean h=k.high>=hi,l=k.low<=lo;if(h&&l)return false;if(up){if(h)return true;if(l)return false;}else{if(l)return true;if(h)return false;}}return false;}
    public static Backtest backtest(List<MarketDataService.Candle> x){Backtest b=new Backtest();if(x==null||x.size()<MIN_BARS+HORIZON+10)return b;S s=prep(x);int n=x.size(),last=n-1-HORIZON;int upBase=0,dnBase=0;int lastEvent=-100;for(int e=60;e<=last;e++){double thr=Math.max(s.atr14[e],x.get(e).close*0.001);b.bars++;boolean upHit=reaches(x,e,thr,true),dnHit=reaches(x,e,thr,false);if(upHit)upBase++;if(dnHit)dnBase++;Result r=at(x,s,e);if(r==null||r.stage<3||r.dir.equals("NÖTR")||e-lastEvent<HORIZON)continue;lastEvent=e;b.signals++;if(r.dir.equals("YUKARI")){b.upSignals++;if(upHit){b.upHits++;b.hits++;}}else{b.downSignals++;if(dnHit){b.downHits++;b.hits++;}}}if(b.signals>0&&b.bars>0){b.hitRate=(double)b.hits/b.signals;double bu=(double)upBase/b.bars,bd=(double)dnBase/b.bars;b.baselineRate=(b.upSignals*bu+b.downSignals*bd)/b.signals;b.edge=b.hitRate-b.baselineRate;}return b;}
}
