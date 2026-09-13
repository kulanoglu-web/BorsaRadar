package com.kulanoglu.borsaradar;

/** Teknik sinyali degistirmeden, haber/KAP/makro ile birlikte okunacak karar durumunu uretir. */
public final class DecisionContextEngine {
    private DecisionContextEngine(){}
    public static final class Result {
        public String state, note;
        public int confidenceAdjustment;
        public boolean caution;
    }
    public static Result evaluate(ShortPulseEngine.Result tech, CatalystContextEngine.Result ctx){
        Result r=new Result();
        if(tech==null){r.state="VERI YOK";r.note="Teknik veri yok.";r.caution=true;return r;}
        if(ctx==null||!ctx.hasContext){r.state="TEKNIK ODAK";r.note="Bilgi akisi yetersiz; teknik sinyal tek basina goruntuleniyor.";r.caution=true;return r;}
        boolean weak=tech.score<=-1.3;
        boolean strong=tech.score>=2.7;
        if(weak&&ctx.combinedScore>=3){r.state="SATIS SINYALI TEYITSIZ";r.note="Teknik zayif ama bilgi akisi pozitif; azaltma karari icin ek teyit beklenmeli.";r.confidenceAdjustment=-18;r.caution=true;}
        else if(strong&&ctx.combinedScore<=-3){r.state="ALIS SINYALI TEYITSIZ";r.note="Teknik guclu ama bilgi akisi negatif; yeni pozisyon icin risk yuksek.";r.confidenceAdjustment=-20;r.caution=true;}
        else if(strong&&ctx.combinedScore>=3){r.state="CIFT TEYIT POZITIF";r.note="Teknik ve bilgi akisi ayni yonde pozitif.";r.confidenceAdjustment=10;}
        else if(weak&&ctx.combinedScore<=-3){r.state="CIFT TEYIT NEGATIF";r.note="Teknik ve bilgi akisi ayni yonde negatif.";r.confidenceAdjustment=10;r.caution=true;}
        else {r.state="KARISIK / NOTR";r.note="Teknik ve bilgi akisi belirgin ortak yon vermiyor.";r.caution=true;}
        if(ctx.macroRisk>=7){r.caution=true;r.confidenceAdjustment-=8;r.note += " Makro risk yuksek.";}
        if(ctx.qualityScore<45){r.caution=true;r.confidenceAdjustment-=8;r.note += " Baglam kalitesi dusuk.";}
        return r;
    }
}
