package com.kulanoglu.borsaradar;

import java.util.List;

/** BR-KarKoru: short-horizon risk/profit protection for open positions. */
public final class ProfitGuardEngine {
    private ProfitGuardEngine() {}

    public static final class Result {
        public double stopPrice, peakPrice, pullbackPct;
        public String action, reason;
    }

    public static Result analyze(List<MarketDataService.Candle> x, double entry) {
        Result r = new Result();
        if (x == null || x.size() < 3 || entry <= 0) {
            r.action="TUT"; r.reason="BR-KarKoru: veri yetersiz"; return r;
        }
        int start=Math.max(0,x.size()-12);
        double peak=entry;
        for(int i=start;i<x.size();i++) peak=Math.max(peak,x.get(i).high);
        MarketDataService.Candle last=x.get(x.size()-1);
        IndicatorEngine.Snapshot s=IndicatorEngine.analyze(x);
        double gain=(peak-entry)/entry*100.0;
        double pull=(peak-last.close)/peak*100.0;
        double atrPct=s.atr14>0 ? s.atr14/last.close*100.0 : 2.0;

        // Tested short-horizon compromise: protect gains more tightly after +6%, never loosen past ~6%.
        double trailPct = gain >= 12 ? Math.max(3.5, Math.min(5.0, atrPct*1.55))
                : gain >= 6 ? Math.max(4.0, Math.min(6.0, atrPct*1.8))
                : Math.max(3.0, Math.min(4.5, atrPct*1.5));
        double initialStop=entry*(1.0-Math.max(0.025,Math.min(0.045,atrPct*0.012)));
        double trailing=peak*(1.0-trailPct/100.0);
        r.stopPrice=Math.max(initialStop, gain>3 ? trailing : initialStop);
        r.peakPrice=peak; r.pullbackPct=pull;

        boolean flowBreak=s.volumePressure20 < -0.08 || s.cmf20 < -0.05;
        boolean momentumBreak=s.momentumAtr20 < 0 || s.rsi14 < 48;
        if(last.close <= r.stopPrice || (gain>=6 && pull>=trailPct*0.8 && flowBreak && momentumBreak)) {
            r.action="KAR KORU / CIK";
        } else if(gain>=6 && (flowBreak || momentumBreak)) {
            r.action="STOP YUKSELT";
        } else r.action="TUT";
        r.reason="BR-KarKoru • zirve "+IndicatorEngine.fmt(peak)+" • geri cekilme %"+IndicatorEngine.fmt(pull)+" • stop "+IndicatorEngine.fmt(r.stopPrice);
        return r;
    }
}
