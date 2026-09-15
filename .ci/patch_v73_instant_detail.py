from pathlib import Path
import re
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
start=s.find('    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){')
end=s.find('    private void renderStockDetail',start)
if start<0 or end<0: raise SystemExit('fast renderer boundaries missing')
new='''    private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){
        if(data==null||data.isEmpty())return;
        int n=data.size();
        MarketDataService.Candle last=data.get(n-1);
        MarketDataService.Candle prev=data.get(Math.max(0,n-2));
        double ch=prev.close!=0?(last.close/prev.close-1.0)*100.0:0.0;
        List<MarketDataService.Candle> chart=data.subList(Math.max(0,n-20),n);
        shell(symbol+" • hızlı görünüm");
        LinearLayout q=card();
        q.addView(bold(symbol,25,Color.WHITE));
        q.addView(bold(money(last.close,symbol),28,ch>=0?GREEN:RED));
        q.addView(bold((ch>=0?"▲ +":"▼ ")+fmt(ch)+"%",16,ch>=0?GREEN:RED));
        q.addView(txt("Son fiyat hemen gösterildi • Derin teknik analiz aşağıda tamamlanacak",12,Color.GRAY));
        content.addView(q); spacer(7);
        LinearLayout cc=card(); cc.addView(bold("Hızlı grafik",17,Color.WHITE));
        cc.addView(new PriceChartView(this,chart,"SON "+chart.size()+" GÜN"),new LinearLayout.LayoutParams(-1,dp(280)));
        content.addView(cc); spacer(7);
        ShortTermTargetEngine.Target st=ShortTermTargetEngine.calculate(data,"1d");
        if(st!=null){String cur=MarketSymbol.marketIndex(symbol)==0?"TL":"€";LinearLayout t=card();t.addView(bold("Kısa Vade Hedef Planı",17,Color.WHITE));t.addView(txt(st.summary(cur),13,Color.DKGRAY));content.addView(t);spacer(7);}
        LinearLayout wait=card(); wait.addView(bold("Derin analiz arka planda sürüyor",14,AMBER));
        wait.addView(txt("Bu sırada ekranı kullanabilir, geri/ileri geçiş yapabilirsin.",12,Color.GRAY)); content.addView(wait);
    }

'''
s=s[:start]+new+s[end:]
# Guard should show real UI error if even the minimal renderer fails.
s=s.replace('''catch(Throwable uiErr){shell(symbol+" • analiz");content.addView(txt("Hızlı görünüm hazırlanamadı; temel analiz devam ediyor.",14,Color.GRAY));}''','''catch(Throwable uiErr){shell(symbol+" • analiz");content.addView(txt("Hızlı görünüm hatası: "+uiErr.getClass().getSimpleName()+" / "+String.valueOf(uiErr.getMessage()),14,RED));}''')
p.write_text(s,encoding='utf-8')
