package com.kulanoglu.borsaradar;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URLEncoder;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Hafif haber/katalizör katmanı. Özellikle global hisselerde teknik sinyalin
 * tek başına SAT/AZALT üretmesini engellemek için son haber başlıklarını puanlar.
 * Haber metninin tamamını değil, güncel başlık + zaman bilgisini kullanır.
 */
public final class NewsContextService {
    private NewsContextService(){}

    public static final class Result {
        public double score;
        public int positiveCount, negativeCount, freshCount;
        public String summary="haber verisi yok";
        public final List<String> catalysts=new ArrayList<>();
    }

    private static final String[] POSITIVE={
            "partnership","partner","collaboration","collaborate","deal","contract","agreement",
            "expands","expansion","launch","launches","adoption","demand","record revenue","revenue beat",
            "beats estimates","beat estimates","guidance raised","raises guidance","upgrade","upgraded",
            "orders","backlog","capacity","data center","ai infrastructure","cloud","sovereign ai",
            "nvlink","blackwell","rubin","accelerator","new customer","strategic investment"
    };
    private static final String[] NEGATIVE={
            "downgrade","downgraded","cuts guidance","guidance cut","misses estimates","missed estimates",
            "delay","delayed","probe","investigation","lawsuit","ban","restriction","export curbs",
            "weak demand","order cut","cancels","cancelled","recall","shortfall","margin pressure",
            "antitrust","warning","slump","plunge"
    };

    public static Result safeAnalyze(String rawSymbol){
        Result out=new Result();
        try{return analyze(rawSymbol);}catch(Exception e){return out;}
    }

    public static Result analyze(String rawSymbol)throws Exception{
        Result out=new Result();
        String q=rawSymbol==null?"":rawSymbol.replace(".DE","").replace(".IS","").trim();
        if(q.isEmpty())return out;
        String u="https://query1.finance.yahoo.com/v1/finance/search?q="+
                URLEncoder.encode(q,"UTF-8")+"&quotesCount=1&newsCount=20&enableFuzzyQuery=false";
        HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();
        try{
            c.setConnectTimeout(6500);c.setReadTimeout(7500);c.setRequestMethod("GET");
            c.setRequestProperty("User-Agent","Mozilla/5.0 BorsaRadar/3.8");
            c.setRequestProperty("Accept","application/json");
            int code=c.getResponseCode();if(code<200||code>=300)throw new Exception("news HTTP "+code);
            StringBuilder sb=new StringBuilder();try(BufferedReader br=new BufferedReader(new InputStreamReader(c.getInputStream()))){String line;while((line=br.readLine())!=null)sb.append(line);}
            JSONObject root=new JSONObject(sb.toString());
            JSONArray news=root.optJSONArray("news");if(news==null||news.length()==0)return out;
            long now=System.currentTimeMillis()/1000L;
            double score=0;
            for(int i=0;i<news.length();i++){
                JSONObject n=news.optJSONObject(i);if(n==null)continue;
                String title=n.optString("title","").toLowerCase(Locale.ROOT);
                long t=n.optLong("providerPublishTime",0L);
                double ageDays=t<=0?30.0:Math.max(0,(now-t)/86400.0);
                double recency=ageDays<=2?1.0:ageDays<=7?0.72:ageDays<=30?0.38:0.15;
                if(ageDays<=7)out.freshCount++;
                double local=0;
                for(String k:POSITIVE)if(title.contains(k)){local+=1;break;}
                for(String k:NEGATIVE)if(title.contains(k)){local-=1;break;}
                if(title.contains("earnings")||title.contains("revenue")||title.contains("guidance"))local*=1.25;
                if(local>0){out.positiveCount++;if(out.catalysts.size()<4)out.catalysts.add(n.optString("title",""));}
                if(local<0)out.negativeCount++;
                score+=local*recency;
            }
            out.score=Math.max(-8,Math.min(8,score));
            if(out.positiveCount==0&&out.negativeCount==0)out.summary="haber tonu nötr";
            else out.summary="haber skoru "+String.format(Locale.US,"%+.1f",out.score)+" • +"+out.positiveCount+" / -"+out.negativeCount+" • son 7g "+out.freshCount;
            return out;
        }finally{c.disconnect();}
    }
}
