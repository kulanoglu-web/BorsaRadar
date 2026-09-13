package com.kulanoglu.borsaradar;

import java.util.Calendar;
import java.util.List;

/** Cuma/Pazartesi davranisini ayri bir zayif baglam sinyali olarak tutar; ana teknik sinyali ezmez. */
public final class CalendarEffectEngine {
    private CalendarEffectEngine(){}
    public static final class Result { public double fridayAvg,mondayAvg; public String note; }
    public static Result analyze(List<MarketDataService.Candle>x){
        Result r=new Result(); double fs=0,ms=0;int fn=0,mn=0;Calendar c=Calendar.getInstance();
        for(int i=1;i<x.size();i++){c.setTimeInMillis(x.get(i).time*1000L);double ret=x.get(i-1).close==0?0:(x.get(i).close/x.get(i-1).close-1)*100;int d=c.get(Calendar.DAY_OF_WEEK);if(d==Calendar.FRIDAY){fs+=ret;fn++;}if(d==Calendar.MONDAY){ms+=ret;mn++;}}
        r.fridayAvg=fn==0?0:fs/fn;r.mondayAvg=mn==0?0:ms/mn;
        r.note="Cuma ort. %"+fmt(r.fridayAvg)+" • Pazartesi ort. %"+fmt(r.mondayAvg)+" • ikincil bağlam";
        return r;
    }
    private static String fmt(double x){return String.format(java.util.Locale.US,"%.2f",x);}
}
