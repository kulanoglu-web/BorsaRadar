package com.kulanoglu.borsaradar;

/**
 * Temel veriyi teknik zamanlamadan ayri degerlendirir.
 * Eksik finansal veri tahmin edilmez; coverage sonucu guven seviyesine yansir.
 */
public final class FundamentalAssessmentEngine {
    private FundamentalAssessmentEngine(){}

    public static final class Result {
        public int score,coverage;
        public boolean stretched,discounted;
        public String valuation,risk,summary;
    }

    public static Result assess(String symbol,MarketDataService.Fundamentals f){
        Result r=new Result();
        if(f==null){
            r.valuation="VERI YOK";r.risk="BELIRSIZ";r.summary="Temel veri yok";return r;
        }
        int known=0;
        double pb=f.priceToBook,pe=f.trailingPE;
        if(validPositive(pb)){
            known++;
            if(pb<=0.75)r.score+=2;
            else if(pb<=1.5)r.score+=1;
            else if(pb>=6)r.score-=2;
            else if(pb>=4)r.score-=1;
        }
        if(validPositive(pe)){
            known++;
            if(pe<=7)r.score+=2;
            else if(pe<=12)r.score+=1;
            else if(pe>=35)r.score-=2;
            else if(pe>=22)r.score-=1;
        }
        if(!Double.isNaN(f.equity)){known++;if(f.equity<=0)r.score-=2;}
        if(!Double.isNaN(f.netIncome)){known++;if(f.netIncome<0)r.score-=2;else if(f.netIncome>0)r.score+=1;}

        r.coverage=(int)Math.round(known/4d*100d);
        r.score=Math.max(-5,Math.min(5,r.score));
        r.discounted=r.score>=2&&r.coverage>=50;
        r.stretched=r.score<=-2&&r.coverage>=50;
        r.valuation=r.score>=2?"UCUZ":r.score<=-2?"PAHALI":"MAKUL/BELIRSIZ";
        r.risk=(!Double.isNaN(f.equity)&&f.equity<=0)||(!Double.isNaN(f.netIncome)&&f.netIncome<0)?"YUKSEK":r.coverage<50?"BELIRSIZ":"NORMAL";
        r.summary="Temel "+r.valuation+" • skor "+r.score+" • kapsam %"+r.coverage+
                " • F/K "+fmt(pe)+" • PD/DD "+fmt(pb)+" • risk "+r.risk;
        return r;
    }

    private static boolean validPositive(double x){return !Double.isNaN(x)&&!Double.isInfinite(x)&&x>0;}
    private static String fmt(double x){return validPositive(x)?String.format(java.util.Locale.GERMANY,"%.2f",x):"—";}
}
