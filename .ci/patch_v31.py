from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Daha uzun hesap penceresi: grafik kısa kalır, erken kırılım motoru 20+ günü görebilir.
s=s.replace('MarketDataService.fetchDaily(h.symbol, "6mo")','MarketDataService.fetchDaily(h.symbol, "3mo")')
s=s.replace('MarketDataService.fetchDaily(sym, "1y")','MarketDataService.fetchDaily(sym, "3mo")')
s=s.replace('MarketDataService.fetchDaily(symbol, "1y")','MarketDataService.fetchDaily(symbol, "3mo")')
s=s.replace('MarketDataService.fetchDaily(sym,"1mo")','MarketDataService.fetchDaily(sym,"3mo")')
s=s.replace('MarketDataService.fetchDaily(sym, "1mo")','MarketDataService.fetchDaily(sym, "3mo")')
s=s.replace('MarketDataService.fetchDaily(symbol,"1mo")','MarketDataService.fetchDaily(symbol,"3mo")')
s=s.replace('MarketDataService.fetchDaily(symbol, "1mo")','MarketDataService.fetchDaily(symbol,"3mo")')
s=s.replace('MarketDataService.fetchDaily(h.symbol,"1mo")','MarketDataService.fetchDaily(h.symbol,"3mo")')
s=s.replace('MarketDataService.fetchDaily(h.symbol, "1mo")','MarketDataService.fetchDaily(h.symbol,"3mo")')
s=s.replace('"Telefon her hisse için yalnızca yaklaşık 1 aylık günlük veri çeker; karar motoru son 10–12 işlem gününe ağırlık verir."',
            '"Hesaplama 3 aylık veride yapılır; grafik kısa tutulur. Radar artık yükseliş sonrası değil, sıkışma + ivme + hacim/para akışı ile kırılım öncesini öne çıkarır."')

# Eski ekran metinleri / metod görünümü.
s=s.replace('"1 yıllık günlük veri indiriliyor ve strateji geriye dönük çalıştırılıyor..."','"Güncel teknik veri alınıyor; grafik son 10 işlem gününü gösterir..."')
s=s.replace('"1Y Backtest"','"Grafik / Analiz"')
s=s.replace('"Detaylı backtest yenile"','"Grafik / Analiz"')
s=s.replace('"1Y backtest: " + r.bt.summary','"BorsaRadar yöntem sonucu: " + MethodEngine.analyze(r.s).summary')
s=s.replace('shell(symbol + " Backtest")','shell(symbol + " Analiz")')
s=s.replace('shell(symbol + " Backtest Sonucu")','shell(symbol + " Analiz Sonucu")')
s=s.replace('"Teknik sinyal: " + s.signal + " • Teknik skor: " + s.score + " • Ölçek: -14…+15"','MethodEngine.analyze(s).label + " • " + MethodEngine.analyze(s).summary')
s=s.replace('"Mantık: güçlü AL/ERKEN sinyaliyle giriş; ATR + EMA50 tabanlı ilk stop; ATR trailing ve trend/MACD bozulmasında çıkış."','"Metodlar: EarlyBreak + BR-Pulse + FlowBreak + TrendGuard + V30-Live + BR-KarKoru. EarlyBreak sıkışma, ivmelenme, EMA yakınlığı ve para/hacim akışıyla kırılımı oluşmadan yakalamaya çalışır."')

s=re.sub(r'    private String decision\(IndicatorEngine\.Snapshot s\) \{.*?\n    \}', '''    private String decision(IndicatorEngine.Snapshot s) {
        MethodEngine.Result m = MethodEngine.analyze(s);
        return m.label + " • %" + String.format(Locale.US, "%.0f", m.percent);
    }''', s, count=1, flags=re.S)
s=re.sub(r'    private int decisionColor\(IndicatorEngine\.Snapshot s\) \{.*?\n    \}', '''    private int decisionColor(IndicatorEngine.Snapshot s) {
        MethodEngine.Result m = MethodEngine.analyze(s);
        if (m.label.contains("AL")) return GREEN;
        if (m.label.contains("SAT") || m.label.contains("RİSK") || m.label.contains("AZALT")) return RED;
        return Color.rgb(225, 145, 0);
    }''', s, count=1, flags=re.S)

s=s.replace('return "Neye göre: " + android.text.TextUtils.join(" • ", why) + ".";', '''MethodEngine.Result m = MethodEngine.analyze(s);
        return "Neye göre: " + android.text.TextUtils.join(" • ", why) + ". • " + m.summary
                + " • Bu yüzde kazanç garantisi değil, indikatör/metod uyum gücüdür.";''')
s=s.replace('return "İndikatör uzlaşması: " + buy + " AL • " + neutral + " NÖTR • " + sell + " SAT";', '''MethodEngine.Result m = MethodEngine.analyze(s);
        return "Analiz %" + String.format(Locale.US, "%.0f", m.percent)
                + " • " + buy + " AL • " + neutral + " NÖTR • " + sell + " SAT";''')
s=s.replace('" • skor " + r.s.score + "/15"','" • analiz %" + String.format(Locale.US, "%.0f", MethodEngine.analyze(r.s).percent)')
s=s.replace('"Fiyat " + money(r.s.close) + " • " + r.s.reason','"Fiyat " + money(r.s.close) + " • " + MethodEngine.analyze(r.s).summary')
s=s.replace('if (r.s.score >= 5 && !r.s.trap) shortTerm.add(r);','if (MethodEngine.analyze(r.s).percent >= 62 && !r.s.trap) shortTerm.add(r);')
s=s.replace('if (r.s.trendUp && r.s.cmf20 > 0 && !r.s.trap) longTerm.add(r);','if (MethodEngine.analyze(r.s).percent >= 68 && r.s.trendUp && !r.s.trap) longTerm.add(r);')
s=s.replace('if (dividendWatch.contains(r.symbol) && r.s.score >= 2 && !r.s.trap) dividend.add(r);','if (dividendWatch.contains(r.symbol) && MethodEngine.analyze(r.s).percent >= 52 && !r.s.trap) dividend.add(r);')
s=s.replace('" • skor " + r.s.score + " (-14…+15)"','" • analiz %" + String.format(Locale.US, "%.0f", MethodEngine.analyze(r.s).percent)')
s=s.replace('new PriceChartView(this, data)', 'new PriceChartView(this, data, "1 GÜN • SON 10 İŞLEM GÜNÜ")')

# Portföy kâr koruma görünümü.
s=s.replace('String d = decision(s);', 'String d = decision(s);\n                    ProfitGuardEngine.Result pg = ProfitGuardEngine.analyze(data, h.avg);')
s=s.replace('explainDecision(s) + "\\n" + indicatorConsensus(s)', 'explainDecision(s) + "\\n" + indicatorConsensus(s) + "\\n" + pg.action + " • " + pg.reason')

# Hisse detayında sağ/sol gezinme. Radar sırası varsa o sıra; yoksa tüm BIST sırası.
needle='''        Button add=button("Portföye Ekle",GREEN);content.addView(add);add.setOnClickListener(v->portfolioDialog(null,symbol));
    }

    private void showBaskets()'''
replacement='''        LinearLayout navRow=new LinearLayout(this); navRow.setOrientation(LinearLayout.HORIZONTAL);
        Button prev=button("← Önceki",NAVY2), add=button("Portföye Ekle",GREEN), next=button("Sonraki →",NAVY2);
        navRow.addView(prev,new LinearLayout.LayoutParams(0,-2,1));
        navRow.addView(add,new LinearLayout.LayoutParams(0,-2,1.25f));
        navRow.addView(next,new LinearLayout.LayoutParams(0,-2,1));
        content.addView(navRow);
        prev.setOnClickListener(v->analyzeStock(adjacentSymbol(symbol,-1)));
        next.setOnClickListener(v->analyzeStock(adjacentSymbol(symbol,1)));
        add.setOnClickListener(v->portfolioDialog(null,symbol));
        LinearLayout tradeRow=new LinearLayout(this); tradeRow.setOrientation(LinearLayout.HORIZONTAL);
        Button buy=button("Ziraat'ta AL",GREEN), sell=button("Ziraat'ta SAT",RED);
        tradeRow.addView(buy,new LinearLayout.LayoutParams(0,-2,1));
        tradeRow.addView(sell,new LinearLayout.LayoutParams(0,-2,1));
        content.addView(tradeRow);
        buy.setOnClickListener(v->prepareOrder(symbol,r.price,"AL"));
        sell.setOnClickListener(v->prepareOrder(symbol,r.price,"SAT"));
        content.addView(txt("Emir burada hazırlanır; nihai onay Ziraat Trader içinde verilir.",12,Color.GRAY));
        content.addView(txt("← → ile radar listesindeki diğer hisselere geçebilirsin.",12,Color.GRAY));
    }

    private String adjacentSymbol(String symbol,int delta) {
        List<String> order=new ArrayList<>();
        synchronized(radarResults){ for(RadarItem r:radarResults) order.add(r.symbol); }
        if(order.size()<2) order.addAll(Arrays.asList(ALL_SYMBOLS));
        int i=order.indexOf(symbol);
        if(i<0){ order.add(0,symbol); i=0; }
        int n=order.size();
        return order.get((i+delta+n)%n);
    }

    private void showBaskets()'''
if needle in s:
    s=s.replace(needle,replacement)

s=s.replace('TextView h=bold("En güçlü adaylar",18,NAVY);content.addView(h);',
            'TextView h=bold("Erken kırılım + güçlü adaylar",18,NAVY);content.addView(h);')

# Tüm ekranlarda görünür telif ve risk uyarısı.
s=s.replace('TextView foot=txt("BorsaRadar • 1–10 işlem günü odaklı teknik karar destek",11,Color.rgb(100,110,124));',
'''TextView foot=txt("© 2026 BorsaRadar • Tüm hakları saklıdır.  Yatırım danışmanlığı değildir. AL/SAT sinyalleri kesin veya garantili değildir. Kâr garantisi yoktur; yatırımlar zarar riski içerir.",10,Color.rgb(100,110,124));''')

# Bildirim ve broker entegrasyonu için importlar.
s=s.replace('import android.app.Activity;','import android.app.Activity;\nimport android.app.Notification;\nimport android.app.NotificationChannel;\nimport android.app.NotificationManager;')
s=s.replace('import android.content.Context;','import android.content.Context;\nimport android.content.Intent;\nimport android.net.Uri;\nimport android.os.Build;')

# Uygulama açılırken bildirim kanalını hazırla ve Android 13+ izni iste.
s=s.replace('''        loadPortfolio();
        loadRadarCache();
        showPortfolio();''','''        loadPortfolio();
        loadRadarCache();
        setupAlerts();
        showPortfolio();''')

# Portföy güncellemesinde risk alarmı.
s=s.replace('''            try { List<MarketDataService.Candle> d=MarketDataService.fetchDaily(h.symbol,"3mo"); holdingSignals.put(h.symbol,ShortPulseEngine.analyze(d)); } catch(Exception ignored){}''','''            try {
                List<MarketDataService.Candle> d=MarketDataService.fetchDaily(h.symbol,"3mo");
                ShortPulseEngine.Result sr=ShortPulseEngine.analyze(d);
                holdingSignals.put(h.symbol,sr);
                double pnlPct=h.cost>0?(sr.price/h.cost-1)*100:0;
                if(sr.price<=sr.stopReference || sr.recommendation.contains("SAT") || sr.recommendation.contains("RİSK"))
                    notifyAlert("Zarar önleme: "+h.symbol, sr.recommendation+" • fiyat "+money(sr.price)+" • stop "+money(sr.stopReference));
                else if(pnlPct>=8 && !sr.recommendation.contains("AL"))
                    notifyAlert("Kâr koruma: "+h.symbol, "Pozisyon +%"+fmt(pnlPct)+" • momentum zayıflayabilir, kâr korumayı değerlendir.");
            } catch(Exception ignored){}''')

# Radar bittiğinde güçlü/erken fırsat alarmı.
s=s.replace('''                radarResults.clear(); radarResults.addAll(sorted); saveRadarCache();
                main.post(this::showRadar);''','''                radarResults.clear(); radarResults.addAll(sorted); saveRadarCache();
                if(!sorted.isEmpty()){
                    RadarItem best=sorted.get(0);
                    if((best.recommendation.contains("ERKEN AL") || best.recommendation.equals("AL") || best.recommendation.contains("KADEMELİ AL")) && best.confidence>=72)
                        notifyAlert("Fırsat alarmı: "+best.symbol, best.recommendation+" • güven %"+(int)best.confidence+" • "+best.horizon);
                }
                main.post(this::showRadar);''')

# Yardımcı metodları sınıf sonuna ekle.
insert='''
    private void setupAlerts(){
        NotificationManager nm=(NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE);
        if(Build.VERSION.SDK_INT>=26){
            NotificationChannel ch=new NotificationChannel("borsaradar_alerts","BorsaRadar Alarmları",NotificationManager.IMPORTANCE_HIGH);
            ch.setDescription("Fırsat, kâr koruma ve zarar önleme uyarıları");
            nm.createNotificationChannel(ch);
        }
        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=android.content.pm.PackageManager.PERMISSION_GRANTED){
            requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},901);
        }
    }

    private void notifyAlert(String title,String text){
        try{
            Notification.Builder b=Build.VERSION.SDK_INT>=26?new Notification.Builder(this,"borsaradar_alerts"):new Notification.Builder(this);
            b.setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(title).setContentText(text).setStyle(new Notification.BigTextStyle().bigText(text)).setAutoCancel(true);
            ((NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE)).notify((int)(System.currentTimeMillis()%100000),b.build());
        }catch(Exception ignored){}
    }

    private void prepareOrder(String symbol,double price,String side){
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(6),dp(18),0);
        EditText qty=new EditText(this); qty.setHint("Lot"); qty.setInputType(InputType.TYPE_CLASS_NUMBER);
        EditText px=new EditText(this); px.setHint("Limit fiyat"); px.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL); px.setText(String.format(Locale.US,"%.2f",price));
        box.addView(txt(symbol+" • "+side+" emri",16,side.equals("AL")?GREEN:RED)); box.addView(qty); box.addView(px);
        new AlertDialog.Builder(this).setTitle("Emri hazırla").setView(box)
                .setMessage("Bu ekran emir göndermez. Lot ve fiyatı kontrol ettikten sonra Ziraat Trader açılır; nihai onay aracı kurum uygulamasında verilir.")
                .setPositiveButton("Ziraat Trader'ı Aç",(d,w)->openZiraatTrader())
                .setNegativeButton("İptal",null).show();
    }

    private void openZiraatTrader(){
        try{
            Intent i=getPackageManager().getLaunchIntentForPackage("com.matriksmobile.android.ziraatTrader");
            if(i!=null){ startActivity(i); return; }
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=com.matriksmobile.android.ziraatTrader")));
        }catch(Exception e){
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps/details?id=com.matriksmobile.android.ziraatTrader")));
        }
    }
'''
s=s.replace('\n    private String money(double x){return String.format(Locale.US,"%.2f ₺",x);} private String fmt(double x){return String.format(Locale.US,"%.2f",x);}\n}',insert+'\n    private String money(double x){return String.format(Locale.US,"%.2f ₺",x);} private String fmt(double x){return String.format(Locale.US,"%.2f",x);}\n}')

p.write_text(s, encoding='utf-8')

# Bildirim izni ve sürüm.
m=Path('app/src/main/AndroidManifest.xml'); ms=m.read_text(encoding='utf-8')
if 'POST_NOTIFICATIONS' not in ms:
    ms=ms.replace('<uses-permission android:name="android.permission.INTERNET" />','<uses-permission android:name="android.permission.INTERNET" />\n    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />')
m.write_text(ms,encoding='utf-8')

b=Path('app/build.gradle'); g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+', 'versionCode 36', g)
g=re.sub(r"versionName\s+'[^']+'", "versionName '3.6.0'", g)
b.write_text(g, encoding='utf-8')
