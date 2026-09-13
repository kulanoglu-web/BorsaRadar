package com.kulanoglu.borsaradar;

/**
 * Teknik motorun yanında çalışan bağımsız bağlam katmanı.
 * Global hisselerde güncel haber/katalizör akışının teknik zayıflıkla çelişip
 * çelişmediğini işaretler; temel teknik hesapları değiştirmez.
 */
public final class CatalystContextEngine {
    private CatalystContextEngine(){}

    public static final class Result {
        public double newsScore;
        public double contextWeight;
        public boolean positiveCatalyst;
        public boolean negativeCatalyst;
        public boolean technicalConflict;
        public String note;
    }

    public static Result analyze(String symbol,double technicalScore){
        Result out=new Result();
        NewsContextService.Result news=NewsContextService.safeAnalyze(symbol);
        out.newsScore=news.score;
        out.contextWeight=Math.max(-2.2,Math.min(2.2,news.score*0.34));
        out.positiveCatalyst=news.score>=3.0;
        out.negativeCatalyst=news.score<=-3.0;
        out.technicalConflict=technicalScore<=-1.3 && out.positiveCatalyst;
        if(out.technicalConflict) out.note="Teknik zayıflık var; ancak güncel pozitif katalizörler karşı yönde. Tek başına teknik skorla karar verme.";
        else if(out.positiveCatalyst) out.note="Güncel haber/katalizör akışı pozitif.";
        else if(out.negativeCatalyst) out.note="Güncel haber/katalizör akışı negatif.";
        else out.note="Haber/katalizör etkisi nötr veya yetersiz.";
        return out;
    }
}
