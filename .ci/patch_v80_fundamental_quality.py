from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/FundamentalQualityEngine.java')
p.write_text('''package com.kulanoglu.borsaradar;

/** Fundamental quality/risk layer. Values must come from real filings/provider data; missing fields stay neutral. */
public final class FundamentalQualityEngine {
 public static final class Input {
  public Double revenueGrowth, grossProfitGrowth, ebitdaGrowth, netIncomeGrowth;
  public Double currentAssetsGrowth, fixedAssetsGrowth, totalAssetsGrowth, equityGrowth;
  public Double netDebtToEquity, netCashChange, pe;
 }
 public static final class Result {
  public final int score; public final String label, strong, watch, risk;
  Result(int s,String l,String a,String b,String c){score=s;label=l;strong=a;watch=b;risk=c;}
 }
 private FundamentalQualityEngine(){}
 private static boolean ok(Double x){return x!=null&&!x.isNaN()&&!x.isInfinite();}
 private static String pct(String n,Double x){return ok(x)?n+" "+(x>=0?"+":"")+String.format(java.util.Locale.US,"%.1f%%",x):"";}
 public static Result evaluate(Input i){
  if(i==null)return new Result(50,"VERİ BEKLENİYOR","","",""); int s=50;
  StringBuilder g=new StringBuilder(), y=new StringBuilder(), r=new StringBuilder();
  if(ok(i.revenueGrowth)){if(i.revenueGrowth>2){s+=8;g.append(pct("Ciro",i.revenueGrowth)).append(" • ");}else if(i.revenueGrowth<0){s-=7;y.append(pct("Ciro",i.revenueGrowth)).append(" • ");}}
  if(ok(i.grossProfitGrowth)){if(i.grossProfitGrowth>=0){s+=5;g.append(pct("Brüt kâr",i.grossProfitGrowth)).append(" • ");}else if(i.grossProfitGrowth<-10){s-=9;y.append(pct("Brüt kâr",i.grossProfitGrowth)).append(" • ");}}
  if(ok(i.ebitdaGrowth)){if(i.ebitdaGrowth>=0){s+=7;g.append(pct("FAVÖK",i.ebitdaGrowth)).append(" • ");}else if(i.ebitdaGrowth<-5){s-=10;y.append(pct("FAVÖK",i.ebitdaGrowth)).append(" • ");}}
  if(ok(i.netIncomeGrowth)){if(i.netIncomeGrowth>0){s+=8;g.append(pct("Net kâr",i.netIncomeGrowth)).append(" • ");}else if(i.netIncomeGrowth<-25){s-=14;r.append(pct("Net dönem kârı",i.netIncomeGrowth)).append(" • ");}}
  if(ok(i.equityGrowth)){if(i.equityGrowth>=0){s+=5;g.append(pct("Özkaynak",i.equityGrowth)).append(" • ");}else{s-=7;y.append(pct("Özkaynak",i.equityGrowth)).append(" • ");}}
  if(ok(i.netDebtToEquity)){if(i.netDebtToEquity<0){s+=10;g.append("Net nakit • ");}else if(i.netDebtToEquity>50){s-=12;r.append("Net borç/özkaynak yüksek • ");}}
  if(ok(i.netCashChange)){if(i.netCashChange>0){s+=6;g.append("Net parasal/nakit pozisyon güçleniyor • ");}else if(i.netCashChange<0){s-=8;r.append("Net parasal/nakit pozisyon zayıflıyor • ");}}
  if(ok(i.currentAssetsGrowth)&&i.currentAssetsGrowth<-5){s-=5;y.append(pct("Dönen varlık",i.currentAssetsGrowth)).append(" • ");}
  if(ok(i.totalAssetsGrowth)&&i.totalAssetsGrowth<-5){s-=4;y.append(pct("Toplam varlık",i.totalAssetsGrowth)).append(" • ");}
  if(ok(i.pe)){if(i.pe>0&&i.pe<12)s+=4; else if(i.pe>35)s-=5;}
  s=Math.max(0,Math.min(100,s)); String l=s>=70?"GÜÇLÜ":s>=55?"OLUMLU":s>=40?"İZLE":"RİSKLİ";
  return new Result(s,l,g.toString(),y.toString(),r.toString());
 }
}
''',encoding='utf-8')
