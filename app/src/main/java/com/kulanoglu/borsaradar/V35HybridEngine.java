package com.kulanoglu.borsaradar;

import java.util.List;
import java.util.Locale;

/**
 * V35-Live: V30 mantigini secim/kalite katmani olarak korur; EarlyBreak giris zamanlamasi,
 * ATR stop ve kar koruma ile birlestirir. Gecmis test parametrelerini telefonda birebir
 * yeniden optimize etmez; canli karar katmanidir.
 */
public final class V35HybridEngine {
    private V35HybridEngine() {}

    public static final class Result {
        public String action, phase, reason;
        public double confidence, stopPrice, price;
        public boolean opportunity, risk;
    }

    public static Result analyze(List<MarketDataService.Candle> data, double entryPrice) {
        if (data == null || data.size() < 20) throw new IllegalArgumentException("V35 icin en az 20 gun veri gerekli");
        Result out = new Result();
        ShortPulseEngine.Result pulse = ShortPulseEngine.analyze(data);
        IndicatorEngine.Snapshot s = IndicatorEngine.analyze(data);
        out.price = pulse.price;
        out.phase = pulse.phaseText;

        // V30-Live kalite/struktur kapisi: trend, para akisi ve momentum ayni yone bakmali.
        boolean structural = s.trendUp && s.cmf20 > 0 && s.momentumAtr20 > 0 && !s.trap;
        boolean early = pulse.earlyBreakout && pulse.confidence >= 68 && !pulse.chaseRisk;
        boolean confirmed = pulse.breakout && pulse.score >= 3.5 && !pulse.chaseRisk;

        ProfitGuardEngine.Result guard = null;
        if (entryPrice > 0) guard = ProfitGuardEngine.analyze(data, entryPrice);

        if (guard != null && (guard.action.contains("CIK") || out.price <= guard.stopPrice)) {
            out.action = "SAT / KÂR-ZARAR KORU";
            out.risk = true;
            out.stopPrice = guard.stopPrice;
            out.confidence = Math.max(72, pulse.confidence);
            out.reason = guard.reason + " • V35 risk cikisi";
            return out;
        }
        if (pulse.recommendation.contains("SAT") || pulse.recommendation.contains("RİSK")) {
            out.action = "SAT / RİSKİ AZALT";
            out.risk = true;
        } else if (structural && early) {
            out.action = "V35 ERKEN AL";
            out.opportunity = true;
        } else if (structural && confirmed) {
            out.action = "V35 AL";
            out.opportunity = true;
        } else if (pulse.chaseRisk) {
            out.action = "KOVALAMA / BEKLE";
        } else if (structural && pulse.score >= 2.7) {
            out.action = "KADEMELİ AL / İZLE";
        } else {
            out.action = "TUT / İZLE";
        }
        out.stopPrice = guard != null ? Math.max(pulse.stopReference, guard.stopPrice) : pulse.stopReference;
        double base = pulse.confidence + (structural ? 6 : -4) + (early ? 4 : 0);
        out.confidence = Math.max(30, Math.min(94, base));
        out.reason = String.format(Locale.US,
                "V35 • V30 yapı %s • %s • güven %.0f%% • stop %.2f • %s",
                structural ? "uygun" : "zayıf", pulse.phaseText, out.confidence, out.stopPrice, pulse.explanation);
        return out;
    }
}
