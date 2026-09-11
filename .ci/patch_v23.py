from pathlib import Path
import re

root=Path('build-v23/BorsaRadar')
pkg=root/'app/src/main/java/com/kulanoglu/borsaradar'

# Version bump
grad=root/'app/build.gradle'
g=grad.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 23',g)
g=re.sub(r'versionName\s+[\'\"][^\'\"]+[\'\"]','versionName "2.3.0"',g)
grad.write_text(g,encoding='utf-8')

# Live data service: normal phone use is limited to the most recent ~2 trading weeks.
market=r'''package com.kulanoglu.borsaradar;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;

public final class MarketDataService {
    private static final Object RATE_LOCK = new Object();
    private static long lastRequestAt = 0L;
    private MarketDataService() {}

    public static final class Candle {
        public final long time;
        public final double open, high, low, close, volume;
        public Candle(long time,double open,double high,double low,double close,double volume){
            this.time=time; this.open=open; this.high=high; this.low=low; this.close=close; this.volume=volume;
        }
    }

    public static List<Candle> fetchDaily(String bistSymbol,String ignoredRange) throws Exception {
        String symbol=bistSymbol.endsWith(".IS")?bistSymbol:bistSymbol+".IS";
        Exception last=null;
        String[] hosts={"query1.finance.yahoo.com","query2.finance.yahoo.com"};
        for(int attempt=0;attempt<4;attempt++){
            String url="https://"+hosts[attempt%hosts.length]+"/v8/finance/chart/"+symbol+
                    "?range=1mo&interval=1d&includePrePost=false&events=div%2Csplits";
            try{
                throttle();
                List<Candle> all=fetch(url);
                int from=Math.max(0,all.size()-12);
                return new ArrayList<>(all.subList(from,all.size()));
            }catch(Exception e){
                last=e;
                try{Thread.sleep(450L*(attempt+1));}catch(InterruptedException x){Thread.currentThread().interrupt();throw x;}
            }
        }
        throw last==null?new Exception("Veri alınamadı"):last;
    }

    private static void throttle() throws InterruptedException {
        synchronized(RATE_LOCK){
            long wait=190L-(System.currentTimeMillis()-lastRequestAt);
            if(wait>0) Thread.sleep(wait);
            lastRequestAt=System.currentTimeMillis();
        }
    }

    private static List<Candle> fetch(String address) throws Exception {
        HttpURLConnection conn=null;
        try{
            conn=(HttpURLConnection)new URL(address).openConnection();
            conn.setConnectTimeout(8000); conn.setReadTimeout(9000); conn.setRequestMethod("GET");
            conn.setRequestProperty("User-Agent","Mozilla/5.0 BorsaRadar/2.3");
            conn.setRequestProperty("Accept","application/json");
            int code=conn.getResponseCode();
            if(code<200||code>=300) throw new Exception("HTTP "+code);
            StringBuilder sb=new StringBuilder();
            try(BufferedReader br=new BufferedReader(new InputStreamReader(conn.getInputStream()))){
                String line; while((line=br.readLine())!=null) sb.append(line);
            }
            JSONObject root=new JSONObject(sb.toString());
            JSONObject chart=root.getJSONObject("chart");
            if(!chart.isNull("error")) throw new Exception("Veri kaynağı hatası");
            JSONArray result=chart.getJSONArray("result");
            if(result.length()==0) throw new Exception("Veri yok");
            JSONObject r=result.getJSONObject(0);
            JSONArray ts=r.getJSONArray("timestamp");
            JSONObject q=r.getJSONObject("indicators").getJSONArray("quote").getJSONObject(0);
            JSONArray o=q.getJSONArray("open"),h=q.getJSONArray("high"),l=q.getJSONArray("low"),c=q.getJSONArray("close"),v=q.getJSONArray("volume");
            List<Candle> out=new ArrayList<>();
            int n=Math.min(ts.length(),c.length());
            for(int i=0;i<n;i++){
                if(c.isNull(i)||h.isNull(i)||l.isNull(i)||o.isNull(i)) continue;
                double close=c.optDouble(i,Double.NaN),high=h.optDouble(i,Double.NaN),low=l.optDouble(i,Double.NaN),open=o.optDouble(i,Double.NaN);
                double volume=v.isNull(i)?0.0:v.optDouble(i,0.0);
                if(Double.isNaN(close)||Double.isNaN(high)||Double.isNaN(low)||Double.isNaN(open)) continue;
                out.add(new Candle(ts.getLong(i),open,high,low,close,volume));
            }
            if(out.size()<8) throw new Exception("Yetersiz veri: "+out.size()+" gün");
            return out;
        }finally{if(conn!=null) conn.disconnect();}
    }
}
'''
(pkg/'MarketDataService.java').write_text(market,encoding='utf-8')

# BorsaPulse-2W replaces long-horizon scoring while keeping Snapshot API compatible with the existing screens.
ind=r'''package com.kulanoglu.borsaradar;

import java.util.List;

public final class IndicatorEngine {
    private IndicatorEngine() {}
    public static final class Snapshot {
        public double close, ema20, ema50, rsi14, macd, macdSignal, atr14, cmf20, relVolume, bbWidth;
        public double cci20, stochastic14, adx14;
        public double trendEfficiency20, momentumAtr20, volumePressure20;
        public boolean breakout20, preBreakout, trendUp, volumeOk, trap;
        public int score;
        public String signal, reason;
    }

    public static Snapshot analyze(List<MarketDataService.Candle> x){
        Snapshot s=new Snapshot();
        int n=x.size();
        if(n==0){s.signal="NÖTR";s.reason="Veri yok";return s;}
        int end=n-1;
        s.close=x.get(end).close;
        // Compatibility names remain, but periods are intentionally short for a 1-2 week decision horizon.
        s.ema20=ema(x,3,end);      // fast trend
        s.ema50=ema(x,8,end);      // slow trend
        s.rsi14=rsi(x,5,end);
        double e3=ema(x,3,end), e8=ema(x,8,end);
        s.macd=e3-e8;
        s.macdSignal=emaDiffSignal(x,end);
        s.atr14=atr(x,5,end);
        s.cmf20=cmf(x,8,end);
        s.relVolume=relativeVolume(x,8,end);
        s.bbWidth=bollingerWidth(x,8,end);
        s.cci20=cci(x,8,end);
        s.stochastic14=stochastic(x,7,end);
        s.adx14=adx(x,7,end);
        s.trendEfficiency20=trendEfficiency(x,8,end);
        s.momentumAtr20=momentumAtr(x,5,end,s.atr14);
        s.volumePressure20=volumePressure(x,8,end);
        double highPrev=highestHigh(x,8,end-1);
        s.breakout20=end>0 && s.close>highPrev;
        double dist=highPrev>0?(highPrev-s.close)/highPrev:1;
        s.preBreakout=!s.breakout20&&dist>=0&&dist<=0.018&&s.relVolume>=1.0;
        s.trendUp=s.close>s.ema20&&s.ema20>s.ema50;
        s.volumeOk=s.relVolume>=1.12;
        MarketDataService.Candle last=x.get(end);
        double range=Math.max(0.0001,last.high-last.low);
        double upper=last.high-Math.max(last.open,last.close);
        s.trap=(upper/range>0.58&&s.relVolume>1.35)||(s.rsi14>82&&s.breakout20);

        double raw=0;
        if(s.trendUp) raw+=2.2; else if(s.close<s.ema50) raw-=1.8;
        if(s.rsi14>=52&&s.rsi14<=72) raw+=1.2; else if(s.rsi14>82) raw-=1.3; else if(s.rsi14<32) raw-=0.8;
        if(s.macd>s.macdSignal) raw+=1.5; else raw-=1.0;
        if(s.cmf20>0.05) raw+=1.2; else if(s.cmf20<-0.08) raw-=1.1;
        if(s.relVolume>=1.20) raw+=1.2; else if(s.relVolume<0.70) raw-=0.5;
        if(s.breakout20) raw+=1.5; else if(s.preBreakout) raw+=0.8;
        if(s.trendEfficiency20>0.32) raw+=1.2; else if(s.trendEfficiency20<-0.25) raw-=1.0;
        if(s.momentumAtr20>0.85) raw+=1.2; else if(s.momentumAtr20<-0.85) raw-=1.0;
        if(s.volumePressure20>0.10) raw+=1.0; else if(s.volumePressure20<-0.10) raw-=0.8;
        if(s.stochastic14>=55&&s.stochastic14<=90) raw+=0.6; else if(s.stochastic14>95) raw-=0.5;
        if(s.trap) raw-=2.8;
        s.score=(int)Math.round(raw);

        if(s.trap&&s.score<7) s.signal="KOVALAMA";
        else if(s.score>=8) s.signal="AL";
        else if(s.score>=6) s.signal="ERKEN";
        else if(s.score>=3) s.signal="İZLE";
        else if(s.score<=-3) s.signal="SAT/RİSK";
        else s.signal="NÖTR";
        s.reason="BorsaPulse-2W "+s.score+" • RSI5 "+fmt(s.rsi14)+" • RVOL8 "+fmt(s.relVolume)+" • CMF8 "+fmt(s.cmf20)+" • TrendVerim8 "+fmt(s.trendEfficiency20)+" • ATR-Mom5 "+fmt(s.momentumAtr20)+" • HacimBaskı8 "+fmt(s.volumePressure20);
        return s;
    }

    public static double ema(List<MarketDataService.Candle>x,int period,int end){if(x.isEmpty()||end<0)return Double.NaN;int start=Math.max(0,end-period*3+1);double k=2.0/(period+1.0),e=x.get(start).close;for(int i=start+1;i<=end;i++)e=x.get(i).close*k+e*(1-k);return e;}
    public static double rsi(List<MarketDataService.Candle>x,int period,int end){if(end<1)return 50;int start=Math.max(1,end-period+1);double g=0,l=0;int c=0;for(int i=start;i<=end;i++){double d=x.get(i).close-x.get(i-1).close;if(d>=0)g+=d;else l-=d;c++;}if(c==0)return 50;if(l==0)return 100;double rs=(g/c)/(l/c);return 100-100/(1+rs);}
    public static double atr(List<MarketDataService.Candle>x,int period,int end){if(end<1)return 0;int start=Math.max(1,end-period+1);double sum=0;int c=0;for(int i=start;i<=end;i++){MarketDataService.Candle a=x.get(i),p=x.get(i-1);sum+=Math.max(a.high-a.low,Math.max(Math.abs(a.high-p.close),Math.abs(a.low-p.close)));c++;}return c==0?0:sum/c;}
    public static double cmf(List<MarketDataService.Candle>x,int period,int end){int start=Math.max(0,end-period+1);double mfv=0,vol=0;for(int i=start;i<=end;i++){MarketDataService.Candle a=x.get(i);double den=a.high-a.low,m=den==0?0:((a.close-a.low)-(a.high-a.close))/den;mfv+=m*a.volume;vol+=a.volume;}return vol==0?0:mfv/vol;}
    public static double relativeVolume(List<MarketDataService.Candle>x,int period,int end){if(end<=0)return 1;int start=Math.max(0,end-period);double sum=0;int c=0;for(int i=start;i<end;i++){sum+=x.get(i).volume;c++;}double avg=c==0?0:sum/c;return avg<=0?1:x.get(end).volume/avg;}
    public static double bollingerWidth(List<MarketDataService.Candle>x,int period,int end){int start=Math.max(0,end-period+1),c=end-start+1;double m=0;for(int i=start;i<=end;i++)m+=x.get(i).close;m/=Math.max(1,c);double v=0;for(int i=start;i<=end;i++){double d=x.get(i).close-m;v+=d*d;}double sd=Math.sqrt(v/Math.max(1,c));return m==0?0:4*sd/m;}
    public static double cci(List<MarketDataService.Candle>x,int period,int end){int start=Math.max(0,end-period+1),c=end-start+1;double m=0;for(int i=start;i<=end;i++)m+=typ(x.get(i));m/=Math.max(1,c);double d=0;for(int i=start;i<=end;i++)d+=Math.abs(typ(x.get(i))-m);d/=Math.max(1,c);return d==0?0:(typ(x.get(end))-m)/(0.015*d);}
    public static double stochastic(List<MarketDataService.Candle>x,int period,int end){int start=Math.max(0,end-period+1);double h=-Double.MAX_VALUE,l=Double.MAX_VALUE;for(int i=start;i<=end;i++){h=Math.max(h,x.get(i).high);l=Math.min(l,x.get(i).low);}return h==l?50:100*(x.get(end).close-l)/(h-l);}
    public static double adx(List<MarketDataService.Candle>x,int period,int end){if(end<2)return 0;int start=Math.max(1,end-period+1);double tr=0,p=0,m=0;for(int i=start;i<=end;i++){MarketDataService.Candle a=x.get(i),b=x.get(i-1);tr+=Math.max(a.high-a.low,Math.max(Math.abs(a.high-b.close),Math.abs(a.low-b.close)));double up=a.high-b.high,dn=b.low-a.low;if(up>dn&&up>0)p+=up;if(dn>up&&dn>0)m+=dn;}if(tr==0)return 0;double pdi=100*p/tr,mdi=100*m/tr;return pdi+mdi==0?0:100*Math.abs(pdi-mdi)/(pdi+mdi);}
    public static double trendEfficiency(List<MarketDataService.Candle>x,int period,int end){int start=Math.max(0,end-period);double path=0;for(int i=start+1;i<=end;i++)path+=Math.abs(x.get(i).close-x.get(i-1).close);return path==0?0:(x.get(end).close-x.get(start).close)/path;}
    public static double momentumAtr(List<MarketDataService.Candle>x,int period,int end,double atr){int start=Math.max(0,end-period);return atr<=0?0:(x.get(end).close-x.get(start).close)/(atr*Math.sqrt(Math.max(1,period)));}
    public static double volumePressure(List<MarketDataService.Candle>x,int period,int end){int start=Math.max(1,end-period+1);double s=0,t=0;for(int i=start;i<=end;i++){double v=x.get(i).volume;s+=Math.signum(x.get(i).close-x.get(i-1).close)*v;t+=v;}return t==0?0:s/t;}
    private static double highestHigh(List<MarketDataService.Candle>x,int period,int end){if(end<0)return x.get(0).high;int start=Math.max(0,end-period+1);double m=-Double.MAX_VALUE;for(int i=start;i<=end;i++)m=Math.max(m,x.get(i).high);return m;}
    private static double emaDiffSignal(List<MarketDataService.Candle>x,int end){int start=Math.max(0,end-5);double e=0;int c=0;for(int i=start;i<=end;i++){e+=ema(x,3,i)-ema(x,8,i);c++;}return c==0?0:e/c;}
    private static double typ(MarketDataService.Candle c){return(c.high+c.low+c.close)/3.0;}
    public static String fmt(double x){return String.format(java.util.Locale.US,"%.2f",x);}
}
'''
(pkg/'IndicatorEngine.java').write_text(ind,encoding='utf-8')

# UI and wording patches: keep all existing portfolio/radar functionality, but make it shorter-horizon and more trader-like.
mp=pkg/'MainActivity.java'
m=mp.read_text(encoding='utf-8')
m=m.replace('1Y Backtest','Metod Testi')
m=m.replace('20 günlük kırılım','8 günlük kırılım')
m=m.replace('20 günlük hareketi','kısa dönem hareketini')
m=m.replace('BIST Radar','Tüm Borsa')
m=m.replace('3 Strateji','3 Plan')
m=m.replace('Portföyüm','PORTFÖY')
m=m.replace('TUPRS portföyde değerlendirilir, bağımsız radar taramasına alınmaz.','Portföy ayrı izlenir. Tavsiye yöntemi son 1–2 haftalık fiyat/hacim davranışına odaklanır.')
m=m.replace('Color.rgb(247, 249, 252)','Color.rgb(242, 245, 248)')
m=m.replace('private static final int NAVY = Color.rgb(11, 31, 58);','private static final int NAVY = Color.rgb(7, 45, 78);')
m=m.replace('private static final int RED = Color.rgb(200, 16, 46);','private static final int RED = Color.rgb(202, 33, 42);')
m=m.replace('private static final int GREEN = Color.rgb(0, 128, 96);','private static final int GREEN = Color.rgb(0, 145, 105);')
# remove phone-side long backtest action from portfolio card; historical research belongs in model development, not repeated downloads
m=m.replace('buttons.addView(bt, new LinearLayout.LayoutParams(0, -2, 1));','')
m=m.replace('bt.setOnClickListener(v -> runSingleBacktest(h.symbol));','')
# Emphasize custom method in explanations
m=m.replace('İndikatör uzlaşması:', 'BorsaPulse uzlaşması:')
m=m.replace('Teknik ayrıntı:', 'BorsaPulse ayrıntı:')
mp.write_text(m,encoding='utf-8')

print('v2.3 patch complete')
