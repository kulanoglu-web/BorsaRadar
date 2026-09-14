from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

s=s.replace('button("Radar",GREEN)', 'button("Tarama",GREEN)')
s=s.replace('shell("Tüm Borsa İstanbul Radarı")', 'shell("Güncel Fırsat Taraması")')
s=s.replace('button(scanRunning?"Tarama devam ediyor…":"Tüm BIST\'i Tara",GREEN)', 'button(scanRunning?"Tarama devam ediyor…":"Güncel AL/SAT Fırsatlarını Tara",GREEN)')

# This patch runs after international-market patches. Keep the last completed
# snapshot visible while a fresh primary-market scan is collected separately.
pat=r'    private void scanRadar\(\) \{.*?\n    \}\n\n    private void renderRadarList'
rep='''    private void scanRadar() {
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
                radarResults.clear();radarResults.addAll(sorted);
                saveRadarCache();scanRunning=false;
                main.post(this::showRadar);
            }else if(done%10==0)main.post(this::showRadar);
        });
    }

    private void renderRadarList'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('persistent radar method patch failed')

m=re.search(r'(private void showBaskets\(\) \{.*?shell\([^;]+;)',s,re.S)
if not m:
    raise SystemExit('three basket insertion point missing')
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
