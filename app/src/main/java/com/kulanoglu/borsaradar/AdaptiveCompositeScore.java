package com.kulanoglu.borsaradar;

/** Teknik motorlari adaptif agirliklarla birlestirir; baglam ayri ve sinirli katkidir. */
public final class AdaptiveCompositeScore {
    private AdaptiveCompositeScore(){}
    public static final class Result {public double score,rawScore,reliability;public String label,summary;}
    public static Result score(FullAnalysisEngine.Result a,AdaptiveMethodWeights.Result w){
        Result r=new Result(); if(a==null||w==null){r.label="VERI YOK";return r;}
        double legacy=(a.legacy.technicalStrength-50)/10.0;
        double pulse=a.pulse.score;
        double v35=a.v35==null?0:(a.v35.opportunity?4:a.v35.risk?-4:0);
        double add=(a.additional.score-50)/10.0;
        double ctx=a.context.hasContext?a.context.combinedScore/2.0:0;
        r.rawScore=legacy*w.weights.get("LEGACY")+pulse*w.weights.get("SHORT_PULSE")+v35*w.weights.get("V35")+add*w.weights.get("ADDITIONAL")+ctx*w.weights.get("CONTEXT");
        r.reliability=OverfitGuard.multiplier(a.backtest,a.walkForward);
        r.score=r.rawScore*r.reliability;
        r.label=r.score>=2.5?"GUCLU ADAY":r.score>=1?"POZITIF":r.score<=-2.5?"YUKSEK RISK":r.score<=-1?"ZAYIF":"NOTR";
        r.summary="Adaptif skor "+IndicatorEngine.fmt(r.score)+" • ham "+IndicatorEngine.fmt(r.rawScore)+" • guven katsayi "+IndicatorEngine.fmt(r.reliability)+" • "+r.label;
        return r;
    }
}
