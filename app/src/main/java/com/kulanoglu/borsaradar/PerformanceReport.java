package com.kulanoglu.borsaradar;
import java.util.*;
public final class PerformanceReport{
 private PerformanceReport(){}
 public static final class Row{public final String id,signal;public final double entry,current,returnPct;public final boolean targetHit,stopHit;Row(String i,String s,double e,double c,double r,boolean t,boolean st){id=i;signal=s;entry=e;current=c;returnPct=r;targetHit=t;stopHit=st;}}
 public static final class Summary{public int count,winners,targetHits,stopHits;public double sumReturnPct;public double avgReturnPct(){return count==0?Double.NaN:sumReturnPct/count;}public double winRatePct(){return count==0?Double.NaN:100d*winners/count;}}
 public static Map<String,Row> evaluate(List<PortfolioBook.Position> pos,Map<String,List<MarketDataService.Candle>> history,Map<String,Double> prices){
  Map<String,Row> out=new LinkedHashMap<>();if(pos==null)return out;
  for(PortfolioBook.Position p:pos){Double cur=prices==null?null:prices.get(p.symbol);if(cur==null||!(cur>0))continue;List<MarketDataService.Candle>d=history==null?null:history.get(p.symbol);boolean th=false,sh=false;
   if(d!=null&&!d.isEmpty()){int idx=findEntry(d,p.date);if(idx>=20){List<MarketDataService.Candle> sub=d.subList(0,idx+1);BrokerStyleIndicator.Result br=BrokerStyleIndicator.analyze(sub,null);if(br!=null){double target=br.daily.target1,stop=br.daily.stop;for(int i=idx+1;i<d.size();i++){MarketDataService.Candle c=d.get(i);boolean t=c.high>=target,s=c.low<=stop;if(t&&s){sh=true;break;}if(s){sh=true;break;}if(t){th=true;break;}}}}}
   out.put(p.id,new Row(p.id,p.signal,p.price,cur,(cur/p.price-1d)*100d,th,sh));
  }return out;
 }
 public static Map<String,Summary> summarize(List<PortfolioBook.Position> pos,Map<String,Row> rows){Map<String,Summary>m=new LinkedHashMap<>();if(pos==null)return m;for(PortfolioBook.Position p:pos){Row r=rows.get(p.id);if(r==null)continue;Summary s=m.get(p.signal);if(s==null){s=new Summary();m.put(p.signal,s);}s.count++;s.sumReturnPct+=r.returnPct;if(r.returnPct>0)s.winners++;if(r.targetHit)s.targetHits++;if(r.stopHit)s.stopHits++;}return m;}
 private static int findEntry(List<MarketDataService.Candle>d,long ms){if(d==null||d.isEmpty())return -1;long sec=ms/1000L,best=Long.MAX_VALUE;int bi=-1;for(int i=0;i<d.size();i++){long x=Math.abs(d.get(i).time-sec);if(x<best){best=x;bi=i;}}return bi;}
}