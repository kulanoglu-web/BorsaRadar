package com.kulanoglu.borsaradar;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public final class MarketDataService {
    private static final Object RATE_LOCK=new Object();
    private static long lastRequestAt=0L;
    private static final Map<String,Cache> CACHE=new ConcurrentHashMap<>();
    private MarketDataService(){}

    public static final class Candle {
        public final long time; public final double open,high,low,close,volume;
        public final String symbol;
        public Candle(long time,double open,double high,double low,double close,double volume){this(time,open,high,low,close,volume,"");}
        public Candle(long time,double open,double high,double low,double close,double volume,String symbol){this.time=time;this.open=open;this.high=high;this.low=low;this.close=close;this.volume=volume;this.symbol=symbol==null?"":symbol;}
    }
    private static final class Cache { final long at; final List<Candle> data; Cache(long a,List<Candle>d){at=a;data=d;} }

    public static List<Candle> fetchDaily(String symbol,String range)throws Exception{
        return fetchSeries(symbol,range,"1d",0);
    }

    public static List<Candle> fetchSeries(String inputSymbol,String range,String interval,int maxPoints)throws Exception{
        String symbol=normalizeSymbol(inputSymbol);
        String key=symbol+"|"+range+"|"+interval; Cache c=CACHE.get(key); long now=System.currentTimeMillis();
        List<Candle> raw;
        if(c!=null && now-c.at<180_000L) raw=new ArrayList<>(c.data);
        else {
            Exception last=null;
            String[] hosts={"query1.finance.yahoo.com","query2.finance.yahoo.com"}; raw=null;
            for(int attempt=0;attempt<3;attempt++){
                String u="https://"+hosts[attempt%2]+"/v8/finance/chart/"+symbol+"?range="+range+"&interval="+interval+"&includePrePost=false&events=div%2Csplits";
                try{throttle();raw=fetch(u,symbol);CACHE.put(key,new Cache(now,raw));break;}catch(Exception e){last=e;try{Thread.sleep(350L*(attempt+1));}catch(InterruptedException ie){Thread.currentThread().interrupt();throw ie;}}
            }
            if(raw==null){ if(c!=null) raw=new ArrayList<>(c.data); else throw last==null?new Exception("Veri alınamadı"):last; }
        }
        if(maxPoints>0) return downsample(raw,maxPoints);
        return raw;
    }

    public static String normalizeSymbol(String input){
        if(input==null)return "";
        String s=input.trim().toUpperCase();
        // UI/portfolio market prefixes are routing hints, not Yahoo ticker syntax.
        // Examples: US:NVDA -> NVDA, DE:S92 -> S92.DE, BIST:THYAO -> THYAO.IS.
        if(s.startsWith("US:")||s.startsWith("USA:")||s.startsWith("NASDAQ:")||s.startsWith("NYSE:")){
            int k=s.indexOf(':'); return s.substring(k+1).trim();
        }
        if(s.startsWith("DE:")||s.startsWith("GER:")||s.startsWith("XETRA:")){
            int k=s.indexOf(':'); String code=s.substring(k+1).trim(); return code.endsWith(".DE")?code:code+".DE";
        }
        if(s.startsWith("BIST:")||s.startsWith("TR:")){
            int k=s.indexOf(':'); String code=s.substring(k+1).trim(); return code.endsWith(".IS")?code:code+".IS";
        }
        if(s.endsWith(".IS")||s.endsWith(".DE")||s.endsWith(".L")||s.endsWith(".PA")||s.contains("=")||s.startsWith("^"))return s;
        if(inUniverse(s,GlobalStockUniverse.USA))return s;
        if(inUniverse(s,GlobalStockUniverse.GERMANY))return s+".DE";
        return s+".IS";
    }

    public static boolean isGlobalSymbol(String input){
        if(input==null)return false;
        String s=input.trim().toUpperCase();
        if(s.startsWith("US:")||s.startsWith("USA:")||s.startsWith("NASDAQ:")||s.startsWith("NYSE:")||s.startsWith("DE:")||s.startsWith("GER:")||s.startsWith("XETRA:"))return true;
        if(s.startsWith("BIST:")||s.startsWith("TR:"))return false;
        if(s.endsWith(".DE")||s.endsWith(".L")||s.endsWith(".PA"))return true;
        if(s.endsWith(".IS"))return false;
        return inUniverse(s,GlobalStockUniverse.USA)||inUniverse(s,GlobalStockUniverse.GERMANY);
    }

    private static boolean inUniverse(String code,String[] entries){
        for(String e:entries)if(GlobalStockUniverse.code(e).equals(code))return true;
        return false;
    }

    public static List<Candle> aggregateHours(List<Candle> src,int hours){
        if(hours<=1)return new ArrayList<>(src);
        List<Candle> out=new ArrayList<>();
        for(int i=0;i<src.size();i+=hours){
            int end=Math.min(src.size(),i+hours); Candle first=src.get(i), last=src.get(end-1);
            double hi=first.high, lo=first.low, vol=0;
            for(int j=i;j<end;j++){Candle c=src.get(j);hi=Math.max(hi,c.high);lo=Math.min(lo,c.low);vol+=c.volume;}
            out.add(new Candle(last.time,first.open,hi,lo,last.close,vol,last.symbol));
        }
        return out;
    }

    public static List<Candle> downsample(List<Candle> src,int maxPoints){
        if(maxPoints<=0 || src.size()<=maxPoints)return new ArrayList<>(src);
        List<Candle> out=new ArrayList<>();
        double step=(double)src.size()/maxPoints;
        int last=-1;
        for(int k=0;k<maxPoints;k++){
            int idx=Math.min(src.size()-1,(int)Math.floor(k*step));
            if(idx!=last){out.add(src.get(idx));last=idx;}
        }
        if(out.isEmpty() || out.get(out.size()-1).time!=src.get(src.size()-1).time) out.add(src.get(src.size()-1));
        return out;
    }

    private static void throttle()throws InterruptedException{synchronized(RATE_LOCK){long w=180L-(System.currentTimeMillis()-lastRequestAt);if(w>0)Thread.sleep(w);lastRequestAt=System.currentTimeMillis();}}

    private static List<Candle> fetch(String address,String symbol)throws Exception{
        HttpURLConnection conn=null;try{
            conn=(HttpURLConnection)new URL(address).openConnection();conn.setConnectTimeout(9000);conn.setReadTimeout(10000);conn.setRequestMethod("GET");
            conn.setRequestProperty("User-Agent","Mozilla/5.0 BorsaRadar/3.8");conn.setRequestProperty("Accept","application/json");
            int code=conn.getResponseCode();if(code<200||code>=300)throw new Exception("HTTP "+code);
            StringBuilder sb=new StringBuilder();try(BufferedReader br=new BufferedReader(new InputStreamReader(conn.getInputStream()))){String line;while((line=br.readLine())!=null)sb.append(line);}
            JSONObject chart=new JSONObject(sb.toString()).getJSONObject("chart");if(!chart.isNull("error"))throw new Exception("Veri kaynağı hatası");
            JSONArray result=chart.getJSONArray("result");if(result.length()==0)throw new Exception("Veri yok");JSONObject r=result.getJSONObject(0);
            JSONArray ts=r.getJSONArray("timestamp");JSONObject q=r.getJSONObject("indicators").getJSONArray("quote").getJSONObject(0);
            JSONArray o=q.getJSONArray("open"),h=q.getJSONArray("high"),l=q.getJSONArray("low"),cl=q.getJSONArray("close"),v=q.getJSONArray("volume");
            List<Candle> out=new ArrayList<>();int n=Math.min(ts.length(),cl.length());
            for(int i=0;i<n;i++){if(cl.isNull(i)||h.isNull(i)||l.isNull(i)||o.isNull(i))continue;double cv=cl.optDouble(i,Double.NaN),hv=h.optDouble(i,Double.NaN),lv=l.optDouble(i,Double.NaN),ov=o.optDouble(i,Double.NaN);if(Double.isNaN(cv)||Double.isNaN(hv)||Double.isNaN(lv)||Double.isNaN(ov))continue;out.add(new Candle(ts.getLong(i),ov,hv,lv,cv,v.isNull(i)?0:v.optDouble(i,0),symbol));}
            if(out.size()<10)throw new Exception("Yetersiz veri: "+out.size());return out;
        }finally{if(conn!=null)conn.disconnect();}
    }
}
