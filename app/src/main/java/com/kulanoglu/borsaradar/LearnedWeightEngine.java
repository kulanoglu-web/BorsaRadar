package com.kulanoglu.borsaradar;

import java.util.LinkedHashMap;
import java.util.Map;

/** Hisse bazli basariyi agirliklara cevirir; hicbir metodun asiri baskin olmasina izin vermez. */
public final class LearnedWeightEngine {
    private LearnedWeightEngine(){}
    public static final class Result {
        public final Map<String,Double> weights=new LinkedHashMap<>();
        public String summary;
    }
    public static Result build(MethodPerformanceLearner.Result p){
        Result r=new Result();
        String[] keys={"INDICATOR","METHOD","SHORT","MOST_QQE","V35"};
        double total=0;
        for(String k:keys){
            MethodPerformanceLearner.Stat s=p==null?null:p.stats.get(k);
            double evidence=s==null?0:Math.min(1.0,s.samples/18.0);
            double acc=s==null?50:s.accuracy;
            double w=.20 + evidence*((acc-50)/100.0);
            w=Math.max(.10,Math.min(.32,w));
            r.weights.put(k,w); total+=w;
        }
        for(String k:keys)r.weights.put(k,r.weights.get(k)/total);
        StringBuilder b=new StringBuilder("Ogrenilen agirlik: ");
        for(String k:keys)b.append(k).append(' ').append(IndicatorEngine.fmt(r.weights.get(k)*100)).append("% • ");
        r.summary=b.substring(0,b.length()-3);
        return r;
    }
}
