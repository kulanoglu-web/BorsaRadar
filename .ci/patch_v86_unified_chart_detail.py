from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v86: one chart implementation for every stock, regardless of whether fast or deep analysis wins the race.
# Deep renderer: never omit the chart card; use the same PriceChartView and safe chart list.
needle='LinearLayout chartCard=card(); chartCard.addView(bold("Grafik",17,Color.WHITE));\n        chartCard.addView(new PriceChartView(this,chart,frame+" • "+chart.size()+" nokta"),new LinearLayout.LayoutParams(-1,dp(310)));'
if needle in s:
    repl='java.util.List<MarketDataService.Candle> visibleChart=(chart==null)?java.util.Collections.emptyList():chart;\n        LinearLayout chartCard=card(); chartCard.addView(bold("Grafik",17,Color.WHITE));\n        if(!visibleChart.isEmpty()) chartCard.addView(new PriceChartView(this,visibleChart,frame+" • "+visibleChart.size()+" nokta"),new LinearLayout.LayoutParams(-1,dp(350)));\n        else chartCard.addView(txt("Grafik verisi bekleniyor",13,Color.GRAY));'
    s=s.replace(needle,repl,1)
# Fast renderer already uses PriceChartView; normalize its height and title.
s=s.replace('new PriceChartView(this,chart,"GÜNCEL"),new LinearLayout.LayoutParams(-1,dp(350))','new PriceChartView(this,chart,"GÜNCEL"),new LinearLayout.LayoutParams(-1,dp(350))')
# Ensure every detailed result uses the latest chart close for visible price.
old='double visiblePrice=(chart!=null&&!chart.isEmpty()&&chart.get(chart.size()-1).close>0)?chart.get(chart.size()-1).close:r.price;'
if old in s:
    s=s.replace(old,'double visiblePrice=(chart!=null&&!chart.isEmpty()&&chart.get(chart.size()-1).close>0)?chart.get(chart.size()-1).close:r.price;',1)
# Critical guard: both renderers must contain PriceChartView after all patches.
fast=s.find('private void renderFastTechnicalDetail')
deep=s.find('private void renderStockDetail',fast)
if fast<0 or deep<0: raise SystemExit('detail renderer boundaries missing')
fast_block=s[fast:deep]
next_method=s.find('private void ',deep+20)
if next_method<0: next_method=len(s)
deep_block=s[deep:next_method]
if 'PriceChartView' not in fast_block: raise SystemExit('fast renderer missing chart')
if 'PriceChartView' not in deep_block: raise SystemExit('deep renderer missing chart')
p.write_text(s,encoding='utf-8')
