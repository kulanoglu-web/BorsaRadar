from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

pat=r'''    private void renderStockDetail\(String symbol,FullAnalysisEngine\.Result a,List<MarketDataService\.Candle> chart\) \{.*?\n    \}\n'''
rep='''    private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart) {
        renderStockDetail(symbol,a,chart,"10G");
    }

    private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame) {
        ShortPulseEngine.Result r=a.pulse; CatalystContextEngine.Result cx=a.context;
        shell(symbol+" • "+frame);

        LinearLayout quote=card();
        LinearLayout top=new LinearLayout(this); top.setOrientation(LinearLayout.HORIZONTAL); top.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout left=new LinearLayout(this); left.setOrientation(LinearLayout.VERTICAL);
        left.addView(bold(symbol,26,Color.WHITE));
        left.addView(txt(marketName(MarketSymbol.marketIndex(symbol))+" • "+frame,12,Color.GRAY));
        top.addView(left,new LinearLayout.LayoutParams(0,-2,1));
        TextView px=bold(money(r.price,symbol),28,r.changePct>=0?GREEN:RED); px.setGravity(Gravity.RIGHT); top.addView(px);
        quote.addView(top);
        TextView move=bold((r.changePct>=0?"▲ +":"▼ ")+fmt(r.changePct)+"%",16,r.changePct>=0?GREEN:RED); move.setGravity(Gravity.RIGHT); quote.addView(move);
        quote.addView(txt("ATR %"+fmt(r.atrPct)+"   •   RelVol x"+fmt(r.relativeVolume)+"   •   Güven %"+(int)r.confidence,13,Color.DKGRAY));
        content.addView(quote); spacer(7);

        LinearLayout tf1=new LinearLayout(this); tf1.setOrientation(LinearLayout.HORIZONTAL);
        String[] frames={"1S","4S","1G","1Hf","1Ay","3Ay","6Ay","1Y"};
        for(String x:frames){Button b=button(x,x.equals(frame)?RED:Color.rgb(49,55,63)); b.setTextSize(12); tf1.addView(b,new LinearLayout.LayoutParams(0,-2,1)); b.setOnClickListener(v->loadFullChartFrame(symbol,a,x));}
        content.addView(tf1); spacer(5);

        LinearLayout chartCard=card(); chartCard.addView(bold("Grafik",17,Color.WHITE));
        chartCard.addView(new PriceChartView(this,chart,frame+" • "+chart.size()+" nokta"),new LinearLayout.LayoutParams(-1,dp(310)));
        content.addView(chartCard); spacer(7);

        LinearLayout action=new LinearLayout(this); action.setOrientation(LinearLayout.HORIZONTAL);
        String rec=r.recommendation==null?"BEKLE":r.recommendation;
        int recColor=rec.contains("SAT")||rec.contains("RİSK")?RED:rec.contains("AL")?GREEN:AMBER;
        Button signal=button(rec,recColor); signal.setTextSize(19);
        Button add=button("Portföye Ekle",Color.rgb(49,55,63)); add.setTextSize(15);
        action.addView(signal,new LinearLayout.LayoutParams(0,dp(58),1.15f)); action.addView(add,new LinearLayout.LayoutParams(0,dp(58),1));
        content.addView(action); add.setOnClickListener(v->portfolioDialog(null,symbol)); spacer(7);

        LinearLayout decision=card(); decision.addView(bold("Karar Özeti",18,Color.WHITE));
        decision.addView(bold(a.decision.state,18,a.decision.caution?AMBER:recColor));
        decision.addView(txt(a.decision.note,14,Color.DKGRAY));
        decision.addView(txt("Birleşik güven %"+a.combinedConfidence+"   •   "+a.consensus.label,13,Color.DKGRAY));
        decision.addView(txt("Stop ref. "+money(r.stopReference,symbol)+"   •   Hedef süre "+r.horizonText,13,Color.DKGRAY));
        content.addView(decision); spacer(7);

        LinearLayout meters=card(); meters.addView(bold("Hızlı Teknik Özet",17,Color.WHITE));
        meters.addView(txt("Momentum  "+r.momentumText,13,Color.DKGRAY));
        meters.addView(txt("Para / Hacim  "+r.flowText,13,Color.DKGRAY));
        meters.addView(txt("Trend  "+r.trendText,13,Color.DKGRAY));
        meters.addView(txt("Teknik teyit  +"+a.consensus.positive+" / -"+a.consensus.negative+" / nötr "+a.consensus.neutral,13,Color.DKGRAY));
        content.addView(meters); spacer(7);

        content.addView(contextBanner(cx)); spacer(7);

        LinearLayout detail=card(); detail.addView(bold("Detaylı Analiz",17,Color.WHITE));
        detail.addView(txt(a.legacy.summary,13,Color.DKGRAY));
        detail.addView(txt(a.additional.summary,13,Color.DKGRAY));
        detail.addView(txt(a.advanced.summary,13,Color.DKGRAY));
        detail.addView(txt(a.backtest.summary,13,Color.DKGRAY));
        detail.addView(txt(a.walkForward.summary,13,Color.DKGRAY));
        detail.addView(txt("En başarılı teknik aile: "+a.learnedPerformance.bestMethod+" • Öğrenilmiş skor "+fmt(a.learnedScore.score),13,PURPLE));
        content.addView(detail); spacer(7);

        LinearLayout hz=card(); hz.addView(bold("Zaman Ufku",17,Color.WHITE));
        hz.addView(txt(a.horizons.shortTerm.label+" • "+fmt(a.horizons.shortTerm.strength)+"/100 • "+a.horizons.shortTerm.note,13,Color.DKGRAY));
        hz.addView(txt(a.horizons.mediumTerm.label+" • "+fmt(a.horizons.mediumTerm.strength)+"/100 • "+a.horizons.mediumTerm.note,13,Color.DKGRAY));
        hz.addView(txt(a.horizons.longTerm.label+" • "+fmt(a.horizons.longTerm.strength)+"/100 • "+a.horizons.longTerm.note,13,Color.DKGRAY));
        content.addView(hz); spacer(7);

        LinearLayout navRow=new LinearLayout(this); navRow.setOrientation(LinearLayout.HORIZONTAL);
        Button prev=button("← Önceki",Color.rgb(49,55,63)), next=button("Sonraki →",Color.rgb(49,55,63));
        navRow.addView(prev,new LinearLayout.LayoutParams(0,-2,1)); navRow.addView(next,new LinearLayout.LayoutParams(0,-2,1)); content.addView(navRow);
        prev.setOnClickListener(v->analyzeStock(adjacentSymbol(symbol,-1))); next.setOnClickListener(v->analyzeStock(adjacentSymbol(symbol,1)));
    }

    private void loadFullChartFrame(String symbol,FullAnalysisEngine.Result a,String frame){
        shell(symbol+" • "+frame+" yükleniyor");
        ProgressBar p=new ProgressBar(this); content.addView(p); content.addView(txt("Grafik verisi alınıyor…",14,Color.GRAY));
        io.execute(()->{try{
            List<MarketDataService.Candle>d;
            if(frame.equals("1S")) d=MarketDataService.fetchSeries(symbol,"5d","1h",100);
            else if(frame.equals("4S")){d=MarketDataService.fetchSeries(symbol,"1mo","1h",0); d=MarketDataService.downsample(MarketDataService.aggregateHours(d,4),100);}
            else if(frame.equals("1G")) d=MarketDataService.fetchSeries(symbol,"3mo","1d",100);
            else if(frame.equals("1Hf")) d=MarketDataService.fetchSeries(symbol,"1y","1wk",100);
            else if(frame.equals("1Ay")) d=MarketDataService.fetchSeries(symbol,"1mo","1d",60);
            else if(frame.equals("6Ay")) d=MarketDataService.fetchSeries(symbol,"6mo","1d",120);
            else if(frame.equals("1Y")) d=MarketDataService.fetchSeries(symbol,"1y","1d",120);
            else d=MarketDataService.fetchSeries(symbol,"3mo","1d",90);
            final List<MarketDataService.Candle> out=d;
            main.post(()->renderStockDetail(symbol,a,out,frame));
        }catch(Exception e){main.post(()->{shell(symbol+" • "+frame); content.addView(txt("Grafik verisi alınamadı: "+e.getMessage(),15,RED));});}});
    }
'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('trade detail patch failed: renderStockDetail not found')

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 51',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.3'",g)
b.write_text(g,encoding='utf-8')
p.write_text(s,encoding='utf-8')
