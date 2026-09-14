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

        // Saatlik tarama tüm BIST'i yeniden indirmez. Ana radarın son kalıcı sonucundan
        // en güçlü adayları alır ve yalnız bunları 1 saatlik veriyle doğrular.
        List<String> targets=new ArrayList<>();
        if("1S".equals(mode) && !radarResults.isEmpty()){
            List<RadarItem> base=new ArrayList<>(radarResults);
            base.sort((a,b)->Double.compare(b.rankedScore,a.rankedScore));
            int limit=Math.min(60,base.size());
            for(int i=0;i<limit;i++){
                RadarItem x=base.get(i);
                if(x.recommendation!=null && (x.recommendation.contains("SAT")||x.recommendation.contains("RİSK")))continue;
                targets.add(x.symbol);
            }
        }
        if(targets.isEmpty())targets.addAll(Arrays.asList(ALL_SYMBOLS));
        final int targetCount=targets.size();
        main.post(this::showHourlyRadar);
        for(String sym:targets)io.execute(()->{
            try{
                List<MarketDataService.Candle>d;
                if("1S".equals(mode))d=MarketDataService.fetchSeries(sym,"5d","1h",100);
                else d=MarketDataService.fetchSeries(sym,"1mo","1d",40);
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                RadarTechnicalEngine.Result rt=RadarTechnicalEngine.analyze(d);
                RadarItem item=new RadarItem(sym,r); item.score=rt.score; item.rankedScore=rt.score; item.why=rt.summary+" • "+item.why;
                if(r.price>0)buffer.add(item);
            }catch(Exception e){shortScanFailed.incrementAndGet();}
            int done=shortScanDone.incrementAndGet();
            if(done>=targetCount){
                List<RadarItem> sorted=new ArrayList<>(buffer);
                sorted.sort((a,b)->Double.compare(b.rankedScore,a.rankedScore));
                if(!sorted.isEmpty()){shortRadarResults.clear();int n=Math.min(40,sorted.size());shortRadarResults.addAll(sorted.subList(0,n));saveShortRadarCache();}
                shortScanRunning=false;main.post(this::showHourlyRadar);
            }else if(done%15==0)main.post(this::showHourlyRadar);
        });
    }

    '''
s=s[:start]+method+s[end:]
p.write_text(s,encoding='utf-8')
