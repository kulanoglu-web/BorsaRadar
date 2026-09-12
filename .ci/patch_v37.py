from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Analiz motoru 3 aylık günlük veride sabit kalır; grafik zaman dilimleri sadece seçildiğinde yüklenir.
s=re.sub(r'''    private void analyzeStock\(String symbol\) \{.*?\n    \}\n\n    private void renderStockDetail''', '''    private void analyzeStock(String symbol) {
        shell(symbol+" • analiz");
        ProgressBar p=new ProgressBar(this);content.addView(p);content.addView(txt("Karar verisi alınıyor…",15,NAVY));
        io.execute(()->{
            try{
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"3mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                List<MarketDataService.Candle> chart=MarketDataService.downsample(d,90);
                main.post(()->renderStockDetail(symbol,r,chart,"3Ay"));
            }catch(Exception e){main.post(()->{shell(symbol+" • analiz");content.addView(txt("Veri alınamadı: "+e.getMessage(),15,RED));});}
        });
    }

    private void renderStockDetail''', s, count=1, flags=re.S)

s=re.sub(r'''    private void renderStockDetail\(String symbol,ShortPulseEngine\.Result r,List<MarketDataService\.Candle> chart\) \{.*?\n    \}\n\n    private String adjacentSymbol''', '''    private void renderStockDetail(String symbol,ShortPulseEngine.Result r,List<MarketDataService.Candle> chart,String frame) {
        shell(symbol+" • "+frame);
        LinearLayout q=card();q.addView(bold(symbol,22,NAVY));q.addView(bold(money(r.price),25,r.changePct>=0?GREEN:RED));
        q.addView(txt("Son gün %"+fmt(r.changePct)+"  •  ATR% "+fmt(r.atrPct)+"  •  RelVol x"+fmt(r.relativeVolume),14,Color.DKGRAY));content.addView(q);spacer(7);
        content.addView(signalBanner(r));spacer(7);

        LinearLayout tf1=new LinearLayout(this);tf1.setOrientation(LinearLayout.HORIZONTAL);
        String[] a={"1S","4S","1G","1Hf"};
        for(String x:a){Button b=button(x,x.equals(frame)?GREEN:NAVY2);tf1.addView(b,new LinearLayout.LayoutParams(0,-2,1));b.setOnClickListener(v->loadChartFrame(symbol,r,x));}
        content.addView(tf1);
        LinearLayout tf2=new LinearLayout(this);tf2.setOrientation(LinearLayout.HORIZONTAL);
        String[] b2={"1Ay","3Ay","6Ay","1Y"};
        for(String x:b2){Button b=button(x,x.equals(frame)?GREEN:NAVY2);tf2.addView(b,new LinearLayout.LayoutParams(0,-2,1));b.setOnClickListener(v->loadChartFrame(symbol,r,x));}
        content.addView(tf2);
        content.addView(txt("Veri yalnız seçtiğin zaman diliminde yüklenir. 1Y görünüm en fazla 120 grafik noktasıyla seyreltilir.",11,Color.GRAY));
        content.addView(new PriceChartView(this,chart,frame+" • "+chart.size()+" nokta"),new LinearLayout.LayoutParams(-1,dp(300)));spacer(7);

        LinearLayout info=card();info.addView(bold("Neye göre?",17,NAVY));info.addView(txt(r.explanation,14,Color.DKGRAY));
        info.addView(txt("Momentum: "+r.momentumText+"  •  Para/hacim: "+r.flowText+"  •  Trend: "+r.trendText,13,Color.DKGRAY));
        info.addView(txt("Hedef: "+r.horizonText+"  •  Güven %"+(int)r.confidence+"  •  Stop ref. "+money(r.stopReference),13,NAVY2));content.addView(info);

        LinearLayout navRow=new LinearLayout(this); navRow.setOrientation(LinearLayout.HORIZONTAL);
        Button prev=button("← Önceki",NAVY2), add=button("Portföye Ekle",GREEN), next=button("Sonraki →",NAVY2);
        navRow.addView(prev,new LinearLayout.LayoutParams(0,-2,1));navRow.addView(add,new LinearLayout.LayoutParams(0,-2,1.25f));navRow.addView(next,new LinearLayout.LayoutParams(0,-2,1));content.addView(navRow);
        prev.setOnClickListener(v->analyzeStock(adjacentSymbol(symbol,-1)));next.setOnClickListener(v->analyzeStock(adjacentSymbol(symbol,1)));add.setOnClickListener(v->portfolioDialog(null,symbol));
        LinearLayout tradeRow=new LinearLayout(this); tradeRow.setOrientation(LinearLayout.HORIZONTAL);
        Button buy=button("Ziraat'ta AL",GREEN), sell=button("Ziraat'ta SAT",RED);
        tradeRow.addView(buy,new LinearLayout.LayoutParams(0,-2,1));tradeRow.addView(sell,new LinearLayout.LayoutParams(0,-2,1));content.addView(tradeRow);
        buy.setOnClickListener(v->prepareOrder(symbol,r.price,"AL"));sell.setOnClickListener(v->prepareOrder(symbol,r.price,"SAT"));
        content.addView(txt("Emir burada hazırlanır; nihai onay Ziraat Trader içinde verilir. ← → ile diğer hisselere geçebilirsin.",12,Color.GRAY));
    }

    private void loadChartFrame(String symbol,ShortPulseEngine.Result r,String frame){
        shell(symbol+" • "+frame+" yükleniyor");
        ProgressBar p=new ProgressBar(this);content.addView(p);content.addView(txt("Yalnız seçilen grafik verisi alınıyor…",14,NAVY));
        io.execute(()->{
            try{
                List<MarketDataService.Candle>d;
                if(frame.equals("1S")) d=MarketDataService.fetchSeries(symbol,"5d","1h",100);
                else if(frame.equals("4S")){d=MarketDataService.fetchSeries(symbol,"1mo","1h",0);d=MarketDataService.downsample(MarketDataService.aggregateHours(d,4),100);}
                else if(frame.equals("1G")) d=MarketDataService.fetchSeries(symbol,"3mo","1d",100);
                else if(frame.equals("1Hf")) d=MarketDataService.fetchSeries(symbol,"1y","1wk",100);
                else if(frame.equals("1Ay")) d=MarketDataService.fetchSeries(symbol,"1mo","1d",60);
                else if(frame.equals("6Ay")) d=MarketDataService.fetchSeries(symbol,"6mo","1d",120);
                else if(frame.equals("1Y")) d=MarketDataService.fetchSeries(symbol,"1y","1d",120);
                else d=MarketDataService.fetchSeries(symbol,"3mo","1d",90);
                final List<MarketDataService.Candle> out=d;
                main.post(()->renderStockDetail(symbol,r,out,frame));
            }catch(Exception e){main.post(()->{shell(symbol+" • "+frame);content.addView(txt("Grafik verisi alınamadı: "+e.getMessage(),15,RED));});}
        });
    }

    private String adjacentSymbol''', s, count=1, flags=re.S)

# Eğer önceki patch'teki imza farklı kaldıysa doğrudan temel detay metodunu dönüştür.
s=s.replace('renderStockDetail(symbol,r,chart));','renderStockDetail(symbol,r,chart,"3Ay"));')

p.write_text(s,encoding='utf-8')

b=Path('app/build.gradle');g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 37',g)
g=re.sub(r"versionName\s+'[^']+'","versionName '3.7.0'",g)
b.write_text(g,encoding='utf-8')
