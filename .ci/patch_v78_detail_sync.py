from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Patch whichever detail renderer the late build chain generated; never fail the build just because formatting changed.
# Prefer synchronizing any local visible price variable to the latest chart close.
for old in ['double px=a.price;','double px = a.price;','final double px=a.price;','final double px = a.price;']:
    if old in s:
        s=s.replace(old,old.replace('a.price','(chart!=null&&!chart.isEmpty()&&chart.get(chart.size()-1).close>0)?chart.get(chart.size()-1).close:a.price'),1)
        break
# Add target/time strip after hero if that stable UI anchor exists.
marker='content.addView(hero); spacer(7);'
if marker in s and 'bold("Hedef / Süre"' not in s:
    insert='''content.addView(hero); spacer(7);
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
# Timeframe fetches get the dedicated detail executor so radar traffic cannot block them.
s=s.replace('io.execute(()->{try{final List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);','detailIo.execute(()->{try{final List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);',1)
p.write_text(s,encoding='utf-8')
