from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Tek Hisse'de çalışan derin grafik yükleyicisini bütün piyasalarda kullan.
a=s.find('    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){')
b=s.find('    private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('fast detail missing')
q=s[a:b]
start=q.find('for(int i=0;i<ChartTimeframes.LABELS.length;i++)')
end=q.find('        content.addView(quickTf1)',start)
if start<0 or end<0: raise SystemExit('timeframe controls missing')
new='''for(int i=0;i<ChartTimeframes.LABELS.length;i++){
            final int idx=i;
            Button tf=button(ChartTimeframes.LABELS[i],Color.rgb(49,55,63));
            tf.setTextSize(9);
            (i<6?quickTf1:quickTf2).addView(tf,new LinearLayout.LayoutParams(0,-2,1));
            tf.setOnClickListener(v->{
                FullAnalysisEngine.Result cached=null;
                try{cached=FullAnalysisEngine.analyze(symbol,data);}catch(Exception ignored){}
                loadFullChartFrame(symbol,cached,idx);
            });
        }
'''
q=q[:start]+new+q[end:]
s=s[:a]+q+s[b:]
# v152'nin paralel loader'ını tamamen kaldır.
a=s.find('    private void openChartTimeframe(')
if a>=0:
    b=s.find('\n    private ',a+20)
    if b<0: raise SystemExit('openChartTimeframe end missing')
    s=s[:a]+s[b:]
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
a=s.find('private void renderFastTechnicalDetail');b=s.find('private void renderStockDetail',a);q=s[a:b]
checks={
 'uses proven loader':'loadFullChartFrame(symbol,cached,idx)' in q,
 'no parallel loader':'openChartTimeframe(' not in s,
 'all labels':'ChartTimeframes.LABELS.length' in q,
 'no chart prefs':'chart_tf' not in q,
 'deep loader exists':'private void loadFullChartFrame' in s
}
for k,v in checks.items():print('v154',k,v)
if not all(checks.values()):raise SystemExit('v154 verification FAILED')
print('v154 Tek Hisse chart loader reused for all markets')
