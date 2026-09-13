package com.kulanoglu.borsaradar;

/** Hisseye ozel ogrenilmis skoru piyasa rejimi ile sinirli sekilde duzeltir. */
public final class RegimeAdjustedScore {
    private RegimeAdjustedScore(){}
    public static final class Result {public double score;public String label,summary;}
    public static Result apply(LearnedTechnicalScore.Result learned,MarketRegimeService.Result regime){
        Result r=new Result();
        double base=learned==null?0:learned.score;
        double adj=regime==null?0:Math.max(-.8,Math.min(.8,regime.score*.22));
        r.score=base+adj;
        r.label=r.score>=2.3?"REJIMLI GUCLU":r.score>=.8?"REJIMLI POZITIF":r.score<=-2.3?"REJIMLI RISK":r.score<=-.8?"REJIMLI ZAYIF":"REJIMLI NOTR";
        r.summary="Rejim duzeltilmis "+IndicatorEngine.fmt(r.score)+" • "+r.label+" • "+(regime==null?"rejim yok":regime.label);
        return r;
    }
}
