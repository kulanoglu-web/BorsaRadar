package com.kulanoglu.borsaradar;

public final class HourlyRiskGate {
    private HourlyRiskGate(){}
    public static final class Decision {
        public String label, note;
        public double adjustment;
    }
    public static Decision review(String symbol,double technicalScore,String original,double confidence){
        Decision d=new Decision();d.label=original;d.note="";d.adjustment=0;
        CatalystContextEngine.Result c=CatalystContextEngine.analyze(symbol,technicalScore);
        SocialPulseService.Result s=SocialPulseService.safeAnalyze(symbol);
        if(c.hasContext)d.adjustment+=Math.max(-3.0,Math.min(2.0,c.combinedScore*0.45));
        if(s.hasData)d.adjustment+=Math.max(-2.5,Math.min(1.2,s.score*0.45));
        boolean bad=(c.hasContext&&(c.combinedScore<=-2.0||c.newsScore<=-1.8||c.kapScore<=-2.0))||(s.hasData&&s.score<=-1.6);
        double finalScore=technicalScore+d.adjustment;
        if(bad)d.label="BEKLE / RİSK";
        else if(!c.hasContext&&!s.hasData&&original.contains("AL"))d.label="İZLE • VERİ EKSİK";
        else if(finalScore>=5.5&&confidence>=60&&!original.contains("SAT"))d.label="FIRSAT • AL ADAYI";
        else if(original.contains("AL")&&finalScore<4.0)d.label="İZLE / NÖTR";
        d.note=c.note+" • "+s.summary;
        return d;
    }
}
