package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/** Eski teknik motoru korur; yeni baglam katmanini ayrica ekler. */
public final class FullAnalysisEngine {
    private FullAnalysisEngine(){}
    public static final class Result {
        public ShortPulseEngine.Result pulse;
        public LegacyTechnicalEnsemble.Result legacy;
        public CatalystContextEngine.Result context;
        public DecisionContextEngine.Result decision;
        public int combinedConfidence;
        public String summary;
    }
    public static Result analyze(String symbol,List<MarketDataService.Candle> candles){
        Result r=new Result();
        r.pulse=ShortPulseEngine.analyze(candles);
        r.legacy=LegacyTechnicalEnsemble.analyze(candles);
        r.context=CatalystContextEngine.analyze(symbol,r.pulse.score);
        r.decision=DecisionContextEngine.evaluate(r.pulse,r.context);
        r.combinedConfidence=SignalConfidenceEngine.combined(r.pulse,r.context);
        r.summary=String.format(Locale.US,"Pulse %.2f • Eski teknik %.0f/100 • Bilgi %.0f/100 • Guven %d%% • %s",r.pulse.score,r.legacy.technicalStrength,r.context.informationStrength,r.combinedConfidence,r.decision.state);
        return r;
    }
}
