from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Replace both timeframe listeners with one reliable path. The old fast listener
# recomputed FullAnalysisEngine from the stale preview before rendering, which
# could fail silently and make taps look dead.
a=s.find('private void renderFastTechnicalDetail')
b=s.find('private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('fast renderer missing')
q=s[a:b]
start=q.find('for(int i=0;i<ChartTimeframes.LABELS.length;i++)')
if start<0: raise SystemExit('fast timeframe loop missing')
end=q.find('        content.addView(quickTf1)',start)
if end<0: raise SystemExit('fast timeframe loop end missing')
new='''for(int i=0;i<ChartTimeframes.LABELS.length;i++){final int idx=i;String x=ChartTimeframes.LABELS[i];Button tb=button(x,i==initialTf?Color.rgb(25,105,210):Color.rgb(49,55,63));tb.setTextSize(9);(i<6?quickTf1:quickTf2).addView(tb,new LinearLayout.LayoutParams(0,-2,1));tb.setOnClickListener(v->{getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",idx).apply();loadFastChartFrame(symbol,data,idx);});}
'''
q=q[:start]+new+q[end:]
s=s[:a]+q+s[b:]
# Add a dedicated fast loader. It fetches first, then analyzes the SAME selected
# dataset, then renders. No swallowed exception; user gets the actual error.
anchor='    private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame) {'
if anchor not in s: raise SystemExit('deep renderer anchor missing')
helper='''    private void loadFastChartFrame(String symbol,List<MarketDataService.Candle> preview,int index){
        final int idx=Math.max(0,Math.min(index,ChartTimeframes.LABELS.length-1));
        final String frame=ChartTimeframes.LABELS[idx];
        Toast.makeText(this,frame+" grafik yükleniyor…",Toast.LENGTH_SHORT).show();
        io.execute(()->{
            try{
                final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);
                if(out==null||out.isEmpty())throw new Exception("boş veri");
                final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,out);
                main.post(()->renderStockDetail(symbol,aa,out,frame));
            }catch(Exception e){
                final String msg=e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();
                main.post(()->Toast.makeText(this,frame+" grafik hatası: "+msg,Toast.LENGTH_LONG).show());
            }
        });
    }

'''
if 'private void loadFastChartFrame(' not in s:s=s.replace(anchor,helper+anchor,1)
# Deep-detail buttons also use the same explicit async loader already present.
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
a=s.find('private void renderFastTechnicalDetail');b=s.find('private void renderStockDetail',a);q=s[a:b]
checks={
 'fast click dedicated loader':'loadFastChartFrame(symbol,data,idx)' in q,
 'no silent fast catch':'catch(Exception ignored)' not in q[q.find('for(int i=0;i<ChartTimeframes.LABELS.length;i++)'):],
 'selected fetch':'DetailedChartController.fetch(symbol,idx)' in s[s.find('private void loadFastChartFrame'):s.find('private void renderStockDetail',s.find('private void loadFastChartFrame'))],
 'selected analysis':'FullAnalysisEngine.analyze(symbol,out)' in s,
 'visible error':'grafik hatası:' in s,
}
for k,v in checks.items():print('v149',k,v)
if not all(checks.values()):raise SystemExit('v149 timeframe click regression FAILED')
print('v149 timeframe click regression PASS')
