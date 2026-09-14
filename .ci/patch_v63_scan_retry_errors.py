from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Track retry/error state without dropping successfully completed radar results.
# v59 no longer has an automatic-refresh constant, so anchor to a stable field.
anchor='    private boolean appInForeground=false;'
fields='''    private boolean appInForeground=false;
    private static final int MAIN_SCAN_MAX_RETRIES=2;
    private final java.util.concurrent.ConcurrentHashMap<String,String> radarScanErrors=new java.util.concurrent.ConcurrentHashMap<>();
    private final AtomicInteger radarRetryCount=new AtomicInteger(0);'''
if 'MAIN_SCAN_MAX_RETRIES' not in s:
    if anchor not in s: raise SystemExit('retry field anchor missing')
    s=s.replace(anchor,fields,1)

start=s.find('private void scanRadar()')
end=s.find('private void enrichRadarTopCandidates',start)
if start<0 or end<0: raise SystemExit('scanRadar boundaries missing')
replacement='''private void scanRadar() {
        if(scanRunning)return;
        scanRunning=true;
        scanDone.set(0);scanFailed.set(0);radarRetryCount.set(0);
        scanBuffer.clear();radarScanErrors.clear();
        main.post(this::refreshRadarUiIfVisible);
        for(String sym:ALL_SYMBOLS) scanRadarSymbol(sym,0);
    }

    private void scanRadarSymbol(String sym,int attempt){
        io.execute(()->{
            try{
                if(attempt>0){
                    radarRetryCount.incrementAndGet();
                    try{Thread.sleep(650L*attempt);}catch(InterruptedException ie){Thread.currentThread().interrupt();}
                }
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(sym,"3mo");
                if(d==null||d.size()<20)throw new Exception("yetersiz fiyat verisi ("+(d==null?0:d.size())+")");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                RadarTechnicalEngine.Result rt=RadarTechnicalEngine.analyze(d);
                RadarItem item=new RadarItem(sym,r);
                item.score=rt.score; item.rankedScore=rt.score;
                item.why=rt.summary+" • "+item.why;
                scanBuffer.add(item);
                radarScanErrors.remove(sym);
                finishRadarSymbol();
            }catch(Exception e){
                String msg=e.getMessage();
                if(msg==null||msg.trim().isEmpty())msg=e.getClass().getSimpleName();
                radarScanErrors.put(sym,"Deneme "+(attempt+1)+": "+msg);
                if(attempt<MAIN_SCAN_MAX_RETRIES){
                    main.post(this::refreshRadarUiIfVisible);
                    scanRadarSymbol(sym,attempt+1);
                }else{
                    scanFailed.incrementAndGet();
                    finishRadarSymbol();
                }
            }
        });
    }

    private void finishRadarSymbol(){
        int done=scanDone.incrementAndGet();
        if(done>=ALL_SYMBOLS.length){
            List<RadarItem>sorted=new ArrayList<>(scanBuffer);
            sorted.sort((a,b)->Double.compare(b.score,a.score));
            if(!sorted.isEmpty()){radarResults.clear();radarResults.addAll(sorted);saveRadarCache();}
            main.post(this::refreshRadarUiIfVisible);
            enrichRadarTopCandidates(25);
        }else if(done%20==0)main.post(this::refreshRadarUiIfVisible);
    }

    '''
s=s[:start]+replacement+s[end:]

# Add transparent scan health/error reporting to the Radar page after the persistent-radar status line.
needle='top.addView(txt("Kalıcı radar"+(age>=0?" • son tamamlanma "+age+" dk önce":" • henüz tamamlanmış tarama yok")+" • yeniden tarama yalnızca düğmeyle",12,Color.GRAY));'
extra='''top.addView(txt("Kalıcı radar"+(age>=0?" • son tamamlanma "+age+" dk önce":" • henüz tamamlanmış tarama yok")+" • yeniden tarama yalnızca düğmeyle",12,Color.GRAY));
        int terminal=scanDone.get(), failed=scanFailed.get(), retries=radarRetryCount.get();
        top.addView(txt("Tarama durumu: "+terminal+"/"+ALL_SYMBOLS.length+" tamamlandı • başarısız "+failed+" • yeniden deneme "+retries,12,failed>0?AMBER:Color.GRAY));
        if(!radarScanErrors.isEmpty()){
            LinearLayout err=card(); err.addView(bold("Veri alınamayan / yeniden denenen hisseler",15,AMBER));
            int shown=0;
            java.util.ArrayList<String> keys=new java.util.ArrayList<>(radarScanErrors.keySet());
            java.util.Collections.sort(keys);
            for(String k:keys){
                if(shown++>=12)break;
                err.addView(txt(k+" • "+radarScanErrors.get(k),12,Color.GRAY));
            }
            if(keys.size()>12)err.addView(txt("+"+(keys.size()-12)+" hisse daha",12,Color.GRAY));
            content.addView(err);spacer(7);
        }'''
if needle in s and 'Veri alınamayan / yeniden denenen hisseler' not in s:
    s=s.replace(needle,extra,1)

# Version retained here; later patches bump further.
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 54',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.6'",g)
b.write_text(g,encoding='utf-8')
p.write_text(s,encoding='utf-8')
