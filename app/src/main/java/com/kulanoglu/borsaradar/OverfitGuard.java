package com.kulanoglu.borsaradar;

/** Az islem veya zayif walk-forward durumunda adaptif sonuca guveni dusurur. */
public final class OverfitGuard {
    private OverfitGuard(){}
    public static double multiplier(BacktestEngine.Result b,WalkForwardEvaluator.Result w){
        if(b==null||b.trades<3)return .55;
        if(w==null||w.train==null||w.test==null)return .70;
        if(w.stability<45)return .60;
        if(w.stability<65)return .78;
        return 1.0;
    }
}
