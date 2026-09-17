from pathlib import Path
# ONLY timeframe data behavior in this patch. Do not touch bottom navigation/colors/radar.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/ChartTimeframes.java')
s=p.read_text(encoding='utf-8')
old='public static final String[] RANGE={"1d","5d","5d","1mo","1mo","1mo","3mo","1mo","3mo","6mo","1y","2y"};'
# Yahoo intraday history limits make 5m+1d too small and 60m+1mo visually too similar. Give each button a real, distinct window.
new='public static final String[] RANGE={"5d","5d","1mo","1mo","3mo","3mo","6mo","1mo","3mo","6mo","1y","2y"};'
if old not in s: raise SystemExit('timeframe range anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
# Ensure the controller still consumes the selected index and does not silently force one-day data.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/DetailedChartController.java')
c=p.read_text(encoding='utf-8')
checks={'selected index':'ChartTimeframes.INTERVAL[i],range=ChartTimeframes.RANGE[i]' in c,'fetch selected':'fetchSeries(symbol,range,interval,180)' in c,'4h aggregate':'aggregateHours(d,4)' in c}
for k,v in checks.items(): print('v142',k,v)
if not all(checks.values()): raise SystemExit('v142 controller verification FAILED')
print('v142 BIST/timeframe ranges updated')
