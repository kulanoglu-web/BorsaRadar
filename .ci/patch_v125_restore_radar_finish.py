from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('private void scanRadar()')
if a<0: raise SystemExit('scanRadar missing')
b=s.find('\n    private ',a+30)
if b<0: raise SystemExit('scanRadar end missing')
# Restore the old proven completion pattern, but bind it to an immutable selected market.
new='''private void scanRadar() {
        if(scanRunning)return;
        radarMarketChoice=radarMarketChoiceMain;
        final int ownedMarket=radarMarketChoice;
        final String[] scanUniverse=radarUniverse();
        if(scanUniverse==null||scanUniverse.length==0){Toast.makeText(this,"Bu piyasa için taranacak hisse bulunamadı",Toast.LENGTH_LONG).show();return;}
        scanRunning=true;
        radarProgressMarket=ownedMarket;
        radarRunningByMarket[ownedMarket]=true;
        scanDone.set(0);scanFailed.set(0);
        radarDoneByMarket[ownedMarket]=0;radarFailByMarket[ownedMarket]=0;
        radarResults.clear();
        showRadar();
        for(String sym:scanUniverse)io.execute(()->{
            try{
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(sym,"1mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                radarResults.add(new RadarItem(sym,r));
            }catch(Exception e){
                int failed=scanFailed.incrementAndGet();
                radarFailByMarket[ownedMarket]=failed;
            }
            int done=scanDone.incrementAndGet();
            radarDoneByMarket[ownedMarket]=done;
            if(done>=scanUniverse.length){
                List<RadarItem> sorted=new ArrayList<>(radarResults);
                sorted.sort((x,y)->Double.compare(y.score,x.score));
                radarResults.clear();radarResults.addAll(sorted);
                radarDoneByMarket[ownedMarket]=scanUniverse.length;
                radarFailByMarket[ownedMarket]=scanFailed.get();
                radarRunningByMarket[ownedMarket]=false;
                scanRunning=false;
                saveRadarMarketSnapshot(ownedMarket);
                saveRadarCache();
                main.post(()->{if(radarMarketChoiceMain==ownedMarket){radarMarketChoice=ownedMarket;restoreRadarMarketSnapshot(ownedMarket);showRadar();}});
            }else if(done%25==0){
                main.post(()->{if(radarMarketChoiceMain==ownedMarket)showRadar();});
            }
        });
    }
'''
s=s[:a]+new+s[b:]
p.write_text(s,encoding='utf-8')
