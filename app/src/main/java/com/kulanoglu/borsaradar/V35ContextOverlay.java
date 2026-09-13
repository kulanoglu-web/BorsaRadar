package com.kulanoglu.borsaradar;

/** V35 sonucunu korur; sadece haber/KAP/makro ile uyum veya celiski notu ekler. */
public final class V35ContextOverlay {
    private V35ContextOverlay(){}
    public static final class Result { public V35HybridEngine.Result base; public String contextState,note; public int adjustedConfidence; }
    public static Result analyze(String symbol,java.util.List<MarketDataService.Candle>data,double entryPrice){
        Result r=new Result(); r.base=V35HybridEngine.analyze(data,entryPrice);
        ShortPulseEngine.Result p=ShortPulseEngine.analyze(data); CatalystContextEngine.Result c=CatalystContextEngine.analyze(symbol,p.score);
        DecisionContextEngine.Result d=DecisionContextEngine.evaluate(p,c); r.contextState=d.state; r.note=d.note;
        r.adjustedConfidence=Math.max(5,Math.min(95,(int)Math.round(r.base.confidence+d.confidenceAdjustment)));
        return r;
    }
}
