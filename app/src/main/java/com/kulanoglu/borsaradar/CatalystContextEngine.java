package com.kulanoglu.borsaradar;

/** Haber ve KAP bilgisini teknik gorunumun yaninda baglamsal olarak gosterir. */
public final class CatalystContextEngine {
    private CatalystContextEngine(){}
    public static final class Result {
        public double newsScore,kapScore,combinedScore,contextWeight,informationStrength,qualityScore,macroRisk;
        public boolean positiveCatalyst,negativeCatalyst,technicalConflict,hasContext;
        public String note,dataStatus,coverage,summary,strengthLabel,qualityLabel,conflictLabel,macroTag,macroNote;
        public java.util.List<String> topEvents=new java.util.ArrayList<>();
    }
    public static Result analyze(String symbol,double technicalScore){
        Result out=new Result();
        UnifiedContextService.Result ctx=UnifiedContextService.analyze(symbol);
        out.newsScore=ctx.newsScore; out.kapScore=ctx.kapScore; out.combinedScore=ctx.combinedScore;
        out.informationStrength=ctx.informationStrength; out.qualityScore=ctx.qualityScore;
        out.strengthLabel=ctx.strengthLabel; out.qualityLabel=ctx.qualityLabel;
        out.macroRisk=ctx.macroRisk; out.macroTag=ctx.macroTag; out.macroNote=ctx.macroNote;
        out.hasContext=ctx.hasContext;
        out.contextWeight=out.hasContext?Math.max(-2.2,Math.min(2.2,ctx.combinedScore*0.34)):0;
        out.positiveCatalyst=out.hasContext&&ctx.combinedScore>=3.0;
        out.negativeCatalyst=out.hasContext&&ctx.combinedScore<=-3.0;
        TechnicalContextConflictEngine.State cs=TechnicalContextConflictEngine.classify(technicalScore,ctx.combinedScore,out.hasContext);
        out.technicalConflict=cs==TechnicalContextConflictEngine.State.POSITIVE_CONTEXT_CONFLICT||cs==TechnicalContextConflictEngine.State.NEGATIVE_CONTEXT_CONFLICT;
        out.conflictLabel=TechnicalContextConflictEngine.label(cs);
        out.coverage=ctx.coverage; out.summary=ctx.summary; out.topEvents.addAll(ctx.topEvents);
        out.dataStatus=ctx.hasContext?"OK":"NO_CONTEXT";
        if(!out.hasContext)out.note="Bağlam verisi yetersiz: "+ctx.summary;
        else if(out.technicalConflict)out.note=out.conflictLabel+" • teknik sinyal ile bilgi akışı aynı yönde değil.";
        else if(out.positiveCatalyst)out.note="Güncel bilgi akışı pozitif.";
        else if(out.negativeCatalyst)out.note="Güncel bilgi akışı negatif.";
        else out.note="Güncel bilgi akışı nötr.";
        return out;
    }
}
