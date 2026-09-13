package com.kulanoglu.borsaradar;

import java.util.List;

/** Tek doneme ezberlemeyi azaltmak icin eski ve yeni veri dilimlerini ayri test eder. */
public final class WalkForwardEvaluator {
    private WalkForwardEvaluator(){}
    public static final class Result {public BacktestEngine.Result train,test;public double stability;public String summary;}
    public static Result evaluate(String symbol,List<MarketDataService.Candle> data){
        Result r=new Result();
        if(data==null||data.size()<180){r.summary="Walk-forward icin veri yetersiz";return r;}
        int cut=(int)(data.size()*.70);
        r.train=BacktestEngine.run(symbol,data.subList(0,cut));
        r.test=BacktestEngine.run(symbol,data.subList(Math.max(0,cut-70),data.size()));
        double gap=Math.abs(r.train.winRate-r.test.winRate)+Math.abs(r.train.avgTradePct-r.test.avgTradePct)*3;
        r.stability=Math.max(0,100-gap);
        r.summary="WF stabilite "+IndicatorEngine.fmt(r.stability)+"/100 • train "+IndicatorEngine.fmt(r.train.winRate)+"% • test "+IndicatorEngine.fmt(r.test.winRate)+"%";
        return r;
    }
}
