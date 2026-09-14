package com.kulanoglu.borsaradar;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URLEncoder;
import java.net.URL;
import java.util.Locale;

/**
 * Lightweight public social-risk proxy. It reads Google-indexed public X snippets for a symbol.
 * This is deliberately a risk/veto input, not a standalone BUY signal.
 */
public final class SocialPulseService {
    private SocialPulseService(){}

    public static final class Result {
        public boolean hasData;
        public int positiveHits, negativeHits;
        public double score;
        public String status="NO_DATA", summary="Sosyal veri yok";
    }

    public static Result safeAnalyze(String rawSymbol){
        try{return analyze(rawSymbol);}catch(Exception e){Result r=new Result();r.status="SOURCE_ERROR";r.summary="X/web sosyal verisi alınamadı";return r;}
    }

    public static Result analyze(String rawSymbol)throws Exception{
        Result out=new Result();
        String symbol=rawSymbol==null?"":rawSymbol.toUpperCase(Locale.ROOT).replace(".IS","").replace("BIST:","").trim();
        if(symbol.isEmpty())return out;
        String q="site:x.com "+symbol+" hisse";
        String u="https://www.google.com/search?hl=tr&num=20&q="+URLEncoder.encode(q,"UTF-8");
        HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();
        try{
            c.setConnectTimeout(4500);c.setReadTimeout(5500);c.setRequestMethod("GET");
            c.setRequestProperty("User-Agent","Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36");
            c.setRequestProperty("Accept-Language","tr-TR,tr;q=0.9,en;q=0.5");
            int code=c.getResponseCode(); if(code<200||code>=300){out.status="HTTP_"+code;return out;}
            StringBuilder sb=new StringBuilder();try(BufferedReader br=new BufferedReader(new InputStreamReader(c.getInputStream()))){String line;while((line=br.readLine())!=null)sb.append(line).append(' ');}
            String text=sb.toString().replaceAll("<script[^>]*>.*?</script>"," ").replaceAll("<style[^>]*>.*?</style>"," ").replaceAll("<[^>]+>"," ").replace("&amp;","&").toLowerCase(Locale.ROOT);
            String[] neg={"zarar","düşüş","dusuk","düştü","dustu","satış","satis","mağdur","magdur","şikayet","sikayet","çöküş","cokus","risk","kaçın","kacin","bedelli","baskı","baski","taban","spek","manip"};
            String[] pos={"yükseliş","yukselis","yükseldi","yukseldi","alım","alim","güçlü","guclu","olumlu","fırsat","firsat","hedef","kâr","kar","bilanço iyi","bilanco iyi"};
            int nh=0,ph=0;for(String w:neg)nh+=count(text,w);for(String w:pos)ph+=count(text,w);
            out.negativeHits=nh;out.positiveHits=ph;out.hasData=(nh+ph)>=2;
            if(out.hasData){out.score=Math.max(-5,Math.min(5,(ph-nh)*0.8));out.status="OK";out.summary="X/web sosyal risk "+String.format(Locale.US,"%.1f",out.score)+" • +"+ph+"/-"+nh;}
            else {out.status="LOW_COVERAGE";out.summary="X/web sosyal kapsama düşük";}
            return out;
        }finally{c.disconnect();}
    }

    private static int count(String text,String term){int n=0,p=0;while((p=text.indexOf(term,p))>=0){n++;p+=Math.max(1,term.length());}return n;}
}
