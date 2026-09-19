package com.kulanoglu.borsaradar;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TimeZone;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class MarketDataService {
    private static final Map<String,Long> HOST_LAST_REQUEST=new ConcurrentHashMap<>();
    private static final Map<String,Cache> CACHE=new ConcurrentHashMap<>();
    private static final Map<String,Spot> SPOT_CACHE=new ConcurrentHashMap<>();
    private static final ExecutorService AUX_IO=Executors.newFixedThreadPool(4);
    private MarketDataService(){}

    public static final class Candle {
        public final long time; public final double open,high,low,close,volume;
        public final String symbol;
        public Candle(long time,double open,double high,double low,double close,double volume){this(time,open,high,low,close,volume,"");}
        public Candle(long time,double open,double high,double low,double close,double volume,String symbol){this.time=time;this.open=open;this.high=high;this.low=low;this.close=close;this.volume=volume;this.symbol=symbol==null?"":symbol;}
    }
    public static final class Spot {
        public final double price; public final String source; public final long at;
        Spot(double p,String s,long t){price=p;source=s;at=t;}
    }
    private static final class Cache { final long at; final List<Candle> data; final String source; Cache(long a,List<Candle>d,String s){at=a;data=d;source=s;} }

    public static List<Candle> fetchDaily(String symbol,String range)throws Exception{return fetchSeries(symbol,range,"1d",0);}

    public static List<Candle> fetchSeries(String inputSymbol,String range,String interval,int maxPoints)throws Exception{
        String symbol=normalizeSymbol(inputSymbol);
        String key=symbol+"|"+range+"|"+interval;
        Cache cached=CACHE.get(key); long now=System.currentTimeMillis();
        long ttl="1d".equals(interval)?180_000L:75_000L;
        List<Candle> raw=null; String source=""; Exception last=null;
        if(cached!=null && now-cached.at<ttl){raw=new ArrayList<>(cached.data);source=cached.source;}
        else {
            boolean daily="1d".equals(interval);
            boolean stooqFirst=false;
            if(stooqFirst){try{raw=fetchStooqDaily(symbol,range);source="Stooq";}catch(Exception e){last=e;}}
            if(raw==null){try{raw=fetchYahoo(symbol,range,interval);source="Yahoo";}catch(Exception e){last=e;}}
            if(raw==null && daily && !symbol.endsWith(".IS")){try{raw=fetchStooqDaily(symbol,range);source="Stooq";}catch(Exception e){last=e;}}
            if(raw==null){if(cached!=null){raw=new ArrayList<>(cached.data);source=cached.source+"/cache";}else throw last==null?new Exception("Veri alınamadı: "+symbol):last;}
            else CACHE.put(key,new Cache(now,raw,source));
        }
        scheduleGoogleSpot(inputSymbol,symbol);
        if(maxPoints>0)return downsample(raw,maxPoints);
        return raw;
    }

    public static Spot latestSpot(String inputSymbol){String symbol=normalizeSymbol(inputSymbol);Spot s=SPOT_CACHE.get(symbol);if(s!=null&&System.currentTimeMillis()-s.at<120_000L)return s;return null;}
    public static String sourceFor(String inputSymbol,String range,String interval){Cache c=CACHE.get(normalizeSymbol(inputSymbol)+"|"+range+"|"+interval);return c==null?"":c.source;}

    public static String normalizeSymbol(String input){
        if(input==null)return "";String s=input.trim().toUpperCase();
        if(s.startsWith("US:")||s.startsWith("USA:")||s.startsWith("NASDAQ:")||s.startsWith("NYSE:")){int k=s.indexOf(':');return s.substring(k+1).trim();}
        if(s.startsWith("DE:")||s.startsWith("GER:")||s.startsWith("XETRA:")){int k=s.indexOf(':');String code=s.substring(k+1).trim();return code.endsWith(".DE")?code:code+".DE";}
        if(s.startsWith("BIST:")||s.startsWith("TR:")){int k=s.indexOf(':');String code=s.substring(k+1).trim();return code.endsWith(".IS")?code:code+".IS";}
        if(s.endsWith(".IS")||s.endsWith(".DE")||s.endsWith(".L")||s.endsWith(".PA")||s.contains("=")||s.startsWith("^"))return s;
        if(inUniverse(s,GlobalStockUniverse.USA))return s;if(inUniverse(s,GlobalStockUniverse.GERMANY))return s+".DE";return s+".IS";
    }
    public static boolean isGlobalSymbol(String input){if(input==null)return false;String s=input.trim().toUpperCase();if(s.startsWith("US:")||s.startsWith("USA:")||s.startsWith("NASDAQ:")||s.startsWith("NYSE:")||s.startsWith("DE:")||s.startsWith("GER:")||s.startsWith("XETRA:"))return true;if(s.startsWith("BIST:")||s.startsWith("TR:"))return false;if(s.endsWith(".DE")||s.endsWith(".L")||s.endsWith(".PA"))return true;if(s.endsWith(".IS"))return false;return inUniverse(s,GlobalStockUniverse.USA)||inUniverse(s,GlobalStockUniverse.GERMANY);}
    private static boolean inUniverse(String code,String[] entries){for(String e:entries)if(GlobalStockUniverse.code(e).equals(code))return true;return false;}

    public static List<Candle> aggregateHours(List<Candle> src,int hours){if(hours<=1)return new ArrayList<>(src);List<Candle> out=new ArrayList<>();for(int i=0;i<src.size();i+=hours){int end=Math.min(src.size(),i+hours);Candle first=src.get(i),last=src.get(end-1);double hi=first.high,lo=first.low,vol=0;for(int j=i;j<end;j++){Candle c=src.get(j);hi=Math.max(hi,c.high);lo=Math.min(lo,c.low);vol+=c.volume;}out.add(new Candle(last.time,first.open,hi,lo,last.close,vol,last.symbol));}return out;}
    public static List<Candle> downsample(List<Candle> src,int maxPoints){if(maxPoints<=0||src.size()<=maxPoints)return new ArrayList<>(src);List<Candle> out=new ArrayList<>();double step=(double)src.size()/maxPoints;int last=-1;for(int k=0;k<maxPoints;k++){int idx=Math.min(src.size()-1,(int)Math.floor(k*step));if(idx!=last){out.add(src.get(idx));last=idx;}}if(out.isEmpty()||out.get(out.size()-1).time!=src.get(src.size()-1).time)out.add(src.get(src.size()-1));return out;}

    private static List<Candle> fetchYahoo(String symbol,String range,String interval)throws Exception{
        Exception last=null;
        int start=Math.floorMod(symbol.hashCode(),2);
        String[] hosts={"query1.finance.yahoo.com","query2.finance.yahoo.com"};
        String encodedSymbol=URLEncoder.encode(symbol,StandardCharsets.UTF_8.name()).replace("+","%20");
        for(int attempt=0;attempt<2;attempt++){
            String host=hosts[(start+attempt)%2];
            String u="https://"+host+"/v8/finance/chart/"+encodedSymbol+"?range="+range+"&interval="+interval+"&includePrePost=false&events=div%2Csplits";
            try{return fetchYahooJson(u,symbol,host);}catch(Exception e){last=new Exception("Yahoo "+host+" "+symbol+" "+range+"/"+interval+": "+e.getMessage(),e);}
        }
        throw last==null?new Exception("Yahoo veri alınamadı: "+symbol+" "+range+"/"+interval):last;
    }

    private static List<Candle> fetchYahooJson(String address,String symbol,String host)throws Exception{
        String body=httpGet(address,host,1800,2600,"application/json");JSONObject chart=new JSONObject(body).getJSONObject("chart");if(!chart.isNull("error"))throw new Exception("Yahoo veri kaynağı hatası");JSONArray result=chart.getJSONArray("result");if(result.length()==0)throw new Exception("Yahoo veri yok");JSONObject r=result.getJSONObject(0);JSONArray ts=r.getJSONArray("timestamp");JSONObject q=r.getJSONObject("indicators").getJSONArray("quote").getJSONObject(0);JSONArray o=q.getJSONArray("open"),h=q.getJSONArray("high"),l=q.getJSONArray("low"),cl=q.getJSONArray("close"),v=q.getJSONArray("volume");List<Candle> out=new ArrayList<>();int n=Math.min(ts.length(),cl.length());for(int i=0;i<n;i++){if(cl.isNull(i)||h.isNull(i)||l.isNull(i)||o.isNull(i))continue;double cv=cl.optDouble(i,Double.NaN),hv=h.optDouble(i,Double.NaN),lv=l.optDouble(i,Double.NaN),ov=o.optDouble(i,Double.NaN);if(Double.isNaN(cv)||Double.isNaN(hv)||Double.isNaN(lv)||Double.isNaN(ov))continue;out.add(new Candle(ts.getLong(i),ov,hv,lv,cv,v.isNull(i)?0:v.optDouble(i,0),symbol));}if(out.size()<10)throw new Exception("Yahoo yetersiz veri: "+out.size());return out;
    }

    private static List<Candle> fetchStooqDaily(String yahooSymbol,String range)throws Exception{
        String stooq=toStooqSymbol(yahooSymbol);String address="https://stooq.com/q/d/l/?s="+URLEncoder.encode(stooq,"UTF-8")+"&i=d";String csv=httpGet(address,"stooq.com",1600,2200,"text/csv,*/*");List<Candle> all=new ArrayList<>();SimpleDateFormat f=new SimpleDateFormat("yyyy-MM-dd",Locale.US);f.setTimeZone(TimeZone.getTimeZone("UTC"));String[] lines=csv.split("\\r?\\n");for(int i=1;i<lines.length;i++){String[] p=lines[i].trim().split(",");if(p.length<5||p[0].isEmpty())continue;try{Date d=f.parse(p[0]);double o=Double.parseDouble(p[1]),h=Double.parseDouble(p[2]),l=Double.parseDouble(p[3]),c=Double.parseDouble(p[4]);double v=p.length>5?Double.parseDouble(p[5]):0;all.add(new Candle(d.getTime()/1000L,o,h,l,c,v,yahooSymbol));}catch(Exception ignored){}}if(all.size()<20)throw new Exception("Stooq yetersiz veri: "+all.size());int keep=rangeDays(range);if(keep>0&&all.size()>keep)return new ArrayList<>(all.subList(all.size()-keep,all.size()));return all;
    }
    private static int rangeDays(String range){if(range==null)return 0;String r=range.toLowerCase(Locale.US);try{if(r.endsWith("d"))return Integer.parseInt(r.substring(0,r.length()-1));if(r.endsWith("mo"))return Integer.parseInt(r.substring(0,r.length()-2))*23;if(r.endsWith("y"))return Integer.parseInt(r.substring(0,r.length()-1))*252;}catch(Exception ignored){}return 0;}
    private static String toStooqSymbol(String yahoo){String s=yahoo.toLowerCase(Locale.US);if(s.endsWith(".is"))return s.substring(0,s.length()-3)+".tr";if(s.endsWith(".de"))return s;if(s.startsWith("^")||s.contains("="))return s.replace("^","").replace("=x","");if(!s.contains("."))return s+".us";return s;}

    private static void scheduleGoogleSpot(String inputSymbol,String normalized){Spot old=SPOT_CACHE.get(normalized);long now=System.currentTimeMillis();if(old!=null&&now-old.at<90_000L)return;AUX_IO.execute(()->{try{double p=fetchGoogleFinanceSpot(inputSymbol,normalized);if(p>0)SPOT_CACHE.put(normalized,new Spot(p,"Google Finance",System.currentTimeMillis()));}catch(Exception ignored){}});}
    private static double fetchGoogleFinanceSpot(String input,String normalized)throws Exception{String quote=googleQuote(input,normalized);String body=httpGet("https://www.google.com/finance/quote/"+quote,"www.google.com",2500,3500,"text/html,*/*");Pattern[] pats={Pattern.compile("data-last-price=\\\"([0-9.,]+)\\\""),Pattern.compile("class=\\\"YMlKec fxKbKc\\\"[^>]*>(?:[^0-9]*)([0-9.,]+)<")};for(Pattern p:pats){Matcher m=p.matcher(body);if(m.find()){String n=m.group(1).replace(",","");try{return Double.parseDouble(n);}catch(Exception ignored){}}}throw new Exception("Google Finance fiyatı bulunamadı");}
    private static String googleQuote(String input,String normalized){String n=normalized.toUpperCase(Locale.US);if(n.endsWith(".IS"))return n.substring(0,n.length()-3)+":IST";if(n.endsWith(".DE"))return n.substring(0,n.length()-3)+":ETR";String raw=input==null?"":input.toUpperCase(Locale.US);if(raw.startsWith("NYSE:"))return raw.substring(5)+":NYSE";return n+":NASDAQ";}

    private static String httpGet(String address,String host,int connectMs,int readMs,String accept)throws Exception{perHostPace(host);HttpURLConnection conn=null;try{conn=(HttpURLConnection)new URL(address).openConnection();conn.setConnectTimeout(connectMs);conn.setReadTimeout(readMs);conn.setRequestMethod("GET");conn.setRequestProperty("User-Agent","Mozilla/5.0 (Linux; Android 13) BorsaRadar/3.12");conn.setRequestProperty("Accept",accept);conn.setRequestProperty("Accept-Language","tr-TR,tr;q=0.9,en;q=0.7");int code=conn.getResponseCode();if(code<200||code>=300)throw new Exception(host+" HTTP "+code);StringBuilder sb=new StringBuilder();try(BufferedReader br=new BufferedReader(new InputStreamReader(conn.getInputStream(),StandardCharsets.UTF_8))){String line;while((line=br.readLine())!=null)sb.append(line).append('\n');}return sb.toString();}finally{if(conn!=null)conn.disconnect();}}
    private static void perHostPace(String host)throws InterruptedException{synchronized(host.intern()){long now=System.currentTimeMillis();Long prev=HOST_LAST_REQUEST.get(host);long wait=prev==null?0L:35L-(now-prev);if(wait>0)Thread.sleep(wait);HOST_LAST_REQUEST.put(host,System.currentTimeMillis());}}
}
