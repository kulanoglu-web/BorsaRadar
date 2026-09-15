from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v84: every single-stock fast result uses the full shared chart rather than a separate 20-point mini chart.
s=s.replace('List<MarketDataService.Candle> chart=data.subList(Math.max(0,n-20),n);','List<MarketDataService.Candle> chart=data;')
s=s.replace('cc.addView(bold("Hızlı grafik",17,Color.WHITE));','cc.addView(bold("Grafik",17,Color.WHITE));')
s=s.replace('cc.addView(new PriceChartView(this,chart,"SON "+chart.size()+" GÜN"),new LinearLayout.LayoutParams(-1,dp(280)));','cc.addView(new PriceChartView(this,chart,"GÜNCEL"),new LinearLayout.LayoutParams(-1,dp(350)));')
# Add an explicit refresh action to the fast/result screen. It reruns the existing single-stock path only on tap.
anchor='q.addView(txt("Son fiyat hemen gösterildi • Derin teknik analiz aşağıda tamamlanacak",12,Color.GRAY));'
if anchor in s:
    s=s.replace(anchor,anchor+'\n        Button refresh=new Button(this); refresh.setText("↻ Yenile"); refresh.setOnClickListener(v->{ try{ openSingleStock(symbol); }catch(Throwable ignored){} }); q.addView(refresh);',1)
# Avoid a misleading endless wait card; results are a stable screen until user refreshes.
s=s.replace('LinearLayout wait=card(); wait.addView(bold("Derin analiz arka planda sürüyor",14,AMBER));\n        wait.addView(txt("Bu sırada ekranı kullanabilir, geri/ileri geçiş yapabilirsin.",12,Color.GRAY)); content.addView(wait);','LinearLayout wait=card(); wait.addView(bold("Sonuç ekranı",14,AMBER));\n        wait.addView(txt("Sonuçlar bu ekranda kalır. Yeni veri için Yenile düğmesini kullan.",12,Color.GRAY)); content.addView(wait);')
p.write_text(s,encoding='utf-8')
