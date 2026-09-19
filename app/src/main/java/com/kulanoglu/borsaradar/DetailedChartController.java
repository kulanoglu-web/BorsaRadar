package com.kulanoglu.borsaradar;
import java.util.*;
/** Seçilen zaman dilimini doğrudan veri servisine taşır. Grafik state'i burada değiştirilmez. */
public final class DetailedChartController {
 public static List<MarketDataService.Candle> fetch(String symbol,int index)throws Exception{
  int i=ChartTimeframes.clamp(index);
  List<MarketDataService.Candle> d=MarketDataService.fetchSeries(symbol,ChartTimeframes.RANGE[i],ChartTimeframes.INTERVAL[i],0);
  if(d==null||d.isEmpty())throw new Exception(ChartTimeframes.label(i)+" için grafik verisi yok");
  int n=visiblePoints(i);
  if(n>0&&d.size()>n)d=new ArrayList<>(d.subList(d.size()-n,d.size()));
  return d;
 }
 public static List<MarketDataService.Candle> cached(String symbol,int index){
  int i=ChartTimeframes.clamp(index);
  List<MarketDataService.Candle> d=MarketDataService.cachedSeries(symbol,ChartTimeframes.RANGE[i],ChartTimeframes.INTERVAL[i]);
  if(d==null||d.isEmpty())return null;
  int n=visiblePoints(i);
  if(n>0&&d.size()>n)d=new ArrayList<>(d.subList(d.size()-n,d.size()));
  return d;
 }
 private static int visiblePoints(int i){
  switch(i){case 0:return 5;case 1:return 15;case 2:return 30;case 3:return 12;case 4:return 16;case 5:return 96;case 6:return 80;case 7:return 180;case 8:return 90;case 9:return 180;case 10:return 260;case 11:return 520;default:return 0;}
 }
 public static String label(int i){return ChartTimeframes.label(i);}
 private DetailedChartController(){}
}
