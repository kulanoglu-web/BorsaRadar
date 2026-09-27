package com.kulanoglu.borsaradar;

import java.util.List;

public final class BacktestEngine {
    private BacktestEngine() {}

    public static final class Result {
        public int trades, wins, losses;
        public double netPct, maxDrawdownPct, winRate, avgTradePct;
        public double customSignalReturnPct, customWinRate, custom2dReturnPct, custom10dReturnPct, custom20dReturnPct, profitFactor, expectancyPct;
        public int customSignals, customWins, custom2dWins, custom10dWins, custom20dWins;
        public String bestProfile="BALANCED";
        public double fastScore, balancedScore, confirmedScore;
        public String summary;
    }

    /** Genel optimizasyonda TUPRS varsayilan olarak haric tutulur. */
    public static Result run(String symbol,List<MarketDataService.Candle> x) {
        String s=symbol==null?"":symbol.trim().toUpperCase();
        if("TUPRS".equals(s)||"TUPRS.IS".equals(s)){
            Result r=new Result(); r.summary="TUPRS genel optimizasyon/backtest havuzundan hariç"; return r;
        }
        return runInternal(s,x);
    }

    public static Result run(List<MarketDataService.Candle> x) {
        return runInternal(symbolFromSlice(x),x);
    }

    private static Result runInternal(String symbol,List<MarketDataService.Candle> x) {
        Result r = new Result();
        if (x==null || x.size() < 90) { r.summary = "Backtest için yetersiz veri"; return r; }

        double capital = 1.0, peak = 1.0, maxDd = 0;
        boolean in = false;
        double entry = 0, stop = 0, highest = 0;
        double tradeSum = 0;
        double customReturnSum=0, custom2Sum=0, custom10Sum=0, custom20Sum=0, grossWin=0, grossLoss=0;
        int customSignals=0,customWins=0;

        for (int i = 60; i < x.size(); i++) {
            List<MarketDataService.Candle> slice = x.subList(0, i + 1);
            IndicatorEngine.Snapshot s = IndicatorEngine.analyze(slice);
            double price = x.get(i).close;

            // BRTV/BRM/BRH forward validation: only information available up to day i is used.
            try {
                ShortPulseEngine.Result pulse=ShortPulseEngine.analyze(slice, symbol);
                if((pulse.recommendation.contains("AL") || pulse.earlyBreakout) && i+5<x.size()){
                    double future=x.get(i+5).close;
                    double forward=price==0?0:(future/price-1.0)*100.0;
                    customReturnSum+=forward; customSignals++; if(forward>0)customWins++;
                    if(i+2<x.size()){double z=(x.get(i+2).close/price-1)*100;custom2Sum+=z;if(z>0)r.custom2dWins++;}
                    if(i+10<x.size()){double z=(x.get(i+10).close/price-1)*100;custom10Sum+=z;if(z>0)r.custom10dWins++;}
                    if(i+20<x.size()){double z=(x.get(i+20).close/price-1)*100;custom20Sum+=z;if(z>0)r.custom20dWins++;}
                }
            } catch(Exception ignored) {}

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
                    tradeSum += ret; if(ret>0)grossWin+=ret;else grossLoss+=-ret;
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
        r.customSignals=customSignals; r.customWins=customWins;
        r.customWinRate=customSignals==0?0:100.0*customWins/customSignals;
        r.customSignalReturnPct=customSignals==0?0:customReturnSum/customSignals;
        r.custom2dReturnPct=customSignals==0?0:custom2Sum/customSignals; r.custom10dReturnPct=customSignals==0?0:custom10Sum/customSignals; r.custom20dReturnPct=customSignals==0?0:custom20Sum/customSignals;
        r.profitFactor=grossLoss==0?(grossWin>0?99:0):grossWin/grossLoss; r.expectancyPct=r.avgTradePct;
        ProfileTest fast=testProfile(symbol,x,ShortPulseEngine.Profile.FAST);
        ProfileTest balanced=testProfile(symbol,x,ShortPulseEngine.Profile.BALANCED);
        ProfileTest confirmed=testProfile(symbol,x,ShortPulseEngine.Profile.CONFIRMED);
        r.fastScore=fast.score(); r.balancedScore=balanced.score(); r.confirmedScore=confirmed.score();
        if(r.fastScore>=r.balancedScore && r.fastScore>=r.confirmedScore)r.bestProfile="FAST";
        else if(r.confirmedScore>=r.fastScore && r.confirmedScore>=r.balancedScore)r.bestProfile="CONFIRMED";
        else r.bestProfile="BALANCED";
        r.summary = "İşlem " + r.trades
                + " • Kazanma %" + IndicatorEngine.fmt(r.winRate)
                + " • Net %" + IndicatorEngine.fmt(r.netPct)
                + " • MaxDD %" + IndicatorEngine.fmt(r.maxDrawdownPct)
                + " • Ort. işlem %" + IndicatorEngine.fmt(r.avgTradePct)
                + " • BR sinyal " + r.customSignals
                + " • BR başarı %" + IndicatorEngine.fmt(r.customWinRate)
                + " • BR 2g %" + IndicatorEngine.fmt(r.custom2dReturnPct)
                + " • BR 5g %" + IndicatorEngine.fmt(r.customSignalReturnPct)
                + " • BR 10g %" + IndicatorEngine.fmt(r.custom10dReturnPct)
                + " • BR 20g %" + IndicatorEngine.fmt(r.custom20dReturnPct)
                + " • PF " + IndicatorEngine.fmt(r.profitFactor)
                + " • En iyi profil " + r.bestProfile
                + " [F " + IndicatorEngine.fmt(r.fastScore)
                + " / B " + IndicatorEngine.fmt(r.balancedScore)
                + " / C " + IndicatorEngine.fmt(r.confirmedScore) + "]";
        return r;
    }
    private static final class ProfileTest {
        int signals,wins; double sum;
        double score(){if(signals<3)return -999;double win=100.0*wins/signals,avg=sum/signals;return avg*2.2+win/18.0-Math.max(0,5-signals)*0.4;}
    }
    private static ProfileTest testProfile(String symbol,List<MarketDataService.Candle>x,ShortPulseEngine.Profile profile){
        ProfileTest t=new ProfileTest();
        for(int i=60;i+5<x.size();i++){
            try{
                List<MarketDataService.Candle>slice=x.subList(0,i+1);
                ShortPulseEngine.Result p=ShortPulseEngine.analyze(slice,symbol,profile);
                if("AL".equals(p.recommendation)||p.earlyBreakout){
                    double price=x.get(i).close,future=x.get(i+5).close;
                    double ret=price==0?0:(future/price-1.0)*100.0;
                    t.signals++;t.sum+=ret;if(ret>0)t.wins++;
                }
            }catch(Exception ignored){}
        }
        return t;
    }

    private static String symbolFromSlice(List<MarketDataService.Candle> x){
        if(x==null||x.isEmpty())return "";
        String s=x.get(x.size()-1).symbol;
        return s==null?"":s;
    }
}
