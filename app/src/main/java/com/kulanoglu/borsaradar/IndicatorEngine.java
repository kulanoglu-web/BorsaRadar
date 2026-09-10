package com.kulanoglu.borsaradar;

import java.util.List;

public final class IndicatorEngine {
    private IndicatorEngine() {}

    public static final class Snapshot {
        public double close, ema20, ema50, rsi14, macd, macdSignal, atr14, cmf20, relVolume, bbWidth;
        public boolean breakout20, preBreakout, trendUp, volumeOk, trap;
        public int score;
        public String signal;
        public String reason;
    }

    public static Snapshot analyze(List<MarketDataService.Candle> x) {
        Snapshot s = new Snapshot();
        int n = x.size();
        s.close = x.get(n - 1).close;
        s.ema20 = ema(x, 20, n - 1);
        s.ema50 = ema(x, 50, n - 1);
        s.rsi14 = rsi(x, 14, n - 1);
        double ema12 = ema(x, 12, n - 1);
        double ema26 = ema(x, 26, n - 1);
        s.macd = ema12 - ema26;
        s.macdSignal = macdSignal(x, n - 1);
        s.atr14 = atr(x, 14, n - 1);
        s.cmf20 = cmf(x, 20, n - 1);
        s.relVolume = relativeVolume(x, 20, n - 1);
        s.bbWidth = bollingerWidth(x, 20, n - 1);

        double high20Prev = highestHigh(x, 20, n - 2);
        s.breakout20 = s.close > high20Prev;
        double dist = high20Prev > 0 ? (high20Prev - s.close) / high20Prev : 1;
        s.preBreakout = !s.breakout20 && dist >= 0 && dist <= 0.025 && s.relVolume >= 1.0;
        s.trendUp = s.close > s.ema20 && s.ema20 > s.ema50;
        s.volumeOk = s.relVolume >= 1.15;

        MarketDataService.Candle last = x.get(n - 1);
        double range = Math.max(0.0001, last.high - last.low);
        double upperWick = last.high - Math.max(last.open, last.close);
        s.trap = (upperWick / range > 0.55 && s.relVolume > 1.4) || (s.rsi14 > 78 && s.breakout20);

        int score = 0;
        if (s.trendUp) score += 2; else if (s.close < s.ema50) score -= 2;
        if (s.rsi14 >= 52 && s.rsi14 <= 70) score += 1;
        if (s.rsi14 < 35) score -= 1;
        if (s.macd > s.macdSignal && s.macd > 0) score += 2; else if (s.macd < s.macdSignal) score -= 1;
        if (s.cmf20 > 0.05) score += 1; else if (s.cmf20 < -0.08) score -= 1;
        if (s.volumeOk) score += 1;
        if (s.breakout20) score += 2;
        if (s.preBreakout) score += 1;
        if (s.trap) score -= 3;
        s.score = score;

        if (s.trap && score < 4) s.signal = "KOVALAMA";
        else if (score >= 7) s.signal = "AL";
        else if (score >= 5 && s.preBreakout) s.signal = "ERKEN";
        else if (score >= 3) s.signal = "İZLE";
        else if (score <= -2) s.signal = "SAT/RİSK";
        else s.signal = "NÖTR";

        s.reason = "Skor " + score
                + " • RSI " + fmt(s.rsi14)
                + " • RVOL " + fmt(s.relVolume)
                + " • CMF " + fmt(s.cmf20)
                + " • ATR " + fmt(s.atr14);
        return s;
    }

    public static double ema(List<MarketDataService.Candle> x, int period, int end) {
        if (x.isEmpty() || end < 0) return Double.NaN;
        int start = Math.max(0, end - Math.max(period * 4, period) + 1);
        double k = 2.0 / (period + 1.0);
        double e = x.get(start).close;
        for (int i = start + 1; i <= end; i++) e = x.get(i).close * k + e * (1.0 - k);
        return e;
    }

    public static double rsi(List<MarketDataService.Candle> x, int period, int end) {
        if (end < period) return 50.0;
        double gain = 0, loss = 0;
        int start = end - period + 1;
        for (int i = start; i <= end; i++) {
            double d = x.get(i).close - x.get(i - 1).close;
            if (d >= 0) gain += d; else loss -= d;
        }
        if (loss == 0) return 100.0;
        double rs = (gain / period) / (loss / period);
        return 100.0 - (100.0 / (1.0 + rs));
    }

    public static double atr(List<MarketDataService.Candle> x, int period, int end) {
        if (end < 1) return 0;
        int start = Math.max(1, end - period + 1);
        double sum = 0; int count = 0;
        for (int i = start; i <= end; i++) {
            MarketDataService.Candle c = x.get(i), p = x.get(i - 1);
            double tr = Math.max(c.high - c.low, Math.max(Math.abs(c.high - p.close), Math.abs(c.low - p.close)));
            sum += tr; count++;
        }
        return count == 0 ? 0 : sum / count;
    }

    public static double cmf(List<MarketDataService.Candle> x, int period, int end) {
        int start = Math.max(0, end - period + 1);
        double mfv = 0, vol = 0;
        for (int i = start; i <= end; i++) {
            MarketDataService.Candle c = x.get(i);
            double den = c.high - c.low;
            double mfm = den == 0 ? 0 : ((c.close - c.low) - (c.high - c.close)) / den;
            mfv += mfm * c.volume; vol += c.volume;
        }
        return vol == 0 ? 0 : mfv / vol;
    }

    public static double relativeVolume(List<MarketDataService.Candle> x, int period, int end) {
        if (end <= 0) return 1;
        int start = Math.max(0, end - period);
        double sum = 0; int count = 0;
        for (int i = start; i < end; i++) { sum += x.get(i).volume; count++; }
        double avg = count == 0 ? 0 : sum / count;
        return avg <= 0 ? 1 : x.get(end).volume / avg;
    }

    public static double bollingerWidth(List<MarketDataService.Candle> x, int period, int end) {
        int start = Math.max(0, end - period + 1);
        int count = end - start + 1;
        double mean = 0;
        for (int i = start; i <= end; i++) mean += x.get(i).close;
        mean /= count;
        double var = 0;
        for (int i = start; i <= end; i++) { double d = x.get(i).close - mean; var += d*d; }
        double sd = Math.sqrt(var / count);
        return mean == 0 ? 0 : (4.0 * sd) / mean;
    }

    private static double highestHigh(List<MarketDataService.Candle> x, int period, int end) {
        int start = Math.max(0, end - period + 1);
        double m = -Double.MAX_VALUE;
        for (int i = start; i <= end; i++) m = Math.max(m, x.get(i).high);
        return m;
    }

    private static double macdAt(List<MarketDataService.Candle> x, int end) {
        return ema(x, 12, end) - ema(x, 26, end);
    }

    private static double macdSignal(List<MarketDataService.Candle> x, int end) {
        int start = Math.max(0, end - 40);
        double k = 2.0 / 10.0;
        double e = macdAt(x, start);
        for (int i = start + 1; i <= end; i++) e = macdAt(x, i) * k + e * (1.0 - k);
        return e;
    }

    public static String fmt(double x) {
        return String.format(java.util.Locale.US, "%.2f", x);
    }
}
