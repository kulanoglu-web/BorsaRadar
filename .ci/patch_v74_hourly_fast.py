from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
start=s.find('private void scanShortTerm(String mode)')
end=s.find('private void saveShortRadarCache()',start)
if start<0 or end<0: raise SystemExit('short scan boundaries missing')
method='''private void scanShortTerm(String mode){
        if(shortScanRunning)return;
        shortScanRunning=true;shortScanMode=mode;shortScanDone.set(0);shortScanFailed.set(0);
        final List<RadarItem> buffer=Collections.synchronizedList(new ArrayList<>());
        final String[] universe=marketSymbols(primaryMarket());
        // Hourly radar is intentionally light: 2 days/1h is enough for the first ranking.
        // Deep/news enrichment is reserved for the strongest candidates after the list is visible.
        showHourlyRadar();
        for(String sym:universe)io.execute(()->{
            try{
                List<MarketDataService.Candle>d;
                if("1S".equals(mode)) d=MarketDataService.fetchSeries(sym,"2d","1h",48);
                else d=MarketDataService.fetchSeries(sym,"1mo","1d",30);
                if(d!=null&&d.size()>=8){
                    ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                    RadarItem item=new RadarItem(sym,r);
                    item.score=r.score; item.rankedScore=r.score;
                    if(r.price>0 && r.confidence>=35) buffer.add(item);
                }
            }catch(Exception e){shortScanFailed.incrementAndGet();}
            int done=shortScanDone.incrementAndGet();
            if(done>=universe.length){
                List<RadarItem> sorted=new ArrayList<>(buffer);
                sorted.sort((a,b)->Double.compare(b.rankedScore,a.rankedScore));
                if(!sorted.isEmpty()){shortRadarResults.clear();int n=Math.min(30,sorted.size());shortRadarResults.addAll(sorted.subList(0,n));saveShortRadarCache();}
                shortScanRunning=false;main.post(this::showHourlyRadar);
            }else if(done%20==0)main.post(this::showHourlyRadar);
        });
    }

    '''
s=s[:start]+method+s[end:]
# Correct progress maximum for separate BIST/DE/US profiles.
s=s.replace('pb.setMax(ALL_SYMBOLS.length);pb.setProgress(shortScanDone.get())','pb.setMax(marketSymbols(primaryMarket()).length);pb.setProgress(shortScanDone.get())')
s=s.replace('shortScanDone.get()+"/"+ALL_SYMBOLS.length','shortScanDone.get()+"/"+marketSymbols(primaryMarket()).length')
p.write_text(s,encoding='utf-8')
