from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Foreground auto-refresh state. 15 minutes matches the practical market-data delay
# without hammering the data source. Completed results always remain visible.
field_anchor='    private String shortScanMode="1S";'
fields='''    private String shortScanMode="1S";
    private static final long MAIN_RADAR_REFRESH_MS=15L*60L*1000L;
    private static final long MAIN_RADAR_FIRST_CHECK_MS=3500L;
    private boolean appInForeground=false;
    private String currentPage="";
    private long lastRadarRefreshAt=0L;
    private final Runnable autoRadarRefresh=new Runnable(){
        @Override public void run(){
            if(!appInForeground)return;
            long now=System.currentTimeMillis();
            if(primaryMarket()==0 && !scanRunning && (radarResults.isEmpty() || now-lastRadarRefreshAt>=MAIN_RADAR_REFRESH_MS)) scanRadar();
            main.postDelayed(this,MAIN_RADAR_REFRESH_MS);
        }
    };'''
if 'MAIN_RADAR_REFRESH_MS' not in s:
    if field_anchor not in s: raise SystemExit('continuous radar field anchor missing')
    s=s.replace(field_anchor,fields,1)

# Track page so background refresh never yanks the user away from Portfolio/Detail/3 Strategy.
s=s.replace('private void shell(String page) {','private void shell(String page) {\n        currentPage=page==null?"":page;',1)

# Helper methods before showPortfolio.
marker='    private void showPortfolio()'
helpers='''    private boolean radarPageVisible(){
        return currentPage.contains("Radar") || currentPage.contains("radar");
    }

    private void refreshRadarUiIfVisible(){
        if(radarPageVisible()) showRadar();
    }

    private void markRadarRefreshCompleted(){
        lastRadarRefreshAt=System.currentTimeMillis();
        getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putLong(profileKey("radar_last_refresh"),lastRadarRefreshAt).apply();
    }

    @Override protected void onResume(){
        super.onResume();
        appInForeground=true;
        lastRadarRefreshAt=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong(profileKey("radar_last_refresh"),0L);
        main.removeCallbacks(autoRadarRefresh);
        main.postDelayed(autoRadarRefresh,MAIN_RADAR_FIRST_CHECK_MS);
    }

    @Override protected void onPause(){
        appInForeground=false;
        main.removeCallbacks(autoRadarRefresh);
        super.onPause();
    }

'''
if 'private boolean radarPageVisible()' not in s:
    if marker not in s: raise SystemExit('showPortfolio marker missing')
    s=s.replace(marker,helpers+marker,1)

# Ensure destroy also removes callbacks.
s=s.replace('''    @Override protected void onDestroy() {
        io.shutdownNow();''','''    @Override protected void onDestroy() {
        main.removeCallbacks(autoRadarRefresh);
        io.shutdownNow();''',1)

# Main scan: keep old completed list on screen while scanBuffer is filled.
# Never force navigation during an automatic background refresh.
start=s.find('private void scanRadar()')
end=s.find('private void enrichRadarTopCandidates',start)
if start<0 or end<0: raise SystemExit('scanRadar boundaries missing')
main_scan='''private void scanRadar() {
        if(scanRunning)return;
        scanRunning=true;scanDone.set(0);scanFailed.set(0);scanBuffer.clear();
        main.post(this::refreshRadarUiIfVisible);
        for(String sym:ALL_SYMBOLS)io.execute(()->{
            try{
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(sym,"3mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                RadarTechnicalEngine.Result rt=RadarTechnicalEngine.analyze(d);
                RadarItem item=new RadarItem(sym,r);
                item.score=rt.score; item.rankedScore=rt.score;
                item.why=rt.summary+" • "+item.why;
                scanBuffer.add(item);
            }catch(Exception e){scanFailed.incrementAndGet();}
            int done=scanDone.incrementAndGet();
            if(done>=ALL_SYMBOLS.length){
                List<RadarItem>sorted=new ArrayList<>(scanBuffer);
                sorted.sort((a,b)->Double.compare(b.score,a.score));
                if(!sorted.isEmpty()){radarResults.clear();radarResults.addAll(sorted);saveRadarCache();}
                main.post(this::refreshRadarUiIfVisible);
                enrichRadarTopCandidates(25);
            }else if(done%25==0)main.post(this::refreshRadarUiIfVisible);
        });
    }

    '''
s=s[:start]+main_scan+s[end:]

# Enrichment used to call showRadar directly; route those calls through the visibility guard.
s=s.replace('if(n==0){scanRunning=false;main.post(this::showRadar);return;}','if(n==0){scanRunning=false;markRadarRefreshCompleted();main.post(this::refreshRadarUiIfVisible);return;}',1)
s=s.replace('saveRadarCache();scanRunning=false;\n                    main.post(this::showRadar);','saveRadarCache();scanRunning=false;markRadarRefreshCompleted();\n                    main.post(this::refreshRadarUiIfVisible);',1)
s=s.replace('}else if(k%5==0)main.post(this::showRadar);','}else if(k%5==0)main.post(this::refreshRadarUiIfVisible);',1)

# Radar screen status: explicitly tell user that the old list stays visible and auto-refresh is active.
status_anchor='''top.addView(txt("Son tamamlanan tarama ekranda kalır. Yeni tarama arkada hazırlanır; bitince liste tek seferde yenilenir. En güçlü adaylar haber/KAP/makro bağlamıyla ikinci kez sıralanır.",13,Color.DKGRAY));'''
status_repl=status_anchor+'''\n        long age=lastRadarRefreshAt>0?Math.max(0,(System.currentTimeMillis()-lastRadarRefreshAt)/60000L):-1;\n        top.addView(txt("Otomatik yenileme: 15 dk"+(age>=0?" • son tamamlanma "+age+" dk önce":" • ilk tarama hazırlanıyor"),12,Color.GRAY));'''
if status_anchor in s and 'Otomatik yenileme: 15 dk' not in s:
    s=s.replace(status_anchor,status_repl,1)

# Version bump.
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 52',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.4'",g)
b.write_text(g,encoding='utf-8')
p.write_text(s,encoding='utf-8')
