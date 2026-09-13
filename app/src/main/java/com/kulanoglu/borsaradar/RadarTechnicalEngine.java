package com.kulanoglu.borsaradar;

import java.util.List;

/** Birinci radar aşamasında birden fazla teknik aileyi ağ çağrısı yapmadan birleştirir. */
public final class RadarTechnicalEngine {
    private RadarTechnicalEngine(){}

    public static final class Result {
        public double score;
        public String label;
        public String summary;
    }

    public static Result analyze(List<MarketDataService.Candle> candles){
        Result r=new Result();
        ShortPulseEngine.Result pulse=ShortPulseEngine.analyze(candles);
        LegacyTechnicalEnsemble.Result legacy=LegacyTechnicalEnsemble.analyze(candles);
        AdditionalIndicatorEngine.Result add=AdditionalIndicatorEngine.analyze(candles);
        AdvancedIndicatorEngine.Result adv=AdvancedIndicatorEngine.analyze(candles);

        double legacyScore=Math.max(-5,Math.min(5,(legacy.technicalStrength-50.0)/10.0));
        double pulseScore=Math.max(-5,Math.min(5,pulse.score));
        int addVotes=(add.mostBull?1:-1)+(add.qqeBull?1:-1)+(add.abovePivot?1:-1);
        double addScore=addVotes*(5.0/3.0);

        int advVotes=0;
        advVotes += adv.mfi14>=55?1:adv.mfi14<=45?-1:0;
        advVotes += adv.obvSlope>0?1:adv.obvSlope<0?-1:0;
        advVotes += adv.williamsR14>-45?1:adv.williamsR14<-65?-1:0;
        advVotes += adv.donchianPosition>=.60?1:adv.donchianPosition<=.40?-1:0;
        advVotes += adv.ichimokuBull?1:-1;
        double advScore=advVotes;

        r.score=.40*legacyScore+.30*pulseScore+.15*addScore+.15*advScore;
        r.score=Math.max(-5,Math.min(5,r.score));
        r.label=r.score>=2.4?"TEKNIK GÜÇLÜ":r.score>=1.1?"TEKNIK POZITIF":r.score<=-2.4?"TEKNIK ZAYIF":r.score<=-1.1?"TEKNIK NEGATIF":"TEKNIK NÖTR";
        r.summary="Radar teknik "+IndicatorEngine.fmt(r.score)+"/5 • "+r.label+" • Eski "+IndicatorEngine.fmt(legacyScore)+" • Pulse "+IndicatorEngine.fmt(pulseScore)+" • MOST/QQE "+IndicatorEngine.fmt(addScore)+" • gelişmiş "+IndicatorEngine.fmt(advScore);
        return r;
    }
}
