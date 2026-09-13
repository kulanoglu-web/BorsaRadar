package com.kulanoglu.borsaradar;

import java.util.List;

/** Aynı veriyi kısa/orta/uzun teknik pencerelerde ayrı okur. */
public final class MultiHorizonEngine {
    private MultiHorizonEngine(){}
    public static final class View { public String label; public double strength; public String note; }
    public static final class Result { public View shortTerm,mediumTerm,longTerm; }
    public static Result analyze(List<MarketDataService.Candle>x){
        Result r=new Result();
        r.shortTerm=view("1–5 gün",slice(x,Math.min(25,x.size())));
        r.mediumTerm=view("1–4 hafta",slice(x,Math.min(60,x.size())));
        r.longTerm=view("1–3 ay",slice(x,Math.min(120,x.size())));
        return r;
    }
    private static View view(String label,List<MarketDataService.Candle>x){View v=new View();v.label=label;IndicatorEngine.Snapshot s=IndicatorEngine.analyze(x);MethodEngine.Result m=MethodEngine.analyze(s);v.strength=m.percent;v.note=m.label+" • "+s.signal;return v;}
    private static List<MarketDataService.Candle> slice(List<MarketDataService.Candle>x,int n){return x.subList(Math.max(0,x.size()-n),x.size());}
}
