package com.kulanoglu.borsaradar;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Haber + KAP baglamini tek sonucta birlestirir. Teknik skoru degistirmez. */
public final class UnifiedContextService {
    private UnifiedContextService(){}
    public static final class Result {
        public double combinedScore,newsScore,kapScore,informationStrength,qualityScore,macroRisk,macroSensitivity;
        public boolean newsOk,kapOk,hasContext,stale;
        public int kapEvents,criticalEvents,healthScore;
        public String coverage="YOK",summary="baglam verisi yok",healthLabel="YOK",qualityLabel="YOK",strengthLabel="ZAYIF",macroTag="NONE",macroNote="Makro etki yok";
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
        out.criticalEvents=news.criticalCount+kr.criticalCount;
        boolean hasNews=news.hasData&&news.acceptedCount>0;
        boolean hasKap=kap.sourceOk&&kap.matched>0;
        out.hasContext=hasNews||hasKap;
        if(!out.hasContext){
            Result stale=ContextCache.getStale(symbol);
            if(stale!=null){stale.stale=true;stale.summary="ESKİ VERİ ("+ContextCache.ageMinutes(symbol)+" dk) • "+stale.summary;return stale;}
        }
        if(hasKap&&hasNews)out.combinedScore=clamp(kap.contextScore*.55+news.score*.45,-8,8);
        else if(hasKap)out.combinedScore=clamp(kap.contextScore,-8,8);
        else if(hasNews)out.combinedScore=clamp(news.score,-8,8);
        else out.combinedScore=0;
        for(String s:kr.topEvents)if(out.topEvents.size()<5)out.topEvents.add("KAP • "+s);
        for(String s:news.catalysts)if(out.topEvents.size()<5)out.topEvents.add("HABER • "+s);
        out.coverage=SourceCoverageTracker.label(out.newsOk,out.kapOk,false);
        ContextHealthEngine.Result h=ContextHealthEngine.evaluate(out); out.healthScore=h.score; out.healthLabel=h.label;
        ContextQualityEngine.Result q=ContextQualityEngine.score(out.newsOk,out.kapOk,news.acceptedCount,out.kapEvents,out.criticalEvents);
        out.qualityScore=q.quality; out.qualityLabel=q.label;
        InformationStrengthEngine.Result is=InformationStrengthEngine.score(out.combinedScore,out.qualityScore,out.criticalEvents);
        out.informationStrength=is.strength; out.strengthLabel=is.label;
        MacroHeadlineAggregator.Result mr=MacroHeadlineAggregator.analyze(news.acceptedTitles);
        out.macroTag=mr.tag; out.macroNote=mr.note;
        out.macroSensitivity=SectorMacroSensitivityEngine.multiplier(symbol,mr.tag);
        out.macroRisk=Math.min(10,mr.maxRisk*out.macroSensitivity);
        out.summary=String.format(Locale.US,"Birleşik %.1f/8 • Haber %.1f • KAP %.1f • Bilgi gücü %.0f/100 %s • kalite %.0f/100 • kritik %d • makro %s %.1f/10 • kapsama %s",out.combinedScore,out.newsScore,out.kapScore,out.informationStrength,out.strengthLabel,out.qualityScore,out.criticalEvents,out.macroTag,out.macroRisk,out.coverage);
        ContextCache.put(symbol,out); return out;
    }
    private static double clamp(double x,double lo,double hi){return Math.max(lo,Math.min(hi,x));}
}
