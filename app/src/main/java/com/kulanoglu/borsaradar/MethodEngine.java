package com.kulanoglu.borsaradar;

import java.util.Locale;

/**
 * BorsaRadar custom short-horizon method ensemble.
 * Percent is a model/indicator alignment score, not a guaranteed win probability.
 */
public final class MethodEngine {
    private MethodEngine() {}

    public static final class Result {
        public final double percent;
        public final double brPulse;
        public final double flowBreak;
        public final double trendGuard;
        public final String label;
        public final String summary;

        Result(double percent, double brPulse, double flowBreak, double trendGuard,
               String label, String summary) {
            this.percent = percent;
            this.brPulse = brPulse;
            this.flowBreak = flowBreak;
            this.trendGuard = trendGuard;
            this.label = label;
            this.summary = summary;
        }
    }

    public static Result analyze(IndicatorEngine.Snapshot s) {
        // BR-Pulse: trend efficiency + ATR-normalized momentum + directional volume pressure.
        double pulse = 50.0;
        pulse += clamp(s.trendEfficiency20, -1, 1) * 22.0;
        pulse += clamp(s.momentumAtr20 / 2.5, -1, 1) * 17.0;
        pulse += clamp(s.volumePressure20, -1, 1) * 11.0;
        pulse = clamp(pulse, 0, 100);

        // FlowBreak: money flow + participation + breakout quality.
        double flow = 50.0;
        flow += clamp(s.cmf20 / 0.25, -1, 1) * 16.0;
        flow += clamp((s.relVolume - 1.0) / 1.3, -1, 1) * 12.0;
        if (s.breakout20) flow += 14.0;
        else if (s.preBreakout) flow += 8.0;
        if (s.trap) flow -= 26.0;
        flow = clamp(flow, 0, 100);

        // TrendGuard: avoids a single hot indicator becoming a false AL.
        double guard = 50.0;
        if (s.trendUp) guard += 15.0;
        else if (s.close < s.ema50) guard -= 15.0;
        if (s.macd > s.macdSignal) guard += 10.0; else guard -= 8.0;
        if (s.adx14 >= 20 && s.trendUp) guard += 8.0;
        if (s.rsi14 >= 48 && s.rsi14 <= 69) guard += 8.0;
        else if (s.rsi14 > 76) guard -= 10.0;
        if (s.stochastic14 > 94) guard -= 7.0;
        guard = clamp(guard, 0, 100);

        double pct = 0.42 * pulse + 0.33 * flow + 0.25 * guard;
        if (s.trap) pct = Math.min(pct, 44.0);
        pct = clamp(pct, 5, 95);

        String label;
        if (pct >= 78 && !s.trap) label = "GÜÇLÜ AL";
        else if (pct >= 68 && !s.trap) label = "AL";
        else if (pct >= 58) label = "KADEMELİ AL / İZLE";
        else if (pct >= 43) label = "TUT / BEKLE";
        else if (pct >= 32) label = "AZALT / RİSK";
        else label = "SAT / RİSK";

        String summary = String.format(Locale.US,
                "Analiz gücü %.0f%% • BR-Pulse %.0f%% • FlowBreak %.0f%% • TrendGuard %.0f%%",
                pct, pulse, flow, guard);
        return new Result(pct, pulse, flow, guard, label, summary);
    }

    private static double clamp(double x, double lo, double hi) {
        return Math.max(lo, Math.min(hi, x));
    }
}
