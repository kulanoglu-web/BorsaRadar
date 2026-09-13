package com.kulanoglu.borsaradar;

public final class SourceCoverageTracker {
    private SourceCoverageTracker(){}
    public static String label(boolean newsOk,boolean officialOk,boolean socialOk){
        int n=(newsOk?1:0)+(officialOk?1:0)+(socialOk?1:0);
        return n==3?"TAM":n==2?"İYİ":n==1?"SINIRLI":"YOK";
    }
}
