package com.kulanoglu.borsaradar;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Haber + KAP baglamini tek sonucta birlestirir. Teknik skoru degistirmez. */
public final class UnifiedContextService {
    private UnifiedContextService(){}
    public static final class Result {
        public double combinedScore,newsScore,kapScore;
        public boolean newsOk,kapOk,hasContext;
        public int kapEvents;
        public String coverage="YOK",summary="baglam verisi yok";
        public final List<String> topEvents=new ArrayList<>();
    }
    public static Result analyze(String symbol){
        UnifiedContextService.Result cached=ContextCache.get(symbol); if(cached!=null)return cached;
        Result out=new Result();
        NewsContextService.Result news=NewsContextService.safeAnalyze(symbol);
        out.newsOk=news.hasData; out.newsScore=news.score;
        KapDisclosureService.Result kap=KapDisclosureService.safeFetch(symbol);
        out.kapOk=kap.sourceOk; out.kapEvents=kap.matched;
        MultiSourceContextEngine.Result kr=MultiSourceContextEngine.analyze(EventDeduplicator.unique(kap.events));
        out.kapScore=kr.contextScore;
        boolean hasNews=news.hasData&&news.acceptedCount>0;
        boolean hasKap=kap.sourceOk&&kap.matched>0;
        out.hasContext=hasNews||hasKap;
        if(hasKap&&hasNews)out.combinedScore=clamp(kap.contextScore*.55+news.score*.45,-8,8);
        else if(hasKap)out.combinedScore=clamp(kap.contextScore,-8,8);
        else if(hasNews)out.combinedScore=clamp(news.score,-8,8);
        else out.combinedScore=0;
        for(String s:kr.topEvents)if(out.topEvents.size()<5)out.topEvents.add("KAP • "+s);
        for(String s:news.catalysts)if(out.topEvents.size()<5)out.topEvents.add("HABER • "+s);
        out.coverage=SourceCoverageTracker.label(out.newsOk,out.kapOk,false);
        out.summary=String.format(Locale.US,"Birleşik %.1f/8 • Haber %.1f • KAP %.1f • KAP olay %d • kapsama %s",out.combinedScore,out.newsScore,out.kapScore,out.kapEvents,out.coverage);
        ContextCache.put(symbol,out); return out;
    }
    private static double clamp(double x,double lo,double hi){return Math.max(lo,Math.min(hi,x));}
}
