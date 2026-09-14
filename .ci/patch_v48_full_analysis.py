from pathlib import Path
import re
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
pat=r'    private void analyzeStock\(String symbol\) \{.*?\n    \}\n\n    private void renderStockDetail\(String symbol,ShortPulseEngine\.Result r,CatalystContextEngine\.Result cx,List<MarketDataService\.Candle> chart\) \{.*?\n    \}'
rep='''    private void analyzeStock(String symbol) {
        shell(symbol+" • analiz"); ProgressBar p=new ProgressBar(this);content.addView(p);content.addView(txt("Fiyat ve teknik göstergeler hazırlanıyor…",15,NAVY));
        io.execute(()->{try{
            List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"6mo");
            if(d==null||d.size()<20)throw new Exception("yetersiz fiyat verisi");
            final List<MarketDataService.Candle> data=d;
            main.post(()->renderFastTechnicalDetail(symbol,data));
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,data);
            List<MarketDataService.Candle>chart=data.subList(Math.max(0,data.size()-10),data.size());
            main.post(()->{ if(currentPage.startsWith(symbol+" •")) renderStockDetail(symbol,a,chart); });
        }catch(Exception e){main.post(()->{shell(symbol+" • analiz");String m=e.getMessage();if(m==null||m.trim().isEmpty())m=e.getClass().getSimpleName();content.addView(txt("Analiz verisi alınamadı: "+m,15,RED));});}});
    }

    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){
        ShortPulseEngine.Result r=ShortPulseEngine.analyze(data);
        RadarTechnicalEngine.Result rt=RadarTechnicalEngine.analyze(data);
        LegacyTechnicalEnsemble.Result legacy=LegacyTechnicalEnsemble.analyze(data);
        AdditionalIndicatorEngine.Result add=AdditionalIndicatorEngine.analyze(data);
        AdvancedIndicatorEngine.Result adv=AdvancedIndicatorEngine.analyze(data);
        List<MarketDataService.Candle>chart=data.subList(Math.max(0,data.size()-35),data.size());
        shell(symbol+" • hızlı teknik");
        LinearLayout q=card();q.addView(bold(symbol,22,NAVY));q.addView(bold(money(r.price,symbol),25,r.changePct>=0?GREEN:RED));q.addView(txt("Son gün %"+fmt(r.changePct)+" • ATR% "+fmt(r.atrPct)+" • RelVol x"+fmt(r.relativeVolume),14,Color.DKGRAY));content.addView(q);spacer(7);
        LinearLayout sig=card();String rec=r.recommendation==null?"BEKLE":r.recommendation;int rc=rec.contains("SAT")||rec.contains("RİSK")?RED:rec.contains("AL")?GREEN:AMBER;sig.addView(bold("Hızlı teknik sonuç: "+rec,19,rc));sig.addView(txt("Radar teknik skor: "+fmt(rt.score),14,Color.DKGRAY));sig.addView(txt(rt.summary,13,Color.DKGRAY));sig.addView(txt("Momentum: "+r.momentumText,13,Color.DKGRAY));sig.addView(txt("Para/Hacim: "+r.flowText,13,Color.DKGRAY));sig.addView(txt("Trend: "+r.trendText,13,Color.DKGRAY));content.addView(sig);spacer(7);
        LinearLayout ind=card();ind.addView(bold("Teknik göstergeler",17,NAVY));ind.addView(txt(legacy.summary,13,Color.DKGRAY));ind.addView(txt(add.summary,13,Color.DKGRAY));ind.addView(txt(adv.summary,13,Color.DKGRAY));content.addView(ind);spacer(7);
        content.addView(new PriceChartView(this,chart,"SON "+chart.size()+" GÜN"),new LinearLayout.LayoutParams(-1,dp(280)));spacer(7);
        LinearLayout wait=card();wait.addView(bold("Derin analiz arka planda sürüyor",15,AMBER));wait.addView(txt("Haber/KAP/makro, geri test ve öğrenilmiş skor hazır olunca ekran otomatik tamamlanır.",12,Color.GRAY));content.addView(wait);
    }

    private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart) {
        ShortPulseEngine.Result r=a.pulse; CatalystContextEngine.Result cx=a.context;
        shell(symbol+" • Son 10 işlem günü");
        LinearLayout q=card();q.addView(bold(symbol,22,NAVY));q.addView(bold(money(r.price,symbol),25,r.changePct>=0?GREEN:RED));
        q.addView(txt("Son gün %"+fmt(r.changePct)+"  •  ATR% "+fmt(r.atrPct)+"  •  RelVol x"+fmt(r.relativeVolume),14,Color.DKGRAY));content.addView(q);spacer(7);
        content.addView(signalBanner(r));spacer(7);content.addView(contextBanner(cx));spacer(7);
        LinearLayout decision=card(); decision.addView(bold(a.decision.state,18,a.decision.caution?AMBER:GREEN));
        decision.addView(txt(a.decision.note,14,Color.DKGRAY)); decision.addView(txt("Birleşik güven %"+a.combinedConfidence+" • "+a.consensus.label,13,NAVY2));
        decision.addView(bold(a.adaptive.summary,14,a.adaptive.score>=1?GREEN:a.adaptive.score<=-1?RED:AMBER));
        decision.addView(bold(a.learnedScore.summary,14,a.learnedScore.score>=.8?GREEN:a.learnedScore.score<=-.8?RED:AMBER));content.addView(decision);spacer(7);
        content.addView(new PriceChartView(this,chart,"SON 10 İŞLEM GÜNÜ"),new LinearLayout.LayoutParams(-1,dp(300)));spacer(7);
        LinearLayout tech=card();tech.addView(bold("Teknik motorlar",17,NAVY));tech.addView(txt(a.legacy.summary,13,Color.DKGRAY));
        tech.addView(txt(a.additional.summary,13,Color.DKGRAY));tech.addView(txt(a.advanced.summary,13,Color.DKGRAY));
        tech.addView(txt("Teknik teyit +"+a.consensus.positive+" / -"+a.consensus.negative+" / nötr "+a.consensus.neutral,13,NAVY2));content.addView(tech);spacer(7);
        LinearLayout learn=card();learn.addView(bold("Geriye dönük öğrenme",17,NAVY));learn.addView(txt(a.backtest.summary,13,Color.DKGRAY));
        learn.addView(txt(a.walkForward.summary,13,Color.DKGRAY));learn.addView(txt(a.adaptiveWeights.summary,13,Color.DKGRAY));
        learn.addView(txt(a.learnedPerformance.summary,13,NAVY2));learn.addView(txt(a.learnedWeights.summary,12,Color.DKGRAY));
        learn.addView(txt("En başarılı teknik aile: "+a.learnedPerformance.bestMethod+" • Hisseye özel öğrenilmiş skor: "+fmt(a.learnedScore.score),13,PURPLE));
        learn.addView(txt("Aşırı uyum koruması: "+fmt(a.adaptive.reliability)+" • geçmiş performans sadece ağırlığı sınırlar, tek başına karar vermez.",12,Color.GRAY));content.addView(learn);spacer(7);
        LinearLayout horizon=card();horizon.addView(bold("Zaman ufku",17,NAVY));
        horizon.addView(txt(a.horizons.shortTerm.label+" • "+fmt(a.horizons.shortTerm.strength)+"/100 • "+a.horizons.shortTerm.note,13,Color.DKGRAY));
        horizon.addView(txt(a.horizons.mediumTerm.label+" • "+fmt(a.horizons.mediumTerm.strength)+"/100 • "+a.horizons.mediumTerm.note,13,Color.DKGRAY));
        horizon.addView(txt(a.horizons.longTerm.label+" • "+fmt(a.horizons.longTerm.strength)+"/100 • "+a.horizons.longTerm.note,13,Color.DKGRAY));content.addView(horizon);spacer(7);
        LinearLayout news=card();news.addView(bold("Bilgi akışı",17,NAVY));news.addView(txt(ContextDisplayFormatter.headline(cx),14,Color.DKGRAY));news.addView(txt(ContextDisplayFormatter.detail(cx),13,Color.DKGRAY));
        news.addView(txt(cx.note,14,cx.technicalConflict?PURPLE:Color.DKGRAY));news.addView(txt(ContextEventFormatter.top(cx,4),12,Color.GRAY));content.addView(news);spacer(7);
        LinearLayout old=card();old.addView(bold("Korunan teknik set",16,NAVY));old.addView(txt(TechnicalInventory.indicators(),12,Color.DKGRAY));old.addView(txt(TechnicalInventory.methods(),12,Color.DKGRAY));old.addView(txt(a.calendar.note,12,Color.GRAY));content.addView(old);spacer(7);
        Button add=button("Portföye Ekle",GREEN);content.addView(add);add.setOnClickListener(v->portfolioDialog(null,symbol));
    }'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('full analysis patch failed')
p.write_text(s,encoding='utf-8')
