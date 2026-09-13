package com.kulanoglu.borsaradar;

import java.util.List;

/** Hissenin ait oldugu ana piyasanin trend rejimini ayri olarak olcer. */
public final class MarketRegimeService {
    private MarketRegimeService(){}
    public static final class Result {
        public String benchmark,label,note;
        public double score;
        public boolean riskOff;
    }
    public static Result analyze(String symbol){
        Result r=new Result();
        String n=MarketDataService.normalizeSymbol(symbol);
        r.benchmark=n.endsWith(".IS")?"^XU100":n.endsWith(".DE")?"^GDAXI":"^IXIC";
        try{
            List<MarketDataService.Candle>d=MarketDataService.fetchDaily(r.benchmark,"3mo");
            IndicatorEngine.Snapshot s=IndicatorEngine.analyze(d);
            r.score=0;
            if(s.trendUp)r.score+=2; else if(s.close<s.ema50)r.score-=2;
            if(s.macd>s.macdSignal)r.score+=1; else r.score-=1;
            if(s.rsi14>=50&&s.rsi14<=70)r.score+=1; else if(s.rsi14<42)r.score-=1;
            if(s.cmf20>0)r.score+=.7; else if(s.cmf20<-.05)r.score-=.7;
            r.riskOff=r.score<=-2;
            r.label=r.score>=2.5?"RISK-ON":r.score<=-2?"RISK-OFF":"KARISIK";
            r.note=r.benchmark+" • "+r.label+" • rejim "+IndicatorEngine.fmt(r.score);
        }catch(Exception e){r.label="VERI YOK";r.note="Piyasa rejimi alinamadi";}
        return r;
    }
}
