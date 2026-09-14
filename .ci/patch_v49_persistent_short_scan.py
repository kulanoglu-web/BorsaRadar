from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

s=s.replace('button("Radar",GREEN)', 'button("Tarama",GREEN)')
s=s.replace('shell("Tüm Borsa İstanbul Radarı")', 'shell("Güncel Fırsat Taraması")')
s=s.replace('button(scanRunning?"Tarama devam ediyor…":"Tüm BIST\'i Tara",GREEN)', 'button(scanRunning?"Tarama devam ediyor…":"Güncel AL/SAT Fırsatlarını Tara",GREEN)')

# Replace only scanRadar by method-name boundaries. This is robust against
# formatting/body changes from v50/v52 and preserves the enrichment method.
start=s.find('private void scanRadar()')
end=s.find('private void enrichRadarTopCandidates',start)
if start<0 or end<0:
    raise SystemExit('persistent radar boundaries missing')
scan='''private void scanRadar() {
        if(scanRunning)return;
        final int pm=primaryMarket(); final String[] universe=marketSymbols(pm);
        scanRunning=true;scanDone.set(0);scanFailed.set(0);
        final List<RadarItem> freshResults=Collections.synchronizedList(new ArrayList<>());
        showRadar();
        for(String sym:universe)io.execute(()->{
            try{
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(sym,"1mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                RadarTechnicalEngine.Result rt=RadarTechnicalEngine.analyze(d);
                RadarItem item=new RadarItem(sym,r);
                item.score=rt.score; item.rankedScore=rt.score;
                item.why=rt.summary+" • "+item.why;
                freshResults.add(item);
            }catch(Exception e){scanFailed.incrementAndGet();}
            int done=scanDone.incrementAndGet();
            if(done>=universe.length){
                List<RadarItem>sorted=new ArrayList<>(freshResults);
                sorted.sort((a,b)->Double.compare(b.rankedScore,a.rankedScore));
                if(!sorted.isEmpty()){radarResults.clear();radarResults.addAll(sorted);}
                main.post(this::showRadar);
                enrichRadarTopCandidates(25);
            }else if(done%10==0)main.post(this::showRadar);
        });
    }

    '''
s=s[:start]+scan+s[end:]

# Add the legacy short-term card only when a suitable insertion point exists.
# v55 later replaces this whole basket screen, so failure here must not abort builds.
m=re.search(r'(private void showBaskets\(\)\s*\{.*?shell\([^;]+;)',s,re.S)
if m:
    ui='''
        LinearLayout shortTermScanCard=card();
        shortTermScanCard.addView(bold("Kısa Vade Güncel AL/SAT Taraması",19,GREEN));
        shortTermScanCard.addView(txt("BIST hisselerini güncel teknik veriyle tarar. Son tamamlanan sonuçlar yeni tarama bitene kadar ekranda ve üçlü stratejide korunur.",13,Color.DKGRAY));
        Button shortTermScanButton=button(scanRunning?"Tarama devam ediyor…":"Kısa Vade Fırsatlarını Tara",GREEN);
        shortTermScanButton.setEnabled(!scanRunning);
        shortTermScanButton.setOnClickListener(v->scanRadar());
        shortTermScanCard.addView(shortTermScanButton); content.addView(shortTermScanCard); spacer(8);
        if(!radarResults.isEmpty()){ content.addView(bold("Güncel 1–3 günlük fırsatlar",17,NAVY)); renderRadarList(new ArrayList<>(radarResults),10); spacer(8); }
'''
    s=s[:m.end()]+ui+s[m.end():]

p.write_text(s,encoding='utf-8')

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 47',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.11.1'",g)
b.write_text(g,encoding='utf-8')
