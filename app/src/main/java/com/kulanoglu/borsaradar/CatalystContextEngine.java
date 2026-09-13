package com.kulanoglu.borsaradar;

/** Haber ve KAP bilgisini teknik gorunumun yaninda baglamsal olarak gosterir. */
public final class CatalystContextEngine {
    private CatalystContextEngine(){}
    public static final class Result {
        public double newsScore,kapScore,combinedScore,contextWeight;
        public boolean positiveCatalyst,negativeCatalyst,technicalConflict,hasContext;
        public String note,dataStatus,coverage,summary;
        public java.util.List<String> topEvents=new java.util.ArrayList<>();
    }
    public static Result analyze(String symbol,double technicalScore){
        Result out=new Result();
        UnifiedContextService.Result ctx=UnifiedContextService.analyze(symbol);
        out.newsScore=ctx.newsScore;
        out.kapScore=ctx.kapScore;
        out.combinedScore=ctx.combinedScore;
        out.hasContext=ctx.hasContext;
        out.contextWeight=out.hasContext?Math.max(-2.2,Math.min(2.2,ctx.combinedScore*0.34)):0;
        out.positiveCatalyst=out.hasContext&&ctx.combinedScore>=3.0;
        out.negativeCatalyst=out.hasContext&&ctx.combinedScore<=-3.0;
        out.technicalConflict=out.hasContext&&technicalScore<=-1.3&&out.positiveCatalyst;
        out.coverage=ctx.coverage;
        out.summary=ctx.summary;
        out.topEvents.addAll(ctx.topEvents);
        out.dataStatus=ctx.hasContext?"OK":"NO_CONTEXT";
        if(!out.hasContext)out.note="Bağlam verisi yetersiz: "+ctx.summary;
        else if(out.technicalConflict)out.note="Teknik zayıflık ile güncel pozitif bilgi akışı çelişiyor.";
        else if(out.positiveCatalyst)out.note="Güncel bilgi akışı pozitif.";
        else if(out.negativeCatalyst)out.note="Güncel bilgi akışı negatif.";
        else out.note="Güncel bilgi akışı nötr.";
        return out;
    }
}
