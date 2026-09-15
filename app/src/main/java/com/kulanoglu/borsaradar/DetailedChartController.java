package com.kulanoglu.borsaradar;
import java.util.*;
public final class DetailedChartController {
 public static List<MarketDataService.Candle> fetch(String symbol,int index)throws Exception{
  int i=Math.max(0,Math.min(index,ChartTimeframes.LABELS.length-1));
  String interval=ChartTimeframes.INTERVAL[i],range=ChartTimeframes.RANGE[i];
  List<MarketDataService.Candle>d=MarketDataService.fetchSeries(symbol,range,interval,180);
  if(i==4&&"60m".equals(interval))d=MarketDataService.aggregateHours(d,4);
  return d;
 }
 public static String label(int index){int i=Math.max(0,Math.min(index,ChartTimeframes.LABELS.length-1));return ChartTimeframes.LABELS[i];}
 private DetailedChartController(){}
}
