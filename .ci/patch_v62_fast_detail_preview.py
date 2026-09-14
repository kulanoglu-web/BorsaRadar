from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Replace the single-stock entry point so the user sees technical output immediately.
start=s.find('private void analyzeStock(String symbol)')
end=s.find('private void renderStockDetail',start)
if start<0 or end<0: raise SystemExit('analyzeStock boundaries missing')
new='''private void analyzeStock(String symbol) {
        shell(symbol+" • analiz");
        ProgressBar p=new ProgressBar(this);content.addView(p);
        content.addView(txt("Fiyat ve teknik göstergeler hazırlanıyor…",15,Color.GRAY));
        detailIo.execute(()->{try{
            // US stocks are displayed in EUR. Prime the cached USD/EUR rate before
            // the fast detail card is rendered so the first price is not shown as — €.
            CurrencyService.refreshIfNeeded();
            List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"6mo");
            if(d==null||d.size()<20)throw new Exception("yetersiz fiyat verisi");
            final List<MarketDataService.Candle> data=d;
            main.post(()->renderFastTechnicalDetail(symbol,data));
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,data);
            List<MarketDataService.Candle>chart=data.subList(Math.max(0,data.size()-10),data.size());
            main.post(()->{
                if(currentPage.startsWith(symbol+" •")) renderStockDetail(symbol,a,chart);
            });
        }catch(Exception e){main.post(()->{
            shell(symbol+" • analiz");
            String m=e.getMessage(); if(m==null||m.trim().isEmpty())m=e.getClass().getSimpleName();
            content.addView(txt("Analiz verisi alınamadı: "+m,15,RED));
        });}});
    }

    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){
        ShortPulseEngine.Result r=ShortPulseEngine.analyze(data);
        RadarTechnicalEngine.Result rt=RadarTechnicalEngine.analyze(data);
        LegacyTechnicalEnsemble.Result legacy=LegacyTechnicalEnsemble.analyze(data);
        AdditionalIndicatorEngine.Result add=AdditionalIndicatorEngine.analyze(data);
        AdvancedIndicatorEngine.Result adv=AdvancedIndicatorEngine.analyze(data);
        List<MarketDataService.Candle> chart=data.subList(Math.max(0,data.size()-35),data.size());
        shell(symbol+" • hızlı teknik");
        LinearLayout q=card();
        q.addView(bold(symbol,25,Color.WHITE));
        q.addView(bold(money(r.price,symbol),28,r.changePct>=0?GREEN:RED));
        q.addView(bold((r.changePct>=0?"▲ +":"▼ ")+fmt(r.changePct)+"%",16,r.changePct>=0?GREEN:RED));
        q.addView(txt("ATR %"+fmt(r.atrPct)+" • RelVol x"+fmt(r.relativeVolume)+" • Güven %"+(int)r.confidence,13,Color.DKGRAY));
        content.addView(q);spacer(7);

        LinearLayout sig=card();
        String rec=r.recommendation==null?"BEKLE":r.recommendation;
        int rc=rec.contains("SAT")||rec.contains("RİSK")?RED:rec.contains("AL")?GREEN:AMBER;
        sig.addView(bold("Hızlı teknik sonuç: "+rec,20,rc));
        sig.addView(txt("Radar teknik skor: "+fmt(rt.score),14,Color.DKGRAY));
        sig.addView(txt(rt.summary,13,Color.DKGRAY));
        sig.addView(txt("Momentum: "+r.momentumText,13,Color.DKGRAY));
        sig.addView(txt("Para/Hacim: "+r.flowText,13,Color.DKGRAY));
        sig.addView(txt("Trend: "+r.trendText,13,Color.DKGRAY));
        content.addView(sig);spacer(7);

        LinearLayout ind=card(); ind.addView(bold("Teknik göstergeler",17,Color.WHITE));
        ind.addView(txt(legacy.summary,13,Color.DKGRAY));
        ind.addView(txt(add.summary,13,Color.DKGRAY));
        ind.addView(txt(adv.summary,13,Color.DKGRAY));
        content.addView(ind);spacer(7);

        LinearLayout cc=card(); cc.addView(bold("Grafik",17,Color.WHITE));
        cc.addView(new PriceChartView(this,chart,"SON "+chart.size()+" GÜN"),new LinearLayout.LayoutParams(-1,dp(280)));
        content.addView(cc);spacer(7);

        LinearLayout wait=card();
        wait.addView(bold("Derin analiz arka planda sürüyor",15,AMBER));
        wait.addView(txt("Haber/KAP/makro, geriye dönük test, öğrenilmiş ağırlıklar ve zaman ufku hazır olunca bu ekran otomatik tamamlanacak.",12,Color.GRAY));
        content.addView(wait);
    }

    '''
s=s[:start]+new+s[end:]

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 54',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.6'",g)
b.write_text(g,encoding='utf-8')
p.write_text(s,encoding='utf-8')
