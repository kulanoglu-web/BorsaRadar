package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/** Eski teknik motoru korur; yeni baglam katmanini ayrica ekler. */
public final class FullAnalysisEngine {
    private FullAnalysisEngine(){}
    public static final class Result {
        public ShortPulseEngine.Result pulse;
        public LegacyTechnicalEnsemble.Result legacy;
        public AdditionalIndicatorEngine.Result additional;
        public AdvancedIndicatorEngine.Result advanced;
        public TechnicalConsensusEngine.Result consensus;
        public MultiHorizonEngine.Result horizons;
        public CalendarEffectEngine.Result calendar;
        public CatalystContextEngine.Result context;
        public DecisionContextEngine.Result decision;
        public int combinedConfidence;
        public String summary;
    }
    public static Result analyze(String symbol,List<MarketDataService.Candle> candles){
        Result r=new Result();
        r.pulse=ShortPulseEngine.analyze(candles);
        r.legacy=LegacyTechnicalEnsemble.analyze(candles);
        r.additional=AdditionalIndicatorEngine.analyze(candles);
        r.advanced=AdvancedIndicatorEngine.analyze(candles);
        r.consensus=TechnicalConsensusEngine.score(r.legacy.indicators,r.additional,r.legacy.methods);
        r.horizons=MultiHorizonEngine.analyze(candles);
        r.calendar=CalendarEffectEngine.analyze(candles);
        r.context=CatalystContextEngine.analyze(symbol,r.pulse.score);
        r.decision=DecisionContextEngine.evaluate(r.pulse,r.context);
        r.combinedConfidence=SignalConfidenceEngine.combined(r.pulse,r.context);
        r.summary=String.format(Locale.US,"Pulse %.2f • Eski teknik %.0f/100 • Teknik teyit +%d/-%d • Bilgi %.0f/100 • Guven %d%% • %s",r.pulse.score,r.legacy.technicalStrength,r.consensus.positive,r.consensus.negative,r.context.informationStrength,r.combinedConfidence,r.decision.state);
        return r;
    }
}
