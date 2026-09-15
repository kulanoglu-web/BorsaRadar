from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v86: one PriceChartView implementation on both fast and full stock-detail paths.
needle='LinearLayout chartCard=card(); chartCard.addView(bold("Grafik",17,Color.WHITE));\n        chartCard.addView(new PriceChartView(this,chart,frame+" • "+chart.size()+" nokta"),new LinearLayout.LayoutParams(-1,dp(310)));'
if needle in s:
    repl='java.util.List<MarketDataService.Candle> visibleChart=(chart==null)?java.util.Collections.emptyList():chart;\n        LinearLayout chartCard=card(); chartCard.addView(bold("Grafik",17,Color.WHITE));\n        if(!visibleChart.isEmpty()) chartCard.addView(new PriceChartView(this,visibleChart,frame+" • "+visibleChart.size()+" nokta"),new LinearLayout.LayoutParams(-1,dp(350)));\n        else chartCard.addView(txt("Grafik verisi bekleniyor",13,Color.GRAY));'
    s=s.replace(needle,repl,1)
# Validate the fast renderer and the full overloaded renderer, not the tiny delegating overload.
fast=s.find('private void renderFastTechnicalDetail')
deep=s.find('private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame)')
load=s.find('private void loadFullChartFrame',deep)
if fast<0 or deep<0 or load<0: raise SystemExit('detail renderer boundaries missing')
if 'PriceChartView' not in s[fast:deep]: raise SystemExit('fast renderer missing chart')
if 'PriceChartView' not in s[deep:load]: raise SystemExit('full renderer missing chart')
p.write_text(s,encoding='utf-8')
