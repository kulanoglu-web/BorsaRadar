package com.kulanoglu.borsaradar;

/** Guvensiz veya zayif baglamda asiri kesin sonuc uretilmesini engelleyen kapı. */
public final class ContextRiskGate {
    private ContextRiskGate(){}
    public static boolean allowStrongContext(UnifiedContextService.Result r){
        return r!=null&&r.hasContext&&r.qualityScore>=ContextThresholds.LOW_QUALITY&&r.healthScore>=35;
    }
    public static String reason(UnifiedContextService.Result r){
        if(r==null||!r.hasContext)return "baglam yok";
        if(r.qualityScore<ContextThresholds.LOW_QUALITY)return "baglam kalitesi dusuk";
        if(r.healthScore<35)return "kaynak sagligi dusuk";
        return "uygun";
    }
}
