package com.kulanoglu.borsaradar;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URLEncoder;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/** Kaynak guveni, olay onemi, tazelik ve tekrar kontrolu kullanan haber baglam katmani. */
public final class NewsContextService {
    private NewsContextService(){}
    public static final class Result {
        public double score; public int positiveCount,negativeCount,freshCount,criticalCount;
        public String summary="haber verisi yok"; public final List<String> catalysts=new ArrayList<>();
    }
    public static Result safeAnalyze(String rawSymbol){try{return analyze(rawSymbol);}catch(Exception e){return new Result();}}
    public static Result analyze(String rawSymbol)throws Exception{
        Result out=new Result(); String q=rawSymbol==null?"":rawSymbol.replace(".DE","").replace(".IS","").trim(); if(q.isEmpty())return out;
        String u="https://query1.finance.yahoo.com/v1/finance/search?q="+URLEncoder.encode(q,"UTF-8")+"&quotesCount=1&newsCount=30&enableFuzzyQuery=false";
        HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();
        try{
            c.setConnectTimeout(6500);c.setReadTimeout(7500);c.setRequestMethod("GET");c.setRequestProperty("User-Agent","Mozilla/5.0 BorsaRadar/3.9");c.setRequestProperty("Accept","application/json");
            int code=c.getResponseCode();if(code<200||code>=300)throw new Exception("news HTTP "+code);
            StringBuilder sb=new StringBuilder();try(BufferedReader br=new BufferedReader(new InputStreamReader(c.getInputStream()))){String line;while((line=br.readLine())!=null)sb.append(line);}
            JSONArray news=new JSONObject(sb.toString()).optJSONArray("news");if(news==null||news.length()==0)return out;
            long now=System.currentTimeMillis()/1000L; double total=0,den=0; Set<String> seen=new HashSet<>();
            for(int i=0;i<news.length();i++){
                JSONObject n=news.optJSONObject(i);if(n==null)continue; String title=n.optString("title",""); if(title.isEmpty())continue;
                String key=EventDeduplicator.key(title); if(!key.isEmpty()&&!seen.add(key))continue;
                long ts=n.optLong("providerPublishTime",0L); double ageHours=ts<=0?999:Math.max(0,(now-ts)/3600.0); if(ageHours<=168)out.freshCount++;
                String provider=n.optString("publisher",""); String link=n.optString("link","");
                InformationImportanceEngine.Source src=SourceTrustResolver.resolve(provider,link);
                InformationImportanceEngine.Score s=InformationImportanceEngine.score(src,title,ageHours,0);
                if(s.importance>=78)out.criticalCount++; if(s.signedImpact>0)out.positiveCount++; else if(s.signedImpact<0)out.negativeCount++;
                double w=Math.max(.10,s.importance/100.0); total+=s.signedImpact*w; den+=w;
                if(s.importance>=58&&out.catalysts.size()<5)out.catalysts.add(s.tier+" • "+title);
            }
            out.score=den==0?0:Math.max(-8,Math.min(8,total/den));
            out.summary=String.format(Locale.US,"haber %.1f/8 • +%d/-%d • kritik %d • 7g %d",out.score,out.positiveCount,out.negativeCount,out.criticalCount,out.freshCount);
            return out;
        }finally{c.disconnect();}
    }
}
