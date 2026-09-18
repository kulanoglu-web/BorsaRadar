from pathlib import Path
# Compatibility guard only. Canonical timeframe behavior now lives in ChartTimeframes.java.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/ChartTimeframes.java')
s=p.read_text(encoding='utf-8')
legacy='public static final String[] RANGE={"1d","5d","5d","1mo","1mo","1mo","3mo","1mo","3mo","6mo","1y","2y"};'
canonical='public static final String[] RANGE={"1d","1d","1d","1d","1d","1d","5d","1mo","3mo","6mo","1y","2y"};'
if legacy in s:
    s=s.replace(legacy,canonical,1)
elif canonical not in s:
    raise SystemExit('v142 unknown timeframe RANGE layout')
p.write_text(s,encoding='utf-8')

# Controller may either aggregate 60m candles for the legacy 4h implementation,
# or use the newer 15m transport plus visible-period trimming. Both are valid.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/DetailedChartController.java')
c=p.read_text(encoding='utf-8')
checks={
 'selected index':'ChartTimeframes.INTERVAL[i],range=ChartTimeframes.RANGE[i]' in c,
 'fetch selected':'fetchSeries(symbol,range,interval,0)' in c,
 'visible period enforced':('maxVisiblePoints(i)' in c or 'aggregateHours(d,4)' in c)
}
for k,v in checks.items(): print('v142',k,v)
if not all(checks.values()): raise SystemExit('v142 controller verification FAILED')
print('v142 canonical timeframe controller preserved')
