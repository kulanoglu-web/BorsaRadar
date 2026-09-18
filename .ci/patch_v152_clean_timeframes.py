from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){')
b=s.find('    private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('detail renderer missing')
q=s[a:b]
# Zaman butonlarını sıfırdan kur: seçim state'i yalnız tıklamada değişir.
start=q.find('for(int i=0;i<ChartTimeframes.LABELS.length;i++)')
end=q.find('        content.addView(quickTf1)',start)
if start<0 or end<0: raise SystemExit('timeframe block missing')
new='''final int selectedTf=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("chart_tf",8);
        for(int i=0;i<ChartTimeframes.LABELS.length;i++){
            final int idx=i;
            Button tf=button(ChartTimeframes.LABELS[i],i==selectedTf?Color.rgb(25,105,210):Color.rgb(49,55,63));
            tf.setTextSize(9);
            (i<6?quickTf1:quickTf2).addView(tf,new LinearLayout.LayoutParams(0,-2,1));
            tf.setOnClickListener(v->openChartTimeframe(symbol,idx));
        }
'''
q=q[:start]+new+q[end:]
s=s[:a]+q+s[b:]
anchor='    private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame) {'
helper='''    private void openChartTimeframe(String symbol,int index){
        final int idx=ChartTimeframes.clamp(index);
        final String frame=ChartTimeframes.label(idx);
        getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",idx).commit();
        io.execute(()->{
            try{
                final java.util.List<MarketDataService.Candle> chart=DetailedChartController.fetch(symbol,idx);
                java.util.List<MarketDataService.Candle> analysis=chart;
                if(chart.size()<40){
                    try{java.util.List<MarketDataService.Candle> x=MarketDataService.fetchSeries(symbol,"3mo","1d",0);if(x!=null&&x.size()>=20)analysis=x;}catch(Exception ignored){}
                }
                final FullAnalysisEngine.Result result=FullAnalysisEngine.analyze(symbol,analysis);
                main.post(()->renderStockDetail(symbol,result,chart,frame));
            }catch(Exception e){
                final String m=e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();
                main.post(()->Toast.makeText(this,frame+" grafik hatası: "+m,Toast.LENGTH_LONG).show());
            }
        });
    }

'''
if anchor not in s: raise SystemExit('render anchor missing')
s=s.replace(anchor,helper+anchor,1)
p.write_text(s,encoding='utf-8')
print('v152 clean timeframe selector installed')
