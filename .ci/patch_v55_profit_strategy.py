from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Keep completed main radar visible while a new scan runs; build new results in a buffer.
pat=r'(\s*private\s+final\s+List<RadarItem>\s+radarResults\s*=\s*Collections\.synchronizedList\(new\s+ArrayList<>\(\)\)\s*;)'
rep=r'''\1
    private final List<RadarItem> scanBuffer=Collections.synchronizedList(new ArrayList<>());
    private final List<RadarItem> shortRadarResults=Collections.synchronizedList(new ArrayList<>());
    private volatile boolean shortScanRunning=false;
    private final AtomicInteger shortScanDone=new AtomicInteger(0), shortScanFailed=new AtomicInteger(0);
    private String shortScanMode="1S";'''
s,n=re.subn(pat,rep,s,count=1)
if n!=1: raise SystemExit('radar fields patch failed')

s=s.replace('''        loadPortfolio();
        loadRadarCache();
        showPortfolio();''','''        loadPortfolio();
        loadRadarCache();
        loadShortRadarCache();
        showPortfolio();''',1)

# Replace main scan using method-name boundaries, independent of intermediate formatting patches.
start=s.find('private void scanRadar()')
end=s.find('private void enrichRadarTopCandidates',start)
if start<0 or end<0: raise SystemExit('persistent main radar boundaries not found')
indent='    '
main_scan='''private void scanRadar() {
        if(scanRunning)return;
        scanRunning=true;scanDone.set(0);scanFailed.set(0);scanBuffer.clear();showRadar();
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
                if(!sorted.isEmpty()){radarResults.clear();radarResults.addAll(sorted);}
                main.post(this::showRadar);
                enrichRadarTopCandidates(25);
            }else if(done%25==0)main.post(this::showRadar);
        });
    }

    '''
s=s[:start]+main_scan+s[end:]

s=s.replace('''top.addView(bold("Tüm hisseler • iki aşamalı radar",19,NAVY));''','''top.addView(bold("Ana Radar • sonuçlar kaybolmaz",19,NAVY));''',1)
s=s.replace('''1) Tüm BIST teknik olarak hızlı taranır. 2) En güçlü 25 aday için haber/KAP/makro bağlamı alınır ve liste yeniden sıralanır. Böylece yüzlerce gereksiz haber isteği yapılmaz.''','''Son tamamlanan tarama ekranda kalır. Yeni tarama arkada hazırlanır; bitince liste tek seferde yenilenir. En güçlü adaylar haber/KAP/makro bağlamıyla ikinci kez sıralanır.''',1)

# Replace baskets using method-name boundaries as well.
start=s.find('private void showBaskets()')
end=s.find('private void basket(',start)
if start<0 or end<0: raise SystemExit('three strategy boundaries not found')
strategy='''private void showBaskets() {
        shell("3 Strateji • Kâr + Temettü");
        LinearLayout shortCard=card();
        shortCard.addView(bold("1 • KISA VADE AL–SAT RADARI",20,GREEN));
        shortCard.addView(txt("Saatlik veya günlük veriyle tüm BIST içinde güncel momentum fırsatlarını ara. Önceki kısa-vade sonucu yeni tarama bitene kadar korunur.",13,Color.DKGRAY));
        LinearLayout scanRow=new LinearLayout(this);scanRow.setOrientation(LinearLayout.HORIZONTAL);
        Button hourly=button(shortScanRunning?"Taranıyor…":"Saatlik Tara",GREEN);
        Button daily=button(shortScanRunning?"Taranıyor…":"Günlük Tara",NAVY2);
        hourly.setEnabled(!shortScanRunning);daily.setEnabled(!shortScanRunning);
        scanRow.addView(hourly,new LinearLayout.LayoutParams(0,-2,1));scanRow.addView(daily,new LinearLayout.LayoutParams(0,-2,1));shortCard.addView(scanRow);
        hourly.setOnClickListener(v->scanShortTerm("1S"));daily.setOnClickListener(v->scanShortTerm("1G"));
        if(shortScanRunning){ProgressBar pb=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);pb.setMax(ALL_SYMBOLS.length);pb.setProgress(shortScanDone.get());shortCard.addView(pb);shortCard.addView(txt(shortScanMode+" • "+shortScanDone.get()+"/"+ALL_SYMBOLS.length+" • başarısız "+shortScanFailed.get(),12,Color.GRAY));}
        content.addView(shortCard);spacer(8);
        if(!shortRadarResults.isEmpty()){content.addView(bold("Güncel kısa-vade fırsatları • "+shortScanMode,17,NAVY));renderRadarList(new ArrayList<>(shortRadarResults),10);spacer(10);}
        if(radarResults.isEmpty()){
            LinearLayout c=card();c.addView(bold("Ana radar sonucu yok",18,NAVY));c.addView(txt("Uzun vade ve temettü sepeti için önce Ana Radar'da BIST taramasını bir kez tamamla. Kısa-vade saatlik/günlük tarama yukarıdan bağımsız çalışır.",13,Color.DKGRAY));content.addView(c);return;
        }
        List<RadarItem>all=new ArrayList<>(radarResults);
        all.sort((a,b)->Double.compare(b.rankedScore,a.rankedScore));
        List<RadarItem>growth=new ArrayList<>(),div=new ArrayList<>();
        List<String>dp=Arrays.asList(DIVIDEND_POOL);
        for(RadarItem r:all){
            if(r.rankedScore>=3.6&&r.confidence>=58&&!r.recommendation.contains("SAT")&&!r.recommendation.contains("RİSK"))growth.add(r);
            if(dp.contains(r.symbol)&&r.rankedScore>=1.5&&!r.recommendation.contains("SAT")&&!r.recommendation.contains("RİSK"))div.add(r);
        }
        basket("2 • UZUN VADE BÜYÜME / KÂR",33333,growth,NAVY2,"Amaç: güçlü trendi ve bağlamı olan hisseleri daha uzun süre taşımak. Kısa dalgalanmada gereksiz satış yerine trend bozulmasını izler.");
        basket("3 • TEMETTÜ + UZUN VADE TUT",33334,div,PURPLE,"Amaç: temettü kalitesi olan hisselerde giriş zamanını teknik görünümle iyileştirip uzun vadeli tutmak.");
        content.addView(txt("Hiçbir sinyal kârı garanti etmez. Sistem fırsat, risk, stop ve güven düzeyini birlikte gösterir; zayıf durumda nakitte beklemek de geçerli sonuçtur.",12,Color.GRAY));
    }

    private void scanShortTerm(String mode){
        if(shortScanRunning)return;
        shortScanRunning=true;shortScanMode=mode;shortScanDone.set(0);shortScanFailed.set(0);
        final List<RadarItem> buffer=Collections.synchronizedList(new ArrayList<>());
        showBaskets();
        for(String sym:ALL_SYMBOLS)io.execute(()->{
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
            if(done>=ALL_SYMBOLS.length){
                List<RadarItem> sorted=new ArrayList<>(buffer);
                sorted.sort((a,b)->Double.compare(b.score,a.score));
                if(!sorted.isEmpty()){shortRadarResults.clear();int n=Math.min(40,sorted.size());shortRadarResults.addAll(sorted.subList(0,n));saveShortRadarCache();}
                shortScanRunning=false;main.post(this::showBaskets);
            }else if(done%30==0)main.post(this::showBaskets);
        });
    }

    private void saveShortRadarCache(){
        JSONArray a=new JSONArray();
        try{int n=Math.min(40,shortRadarResults.size());for(int i=0;i<n;i++){RadarItem r=shortRadarResults.get(i);JSONObject o=new JSONObject();o.put("s",r.symbol);o.put("r",r.recommendation);o.put("w",r.why);o.put("h",r.horizon);o.put("p",r.price);o.put("sc",r.score);o.put("cf",r.confidence);a.put(o);}}catch(Exception ignored){}
        getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString(profileKey("short_radar"),a.toString()).putString(profileKey("short_mode"),shortScanMode).apply();
    }

    private void loadShortRadarCache(){
        shortRadarResults.clear();
        try{android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);shortScanMode=sp.getString(profileKey("short_mode"),"1S");JSONArray a=new JSONArray(sp.getString(profileKey("short_radar"),"[]"));for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);ShortPulseEngine.Result pr=new ShortPulseEngine.Result();pr.recommendation=o.getString("r");pr.explanation=o.getString("w");pr.horizonText=o.getString("h");pr.price=o.getDouble("p");pr.score=o.getDouble("sc");pr.confidence=o.getDouble("cf");RadarItem ri=new RadarItem(o.getString("s"),pr);ri.rankedScore=ri.score;shortRadarResults.add(ri);}}catch(Exception ignored){}
    }

    '''
s=s[:start]+strategy+s[end:]

s=s.replace('''        loadPortfolio(); loadRadarCache(); showPortfolio();''','''        loadPortfolio(); loadRadarCache(); loadShortRadarCache(); showPortfolio();''',1)

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 49',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.1'",g)
b.write_text(g,encoding='utf-8')
p.write_text(s,encoding='utf-8')
