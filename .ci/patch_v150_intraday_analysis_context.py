from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('private void loadFastChartFrame(')
b=s.find('\n    private ',a+20)
if a<0: raise SystemExit('v150 loader missing')
if b<0:b=len(s)
q=s[a:b]
old='''final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);
                if(out==null||out.isEmpty())throw new Exception("boş veri");
                final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,out);
                main.post(()->renderStockDetail(symbol,aa,out,frame));'''
new='''final java.util.List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);
                if(out==null||out.isEmpty())throw new Exception("boş veri");
                // Intraday frames can contain fewer than 20 candles. Keep the selected
                // chart data for rendering, but calculate indicators from a stable
                // 3-month daily context exactly like the working global-stock path.
                java.util.List<MarketDataService.Candle> analysisData=out;
                if(out.size()<40){
                    try{
                        java.util.List<MarketDataService.Candle> ctx=MarketDataService.fetchSeries(symbol,"3mo","1d",180);
                        if(ctx!=null && ctx.size()>=20)analysisData=ctx;
                    }catch(Exception ignored){}
                }
                final FullAnalysisEngine.Result aa=FullAnalysisEngine.analyze(symbol,analysisData);
                main.post(()->renderStockDetail(symbol,aa,out,frame));'''
if old not in q: raise SystemExit('v150 target missing')
q=q.replace(old,new,1)
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
print('v150 selected chart kept', 'renderStockDetail(symbol,aa,out,frame)' in q)
print('v150 analysis context fallback', 'fetchSeries(symbol,"3mo","1d",180)' in q)
