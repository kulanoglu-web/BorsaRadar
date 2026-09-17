from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){')
b=s.find('    private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('fast detail renderer missing')
q=s[a:b]
# Initial fast preview is 3 months. Make that fact the single source of truth:
# persist index 8 before controls render, highlight the persisted index, and use
# exactly the same index for Graf/Genel tab transitions.
anchor='    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){'
if 'final int initialTf=8;' not in q:
    q=q.replace(anchor,anchor+'\n        final int initialTf=8;\n        getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",initialTf).apply();',1)
q=q.replace('Button tb=button(x,i==8?Color.rgb(25,105,210):Color.rgb(49,55,63));','Button tb=button(x,i==initialTf?Color.rgb(25,105,210):Color.rgb(49,55,63));')
# Defensive compatibility if an older patch chain still leaves the old highlight.
q=q.replace('Button tb=button(x,i==5?Color.rgb(25,105,210):Color.rgb(49,55,63));','Button tb=button(x,i==initialTf?Color.rgb(25,105,210):Color.rgb(49,55,63));')
# Never default Grafik/Genel back to 1 day when the screen is showing 3 months.
q=q.replace('getInt("chart_tf",5)','getInt("chart_tf",initialTf)')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
# Regression guards: these are build-time tests for the exact bug seen on-device.
s=p.read_text(encoding='utf-8')
a=s.find('private void renderFastTechnicalDetail');b=s.find('private void renderStockDetail',a);q=s[a:b]
checks={
 'initial state is 3m':'final int initialTf=8;' in q,
 'state persisted':'putInt("chart_tf",initialTf)' in q,
 'highlight uses state':'i==initialTf?Color.rgb(25,105,210)' in q,
 'tabs use same state':'getInt("chart_tf",initialTf)' in q,
 'no stale 1d highlight':'i==5?Color.rgb(25,105,210)' not in q,
 'no stale 1d default':'getInt("chart_tf",5)' not in q,
 'click fetches selected index':'DetailedChartController.fetch(symbol,idx)' in q,
 'clicked frame rendered':'ChartTimeframes.LABELS[idx]' in q,
}
for k,v in checks.items(): print('v148',k,v)
if not all(checks.values()): raise SystemExit('v148 timeframe regression FAILED')
print('v148 timeframe single-source regression PASS')
