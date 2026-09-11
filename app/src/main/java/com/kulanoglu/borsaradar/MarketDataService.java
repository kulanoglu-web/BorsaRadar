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
        public Candle(long time,double open,double high,double low,double close,double volume){this.time=time;this.open=open;this.high=high;this.low=low;this.close=close;this.volume=volume;}
    }
    private static final class Cache { final long at; final List<Candle> data; Cache(long a,List<Candle>d){at=a;data=d;} }

    public static List<Candle> fetchDaily(String bistSymbol,String range)throws Exception{
        String key=bistSymbol+"|"+range; Cache c=CACHE.get(key); long now=System.currentTimeMillis();
        if(c!=null && now-c.at<180_000L)return new ArrayList<>(c.data);
        String symbol=bistSymbol.endsWith(".IS")?bistSymbol:bistSymbol+".IS"; Exception last=null;
        String[] hosts={"query1.finance.yahoo.com","query2.finance.yahoo.com"};
        for(int attempt=0;attempt<3;attempt++){
            String u="https://"+hosts[attempt%2]+"/v8/finance/chart/"+symbol+"?range="+range+"&interval=1d&includePrePost=false&events=div%2Csplits";
            try{throttle();List<Candle>d=fetch(u);CACHE.put(key,new Cache(now,d));return new ArrayList<>(d);}catch(Exception e){last=e;try{Thread.sleep(350L*(attempt+1));}catch(InterruptedException ie){Thread.currentThread().interrupt();throw ie;}}
        }
        if(c!=null)return new ArrayList<>(c.data);
        throw last==null?new Exception("Veri alınamadı"):last;
    }

    private static void throttle()throws InterruptedException{synchronized(RATE_LOCK){long w=180L-(System.currentTimeMillis()-lastRequestAt);if(w>0)Thread.sleep(w);lastRequestAt=System.currentTimeMillis();}}

    private static List<Candle> fetch(String address)throws Exception{
        HttpURLConnection conn=null;try{
            conn=(HttpURLConnection)new URL(address).openConnection();conn.setConnectTimeout(9000);conn.setReadTimeout(10000);conn.setRequestMethod("GET");
            conn.setRequestProperty("User-Agent","Mozilla/5.0 BorsaRadar/3.0");conn.setRequestProperty("Accept","application/json");
            int code=conn.getResponseCode();if(code<200||code>=300)throw new Exception("HTTP "+code);
            StringBuilder sb=new StringBuilder();try(BufferedReader br=new BufferedReader(new InputStreamReader(conn.getInputStream()))){String line;while((line=br.readLine())!=null)sb.append(line);}
            JSONObject chart=new JSONObject(sb.toString()).getJSONObject("chart");if(!chart.isNull("error"))throw new Exception("Veri kaynağı hatası");
            JSONArray result=chart.getJSONArray("result");if(result.length()==0)throw new Exception("Veri yok");JSONObject r=result.getJSONObject(0);
            JSONArray ts=r.getJSONArray("timestamp");JSONObject q=r.getJSONObject("indicators").getJSONArray("quote").getJSONObject(0);
            JSONArray o=q.getJSONArray("open"),h=q.getJSONArray("high"),l=q.getJSONArray("low"),cl=q.getJSONArray("close"),v=q.getJSONArray("volume");
            List<Candle> out=new ArrayList<>();int n=Math.min(ts.length(),cl.length());
            for(int i=0;i<n;i++){if(cl.isNull(i)||h.isNull(i)||l.isNull(i)||o.isNull(i))continue;double cv=cl.optDouble(i,Double.NaN),hv=h.optDouble(i,Double.NaN),lv=l.optDouble(i,Double.NaN),ov=o.optDouble(i,Double.NaN);if(Double.isNaN(cv)||Double.isNaN(hv)||Double.isNaN(lv)||Double.isNaN(ov))continue;out.add(new Candle(ts.getLong(i),ov,hv,lv,cv,v.isNull(i)?0:v.optDouble(i,0)));}
            if(out.size()<10)throw new Exception("Yetersiz veri: "+out.size()+" gün");return out;
        }finally{if(conn!=null)conn.disconnect();}
    }
}
