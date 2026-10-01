package com.kulanoglu.borsaradar;

import java.util.List;

/**
 * Gercek piyasa serilerinden makro/rejim baskisini olcer.
 * Makro tek basina AL uretmez; teknik sinyali destekler veya risk nedeniyle zayiflatir.
 */
public final class MacroRegimeEngine {
    private MacroRegimeEngine(){}

    public static final class Result {
        public double score;
        public int confirmations;
        public int warnings;
        public boolean riskOff;
        public String label;
        public String summary;
    }

    private static double move(String symbol,int days){
        try{
            List<MarketDataService.Candle>d=MarketDataService.fetchSeries(symbol,"3mo","1d",90);
            if(d==null||d.size()<days+2)return Double.NaN;
            double now=d.get(d.size()-1).close,old=d.get(Math.max(0,d.size()-1-days)).close;
            return old==0?Double.NaN:(now/old-1d)*100d;
        }catch(Exception e){return Double.NaN;}
    }

    public static Result analyze(String symbol){
        Result r=new Result();
        String n=MarketDataService.normalizeSymbol(symbol);
        boolean bist=n.endsWith(".IS"),de=n.endsWith(".DE");
        String equity=bist?"^XU100":de?"^GDAXI":"^IXIC";
        double eq5=move(equity,5),eq20=move(equity,20);
        double oil5=move("CL=F",5),gold5=move("GC=F",5),usdtry5=bist?move("TRY=X",5):Double.NaN;

        if(!Double.isNaN(eq5)){if(eq5>=1)r.confirmations++;else if(eq5<=-2)r.warnings++;}
        if(!Double.isNaN(eq20)){if(eq20>=2)r.confirmations++;else if(eq20<=-4)r.warnings+=2;}

        String bare=n.replace(".IS","").replace(".DE","");
        double oilSensitivity=SectorMacroSensitivityEngine.multiplier(bare,"PETROL");
        if(!Double.isNaN(oil5)&&Math.abs(oilSensitivity-1d)>.05){
            if(oil5>=5){if(oilSensitivity>1d)r.warnings++;else r.confirmations++;}
            else if(oil5<=-5){if(oilSensitivity>1d)r.confirmations++;else r.warnings++;}
        }

        if(bist&&!Double.isNaN(usdtry5)){
            if(usdtry5>=3)r.warnings++;
            else if(usdtry5<=-2)r.confirmations++;
        }

        // Gold is used as a broad defensive-stress clue, never as a standalone trade trigger.
        if(!Double.isNaN(gold5)&&gold5>=4&&(!Double.isNaN(eq5)&&eq5<0))r.warnings++;

        r.score=Math.max(-4d,Math.min(4d,r.confirmations-r.warnings));
        r.riskOff=r.warnings>=3||r.score<=-2;
        r.label=r.score>=2?"DESTEKLEYICI":r.score<=-2?"RISKLI":"NOTR";
        r.summary="Makro "+r.label+" • teyit "+r.confirmations+" • risk "+r.warnings+
                " • Endeks5 "+fmt(eq5)+" • Endeks20 "+fmt(eq20)+
                (bist?" • USDTRY5 "+fmt(usdtry5):"")+" • Petrol5 "+fmt(oil5);
        return r;
    }

    private static String fmt(double x){
        return Double.isNaN(x)?"—":String.format(java.util.Locale.GERMANY,"%+.1f%%",x);
    }
}
