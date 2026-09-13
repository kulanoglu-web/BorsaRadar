from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

if 'import android.widget.CheckBox;' not in s:
    s=s.replace('import android.widget.Button;','import android.widget.Button;\nimport android.widget.CheckBox;')

if 'private static final int TERMS_VERSION' not in s:
    s=s.replace('private static final String PREFS = "borsaradar_final";',
                'private static final String PREFS = "borsaradar_final";\n    private static final int TERMS_VERSION = 3;')
else:
    s=re.sub(r'private static final int TERMS_VERSION = \d+;','private static final int TERMS_VERSION = 3;',s)

s=s.replace('''if(!getSharedPreferences(PREFS,Context.MODE_PRIVATE).getBoolean("terms_accepted_v1",false)){
            showTermsAcceptance();
        } else {''','''if(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("terms_version",0) < TERMS_VERSION){
            showTermsAcceptance();
        } else {''')

terms='''    private void showTermsAcceptance(){
        final String EN="BorsaRadar is provided solely for technical analysis and decision support. It is not investment advice, a personal recommendation, portfolio management, or a guarantee of profit. Buy, hold, sell, breakout, target, stop and confidence signals do not guarantee any result. Trading can cause substantial losses, including partial or total loss of invested capital. All investment and trading decisions, order review and execution are solely the user's responsibility. Users must independently verify data, prices and signals. To the maximum extent permitted by law, developer Erdoğan Kulanoğlu is not liable for financial losses caused by market movements, delayed or inaccurate data, outages, incorrect symbols or prices, third-party data sources or use of the app. The app must not be connected to or used with automated trading systems, bots, copy-trading, signal-forwarding tools, automated order bridges or similar third-party software. Such use is prohibited. Personal portfolio records remain on the device and are not sent to the developer. Third-party services are subject to their own terms and privacy policies.";
        final String DE="BorsaRadar dient ausschließlich der technischen Analyse und Entscheidungsunterstützung. Die App ist keine Anlageberatung, keine persönliche Anlageempfehlung, keine Vermögensverwaltung und keine Gewinngarantie. Kauf-, Halte-, Verkaufs-, Breakout-, Ziel-, Stop- und Konfidenzsignale garantieren kein Ergebnis. Wertpapiergeschäfte können zu erheblichen Verlusten bis hin zum teilweisen oder vollständigen Verlust des eingesetzten Kapitals führen. Sämtliche Anlage- und Handelsentscheidungen sowie Prüfung und Ausführung von Aufträgen liegen ausschließlich in der Verantwortung des Nutzers. Daten, Preise und Signale müssen eigenständig geprüft werden. Soweit gesetzlich zulässig, haftet der Entwickler Erdoğan Kulanoğlu nicht für finanzielle Verluste aufgrund von Marktbewegungen, Datenverzögerungen oder -fehlern, Ausfällen, falschen Symbolen oder Preisen, Drittanbieterdaten oder der Nutzung der App. Die App darf nicht mit Auto-Trading-Systemen, Bots, Copy-Trading-, Signalweiterleitungs-, automatischen Order-Bridge- oder ähnlichen Drittprogrammen verbunden oder zusammen verwendet werden. Eine solche Nutzung ist untersagt. Persönliche Portfoliodaten verbleiben auf dem Gerät. Unabdingbare gesetzliche Haftung bleibt unberührt.";
        final String TR="BorsaRadar yalnızca teknik analiz ve karar desteği amacıyla sunulur. Yatırım danışmanlığı, kişiye özel yatırım tavsiyesi, portföy yönetimi veya kazanç garantisi değildir. AL, TUT, SAT, erken kırılım, hedef, stop ve güven yüzdesi sonuç garantisi vermez. Piyasa işlemleri ciddi zarar ve yatırılan sermayenin kısmen veya tamamen kaybı riskini taşır. Tüm yatırım ve işlem kararları, emir kontrolü ve uygulanması tamamen kullanıcının sorumluluğundadır. Kullanıcı verileri, fiyatları ve sinyalleri işlem öncesinde bağımsız olarak kontrol etmelidir. Kanunun izin verdiği azami ölçüde, piyasa hareketleri, gecikmiş veya hatalı veri, kesinti, yanlış sembol veya fiyat, üçüncü taraf veri kaynağı ya da uygulamanın kullanımından doğan mali kayıplardan geliştirici Erdoğan Kulanoğlu sorumlu tutulamaz. Uygulamanın otomatik işlem botu, copy-trading, sinyal aktarma, otomatik emir köprüsü veya benzeri üçüncü taraf programlarla kullanılması yasaktır. Kişisel portföy kayıtları geliştiriciye gönderilmez ve cihazda tutulur.";

        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(16),dp(8),dp(16),dp(8));
        root.addView(bold("BorsaRadar",21,NAVY));
        root.addView(bold("© 2026 Erdoğan Kulanoğlu • All rights reserved",13,NAVY2));
        root.addView(txt("Choose language / Sprache wählen / Dil seçin",12,Color.DKGRAY));

        LinearLayout langs=new LinearLayout(this); langs.setOrientation(LinearLayout.HORIZONTAL);
        Button en=button("English",GREEN), de=button("Deutsch",NAVY2), tr=button("Türkçe",NAVY2);
        langs.addView(en,new LinearLayout.LayoutParams(0,-2,1));
        langs.addView(de,new LinearLayout.LayoutParams(0,-2,1));
        langs.addView(tr,new LinearLayout.LayoutParams(0,-2,1));
        root.addView(langs);

        TextView title=bold("English — Risk, use and liability",16,RED);
        TextView legal=txt(EN,13,Color.DKGRAY);
        LinearLayout legalBox=new LinearLayout(this); legalBox.setOrientation(LinearLayout.VERTICAL); legalBox.addView(title); legalBox.addView(legal);
        ScrollView scroll=new ScrollView(this); scroll.addView(legalBox);
        root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));

        CheckBox accept=new CheckBox(this);
        accept.setText("I have read and accept / Ich habe gelesen und stimme zu / Okudum ve kabul ediyorum");
        accept.setTextSize(13); root.addView(accept);

        LinearLayout actions=new LinearLayout(this); actions.setOrientation(LinearLayout.HORIZONTAL);
        Button no=button("DECLINE / ABLEHNEN / REDDET",RED);
        Button yes=button("ACCEPT / AKZEPTIEREN / KABUL",GREEN); yes.setEnabled(false);
        actions.addView(no,new LinearLayout.LayoutParams(0,-2,1));
        actions.addView(yes,new LinearLayout.LayoutParams(0,-2,1));
        root.addView(actions);

        final String[] language={"EN"};
        en.setOnClickListener(v->{language[0]="EN";title.setText("English — Risk, use and liability");legal.setText(EN);});
        de.setOnClickListener(v->{language[0]="DE";title.setText("Deutsch — Risiko, Nutzung und Haftung");legal.setText(DE);});
        tr.setOnClickListener(v->{language[0]="TR";title.setText("Türkçe — Risk, kullanım ve sorumluluk");legal.setText(TR);});
        accept.setOnCheckedChangeListener((buttonView,isChecked)->yes.setEnabled(isChecked));

        AlertDialog dlg=new AlertDialog.Builder(this).setView(root).setCancelable(false).create();
        yes.setOnClickListener(v->{
            if(!accept.isChecked()) return;
            getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit()
                    .putInt("terms_version",TERMS_VERSION)
                    .putLong("terms_accepted_at",System.currentTimeMillis())
                    .putString("terms_language",language[0])
                    .apply();
            dlg.dismiss(); showPortfolio(); handleNotificationIntent(getIntent());
        });
        no.setOnClickListener(v->finishAndRemoveTask());
        dlg.show();
        if(dlg.getWindow()!=null) dlg.getWindow().setLayout(-1,(int)(getResources().getDisplayMetrics().heightPixels*0.88));
    }
'''

s=re.sub(r'    private void showTermsAcceptance\(\)\{.*?\n    \}\n\n    private void showInfo\(\)\{',
         terms+'\n    private void showInfo(){',s,count=1,flags=re.S)

s=s.replace('''getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putBoolean("terms_accepted_v1",false).apply();
            showTermsAcceptance();''','''showTermsAcceptance();''')
s=s.replace('Sürüm 3.10.2 • Teknik karar destek uygulaması','Sürüm 3.10.4 • Teknik karar destek uygulaması')
s=s.replace('Sürüm 3.10.3 • Teknik karar destek uygulaması','Sürüm 3.10.4 • Teknik karar destek uygulaması')

p.write_text(s,encoding='utf-8')

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 45',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.10.4'",g)
b.write_text(g,encoding='utf-8')
