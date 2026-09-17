from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Fix ONLY detail timeframe buttons. Do not touch radar/result persistence in this step.
# Fast detail: keep current screen visible while data loads; only replace after successful non-empty fetch.
a=s.find('private void renderFastTechnicalDetail')
b=s.find('private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('fast detail renderer missing')
q=s[a:b]
old='tb.setOnClickListener(v->{getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",idx).apply();io.execute(()->{try{final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,data);main.post(()->renderStockDetail(symbol,aa,out,ChartTimeframes.LABELS[idx]));}catch(Exception ignored){}});});'
new='tb.setOnClickListener(v->{getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",idx).apply();tb.setEnabled(false);io.execute(()->{try{final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,data);main.post(()->{tb.setEnabled(true);if(out!=null&&!out.isEmpty())renderStockDetail(symbol,aa,out,ChartTimeframes.LABELS[idx]);else Toast.makeText(this,"Grafik verisi alınamadı",Toast.LENGTH_SHORT).show();});}catch(Exception e){main.post(()->{tb.setEnabled(true);Toast.makeText(this,"Grafik verisi alınamadı",Toast.LENGTH_SHORT).show();});}});});'
if old not in q: raise SystemExit('fast timeframe listener anchor missing')
q=q.replace(old,new,1)
s=s[:a]+q+s[b:]
# Deep detail: remove shell(... yükleniyor), because rebuilding the whole activity before network fetch is what makes the app appear to disappear.
a=s.find('private void loadFullChartFrame(String symbol,FullAnalysisEngine.Result a,int index)')
if a<0: raise SystemExit('deep timeframe loader missing')
b=s.find('private void ',a+20)
if b<0:b=len(s)
q=s[a:b]
old2='''        shell(symbol+" • "+frame+" yükleniyor");
        ProgressBar p=new ProgressBar(this); content.addView(p); content.addView(txt("Grafik verisi alınıyor…",14,Color.GRAY));
        io.execute(()->{try{final List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);main.post(()->renderStockDetail(symbol,a,out,frame));}
        catch(Exception e){main.post(()->{shell(symbol+" • "+frame);content.addView(txt("Grafik verisi alınamadı: "+e.getMessage(),15,RED));});}});'''
new2='''        Toast.makeText(this,frame+" grafik yükleniyor…",Toast.LENGTH_SHORT).show();
        io.execute(()->{try{final List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);main.post(()->{if(out!=null&&!out.isEmpty())renderStockDetail(symbol,a,out,frame);else Toast.makeText(this,"Grafik verisi alınamadı",Toast.LENGTH_SHORT).show();});}
        catch(Exception e){main.post(()->Toast.makeText(this,"Grafik verisi alınamadı",Toast.LENGTH_SHORT).show());}});'''
if old2 not in q: raise SystemExit('deep loader blank-screen anchor missing')
q=q.replace(old2,new2,1)
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
a=s.find('private void loadFullChartFrame(String symbol,FullAnalysisEngine.Result a,int index)');b=s.find('private void ',a+20);deep=s[a:b]
checks={'no shell blank':'shell(' not in deep,'fetch preserved':'DetailedChartController.fetch' in deep,'error toast':'Grafik verisi alınamadı' in deep,'timeframes preserved':'ChartTimeframes.LABELS' in deep}
for k,v in checks.items():print('v140',k,v)
if not all(checks.values()):raise SystemExit('v140 verification FAILED')
