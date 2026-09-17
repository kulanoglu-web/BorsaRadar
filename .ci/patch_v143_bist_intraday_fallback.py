from pathlib import Path
# BIST intraday fallback compatible with the canonical visible-period controller.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/DetailedChartController.java')
s=p.read_text(encoding='utf-8')
if 'String normalized=MarketDataService.normalizeSymbol(symbol);' not in s:
    old='''  List<MarketDataService.Candle>d=MarketDataService.fetchSeries(symbol,range,interval,180);'''
    new='''  String normalized=MarketDataService.normalizeSymbol(symbol);
  List<MarketDataService.Candle>d;
  try{d=MarketDataService.fetchSeries(symbol,range,interval,180);}
  catch(Exception first){
   if(normalized.endsWith(".IS")&&!"1d".equals(interval)){
    String fallback=("1m".equals(interval)?"1d":("5m".equals(interval)||"15m".equals(interval)||"30m".equals(interval))?"1mo":"3mo");
    d=MarketDataService.fetchSeries("BIST:"+normalized.substring(0,normalized.length()-3),fallback,interval,180);
   }else throw first;
  }'''
    if old not in s: raise SystemExit('v143 canonical fetch anchor missing')
    s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
checks={
 'BIST only':'normalized.endsWith(".IS")' in s,
 'intraday only':'!"1d".equals(interval)' in s,
 'selected interval preserved':'fallback,interval,180' in s,
 'visible trimming preserved':'maxVisiblePoints(i)' in s
}
for k,v in checks.items():print('v143',k,v)
if not all(checks.values()):raise SystemExit('v143 verification FAILED')
