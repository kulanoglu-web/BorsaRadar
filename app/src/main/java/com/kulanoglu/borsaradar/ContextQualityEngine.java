package com.kulanoglu.borsaradar;

/** Bağlam verisinin miktarını değil kullanılabilir kalitesini ölçer. */
public final class ContextQualityEngine {
    private ContextQualityEngine(){}
    public static final class Result {
        public double quality; public String label; public String note;
    }
    public static Result score(boolean newsOk, boolean kapOk, int newsAccepted, int kapEvents, int criticalEvents){
        Result r=new Result();
        double q=0;
        if(kapOk)q+=34;
        if(newsOk)q+=22;
        q+=Math.min(20,newsAccepted*2.5);
        q+=Math.min(16,kapEvents*4.0);
        q+=Math.min(8,criticalEvents*2.0);
        r.quality=Math.max(0,Math.min(100,q));
        r.label=r.quality>=78?"GÜÇLÜ":r.quality>=55?"İYİ":r.quality>=30?"SINIRLI":"ZAYIF";
        r.note="Bağlam kalitesi "+Math.round(r.quality)+"/100 • "+r.label;
        return r;
    }
}
