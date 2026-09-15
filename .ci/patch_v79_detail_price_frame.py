from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Detail quote must use the same last candle that the chart uses. Pulse price may be zero/stale.
old='TextView px=bold(money(r.price,symbol),28,r.changePct>=0?GREEN:RED);'
new='double visiblePrice=(chart!=null&&!chart.isEmpty()&&chart.get(chart.size()-1).close>0)?chart.get(chart.size()-1).close:r.price; TextView px=bold(money(visiblePrice,symbol),28,r.changePct>=0?GREEN:RED);'
if old in s: s=s.replace(old,new,1)
# Initial analysis data is the fast daily history, so do not falsely label it as the user's previously selected timeframe.
s=s.replace('renderStockDetail(symbol,a,chart,"10G");','renderStockDetail(symbol,a,chart,"10G");',1)
# When full analysis first renders, keep 10G as initial context. Saved timeframe is only used after its data is actually fetched.
# Improve target visibility by adding it immediately after quote using current chart data.
anchor='content.addView(quote); spacer(7);'
if anchor in s and '"Kısa Vade Planı"' not in s:
    extra='''content.addView(quote); spacer(7);
        try{
            ShortTermTargetEngine.Target st=ShortTermTargetEngine.calculate(chart,"1d");
            if(st!=null){String cur=MarketSymbol.marketIndex(symbol)==0?"TL":"€"; LinearLayout plan=card(); plan.addView(bold("Kısa Vade Planı",17,Color.WHITE)); plan.addView(txt(st.summary(cur),13,Color.LTGRAY)); content.addView(plan); spacer(7);}
        }catch(Throwable ignored){}'''
    s=s.replace(anchor,extra,1)
p.write_text(s,encoding='utf-8')
