package com.kulanoglu.borsaradar;

/** Radar adaylarini teknik skor + onceden yuklenmis baglamla yeniden siralamaya yarar. */
public final class RadarContextRanker {
    private RadarContextRanker(){}
    public static double score(double technical, UnifiedContextService.Result c){
        if(c==null||!c.hasContext)return technical;
        double info=(c.combinedScore/8.0)*1.4;
        double quality=(c.qualityScore>=60?0.25:0);
        double macro=c.macroRisk>=7?-0.55:0;
        return technical+info+quality+macro;
    }
}
