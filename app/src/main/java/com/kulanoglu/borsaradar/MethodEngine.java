package com.kulanoglu.borsaradar;

import java.util.Locale;

/** BorsaRadar live ensemble. Percent is alignment strength, not guaranteed return probability. */
public final class MethodEngine {
    private MethodEngine() {}

    public static final class Result {
        public final double percent, brPulse, flowBreak, trendGuard, v30Live;
        public final String label, summary;
        Result(double percent,double brPulse,double flowBreak,double trendGuard,double v30Live,String label,String summary){
            this.percent=percent; this.brPulse=brPulse; this.flowBreak=flowBreak; this.trendGuard=trendGuard; this.v30Live=v30Live; this.label=label; this.summary=summary;
        }
    }

    public static Result analyze(IndicatorEngine.Snapshot s) {
        double pulse=50.0;
        pulse+=clamp(s.trendEfficiency20,-1,1)*22.0;
        pulse+=clamp(s.momentumAtr20/2.5,-1,1)*17.0;
        pulse+=clamp(s.volumePressure20,-1,1)*11.0;
        pulse=clamp(pulse,0,100);

        double flow=50.0;
        flow+=clamp(s.cmf20/0.25,-1,1)*16.0;
        flow+=clamp((s.relVolume-1.0)/1.3,-1,1)*12.0;
        if(s.breakout20) flow+=14.0; else if(s.preBreakout) flow+=8.0;
        if(s.trap) flow-=26.0;
        flow=clamp(flow,0,100);

        double guard=50.0;
        if(s.trendUp) guard+=15.0; else if(s.close<s.ema50) guard-=15.0;
        if(s.macd>s.macdSignal) guard+=10.0; else guard-=8.0;
        if(s.adx14>=20&&s.trendUp) guard+=8.0;
        if(s.rsi14>=48&&s.rsi14<=69) guard+=8.0; else if(s.rsi14>76) guard-=10.0;
        if(s.stochastic14>94) guard-=7.0;
        guard=clamp(guard,0,100);

        // v30-Live: preserves the validated v30 character without pretending that a phone snapshot
        // can reproduce the historical cross-sectional portfolio backtest exactly.
        // It rewards the same core state: positive money flow, ADX-supported trend, EMA20 strength
        // and persistent ATR-normalized momentum; trap/overextension is penalized.
        double v30=35.0;
        if(s.trendUp) v30+=18.0;
        if(s.close>s.ema20) v30+=12.0; else v30-=14.0;
        if(s.adx14>=18) v30+=10.0;
        if(s.cmf20>0) v30+=12.0; else v30-=10.0;
        v30+=clamp(s.momentumAtr20/3.0,-1,1)*18.0;
        if(s.trap) v30-=28.0;
        if(s.rsi14>78) v30-=8.0;
        v30=clamp(v30,0,100);

        // v30 is the aggressive return engine; defensive families remain majority confirmation.
        double pct=.32*pulse+.25*flow+.18*guard+.25*v30;
        if(s.trap) pct=Math.min(pct,42.0);
        pct=clamp(pct,5,95);

        String label;
        if(pct>=80&&v30>=72&&!s.trap) label="V30 GÜÇLÜ AL";
        else if(pct>=69&&!s.trap) label="AL";
        else if(pct>=58) label="KADEMELİ AL / İZLE";
        else if(pct>=43) label="TUT / BEKLE";
        else if(pct>=32) label="AZALT / RİSK";
        else label="SAT / RİSK";

        String summary=String.format(Locale.US,"Analiz %.0f%% • V30-Live %.0f%% • Pulse %.0f%% • Flow %.0f%% • Guard %.0f%%",pct,v30,pulse,flow,guard);
        return new Result(pct,pulse,flow,guard,v30,label,summary);
    }
    private static double clamp(double x,double lo,double hi){return Math.max(lo,Math.min(hi,x));}
}
