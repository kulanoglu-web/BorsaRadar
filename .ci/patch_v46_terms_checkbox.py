from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Checkbox import.
if 'import android.widget.CheckBox;' not in s:
    s=s.replace('import android.widget.Button;','import android.widget.Button;\nimport android.widget.CheckBox;')

# Versioned terms acceptance: if terms change later, increment TERMS_VERSION and users must accept again.
if 'private static final int TERMS_VERSION' not in s:
    s=s.replace('private static final String PREFS = "borsaradar_final";',
                'private static final String PREFS = "borsaradar_final";\n    private static final int TERMS_VERSION = 2;')

s=s.replace('''if(!getSharedPreferences(PREFS,Context.MODE_PRIVATE).getBoolean("terms_accepted_v1",false)){
            showTermsAcceptance();
        } else {''','''if(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("terms_version",0) < TERMS_VERSION){
            showTermsAcceptance();
        } else {''')

terms='''    private void showTermsAcceptance(){
        ScrollView scroll=new ScrollView(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(8),dp(18),dp(18));
        box.addView(bold("BorsaRadar • Kullanım Şartları / Nutzungsbedingungen / Terms",20,NAVY));
        box.addView(bold("© 2026 Erdoğan Kulanoğlu • Tüm hakları saklıdır / Alle Rechte vorbehalten / All rights reserved",14,NAVY2));
        box.addView(txt("Uygulamayı kullanmadan önce metni okuyun ve aşağıdaki kutuyu işaretleyerek açıkça kabul edin.",13,Color.DKGRAY));

        box.addView(bold("Türkçe — Risk, kullanım ve sorumluluk",16,RED));
        box.addView(txt("BorsaRadar yalnızca teknik analiz ve karar desteği amacıyla sunulur. Yatırım danışmanlığı, kişiye özel yatırım tavsiyesi, portföy yönetimi veya kazanç garantisi değildir. AL, TUT, SAT, erken kırılım, hedef, stop, güven yüzdesi ve diğer göstergeler tahmine dayalı teknik çıktılardır; doğruluk, kâr veya belirli bir sonuç garanti edilmez. Hisse senedi ve diğer piyasa işlemleri ciddi zarar, hızlı değer kaybı ve yatırılan sermayenin kısmen veya tamamen kaybı riskini taşır. Her yatırım ve işlem kararı, emrin kontrolü ve uygulanması tamamen kullanıcının sorumluluğundadır. Kullanıcı uygulama verilerini bağımsız olarak kontrol etmekle yükümlüdür. Kanunun izin verdiği azami ölçüde, piyasa hareketleri, veri gecikmesi veya hatası, kesinti, yanlış sembol/fiyat, üçüncü taraf veri kaynağı veya uygulamanın kullanımından doğan mali kayıplardan geliştirici sorumlu tutulamaz. Uygulama; otomatik işlem botu, copy-trading, harici sinyal aktarma, otomatik emir köprüsü veya benzeri üçüncü taraf programlarla birlikte kullanılmak üzere tasarlanmamıştır ve bu tür kullanım yasaktır. Kullanıcı böyle bir bağlantıyı kuramaz, uygulama çıktısını otomatik emir sistemine aktaramaz ve bu tür üçüncü taraf kullanımlarından doğan tüm sonuçları kendisi üstlenir. Kişisel portföy kayıtları geliştiriciye gönderilmez; cihazda tutulur. Piyasa verileri üçüncü taraf servislerden alınabilir ve onların kendi şartları ile veri politikaları geçerlidir.",13,Color.DKGRAY));

        box.addView(bold("Deutsch — Risiko, Nutzung und Haftung",16,RED));
        box.addView(txt("BorsaRadar dient ausschließlich der technischen Analyse und Entscheidungsunterstützung. Die App ist keine Anlageberatung, keine persönliche Anlageempfehlung, keine Vermögensverwaltung und keine Gewinngarantie. Kauf-, Halte-, Verkaufs-, Breakout-, Ziel-, Stop- und Konfidenzsignale sind technische, prognosebasierte Hinweise; Richtigkeit, Gewinn oder ein bestimmtes Ergebnis werden nicht garantiert. Wertpapiergeschäfte können zu erheblichen Verlusten bis hin zum teilweisen oder vollständigen Verlust des eingesetzten Kapitals führen. Sämtliche Anlage- und Handelsentscheidungen sowie die Prüfung und Ausführung von Aufträgen liegen ausschließlich in der Verantwortung des Nutzers. Der Nutzer muss Daten und Signale eigenständig prüfen. Soweit gesetzlich zulässig, haftet der Entwickler nicht für finanzielle Verluste aufgrund von Marktbewegungen, Datenverzögerungen oder -fehlern, Ausfällen, falschen Symbolen/Preisen, Drittanbieterdaten oder der Nutzung der App. Die App darf nicht mit externen Auto-Trading-Systemen, Bots, Copy-Trading-, Signalweiterleitungs-, automatischen Order-Bridge- oder ähnlichen Drittprogrammen verbunden oder zusammen verwendet werden. Eine solche Nutzung ist untersagt; daraus entstehende Folgen trägt der Nutzer. Personenbezogene Portfoliodaten werden nicht an den Entwickler übertragen und verbleiben auf dem Gerät. Für Drittanbieter gelten deren eigene Bedingungen und Datenschutzregeln. Unabdingbare gesetzliche Haftung, insbesondere bei Vorsatz, grober Fahrlässigkeit sowie Schäden an Leben, Körper oder Gesundheit, bleibt unberührt.",13,Color.DKGRAY));

        box.addView(bold("English — Risk, use and liability",16,RED));
        box.addView(txt("BorsaRadar is provided solely for technical analysis and decision support. It is not investment advice, a personal investment recommendation, portfolio management, or a guarantee of profit. Buy, hold, sell, breakout, target, stop and confidence signals are predictive technical outputs; accuracy, profit or any specific outcome is not guaranteed. Trading shares and other market instruments involves substantial risk, including rapid losses and partial or total loss of invested capital. All investment and trading decisions, order review and execution are solely the user's responsibility. Users must independently verify data and signals. To the maximum extent permitted by applicable law, the developer is not liable for financial losses caused by market movements, delayed or inaccurate data, outages, incorrect symbols/prices, third-party data sources or use of the app. The app must not be connected to or used with external automated trading systems, bots, copy-trading, signal-forwarding tools, automated order bridges or similar third-party software. Such use is prohibited; the user assumes all consequences of any unauthorized third-party integration. Personal portfolio records are not sent to the developer and remain on the device. Third-party data services remain subject to their own terms and privacy policies.",13,Color.DKGRAY));

        CheckBox accept=new CheckBox(this);
        accept.setText("Okudum ve kabul ediyorum / Ich habe gelesen und stimme zu / I have read and accept");
        accept.setTextSize(14); accept.setPadding(0,dp(12),0,dp(6));
        box.addView(accept);
        box.addView(txt("Kabul etmezseniz uygulama kullanılamaz. Kabul kaydı yalnızca bu cihazda ve bu şart sürümü için saklanır.",11,Color.GRAY));
        scroll.addView(box);

        AlertDialog dlg=new AlertDialog.Builder(this)
                .setTitle("Şartların açık kabulü / Zustimmung / Acceptance")
                .setView(scroll)
                .setCancelable(false)
                .setPositiveButton("KABUL ET / AKZEPTIEREN / ACCEPT",null)
                .setNegativeButton("KABUL ETMİYORUM / EXIT",null)
                .create();
        dlg.setOnShowListener(x->{
            Button yes=dlg.getButton(AlertDialog.BUTTON_POSITIVE);
            yes.setEnabled(false);
            accept.setOnCheckedChangeListener((buttonView,isChecked)->yes.setEnabled(isChecked));
            yes.setOnClickListener(v->{
                if(!accept.isChecked()) return;
                getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit()
                        .putInt("terms_version",TERMS_VERSION)
                        .putLong("terms_accepted_at",System.currentTimeMillis())
                        .apply();
                dlg.dismiss();
                showPortfolio();
                handleNotificationIntent(getIntent());
            });
            dlg.getButton(AlertDialog.BUTTON_NEGATIVE).setOnClickListener(v->finishAndRemoveTask());
        });
        dlg.show();
    }
'''

# Replace the previous generated terms dialog with the stricter checkbox/versioned one.
s=re.sub(r'    private void showTermsAcceptance\(\)\{.*?\n    \}\n\n    private void showInfo\(\)\{',
         terms+'\n    private void showInfo(){',s,count=1,flags=re.S)

# Info button should show the terms without deleting the stored acceptance.
s=s.replace('''getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putBoolean("terms_accepted_v1",false).apply();
            showTermsAcceptance();''','''showTermsAcceptance();''')

# Keep visible ownership/version text current.
s=s.replace('Sürüm 3.10.2 • Teknik karar destek uygulaması','Sürüm 3.10.3 • Teknik karar destek uygulaması')

p.write_text(s,encoding='utf-8')

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 44',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.10.3'",g)
b.write_text(g,encoding='utf-8')
