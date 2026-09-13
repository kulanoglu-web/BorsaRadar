package com.kulanoglu.borsaradar;

import java.util.Locale;

/** Makro olaylarin belirli hisselerde ayni etkiye sahip olmadigini belirtmek icin basit hassasiyet katmani. */
public final class SectorSensitivityEngine {
    private SectorSensitivityEngine(){}
    public static final class Result { public double multiplier=1.0; public String sector="GENEL"; public String note="Genel piyasa hassasiyeti"; }
    public static Result forSymbol(String rawSymbol,String macroTag){
        Result r=new Result(); String s=rawSymbol==null?"":rawSymbol.toUpperCase(Locale.ROOT).replace(".IS","").replace(".DE",""); String tag=macroTag==null?"":macroTag;
        if(has(s,"THYAO","PGSUS","TAVHL")){r.sector="HAVACILIK"; if("PETROL".equals(tag)||"GEOPOLITIK".equals(tag))r.multiplier=1.35; r.note="Havacılık: petrol ve jeopolitik gelişmelere yüksek hassasiyet.";}
        else if(has(s,"PETKM","TUPRS")){r.sector="ENERJI/PETROKIMYA"; if("PETROL".equals(tag)||"GEOPOLITIK".equals(tag))r.multiplier=1.30; r.note="Enerji/petrokimya: petrol ve jeopolitik olaylarda farklılaşabilir.";}
        else if(has(s,"AKBNK","GARAN","ISCTR","YKBNK","HALKB","VAKBN")){r.sector="BANKA"; if("FAIZ".equals(tag)||"POLITIK".equals(tag)||"ENFLASYON".equals(tag))r.multiplier=1.25; r.note="Bankacılık: faiz, enflasyon ve ülke riskine yüksek hassasiyet.";}
        else if(has(s,"FROTO","TOASO","DOAS")){r.sector="OTOMOTIV"; if("FAIZ".equals(tag)||"ENFLASYON".equals(tag))r.multiplier=1.12; r.note="Otomotiv: finansman koşulları ve talep değişimine hassas.";}
        else if(has(s,"NVDA","AMD","AVGO","QCOM","INTC","MSFT","META","GOOG","GOOGL")){r.sector="TEKNOLOJI"; if("FAIZ".equals(tag)||"POLITIK".equals(tag))r.multiplier=1.15; r.note="Teknoloji: faiz ve regülasyon beklentilerine duyarlı.";}
        return r;
    }
    private static boolean has(String s,String...xs){for(String x:xs)if(x.equals(s))return true;return false;}
}
