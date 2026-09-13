package com.kulanoglu.borsaradar;

import java.util.ArrayList;
import java.util.List;

/** Tum hisseler icin KAP/haber/X/resmi kaynak olaylarini tek puanda toplar. */
public final class MultiSourceContextEngine {
    private MultiSourceContextEngine(){}
    public static final class Event {
        public final InformationImportanceEngine.Source source; public final String title; public final double ageHours; public final int confirmations;
        public Event(InformationImportanceEngine.Source s,String t,double a,int c){source=s;title=t;ageHours=a;confirmations=c;}
    }
    public static final class Result {
        public double contextScore; public double maxImportance; public int criticalCount; public String summary;
        public final List<String> topEvents=new ArrayList<>();
    }
    public static Result analyze(List<Event> events){
        Result r=new Result(); if(events==null||events.isEmpty()){r.summary="Bağlam verisi yok";return r;}
        double weighted=0,den=0;
        for(Event e:events){
            InformationImportanceEngine.Score s=InformationImportanceEngine.score(e.source,e.title,e.ageHours,e.confirmations);
            double w=Math.max(.15,s.importance/100.0); weighted+=s.signedImpact*w; den+=w;
            r.maxImportance=Math.max(r.maxImportance,s.importance); if(s.importance>=78)r.criticalCount++;
            if(s.importance>=58 && r.topEvents.size()<5)r.topEvents.add(s.tier+" • "+e.title+" • "+s.reason);
        }
        r.contextScore=den==0?0:Math.max(-10,Math.min(10,weighted/den));
        r.summary="Bağlam "+String.format(java.util.Locale.US,"%+.1f",r.contextScore)+"/10 • en önemli "+String.format(java.util.Locale.US,"%.0f",r.maxImportance)+"/100 • kritik "+r.criticalCount;
        return r;
    }
}
