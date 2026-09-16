from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v137 step 1: every stock gets the approved rich detail navigation/timeframe surface.
# Fast preview must already expose the same detailed timeframe choices instead of a dead-end mini chart.
a=s.find('    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){')
b=s.find('    private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('fast detail renderer missing')
q=s[a:b]
old='''        LinearLayout cc=card(); cc.addView(bold("Hızlı grafik",17,Color.WHITE));
        cc.addView(new PriceChartView(this,chart,"SON "+chart.size()+" GÜN"),new LinearLayout.LayoutParams(-1,dp(280)));
        content.addView(cc); spacer(7);'''
new='''        LinearLayout tabs=new LinearLayout(this);tabs.setOrientation(LinearLayout.HORIZONTAL);
        for(String tab:new String[]{"Genel","Grafik","Haber","KAP","Finansal","Teknik"}){Button tb=button(tab,tab.equals("Grafik")?Color.rgb(25,105,210):Color.rgb(49,55,63));tb.setTextSize(10);tabs.addView(tb,new LinearLayout.LayoutParams(0,-2,1));}
        content.addView(tabs);spacer(6);
        LinearLayout tf1=new LinearLayout(this);tf1.setOrientation(LinearLayout.HORIZONTAL);LinearLayout tf2=new LinearLayout(this);tf2.setOrientation(LinearLayout.HORIZONTAL);
        for(int i=0;i<ChartTimeframes.LABELS.length;i++){final int idx=i;String x=ChartTimeframes.LABELS[i];Button tb=button(x,i==5?Color.rgb(25,105,210):Color.rgb(49,55,63));tb.setTextSize(9);(i<6?tf1:tf2).addView(tb,new LinearLayout.LayoutParams(0,-2,1));tb.setOnClickListener(v->{getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",idx).apply();io.execute(()->{try{final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,data);main.post(()->renderStockDetail(symbol,aa,out,ChartTimeframes.LABELS[idx]));}catch(Exception ignored){}});});}
        content.addView(tf1);content.addView(tf2);spacer(6);
        LinearLayout cc=card(); cc.addView(bold("Grafik",17,Color.WHITE));
        PriceChartView fastChart=new PriceChartView(this,chart,"SON "+chart.size()+" GÜN");ShortTermTargetEngine.Target fastTarget=ShortTermTargetEngine.calculate(data,"1d");if(fastTarget!=null)fastChart.setTradeLevels(fastTarget.entry,fastTarget.target1,fastTarget.target2,fastTarget.stop);
        cc.addView(fastChart,new LinearLayout.LayoutParams(-1,dp(350)));
        content.addView(cc); spacer(7);'''
if old not in q: raise SystemExit('fast chart block missing')
q=q.replace(old,new,1)
s=s[:a]+q+s[b:]
# Deep detail: use approved tab labels and blue selected timeframe instead of the old red utility look.
a=s.find('    private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame) {')
b=s.find('    private void loadFullChartFrame',a)
if a<0 or b<0: raise SystemExit('deep detail renderer missing')
q=s[a:b]
q=q.replace('Button b=button(x,x.equals(frame)?RED:Color.rgb(49,55,63));','Button b=button(x,x.equals(frame)?Color.rgb(25,105,210):Color.rgb(49,55,63));')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
# strict verification
s=p.read_text(encoding='utf-8')
a=s.find('private void renderFastTechnicalDetail');b=s.find('private void renderStockDetail',a);fast=s[a:b]
a2=s.find('private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame)');b2=s.find('private void loadFullChartFrame',a2);deep=s[a2:b2]
checks={
 'fast has full timeframe source':'ChartTimeframes.LABELS' in fast,
 'fast has six detail tabs':all(x in fast for x in ['"Genel"','"Grafik"','"Haber"','"KAP"','"Finansal"','"Teknik"']),
 'fast chart taller':'dp(350)' in fast,
 'fast chart trade levels':'setTradeLevels' in fast,
 'deep keeps full timeframes':'ChartTimeframes.LABELS' in deep,
 'no NVDA-only gate':'NVDA' not in fast and 'NVIDIA' not in fast,
}
for k,v in checks.items(): print('v137',k,v)
if not all(checks.values()): raise SystemExit('v137 verification FAILED')
