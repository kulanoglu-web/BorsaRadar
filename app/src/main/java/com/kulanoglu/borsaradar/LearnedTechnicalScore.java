package com.kulanoglu.borsaradar;

/** Ogrenilen hisse-bazli metod agirliklarini bugunku teknik sinyallere uygular. */
public final class LearnedTechnicalScore {
    private LearnedTechnicalScore(){}
    public static final class Result {public double score;public String label,summary;}
    public static Result score(FullAnalysisEngine.Result a,LearnedWeightEngine.Result w){
        Result r=new Result();
        if(a==null||w==null){r.label="VERI YOK";return r;}
        double ind=Math.max(-5,Math.min(5,a.legacy.indicators.score/2.2));
        double met=(a.legacy.methods.percent-50)/10.0;
        double sh=Math.max(-5,Math.min(5,a.pulse.score));
        int aq=(a.additional.mostBull?1:-1)+(a.additional.qqeBull?1:-1)+(a.additional.abovePivot?1:-1);
        double most=aq*1.5;
        double v35=a.v35==null?0:(a.v35.opportunity?4:a.v35.risk?-4:0);
        r.score=ind*w.weights.get("INDICATOR")+met*w.weights.get("METHOD")+sh*w.weights.get("SHORT")+most*w.weights.get("MOST_QQE")+v35*w.weights.get("V35");
        r.label=r.score>=2.3?"OGRENILMIS GUCLU":r.score>=.8?"OGRENILMIS POZITIF":r.score<=-2.3?"OGRENILMIS RISK":r.score<=-.8?"OGRENILMIS ZAYIF":"OGRENILMIS NOTR";
        r.summary="Hisseye ozel skor "+IndicatorEngine.fmt(r.score)+" • "+r.label;
        return r;
    }
}
