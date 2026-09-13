package com.kulanoglu.borsaradar;

import java.util.List;

/** Kabul edilen haber başlıklarında en güçlü makro/jeopolitik riski bulur. */
public final class MacroHeadlineAggregator {
    private MacroHeadlineAggregator(){}
    public static final class Result { public double maxRisk; public String tag="NONE",note="Makro etki yok"; }
    public static Result analyze(List<String> titles){
        Result out=new Result(); if(titles==null)return out;
        for(String t:titles){
            MacroImpactEngine.Result r=MacroImpactEngine.analyze(t);
            if(r.risk>out.maxRisk){out.maxRisk=r.risk;out.tag=r.tag;out.note=r.note;}
        }
        return out;
    }
}
