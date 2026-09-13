package com.kulanoglu.borsaradar;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * KAP'in halka acik son bildirim sonuc sayfasindan hisse kodu ile eslesen basliklari ayiklar.
 * HTML degisikliginde sessizce bos sonuca doner; haber katmanini bozmaz.
 */
public final class KapDisclosureService {
    private KapDisclosureService(){}
    public static final class Result {
        public boolean sourceOk; public int matched; public final List<MultiSourceContextEngine.Event> events=new ArrayList<>();
    }
    public static Result safeFetch(String rawSymbol){try{return fetch(rawSymbol);}catch(Exception e){return new Result();}}
    public static Result fetch(String rawSymbol)throws Exception{
        Result out=new Result();
        if(rawSymbol==null)return out;
        String symbol=rawSymbol.toUpperCase(Locale.ROOT).replace(".IS","").trim();
        if(symbol.isEmpty()||MarketDataService.isGlobalSymbol(rawSymbol))return out;
        String address="https://www.kap.org.tr/tr/bildirim-sorgu-sonuc?cat=6&cmp=Y&slf=ALL&srcbar=Y";
        HttpURLConnection c=(HttpURLConnection)new URL(address).openConnection();
        try{
            c.setConnectTimeout(6500); c.setReadTimeout(8000); c.setRequestMethod("GET");
            c.setRequestProperty("User-Agent","Mozilla/5.0 BorsaRadar/4.1"); c.setRequestProperty("Accept","text/html");
            int code=c.getResponseCode(); if(code<200||code>=300)throw new Exception("KAP HTTP "+code);
            StringBuilder sb=new StringBuilder(); try(BufferedReader br=new BufferedReader(new InputStreamReader(c.getInputStream()))){String line;while((line=br.readLine())!=null)sb.append(line).append('\n');}
            out.sourceOk=true; String html=decode(sb.toString());
            Pattern p=Pattern.compile("(?is)(.{0,220}\\b"+Pattern.quote(symbol)+"\\b.{0,420})"); Matcher m=p.matcher(html);
            java.util.HashSet<String> seen=new java.util.HashSet<>();
            while(m.find()&&out.events.size()<8){
                String text=strip(m.group(1)); if(text.length()<15)continue;
                String key=EventDeduplicator.key(text); if(key.length()<8||!seen.add(key))continue;
                double age=estimateAgeHours(text);
                out.events.add(new MultiSourceContextEngine.Event(InformationImportanceEngine.Source.KAP,text,age,1)); out.matched++;
            }
            return out;
        }finally{c.disconnect();}
    }
    private static String strip(String x){return x.replaceAll("<script(?s:.*?)</script>"," ").replaceAll("<style(?s:.*?)</style>"," ").replaceAll("<[^>]+>"," ").replace('&',' ').replaceAll("\\s+"," ").trim();}
    private static String decode(String x){return x.replace("&amp;","&").replace("&quot;","\"").replace("&#39;","'").replace("&nbsp;"," ");}
    private static double estimateAgeHours(String t){
        String x=t.toLowerCase(Locale.ROOT); if(x.contains("bugün"))return 4; if(x.contains("dün"))return 28; return 96;
    }
}
