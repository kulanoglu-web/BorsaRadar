package com.kulanoglu.borsaradar;

/** Teknik guveni baglamla birlikte okunabilir tek bir guven yuzdesine cevirir. */
public final class SignalConfidenceEngine {
    private SignalConfidenceEngine(){}
    public static int combined(ShortPulseEngine.Result t,CatalystContextEngine.Result c){
        if(t==null)return 0;
        double v=t.confidence;
        DecisionContextEngine.Result d=DecisionContextEngine.evaluate(t,c);
        v+=d.confidenceAdjustment;
        if(c!=null&&c.hasContext&&c.qualityScore>=70)v+=4;
        return (int)Math.max(5,Math.min(95,Math.round(v)));
    }
}
