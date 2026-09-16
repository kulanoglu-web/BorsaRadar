from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){')
b=s.find('    private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('fast detail renderer missing')
q=s[a:b]
# Insert the approved detail controls immediately before the existing fast chart, regardless of earlier chart rewrites.
anchor='        LinearLayout cc=card();'
pos=q.find(anchor)
if pos<0: raise SystemExit('fast chart card anchor missing')
controls='''        LinearLayout detailTabs=new LinearLayout(this);detailTabs.setOrientation(LinearLayout.HORIZONTAL);
        for(String tab:new String[]{"Genel","Grafik","Haber","KAP","Finansal","Teknik"}){Button tb=button(tab,tab.equals("Grafik")?Color.rgb(25,105,210):Color.rgb(49,55,63));tb.setTextSize(10);detailTabs.addView(tb,new LinearLayout.LayoutParams(0,-2,1));}
        content.addView(detailTabs);spacer(6);
        LinearLayout quickTf1=new LinearLayout(this);quickTf1.setOrientation(LinearLayout.HORIZONTAL);LinearLayout quickTf2=new LinearLayout(this);quickTf2.setOrientation(LinearLayout.HORIZONTAL);
        for(int i=0;i<ChartTimeframes.LABELS.length;i++){final int idx=i;String x=ChartTimeframes.LABELS[i];Button tb=button(x,i==5?Color.rgb(25,105,210):Color.rgb(49,55,63));tb.setTextSize(9);(i<6?quickTf1:quickTf2).addView(tb,new LinearLayout.LayoutParams(0,-2,1));tb.setOnClickListener(v->{getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",idx).apply();io.execute(()->{try{final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,data);main.post(()->renderStockDetail(symbol,aa,out,ChartTimeframes.LABELS[idx]));}catch(Exception ignored){}});});}
        content.addView(quickTf1);content.addView(quickTf2);spacer(6);
'''
q=q[:pos]+controls+q[pos:]
# Enlarge whatever fast PriceChartView layout survived the earlier production patches.
q=q.replace('dp(280)', 'dp(350)')
s=s[:a]+q+s[b:]
# Deep detail selected timeframe uses the approved blue accent.
a=s.find('    private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame) {')
b=s.find('    private void loadFullChartFrame',a)
if a<0 or b<0: raise SystemExit('deep detail renderer missing')
q=s[a:b]
q=q.replace('x.equals(frame)?RED:Color.rgb(49,55,63)','x.equals(frame)?Color.rgb(25,105,210):Color.rgb(49,55,63)')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
a=s.find('private void renderFastTechnicalDetail');b=s.find('private void renderStockDetail',a);fast=s[a:b]
a2=s.find('private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame)');b2=s.find('private void loadFullChartFrame',a2);deep=s[a2:b2]
checks={'fast full timeframes':'ChartTimeframes.LABELS' in fast,'six tabs':all(x in fast for x in ['"Genel"','"Grafik"','"Haber"','"KAP"','"Finansal"','"Teknik"']),'larger chart':'dp(350)' in fast,'deep full timeframes':'ChartTimeframes.LABELS' in deep,'all-stock generic':'NVDA' not in fast and 'NVIDIA' not in fast}
for k,v in checks.items():print('v137',k,v)
if not all(checks.values()):raise SystemExit('v137 verification FAILED')
