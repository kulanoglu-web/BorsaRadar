package com.kulanoglu.borsaradar;
import java.util.*;
public final class DetailedChartController {
 public static List<MarketDataService.Candle> fetch(String symbol,int index)throws Exception{
  int i=Math.max(0,Math.min(index,ChartTimeframes.LABELS.length-1));
  String interval=ChartTimeframes.INTERVAL[i],range=ChartTimeframes.RANGE[i];
  List<MarketDataService.Candle>d=MarketDataService.fetchSeries(symbol,range,interval,180);
  // The Yahoo range is only the transport window. Enforce short visible periods explicitly.
  // Longer ranges (3m-2y) are already constrained by RANGE and must not be cut to 180 points.
  int maxPoints=maxVisiblePoints(i);
  if(maxPoints>0 && d.size()>maxPoints)d=new ArrayList<>(d.subList(d.size()-maxPoints,d.size()));
  return d;
 }
 private static int maxVisiblePoints(int i){
  switch(i){
   case 0:return 5;      // 5 dk, 1m candles
   case 1:return 15;     // 15 dk
   case 2:return 30;     // 30 dk
   case 3:return 12;     // 1 saat, 5m candles
   case 4:return 16;     // 4 saat, 15m candles
   case 5:return 96;     // 1 işlem günü, 5m candles (upper bound)
   case 6:return 80;     // 1 hafta, 30m candles (upper bound)
   case 7:return 180;    // 1 ay, hourly; provider/session count varies
   default:return 0;     // 3 ay-2 yıl: RANGE tam görünür dönemi belirler
  }
 }
 public static String label(int index){int i=Math.max(0,Math.min(index,ChartTimeframes.LABELS.length-1));return ChartTimeframes.LABELS[i];}
 private DetailedChartController(){}
}
