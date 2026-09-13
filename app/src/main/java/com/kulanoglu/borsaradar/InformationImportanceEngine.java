package com.kulanoglu.borsaradar;

import java.util.Locale;

/** Kaynak guveni + olay onemi + tazelik + dogrudanlik + tekrar/dogrulama katmani. */
public final class InformationImportanceEngine {
    private InformationImportanceEngine(){}

    public enum Source { KAP, COMPANY, REGULATOR, EXCHANGE, REUTERS, BLOOMBERG, MAJOR_NEWS, X_OFFICIAL, X_OTHER, OTHER }

    public static final class Score {
        public double importance;      // 0..100
        public double signedImpact;    // -10..+10
        public String tier;            // KRITIK / YUKSEK / ORTA / DUSUK
        public String reason;
    }

    public static Score score(Source source,String title,double ageHours,int confirmations){
        String t=title==null?"":title.toLowerCase(Locale.ROOT);
        double trust=trust(source), material=materiality(t), direct=directness(source);
        double fresh=ageHours<=6?1.0:ageHours<=24?.90:ageHours<=72?.72:ageHours<=168?.52:.28;
        double confirm=Math.min(1.0,.72+Math.max(0,confirmations)*.09);
        double imp=(trust*.30+material*.42+direct*.16+confirm*100*.12)*fresh;
        imp=Math.max(0,Math.min(100,imp));
        int direction=direction(t);
        Score s=new Score();s.importance=imp;s.signedImpact=direction*(imp/10.0);
        s.tier=imp>=78?"KRİTİK":imp>=58?"YÜKSEK":imp>=35?"ORTA":"DÜŞÜK";
        s.reason=String.format(Locale.US,"%s • önem %.0f/100 • kaynak %.0f • olay %.0f • tazelik %.2f",s.tier,imp,trust,material,fresh);
        return s;
    }

    private static double trust(Source s){switch(s){
        case KAP: case REGULATOR: case EXCHANGE:return 100;
        case COMPANY:return 94; case REUTERS:return 93; case BLOOMBERG:return 92;
        case MAJOR_NEWS:return 82; case X_OFFICIAL:return 78; case X_OTHER:return 42; default:return 55;}}
    private static double directness(Source s){switch(s){
        case KAP: case COMPANY: case REGULATOR: case EXCHANGE:return 100;
        case REUTERS: case BLOOMBERG:return 88; case X_OFFICIAL:return 82; case MAJOR_NEWS:return 76; default:return 48;}}
    private static double materiality(String t){
        if(has(t,"sermaye artır","bedelsiz","bedelli","temettü","birleşme","satın alma","ihale","sözleşme","contract","guidance","earnings","revenue","kar pay","geri alım","buyback","iflas","default","ceza","ban","export restriction","investigation"))return 100;
        if(has(t,"ortaklık","partnership","sipariş","order","yatırım","capacity","new customer","upgrade","downgrade","hedef fiyat","target price","margin","backlog"))return 78;
        if(has(t,"launch","ürün","product","conference","sunum","interview","rumor","iddia"))return 48;
        return 28;
    }
    private static int direction(String t){
        int p=0,n=0;
        if(has(t,"artır","raised","beat","record","contract","sözleşme","order","sipariş","partnership","ortaklık","buyback","geri alım","upgrade","new customer","capacity increase"))p++;
        if(has(t,"azalt","cut","miss","downgrade","ban","restriction","ceza","investigation","lawsuit","default","iptal","cancel","weak demand","margin pressure"))n++;
        return p==n?0:(p>n?1:-1);
    }
    private static boolean has(String t,String...ks){for(String k:ks)if(t.contains(k))return true;return false;}
}
