# BorsaRadar v0.9

Android package: `com.kulanoglu.borsaradar`

Bu sürümde:
- Manuel portföy girişi; lot ve ortalama maliyet kaydı
- TUPRS manuel portföyde değerlendirilebilir; bağımsız radar/backtest evreninden çıkarılmıştır
- Anahtarsız Yahoo Finance günlük veri bağlantısı (`.IS` sembolleri)
- Portföy için son fiyat, yaklaşık P/L ve teknik sinyal
- BIST radar taraması
- EMA20/50, RSI14, MACD, göreli hacim, CMF, Bollinger width, breakout/pre-breakout, trap filtresi, ATR
- AL / ERKEN / İZLE / NÖTR / SAT-RİSK / KOVALAMA sınıflandırması
- 1 yıllık geriye dönük strateji testi: ATR stop + trailing + trend/MACD çıkışı
- 100.000 TL / 3 strateji ekranı

## Veri notu
Yahoo Finance verisi ücretsiz ve anahtarsız kullanılır; gecikmeli olabilir, bazı sembollerde geçici erişim/rate-limit sorunu olabilir. Uygulama veri yokken sahte fiyat/sinyal üretmez.

## Build
GitHub Actions workflow'u `gradle assembleDebug` çalıştırır ve `app-debug.apk` dosyasını artifact olarak üretir.
