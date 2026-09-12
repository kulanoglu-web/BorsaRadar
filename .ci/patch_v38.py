from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Bildirime basinca uygulamayi ve ilgili hisse detayini acmak icin PendingIntent.
s=s.replace('import android.app.NotificationManager;','import android.app.NotificationManager;\nimport android.app.PendingIntent;')

# V35'i portfoy risk/firsat bildirimlerinin ana karar katmani yap.
old='''ShortPulseEngine.Result sr=ShortPulseEngine.analyze(d);
                holdingSignals.put(h.symbol,sr);
                double pnlPct=h.cost>0?(sr.price/h.cost-1)*100:0;
                if(sr.price<=sr.stopReference || sr.recommendation.contains("SAT") || sr.recommendation.contains("RİSK"))
                    notifyAlert("Zarar önleme: "+h.symbol, sr.recommendation+" • fiyat "+money(sr.price)+" • stop "+money(sr.stopReference));
                else if(pnlPct>=8 && !sr.recommendation.contains("AL"))
                    notifyAlert("Kâr koruma: "+h.symbol, "Pozisyon +%"+fmt(pnlPct)+" • momentum zayıflayabilir, kâr korumayı değerlendir.");'''
new='''ShortPulseEngine.Result sr=ShortPulseEngine.analyze(d);
                holdingSignals.put(h.symbol,sr);
                V35HybridEngine.Result v35=V35HybridEngine.analyze(d,h.cost);
                double pnlPct=h.cost>0?(v35.price/h.cost-1)*100:0;
                if(v35.risk || v35.price<=v35.stopPrice)
                    notifyAlert("V35 zarar önleme: "+h.symbol, v35.action+" • fiyat "+money(v35.price)+" • stop "+money(v35.stopPrice));
                else if(pnlPct>=6 && (v35.action.contains("TUT") || v35.action.contains("İZLE")))
                    notifyAlert("V35 kâr koruma: "+h.symbol, "Pozisyon +%"+fmt(pnlPct)+" • stop "+money(v35.stopPrice)+" • "+v35.phase);'''
if old in s: s=s.replace(old,new)

# Detay ekranında V35 canlı karar kartını ekle.
needle='''content.addView(txt("Emir burada hazırlanır; nihai onay Ziraat Trader içinde verilir.",12,Color.GRAY));'''
replacement='''try {
            V35HybridEngine.Result v35=V35HybridEngine.analyze(data,0);
            int vc=v35.risk?RED:(v35.opportunity?GREEN:Color.rgb(225,145,0));
            content.addView(bold("V35 HYBRID • "+v35.action+" • %"+(int)v35.confidence,17,vc));
            content.addView(txt(v35.reason,12,Color.DKGRAY));
        } catch(Exception ignored) {}
        content.addView(txt("Emir burada hazırlanır; nihai onay Ziraat Trader içinde verilir.",12,Color.GRAY));'''
if needle in s: s=s.replace(needle,replacement)

# Bildirim tiklamasi: title sonundaki sembolu extra olarak MainActivity'ye tasir.
old_notify='''    private void notifyAlert(String title,String text){
        try{
            Notification.Builder b=Build.VERSION.SDK_INT>=26?new Notification.Builder(this,"borsaradar_alerts"):new Notification.Builder(this);
            b.setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(title).setContentText(text).setStyle(new Notification.BigTextStyle().bigText(text)).setAutoCancel(true);
            ((NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE)).notify((int)(System.currentTimeMillis()%100000),b.build());
        }catch(Exception ignored){}
    }'''
new_notify='''    private void notifyAlert(String title,String text){
        try{
            String symbol="";
            int k=title.lastIndexOf(':');
            if(k>=0 && k<title.length()-1) symbol=title.substring(k+1).trim();
            Intent open=new Intent(this,MainActivity.class);
            open.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            if(!symbol.isEmpty()) open.putExtra("open_symbol",symbol);
            int req=(title+text).hashCode();
            PendingIntent pi=PendingIntent.getActivity(this,req,open,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
            Notification.Builder b=Build.VERSION.SDK_INT>=26?new Notification.Builder(this,"borsaradar_alerts"):new Notification.Builder(this);
            b.setSmallIcon(android.R.drawable.ic_dialog_info)
                    .setContentTitle(title).setContentText(text)
                    .setStyle(new Notification.BigTextStyle().bigText(text))
                    .setContentIntent(pi).setAutoCancel(true);
            ((NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE)).notify(req,b.build());
        }catch(Exception ignored){}
    }

    private void handleNotificationIntent(Intent i){
        if(i==null) return;
        final String symbol=i.getStringExtra("open_symbol");
        if(symbol!=null && !symbol.trim().isEmpty()){
            i.removeExtra("open_symbol");
            main.postDelayed(()->analyzeStock(symbol.trim()),180);
        }
    }

    @Override protected void onNewIntent(Intent intent){
        super.onNewIntent(intent);
        setIntent(intent);
        handleNotificationIntent(intent);
    }'''
if old_notify in s: s=s.replace(old_notify,new_notify)

# Soguk baslatmada da bildirimin hedef hissesini ac.
s=s.replace('''        setupAlerts();
        showPortfolio();''','''        setupAlerts();
        showPortfolio();
        handleNotificationIntent(getIntent());''')

# Radar / kanal metinleri.
s=s.replace('"Erken kırılım + güçlü adaylar"','"V35 Hybrid • erken kırılım + güçlü adaylar"')
s=s.replace('"BorsaRadar Alarmları"','"BorsaRadar V35 Alarmları"')
s=s.replace('"Fırsat, kâr koruma ve zarar önleme uyarıları"','"V35 fırsat, kâr koruma ve zarar önleme uyarıları"')

p.write_text(s,encoding='utf-8')

# Sürüm 3.8.1 - bildirim tiklama duzeltmesi
b=Path('app/build.gradle')
t=b.read_text(encoding='utf-8')
t=re.sub(r'versionCode\s+\d+','versionCode 39',t)
t=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.8.1'",t)
b.write_text(t,encoding='utf-8')
