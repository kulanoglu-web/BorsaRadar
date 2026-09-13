package com.kulanoglu.borsaradar;

/** Baglam verisinin ne kadar guvenilir/tam oldugunu ayri bir saglik puaniyla raporlar. */
public final class ContextHealthEngine {
    private ContextHealthEngine(){}
    public static final class Result { public int score; public String label; public String note; }
    public static Result evaluate(UnifiedContextService.Result c){
        Result r=new Result(); if(c==null){r.score=0;r.label="YOK";r.note="Bağlam sonucu yok";return r;}
        int s=0; if(c.newsOk)s+=35; if(c.kapOk)s+=35; if(c.kapEvents>0)s+=15; if(c.topEvents.size()>=2)s+=10; if(c.hasContext)s+=5;
        r.score=Math.min(100,s); r.label=r.score>=80?"GÜÇLÜ":r.score>=55?"ORTA":r.score>=30?"SINIRLI":"ZAYIF";
        r.note="Bağlam veri sağlığı "+r.score+"/100 • "+r.label;
        return r;
    }
}
