package com.kulanoglu.borsaradar;

/** Haber/katalizor katmani; teknik motoru degistirmez, baglam kalitesini ve celiskiyi isaretler. */
public final class CatalystContextEngine {
    private CatalystContextEngine(){}
    public static final class Result {
        public double newsScore,contextWeight;
        public boolean positiveCatalyst,negativeCatalyst,technicalConflict,hasContext;
        public String note,dataStatus,coverage;
    }
    public static Result analyze(String symbol,double technicalScore){
        Result out=new Result(); NewsContextService.Result news=NewsContextService.safeAnalyze(symbol);
        out.newsScore=news.score;out.dataStatus=news.dataStatus;out.hasContext=news.hasData&&news.acceptedCount>0;
        out.contextWeight=out.hasContext?Math.max(-2.2,Math.min(2.2,news.score*0.34)):0;
        out.positiveCatalyst=out.hasContext&&news.score>=3.0;out.negativeCatalyst=out.hasContext&&news.score<=-3.0;
        out.technicalConflict=out.hasContext&&technicalScore<=-1.3&&out.positiveCatalyst;
        out.coverage=SourceCoverageTracker.label(news.hasData,false,false);
        if(!out.hasContext)out.note="Bağlam verisi yetersiz: "+news.summary;
        else if(out.technicalConflict)out.note="Teknik zayıflık ile güncel pozitif bilgi akışı çelişiyor.";
        else if(out.positiveCatalyst)out.note="Güncel bilgi akışı pozitif.";
        else if(out.negativeCatalyst)out.note="Güncel bilgi akışı negatif.";
        else out.note="Güncel bilgi akışı nötr.";
        return out;
    }
}
