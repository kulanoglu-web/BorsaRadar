package com.kulanoglu.borsaradar;

/** Teknik skordan bağımsız bilgi gücü: yön + veri kalitesi + kritik olay yoğunluğu. */
public final class InformationStrengthEngine {
    private InformationStrengthEngine(){}
    public static final class Result {
        public double strength; public double directional; public String label;
    }
    public static Result score(double contextScore,double quality,int criticalEvents){
        Result r=new Result();
        double dir=Math.max(-8,Math.min(8,contextScore));
        double q=Math.max(0,Math.min(100,quality))/100.0;
        double criticalBoost=Math.min(1.5,Math.max(0,criticalEvents)*0.25);
        r.directional=dir*q;
        r.strength=Math.min(100,Math.abs(dir)/8.0*72*q + q*18 + criticalBoost*6.5);
        r.label=r.strength>=72?"ÇOK GÜÇLÜ":r.strength>=50?"GÜÇLÜ":r.strength>=28?"ORTA":"ZAYIF";
        return r;
    }
}
