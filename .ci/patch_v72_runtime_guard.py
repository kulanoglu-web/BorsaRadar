from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# The fast preview is UI-only: never allow a renderer exception to kill the process.
s=s.replace('''            main.post(()->renderFastTechnicalDetail(symbol,data));''','''            main.post(()->{try{renderFastTechnicalDetail(symbol,data);}catch(Throwable uiErr){shell(symbol+" • analiz");content.addView(txt("Hızlı görünüm hazırlanamadı; temel analiz devam ediyor.",14,Color.GRAY));}});''',1)
# Deep detail is also guarded. This keeps the app alive and surfaces the actual error on screen.
s=s.replace('''            main.post(()->renderStockDetail(symbol,a,chart,"10G"));''','''            main.post(()->{try{renderStockDetail(symbol,a,chart,"10G");}catch(Throwable uiErr){shell(symbol+" • analiz");content.addView(txt("Detay ekranı hatası: "+String.valueOf(uiErr.getMessage()),14,RED));}});''',1)
# Timeframe detail renderer guard.
s=s.replace('''main.post(()->renderStockDetail(symbol,a,out,frame));''','''main.post(()->{try{renderStockDetail(symbol,a,out,frame);}catch(Throwable uiErr){shell(symbol+" • "+frame);content.addView(txt("Grafik ekranı hatası: "+String.valueOf(uiErr.getMessage()),14,RED));}});''',1)
p.write_text(s,encoding='utf-8')
