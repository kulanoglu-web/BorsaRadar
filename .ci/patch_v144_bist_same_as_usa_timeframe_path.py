from pathlib import Path
# User confirmed USA/Germany timeframe path works. Remove the BIST-special fetch branch and use the exact same path for every market.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/DetailedChartController.java')
s=p.read_text(encoding='utf-8')
start=s.find('  String normalized=MarketDataService.normalizeSymbol(symbol);')
end=s.find('  if(i==4&&"60m".equals(interval))d=MarketDataService.aggregateHours(d,4);',start)
if start<0 or end<0: raise SystemExit('v143 BIST special branch missing')
replacement='  List<MarketDataService.Candle>d=MarketDataService.fetchSeries(symbol,range,interval,180);\n'
s=s[:start]+replacement+s[end:]
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
checks={'same fetch all markets':'List<MarketDataService.Candle>d=MarketDataService.fetchSeries(symbol,range,interval,180);' in s,'no BIST special branch':'normalized.endsWith(".IS")' not in s,'4h preserved':'aggregateHours(d,4)' in s}
for k,v in checks.items():print('v144',k,v)
if not all(checks.values()):raise SystemExit('v144 verification FAILED')
