package com.kulanoglu.borsaradar;

/** Eski ve yeni teknik indikatorlerin kac tanesinin ayni yone baktigini olcer. */
public final class TechnicalConsensusEngine {
    private TechnicalConsensusEngine(){}
    public static final class Result { public int positive,negative,neutral; public double percent; public String label; }
    public static Result score(IndicatorEngine.Snapshot s,AdditionalIndicatorEngine.Result a,MethodEngine.Result m){
        Result r=new Result();
        vote(r,s.trendUp?1:s.close<s.ema50?-1:0); vote(r,s.macd>s.macdSignal?1:-1); vote(r,s.rsi14>=48&&s.rsi14<=70?1:s.rsi14>78?-1:0);
        vote(r,s.cmf20>0.03?1:s.cmf20<-0.05?-1:0); vote(r,s.cci20>50?1:s.cci20<-100?-1:0); vote(r,s.stochastic14>=50&&s.stochastic14<90?1:s.stochastic14>94?-1:0);
        vote(r,s.adx14>=20&&s.trendUp?1:s.adx14>=20&&s.close<s.ema50?-1:0); vote(r,s.volumePressure20>0.05?1:s.volumePressure20<-0.05?-1:0);
        vote(r,a.mostBull?1:-1); vote(r,a.qqeBull?1:-1); vote(r,a.abovePivot?1:-1); vote(r,m.percent>=58?1:m.percent<43?-1:0);
        int total=r.positive+r.negative+r.neutral; r.percent=total==0?50:100.0*r.positive/total;
        r.label=r.positive>=8?"GENIS TEKNIK TEYIT":r.negative>=7?"GENIS TEKNIK ZAYIFLIK":"KARISIK TEKNIK";
        return r;
    }
    private static void vote(Result r,int v){if(v>0)r.positive++;else if(v<0)r.negative++;else r.neutral++;}
}
