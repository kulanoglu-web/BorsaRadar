package com.kulanoglu.borsaradar;

public final class MarketEvent {
    public String symbol,title,summary,provider,url;
    public long publishedAt;
    public InformationImportanceEngine.Source source=InformationImportanceEngine.Source.OTHER;
    public int confirmations;
    public double relevance=1.0;
    public double ageHours(){return publishedAt<=0?999:Math.max(0,(System.currentTimeMillis()/1000L-publishedAt)/3600.0);}
}
