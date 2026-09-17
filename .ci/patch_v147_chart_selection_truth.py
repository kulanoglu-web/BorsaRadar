from pathlib import Path

# The fast preview is a 3-month daily chart. Do not paint '1 gün' blue before
# a 1-day intraday fetch has actually completed. Once a timeframe is clicked,
# renderStockDetail receives the fetched candles and highlights that real frame.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('private void renderFastTechnicalDetail')
b=s.find('private void renderStockDetail',a)
if a<0 or b<0: raise SystemExit('v147 fast detail renderer missing')
q=s[a:b]
old='Button tb=button(x,i==5?Color.rgb(25,105,210):Color.rgb(49,55,63));'
new='Button tb=button(x,i==8?Color.rgb(25,105,210):Color.rgb(49,55,63));'
if old in q:q=q.replace(old,new,1)
elif 'i==8?Color.rgb(25,105,210)' not in q:raise SystemExit('v147 fast selected timeframe anchor missing')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')

# Long ranges must not be silently cut to 180 daily candles. 3/6 months,
# 1 year and 2 years are already bounded by ChartTimeframes.RANGE.
p=Path('app/src/main/java/com/kulanoglu/borsaradar/DetailedChartController.java')
s=p.read_text(encoding='utf-8')
s=s.replace('default:return 180;   // long ranges already constrained by RANGE','default:return 0;     // long ranges are constrained by RANGE; keep the full requested period')
p.write_text(s,encoding='utf-8')

# Verify the final production source contract.
m=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java').read_text(encoding='utf-8')
c=Path('app/src/main/java/com/kulanoglu/borsaradar/DetailedChartController.java').read_text(encoding='utf-8')
checks={
 'preview says 3 ay':'i==8?Color.rgb(25,105,210)' in m,
 'click fetches selected':'DetailedChartController.fetch(symbol,idx)' in m,
 'deep highlights actual frame':'x.equals(frame)?Color.rgb(25,105,210)' in m,
 'visible trimming':'maxVisiblePoints(i)' in c,
 'long ranges uncut':'default:return 0;' in c
}
for k,v in checks.items():print('v147',k,v)
if not all(checks.values()):raise SystemExit('v147 chart selection verification FAILED')
