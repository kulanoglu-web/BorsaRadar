package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/**
 * Eski teknik metodlari koruyan ensemble. Haber/KAP bu katmani silmez veya yerine gecmez.
 * IndicatorEngine: EMA, RSI, MACD, ATR, CMF, RVOL, Bollinger width, CCI, Stochastic, ADX,
 * breakout/pre-breakout, BRTV, BRM ve BRH. MethodEngine: BR-Pulse, FlowBreak, TrendGuard, V30-Live.
 */
public final class LegacyTechnicalEnsemble {
    private LegacyTechnicalEnsemble(){}
    public static final class Result {
        public IndicatorEngine.Snapshot indicators;
        public MethodEngine.Result methods;
        public double technicalStrength;
        public String label,summary;
    }
    public static Result analyze(List<MarketDataService.Candle> candles){
        Result r=new Result();
        r.indicators=IndicatorEngine.analyze(candles);
        r.methods=MethodEngine.analyze(r.indicators);
        double indicatorPct=Math.max(5,Math.min(95,50+r.indicators.score*3.4));
        r.technicalStrength=.55*r.methods.percent+.45*indicatorPct;
        if(r.indicators.trap)r.technicalStrength=Math.min(r.technicalStrength,43);
        r.label=r.technicalStrength>=72?"TEKNIK GUCLU":r.technicalStrength>=58?"TEKNIK POZITIF":r.technicalStrength>=43?"TEKNIK NOTR":"TEKNIK ZAYIF";
        r.summary=String.format(Locale.US,"Eski metodlar %.0f/100 • %s • %s",r.technicalStrength,r.methods.summary,r.indicators.reason);
        return r;
    }
}
