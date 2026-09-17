from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){')
b=s.find('    private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('fast detail renderer missing')
q=s[a:b]
old='''        for(String tab:new String[]{"Genel","Grafik","Haber","KAP","Finansal","Teknik"}){Button tb=button(tab,tab.equals("Grafik")?Color.rgb(25,105,210):Color.rgb(49,55,63));tb.setTextSize(10);detailTabs.addView(tb,new LinearLayout.LayoutParams(0,-2,1));}'''
new='''        for(String tab:new String[]{"Genel","Grafik","Haber","KAP","Finansal","Teknik"}){final String selectedTab=tab;Button tb=button(tab,tab.equals("Grafik")?Color.rgb(25,105,210):Color.rgb(49,55,63));tb.setTextSize(10);detailTabs.addView(tb,new LinearLayout.LayoutParams(0,-2,1));tb.setOnClickListener(v->{if("Grafik".equals(selectedTab)||"Genel".equals(selectedTab)){io.execute(()->{try{int idx=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("chart_tf",5);final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,data);main.post(()->renderStockDetail(symbol,aa,out,ChartTimeframes.LABELS[idx]));}catch(Exception ignored){}});}else{Toast.makeText(this,selectedTab+" • detay görünümü",Toast.LENGTH_SHORT).show();}});}'''
if old not in q: raise SystemExit('v137 detail tabs block missing')
q=q.replace(old,new,1)
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
a=s.find('private void renderFastTechnicalDetail');b=s.find('private void renderStockDetail',a);fast=s[a:b]
checks={'tab listeners':'tb.setOnClickListener' in fast,'six tabs':all(x in fast for x in ['"Genel"','"Grafik"','"Haber"','"KAP"','"Finansal"','"Teknik"']),'full timeframes':'ChartTimeframes.LABELS' in fast,'generic all-stock':'NVDA' not in fast and 'NVIDIA' not in fast}
for k,v in checks.items():print('v138',k,v)
if not all(checks.values()):raise SystemExit('v138 verification FAILED')
