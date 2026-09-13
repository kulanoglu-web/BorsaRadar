package com.kulanoglu.borsaradar;

import java.util.Locale;

/** Makro/jeopolitik olaylari sirket haberlerinden ayirir ve sektor hassasiyeti icin etiketler. */
public final class MacroImpactEngine {
    private MacroImpactEngine(){}
    public static final class Result { public double risk; public String tag; public String note; }
    public static Result analyze(String title){
        String t=title==null?"":title.toLowerCase(Locale.ROOT); Result r=new Result(); r.tag="NONE"; r.note="Makro etki yok";
        if(has(t,"war","savaş","conflict","missile","hormuz","iran","ukraine")){r.risk=8.5;r.tag="GEOPOLITIK";r.note="Jeopolitik risk: enerji, ulaştırma, döviz ve yabancı akımı etkilenebilir.";}
        else if(has(t,"interest rate","faiz","central bank","tcmb","fed","ecb")){r.risk=7.0;r.tag="FAIZ";r.note="Faiz olayı: iskonto oranı, banka marjı ve büyüme hisselerini etkileyebilir.";}
        else if(has(t,"inflation","enflasyon","cpi","tufe")){r.risk=6.2;r.tag="ENFLASYON";r.note="Enflasyon olayı: faiz beklentisi ve marj baskısını değiştirebilir.";}
        else if(has(t,"oil","petrol","brent","opec")){r.risk=6.8;r.tag="PETROL";r.note="Petrol hareketi: enerji lehine, havacılık/ulaştırma aleyhine farklılaşabilir.";}
        else if(has(t,"election","seçim","judiciary","yargı","sanction","yaptırım")){r.risk=6.5;r.tag="POLITIK";r.note="Politik risk: ülke risk primi ve yabancı yatırımcı davranışı etkilenebilir.";}
        return r;
    }
    private static boolean has(String t,String...ks){for(String k:ks)if(t.contains(k))return true;return false;}
}
