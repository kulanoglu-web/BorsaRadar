# BorsaRadar v0.9.12

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
- Türkçe virgüllü fiyat girişi ve eski hatalı bitişik-kuruş kayıtlarını otomatik düzeltme
- Lacivert/kırmızı yatırım uygulaması teması, renkli sinyal ve kâr/zarar gösterimi
- Programcı bilgisi: Erdoğan Kulanoğlu
- Büyük AL / KADEMELİ AL / TUT-BEKLE / SAT-RİSK AZALT / YENİ ALIM YAPMA karar kutuları
- Kararın trend, RSI, MACD, hacim, para akışı ve kırılım/tuzak gerekçeleri
- Backtest ekranında uygulama içi ve Android geri tuşu desteği
- Backtestten geri dönünce radar tarama sonuçlarını kaybetmeden aynı listeyi gösterme
- 645 Borsa İstanbul payı için kod veya şirket adıyla anlık arama ve öneri
- Portföyde tüm hisseler; bağımsız radarda TUPRS hariç tüm pay evreni
- Google servislerine ihtiyaç duymayan Poco ve Huawei P40 uyumlu tek APK
- Backtest ekranında bir yıllık fiyat grafiği ve güncel fiyat
- İndikatörlerin AL / NÖTR / SAT uzlaşma sayıları
- Son radar sonuçlarından aktif kısa vade, temettü ön eleme ve uzun vade adayları
- Backtest/karar ekranında büyük güncel fiyat ve açık teknik skor ölçeği (-8…+9)
- Huawei/HarmonyOS paket yükleyicisi için tüm sonraki APK'larda sabit uygulama imzası
- Radar detayında taranan tüm sonuçlar arasında önceki/sonraki hisseye geçiş
- Neden yalnızca en güçlü 30 adayın listelendiğini açıklayan kısa bilgi
- Yalnızca skor 8+, yükselen trend, pozitif para akışı ve tuzak bulunmaması halinde `ÇOK GÜÇLÜ FIRSAT • AL`
- Portföyü panoya kopyalama ve panodan geri yükleme
- Portföye hisse kaydedilince fiyat, indikatör, teknik skor ve AL/TUT/SAT yönlendirmesini otomatik getirme
- CCI20, Stokastik14 ve ADX14 göstergeleri
- BorsaRadar'a özel Trend Verimliliği (BRTV), ATR Momentum (BRM) ve Hacim Yön Baskısı (BRH)
- Yeni göstergelerin hem güncel karara hem de her backtest gününe dahil edilmesi; skor ölçeği -14…+15
- Tüm BIST taramasında istek hızı sınırlama, query1/query2 sunucu yedeği ve kademeli yeniden deneme
- Tarama sırasında başarılı ve başarısız veri sayılarını ayrı gösterme

## Veri notu
Yahoo Finance verisi ücretsiz ve anahtarsız kullanılır; gecikmeli olabilir, bazı sembollerde geçici erişim/rate-limit sorunu olabilir. Uygulama veri yokken sahte fiyat/sinyal üretmez.

## Build
GitHub Actions workflow'u `gradle assembleDebug` çalıştırır ve `app-debug.apk` dosyasını artifact olarak üretir.
