package com.kulanoglu.borsaradar;

import java.util.LinkedHashMap;
import java.util.Map;

/** Backtest sonucuna gore teknik metod agirliklarini sinirli aralikta ayarlar. */
public final class AdaptiveMethodWeights {
    private AdaptiveMethodWeights(){}
    public static final class Result {
        public final Map<String,Double> weights=new LinkedHashMap<>();
        public String summary;
    }
    public static Result from(BacktestEngine.Result b){
        Result r=new Result();
        double quality=0;
        if(b!=null&&b.trades>=3){quality=(b.winRate-50)/100.0 + Math.max(-.20,Math.min(.20,b.netPct/100.0));}
        put(r,"LEGACY",.28+quality*.10);
        put(r,"SHORT_PULSE",.25+quality*.08);
        put(r,"V35",.18+quality*.06);
        put(r,"ADDITIONAL",.17+quality*.05);
        put(r,"CONTEXT",.12-quality*.04);
        normalize(r);
        r.summary="Adaptif agirlik • backtest islem "+(b==null?0:b.trades)+" • kazanma %"+(b==null?"0":IndicatorEngine.fmt(b.winRate));
        return r;
    }
    private static void put(Result r,String k,double v){r.weights.put(k,Math.max(.06,Math.min(.45,v)));}
    private static void normalize(Result r){double s=0;for(double v:r.weights.values())s+=v;for(String k:r.weights.keySet())r.weights.put(k,r.weights.get(k)/s);}
}
