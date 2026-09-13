package com.kulanoglu.borsaradar;

/** Maliyet ve mevcut sinyali kullanarak pozisyon bazli risk notu verir. */
public final class PortfolioRiskEngine {
    private PortfolioRiskEngine(){}
    public static final class Result { public String label,note; public double riskScore; }
    public static Result evaluate(double cost,int qty,ShortPulseEngine.Result t,CatalystContextEngine.Result c){
        Result r=new Result();
        if(t==null||cost<=0){r.label="BELIRSIZ";r.note="Pozisyon verisi yetersiz.";return r;}
        double pnlPct=(t.price/cost-1)*100;
        double risk=35;
        if(t.score<=-2.8)risk+=25; else if(t.score<=-1.3)risk+=12; else if(t.score>=3)risk-=10;
        if(c!=null&&c.hasContext){if(c.combinedScore<=-3)risk+=18;if(c.combinedScore>=3)risk-=10;if(c.macroRisk>=7)risk+=10;if(c.qualityScore<40)risk+=5;}
        if(pnlPct<-12)risk+=10; else if(pnlPct>20)risk+=5;
        r.riskScore=Math.max(0,Math.min(100,risk));
        r.label=r.riskScore>=70?"YUKSEK":r.riskScore>=45?"ORTA":"DUSUK";
        r.note="Pozisyon P/L %"+String.format(java.util.Locale.US,"%.1f",pnlPct)+" • risk "+String.format(java.util.Locale.US,"%.0f/100",r.riskScore)+" • "+r.label;
        return r;
    }
}
