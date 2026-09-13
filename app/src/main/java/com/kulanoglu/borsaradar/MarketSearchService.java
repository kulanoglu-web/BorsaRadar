package com.kulanoglu.borsaradar;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URLEncoder;
import java.net.URL;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public final class MarketSearchService {
    private MarketSearchService(){}

    public static List<String> search(String query,int market)throws Exception{
        List<String> out=new ArrayList<>();
        if(query==null || query.trim().length()<1) return out;
        String q=URLEncoder.encode(query.trim(),"UTF-8");
        String address="https://query1.finance.yahoo.com/v1/finance/search?q="+q+"&quotesCount=20&newsCount=0&listsCount=0";
        HttpURLConnection c=(HttpURLConnection)new URL(address).openConnection();
        try{
            c.setConnectTimeout(7000); c.setReadTimeout(8000); c.setRequestProperty("User-Agent","Mozilla/5.0 BorsaRadar/3.9");
            if(c.getResponseCode()<200 || c.getResponseCode()>=300) return out;
            StringBuilder sb=new StringBuilder();
            try(BufferedReader br=new BufferedReader(new InputStreamReader(c.getInputStream()))){String line;while((line=br.readLine())!=null)sb.append(line);}
            JSONArray a=new JSONObject(sb.toString()).optJSONArray("quotes"); if(a==null)return out;
            Set<String> seen=new LinkedHashSet<>();
            for(int i=0;i<a.length();i++){
                JSONObject x=a.optJSONObject(i); if(x==null)continue;
                String symbol=x.optString("symbol","").toUpperCase(Locale.ROOT);
                String exch=x.optString("exchange","").toUpperCase(Locale.ROOT);
                String type=x.optString("quoteType","");
                if(!"EQUITY".equalsIgnoreCase(type))continue;
                boolean ok;
                if(market==1) ok=symbol.endsWith(".DE") || symbol.endsWith(".F") || exch.contains("GER") || exch.contains("FRA") || exch.contains("XETRA");
                else if(market==2) ok=!symbol.contains(".") && (exch.contains("NMS")||exch.contains("NYQ")||exch.contains("NCM")||exch.contains("NGM")||exch.contains("ASE")||exch.contains("NASDAQ")||exch.contains("NYSE"));
                else ok=symbol.endsWith(".IS");
                if(!ok)continue;
                String code=symbol;
                if(market==1){ if(code.endsWith(".DE")||code.endsWith(".F")) code=code.substring(0,code.lastIndexOf('.')); }
                if(market==0 && code.endsWith(".IS")) code=code.substring(0,code.length()-3);
                String name=x.optString("shortname",x.optString("longname",""));
                String item=code+(name.isEmpty()?"":" • "+name);
                if(seen.add(item))out.add(item);
            }
            return out;
        } finally { c.disconnect(); }
    }

    public static String codeFromSuggestion(String value){
        if(value==null)return "";
        String s=value.trim(); int k=s.indexOf(" • "); if(k>0)s=s.substring(0,k); return s.trim().toUpperCase(Locale.ROOT);
    }
}
