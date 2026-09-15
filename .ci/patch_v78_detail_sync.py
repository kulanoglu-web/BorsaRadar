from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# In renderStockDetail, use the chart's latest close as the authoritative visible price.
needle='''        double px=a.price;'''
if needle in s:
    s=s.replace(needle,'''        double px=(chart!=null&&!chart.isEmpty()&&chart.get(chart.size()-1).close>0)?chart.get(chart.size()-1).close:a.price;''',1)
else:
    # Some patch chains use another declaration; inject directly after method opening.
    sig='''private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame){'''
    if sig not in s: raise SystemExit('renderStockDetail signature missing')
    s=s.replace(sig,sig+'''\n        final double syncedPrice=(chart!=null&&!chart.isEmpty()&&chart.get(chart.size()-1).close>0)?chart.get(chart.size()-1).close:a.price;''',1)
    # Replace the first visible a.price formatting inside the renderer only.
    a0=s.find(sig); a1=s.find('private void ',a0+len(sig));
    part=s[a0:a1 if a1>0 else len(s)]
    part=part.replace('a.price','syncedPrice',1)
    s=s[:a0]+part+s[a1 if a1>0 else len(s):]
# Currency conversion must match PriceChartView: US and DE display EUR.
# Add a compact target strip near the top so target/time isn't buried below the chart.
marker='''        content.addView(hero); spacer(7);'''
if marker in s:
    insert='''        content.addView(hero); spacer(7);
        try{
            String iv=ChartTimeframes.INTERVAL[Math.max(0,Math.min(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("chart_tf",3),ChartTimeframes.INTERVAL.length-1))];
            ShortTermTargetEngine.Target topTarget=ShortTermTargetEngine.calculate(chart,iv);
            if(topTarget!=null){
                String cur=MarketSymbol.marketIndex(symbol)==0?"TL":"€";
                LinearLayout tp=card();
                tp.addView(bold("Hedef / Süre",16,Color.WHITE));
                tp.addView(txt(topTarget.summary(cur),13,Color.LTGRAY));
                content.addView(tp); spacer(7);
            }
        }catch(Throwable ignored){}'''
    s=s.replace(marker,insert,1)
# Timeframe loading should use the dedicated detail executor, not compete with full radar scans.
s=s.replace('''        io.execute(()->{try{final List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);''','''        detailIo.execute(()->{try{final List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);''',1)
p.write_text(s,encoding='utf-8')
