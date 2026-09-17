from pathlib import Path
# Compatibility verification: the canonical controller now uses one selected timeframe path
# for all markets, with a BIST-only transport fallback when Yahoo rejects intraday data.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/DetailedChartController.java')
s=p.read_text(encoding='utf-8')
checks={
 'selected fetch path':'MarketDataService.fetchSeries(symbol,range,interval,180)' in s,
 'BIST transport fallback':'normalized.endsWith(".IS")' in s,
 'selected interval preserved':'fallback,interval,180' in s,
 'visible timeframe preserved':'maxVisiblePoints(i)' in s
}
for k,v in checks.items():print('v144',k,v)
if not all(checks.values()):raise SystemExit('v144 canonical timeframe verification FAILED')
print('v144 canonical controller preserved; no destructive rewrite')
