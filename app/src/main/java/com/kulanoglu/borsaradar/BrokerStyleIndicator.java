package com.kulanoglu.borsaradar;

import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class BrokerStyleIndicator {
    private BrokerStyleIndicator(){}
    public static final class Plan {
        public final String horizon; public final double entry,target1,target2,stop,riskPct,rewardPct,rr;
        Plan(String h,double e,double t1,double t2,double s){horizon=h;entry=e;target1=t1;target2=t2;stop=s;riskPct=(1d-s/e)*100d;rewardPct=(t1/e-1d)*100d;rr=riskPct>0?rewardPct/riskPct:Double.NaN;}
        public String summary(String cur){return String.format(Locale.US,"%s: giriş %.2f • hedef %.2f / %.2f (%+.1f%%) • stop %.2f (-%.1f%%) • R:R %.1f",horizon,entry,target1,target2,rewardPct,stop,riskPct,rr)+(cur==null||cur.isEmpty()?"":" "+cur);}
    }
    public static final class Result {
        public final double zScore,z1m,z3m,z12m,beta,sma5,sma20,vsSma5Pct,vsSma20Pct,rangePos5,volumeRatio,atrPct; public final boolean extended; public final String setup; public final int score; public final Plan daily,weekly;
        Result(double z,double z1,double z3,double z12,double b,double s5,double s20,double v5,double v20,double rp,double vr,double atr,boolean ext,String setup,int score,Plan d,Plan w){zScore=z;z1m=z1;z3m=z3;z12m=z12;beta=b;sma5=s5;sma20=s20;vsSma5Pct=v5;vsSma20Pct=v20;rangePos5=rp;volumeRatio=vr;atrPct=atr;extended=ext;this.setup=setup;this.score=score;daily=d;weekly=w;}
        public String summary(){return String.format(Locale.US,"Kurum yöntemi: %s • Z %.2f • Beta %s • SMA5 %+.1f%% • SMA20 %+.1f%% • Skor %d",setup,zScore,Double.isNaN(beta)?"—":String.format(Locale.US,"%.2f",beta),vsSma5Pct,vsSma20Pct,score);}
    }
    public static Result analyze(List<MarketDataService.Candle>d,List<MarketDataService.Candle>index){
        if(d==null||d.size()<21)return null;int n=d.size();double last=d.get(n-1).close;if(!(last>0))return null;
        int[] w={21,63,252};double[] z=new double[3];double zs=0;int zc=0;
        for(int i=0;i<3;i++){z[i]=Double.NaN;if(n<w[i])continue;double m=0;for(int k=n-w[i];k<n;k++)m+=d.get(k).close;m/=w[i];double v=0;for(int k=n-w[i];k<n;k++){double x=d.get(k).close-m;v+=x*x;}double sd=Math.sqrt(v/w[i]);if(sd>0){z[i]=(last-m)/sd;zs+=z[i];zc++;}}
        double zAvg=zc==0?0:zs/zc,s5=sma(d,5),s20=sma(d,20),vs5=(last/s5-1)*100,vs20=(last/s20-1)*100;
        double hi5=-Double.MAX_VALUE,lo5=Double.MAX_VALUE;for(int k=n-5;k<n;k++){hi5=Math.max(hi5,d.get(k).high);lo5=Math.min(lo5,d.get(k).low);}double rp=hi5>lo5?(last-lo5)/(hi5-lo5):.5;
        double vavg=0;for(int k=n-20;k<n;k++)vavg+=d.get(k).volume;vavg/=20;double vr=vavg>0?d.get(n-1).volume/vavg:Double.NaN,atrPct=atrPct(d,14),beta=beta(d,index);
        boolean extended=zAvg>1;String setup=extended?"UZAMIŞ / KOVALAMA":vs20<-1&&vs5>=0?"DÖNÜŞ / GERİ ÇEKİLME":vs5>=0&&vs20>=0?"TREND DEVAMI":vs5<0&&vs20<0?"ZAYIF":"NÖTR";
        int score=50;score+=Math.abs(zAvg)<=.8?15:zAvg>1.5?-20:zAvg>1?-8:0;score+=vs5>=0?10:-10;score+=Math.abs(vs20)<=5?10:vs20>5?-5:-10;score+=(rp>=.2&&rp<=.95)?5:0;score=Math.max(0,Math.min(100,score));
        double ds=clamp(1.1*atrPct,1,2.6),ws=clamp(1.85*ds,1.8,4.5);return new Result(zAvg,z[0],z[1],z[2],beta,s5,s20,vs5,vs20,rp,vr,atrPct,extended,setup,score,plan("Günlük",last,ds,2.7),plan("Haftalık",last,ws,2.45));
    }
    private static Plan plan(String h,double e,double sp,double rr){double s=e*(1-sp/100),t1=e*(1+sp*rr/100),t2=t1+.15*(e-s);return new Plan(h,e,t1,t2,s);}
    private static double clamp(double v,double lo,double hi){return Math.max(lo,Math.min(hi,v));}
    private static double sma(List<MarketDataService.Candle>d,int p){double s=0;int n=d.size();for(int i=n-p;i<n;i++)s+=d.get(i).close;return s/p;}
    private static double atrPct(List<MarketDataService.Candle>d,int p){int n=d.size(),m=Math.min(p,n-1);double tr=0;for(int i=n-m;i<n;i++){MarketDataService.Candle c=d.get(i),pr=d.get(i-1);tr+=Math.max(c.high-c.low,Math.max(Math.abs(c.high-pr.close),Math.abs(c.low-pr.close)));}double last=d.get(n-1).close;return last>0?(tr/m)/last*100:1.5;}
    private static double beta(List<MarketDataService.Candle>d,List<MarketDataService.Candle>idx){if(idx==null||idx.size()<31)return Double.NaN;Map<Long,Double>im=new HashMap<>();for(MarketDataService.Candle c:idx)im.put(c.time/86400L,c.close);java.util.ArrayList<double[]>p=new java.util.ArrayList<>();Double pi=null,ps=null;for(MarketDataService.Candle c:d){Double ic=im.get(c.time/86400L);if(ic==null)continue;if(pi!=null&&ps!=null&&pi>0&&ps>0)p.add(new double[]{c.close/ps-1,ic/pi-1});pi=ic;ps=c.close;}int from=Math.max(0,p.size()-252),m=p.size()-from;if(m<30)return Double.NaN;double ms=0,mi=0;for(int i=from;i<p.size();i++){ms+=p.get(i)[0];mi+=p.get(i)[1];}ms/=m;mi/=m;double cov=0,var=0;for(int i=from;i<p.size();i++){double a=p.get(i)[0]-ms,b=p.get(i)[1]-mi;cov+=a*b;var+=b*b;}return var>0?cov/var:Double.NaN;}
}