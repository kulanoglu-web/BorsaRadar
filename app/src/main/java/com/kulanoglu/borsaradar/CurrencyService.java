package com.kulanoglu.borsaradar;

import java.util.List;

/** Display-only FX conversion. Technical engines remain in native market currency. */
public final class CurrencyService {
    private static final long TTL_MS = 30L * 60L * 1000L;
    private static volatile double usdToEur = Double.NaN;
    private static volatile long updatedAt = 0L;
    private CurrencyService() {}

    public static double usdToEur() {
        double r=usdToEur;
        return Double.isFinite(r)&&r>0?r:Double.NaN;
    }
    public static boolean hasRate(){return Double.isFinite(usdToEur)&&usdToEur>0;}

    public static void refreshIfNeeded(){
        long now=System.currentTimeMillis();
        if(hasRate()&&now-updatedAt<TTL_MS)return;
        synchronized(CurrencyService.class){
            now=System.currentTimeMillis();
            if(hasRate()&&now-updatedAt<TTL_MS)return;
            try{
                // MarketDataService requires >=10 candles; 1mo safely satisfies that requirement.
                List<MarketDataService.Candle> data=MarketDataService.fetchDaily("USDEUR=X","1mo");
                if(data!=null&&!data.isEmpty()){
                    double r=data.get(data.size()-1).close;
                    if(Double.isFinite(r)&&r>0.3&&r<2.0){usdToEur=r;updatedAt=now;return;}
                }
            }catch(Exception ignored){}
            try{
                List<MarketDataService.Candle> data=MarketDataService.fetchDaily("EURUSD=X","1mo");
                if(data!=null&&!data.isEmpty()){
                    double eurUsd=data.get(data.size()-1).close;
                    double r=1.0/eurUsd;
                    if(Double.isFinite(r)&&r>0.3&&r<2.0){usdToEur=r;updatedAt=now;}
                }
            }catch(Exception ignored){}
        }
    }

    public static double displayValue(double nativeValue,String symbol){
        String n=MarketDataService.normalizeSymbol(symbol);
        if(n.endsWith(".IS")||n.endsWith(".DE"))return nativeValue;
        double r=usdToEur();
        return Double.isFinite(r)?nativeValue*r:nativeValue;
    }
    public static boolean isUsDollarInstrument(String symbol){
        String n=MarketDataService.normalizeSymbol(symbol);
        return !(n.endsWith(".IS")||n.endsWith(".DE"));
    }
}
