package com.kulanoglu.borsaradar;

import java.util.List;

public final class BacktestEngine {
    private BacktestEngine() {}

    public static final class Result {
        public int trades, wins, losses;
        public double netPct, maxDrawdownPct, winRate, avgTradePct;
        public String summary;
    }

    public static Result run(List<MarketDataService.Candle> x) {
        Result r = new Result();
        if (x.size() < 90) { r.summary = "Backtest için yetersiz veri"; return r; }

        double capital = 1.0, peak = 1.0, maxDd = 0;
        boolean in = false;
        double entry = 0, stop = 0, highest = 0;
        double tradeSum = 0;

        for (int i = 60; i < x.size(); i++) {
            List<MarketDataService.Candle> slice = x.subList(0, i + 1);
            IndicatorEngine.Snapshot s = IndicatorEngine.analyze(slice);
            double price = x.get(i).close;

            if (!in) {
                if (("AL".equals(s.signal) || "ERKEN".equals(s.signal)) && !s.trap) {
                    in = true;
                    entry = price;
                    highest = price;
                    stop = Math.max(price - 2.2 * s.atr14, s.ema50 * 0.985);
                }
            } else {
                highest = Math.max(highest, price);
                double trail = highest - 2.6 * s.atr14;
                stop = Math.max(stop, trail);
                boolean exit = price < stop || "SAT/RİSK".equals(s.signal) || (price < s.ema20 && s.macd < s.macdSignal);
                if (exit || i == x.size() - 1) {
                    double ret = (price - entry) / entry;
                    capital *= (1.0 + ret);
                    tradeSum += ret;
                    r.trades++;
                    if (ret > 0) r.wins++; else r.losses++;
                    in = false;
                }
            }
            peak = Math.max(peak, capital);
            double dd = peak == 0 ? 0 : (peak - capital) / peak;
            maxDd = Math.max(maxDd, dd);
        }

        r.netPct = (capital - 1.0) * 100.0;
        r.maxDrawdownPct = maxDd * 100.0;
        r.winRate = r.trades == 0 ? 0 : (100.0 * r.wins / r.trades);
        r.avgTradePct = r.trades == 0 ? 0 : (100.0 * tradeSum / r.trades);
        r.summary = "İşlem " + r.trades
                + " • Kazanma %" + IndicatorEngine.fmt(r.winRate)
                + " • Net %" + IndicatorEngine.fmt(r.netPct)
                + " • MaxDD %" + IndicatorEngine.fmt(r.maxDrawdownPct)
                + " • Ort. işlem %" + IndicatorEngine.fmt(r.avgTradePct);
        return r;
    }
}
