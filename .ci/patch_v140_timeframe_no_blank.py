from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Fix ONLY detail timeframe navigation. Radar persistence is deliberately untouched.
a=s.find('private void renderFastTechnicalDetail')
b=s.find('private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('fast detail renderer missing')
q=s[a:b]
old='tb.setOnClickListener(v->{getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",idx).apply();io.execute(()->{try{final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,data);main.post(()->renderStockDetail(symbol,aa,out,ChartTimeframes.LABELS[idx]));}catch(Exception ignored){}});});'
new='tb.setOnClickListener(v->{getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",idx).apply();tb.setEnabled(false);io.execute(()->{try{final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,data);main.post(()->{tb.setEnabled(true);if(out!=null&&!out.isEmpty())renderStockDetail(symbol,aa,out,ChartTimeframes.LABELS[idx]);else Toast.makeText(this,"Grafik verisi alınamadı",Toast.LENGTH_SHORT).show();});}catch(Exception e){main.post(()->{tb.setEnabled(true);Toast.makeText(this,"Grafik verisi alınamadı",Toast.LENGTH_SHORT).show();});}});});'
if old in q:q=q.replace(old,new,1)
elif 'tb.setEnabled(false)' not in q:raise SystemExit('fast timeframe listener anchor missing')
s=s[:a]+q+s[b:]
# Replace ONLY loadFullChartFrame. The next member can return String/etc., so stop at any next private member, not only private void.
a=s.find('private void loadFullChartFrame(String symbol,FullAnalysisEngine.Result a,int index)')
if a<0: raise SystemExit('deep timeframe loader missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
new_method='''private void loadFullChartFrame(String symbol,FullAnalysisEngine.Result a,int index){
        final int idx=Math.max(0,Math.min(index,ChartTimeframes.LABELS.length-1));
        final String frame=ChartTimeframes.LABELS[idx];
        Toast.makeText(this,frame+" grafik yükleniyor…",Toast.LENGTH_SHORT).show();
        io.execute(()->{try{final List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);main.post(()->{if(out!=null&&!out.isEmpty())renderStockDetail(symbol,a,out,frame);else Toast.makeText(this,"Grafik verisi alınamadı",Toast.LENGTH_SHORT).show();});}
        catch(Exception e){main.post(()->Toast.makeText(this,"Grafik verisi alınamadı",Toast.LENGTH_SHORT).show());}});
    }
'''
s=s[:a]+new_method+s[b:]
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
a=s.find('private void loadFullChartFrame(String symbol,FullAnalysisEngine.Result a,int index)');b=s.find('\n    private ',a+20);deep=s[a:b if b>=0 else len(s)]
checks={'no shell blank':'shell(' not in deep,'fetch preserved':'DetailedChartController.fetch' in deep,'error toast':'Grafik verisi alınamadı' in deep,'timeframes preserved':'ChartTimeframes.LABELS' in deep,'adjacent preserved':'adjacentSymbol(' in s}
for k,v in checks.items():print('v140',k,v)
if not all(checks.values()):raise SystemExit('v140 verification FAILED')
