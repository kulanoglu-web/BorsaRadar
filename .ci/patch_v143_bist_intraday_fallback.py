from pathlib import Path
# ONLY BIST timeframe fetching. Germany/USA and navigation/radar are untouched.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/DetailedChartController.java')
s=p.read_text(encoding='utf-8')
old='''  List<MarketDataService.Candle>d=MarketDataService.fetchSeries(symbol,range,interval,180);
  if(i==4&&"60m".equals(interval))d=MarketDataService.aggregateHours(d,4);
  return d;'''
new='''  String normalized=MarketDataService.normalizeSymbol(symbol);
  List<MarketDataService.Candle>d;
  try{d=MarketDataService.fetchSeries(symbol,range,interval,180);}
  catch(Exception first){
   // BIST minute/hour endpoints can reject an otherwise valid .IS request while DE/US work.
   // Retry BIST intraday with a wider Yahoo-supported range, without changing the selected interval.
   if(normalized.endsWith(".IS")&&!"1d".equals(interval)){
    String fallback=("5m".equals(interval)||"15m".equals(interval)||"30m".equals(interval))?"1mo":"3mo";
    d=MarketDataService.fetchSeries("BIST:"+normalized.substring(0,normalized.length()-3),fallback,interval,180);
   }else throw first;
  }
  if(i==4&&"60m".equals(interval))d=MarketDataService.aggregateHours(d,4);
  return d;'''
if old not in s: raise SystemExit('controller fetch anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
checks={'BIST only':'normalized.endsWith(".IS")' in s,'intraday only':'!"1d".equals(interval)' in s,'selected interval preserved':'fallback,interval,180' in s,'4h preserved':'aggregateHours(d,4)' in s}
for k,v in checks.items():print('v143',k,v)
if not all(checks.values()):raise SystemExit('v143 verification FAILED')
