from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
if 'import android.widget.CheckBox;' not in s:
    s=s.replace('import android.widget.Button;','import android.widget.Button;\nimport android.widget.CheckBox;')
if 'private static final int TERMS_VERSION' not in s:
    s=s.replace('private static final String PREFS = "borsaradar_final";','private static final String PREFS = "borsaradar_final";\n    private static final int TERMS_VERSION = 3;')
if 'private void showTermsAcceptance()' not in s:
    method=r'''
    private void showTermsAcceptance(){
        final String EN="BorsaRadar is provided solely for technical analysis and decision support. It is not investment advice, a personal recommendation, portfolio management, or a guarantee of profit. Buy, hold, sell, target, stop and confidence signals do not guarantee results. Trading can cause substantial losses including partial or total loss of invested capital. All decisions, order checks and execution remain solely the user's responsibility. Users must independently verify data, prices and signals. To the maximum extent permitted by law, developer Erdoğan Kulanoğlu is not liable for losses caused by market movements, delayed or inaccurate data, outages, incorrect symbols or prices, third-party services or use of the app. Use with automated trading systems, bots, copy-trading, signal-forwarding tools, automated order bridges or similar third-party software is prohibited. Personal portfolio records remain on the device.";
        final String DE="BorsaRadar dient ausschließlich der technischen Analyse und Entscheidungsunterstützung. Die App ist keine Anlageberatung, keine persönliche Anlageempfehlung, keine Vermögensverwaltung und keine Gewinngarantie. Kauf-, Halte-, Verkaufs-, Ziel-, Stop- und Konfidenzsignale garantieren kein Ergebnis. Wertpapiergeschäfte können zu erheblichen Verlusten bis hin zum teilweisen oder vollständigen Verlust des eingesetzten Kapitals führen. Sämtliche Anlage- und Handelsentscheidungen sowie Prüfung und Ausführung von Aufträgen liegen ausschließlich in der Verantwortung des Nutzers. Daten, Preise und Signale müssen eigenständig geprüft werden. Soweit gesetzlich zulässig, haftet Entwickler Erdoğan Kulanoğlu nicht für finanzielle Verluste aufgrund von Marktbewegungen, Datenverzögerungen oder -fehlern, Ausfällen, falschen Symbolen oder Preisen, Drittanbieterdaten oder der Nutzung der App. Die Nutzung mit Auto-Trading-Systemen, Bots, Copy-Trading, Signalweiterleitung, automatischen Order-Bridges oder ähnlicher Drittsoftware ist untersagt. Persönliche Portfoliodaten verbleiben auf dem Gerät. Unabdingbare gesetzliche Haftung bleibt unberührt.";
        final String TR="BorsaRadar yalnızca teknik analiz ve karar desteği amacıyla sunulur. Yatırım danışmanlığı, kişiye özel yatırım tavsiyesi, portföy yönetimi veya kazanç garantisi değildir. AL, TUT, SAT, hedef, stop ve güven yüzdesi sonuç garantisi vermez. Piyasa işlemleri ciddi zarar ve yatırılan sermayenin kısmen veya tamamen kaybı riskini taşır. Tüm yatırım ve işlem kararları, emir kontrolü ve uygulanması tamamen kullanıcının sorumluluğundadır. Kullanıcı verileri, fiyatları ve sinyalleri bağımsız olarak kontrol etmelidir. Kanunun izin verdiği azami ölçüde piyasa hareketleri, gecikmiş veya hatalı veri, kesinti, yanlış sembol veya fiyat, üçüncü taraf servisler ya da uygulamanın kullanımından doğan mali kayıplardan geliştirici Erdoğan Kulanoğlu sorumlu tutulamaz. Otomatik işlem botu, copy-trading, sinyal aktarma, otomatik emir köprüsü veya benzeri üçüncü taraf yazılımlarla kullanım yasaktır. Kişisel portföy kayıtları cihazda tutulur.";
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(16),dp(8),dp(16),dp(8));
        root.addView(bold("BorsaRadar",21,NAVY)); root.addView(bold("© 2026 Erdoğan Kulanoğlu",13,NAVY2));
        root.addView(txt("Choose language / Sprache wählen / Dil seçin",12,Color.DKGRAY));
        LinearLayout langs=new LinearLayout(this); langs.setOrientation(LinearLayout.HORIZONTAL);
        Button en=button("English",GREEN), de=button("Deutsch",NAVY2), tr=button("Türkçe",NAVY2);
        langs.addView(en,new LinearLayout.LayoutParams(0,-2,1)); langs.addView(de,new LinearLayout.LayoutParams(0,-2,1)); langs.addView(tr,new LinearLayout.LayoutParams(0,-2,1)); root.addView(langs);
        TextView title=bold("English — Risk, use and liability",16,RED); TextView legal=txt(EN,13,Color.DKGRAY);
        LinearLayout lb=new LinearLayout(this); lb.setOrientation(LinearLayout.VERTICAL); lb.addView(title); lb.addView(legal); ScrollView scroll=new ScrollView(this); scroll.addView(lb); root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        CheckBox accept=new CheckBox(this); accept.setText("I have read and accept / Ich habe gelesen und stimme zu / Okudum ve kabul ediyorum"); root.addView(accept);
        LinearLayout actions=new LinearLayout(this); actions.setOrientation(LinearLayout.HORIZONTAL); Button no=button("DECLINE / ABLEHNEN / REDDET",RED), yes=button("ACCEPT / AKZEPTIEREN / KABUL",GREEN); yes.setEnabled(false); actions.addView(no,new LinearLayout.LayoutParams(0,-2,1)); actions.addView(yes,new LinearLayout.LayoutParams(0,-2,1)); root.addView(actions);
        final String[] language={"EN"};
        en.setOnClickListener(v->{language[0]="EN";title.setText("English — Risk, use and liability");legal.setText(EN);});
        de.setOnClickListener(v->{language[0]="DE";title.setText("Deutsch — Risiko, Nutzung und Haftung");legal.setText(DE);});
        tr.setOnClickListener(v->{language[0]="TR";title.setText("Türkçe — Risk, kullanım ve sorumluluk");legal.setText(TR);});
        accept.setOnCheckedChangeListener((b,c)->yes.setEnabled(c));
        AlertDialog dlg=new AlertDialog.Builder(this).setView(root).setCancelable(false).create();
        yes.setOnClickListener(v->{if(!accept.isChecked())return;getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("terms_version",TERMS_VERSION).putLong("terms_accepted_at",System.currentTimeMillis()).putString("terms_language",language[0]).putString("ui_language",language[0]).apply();dlg.dismiss();if(!getSharedPreferences(PREFS,Context.MODE_PRIVATE).getBoolean("intl_setup_done",false))showInternationalSetup();else{showPortfolio();handleNotificationIntent(getIntent());}});
        no.setOnClickListener(v->finishAndRemoveTask()); dlg.show(); if(dlg.getWindow()!=null)dlg.getWindow().setLayout(-1,(int)(getResources().getDisplayMetrics().heightPixels*0.88));
    }
'''
    marker='    private void showInternationalSetup(){'
    if marker in s: s=s.replace(marker,method+'\n'+marker)
    else:
        marker='    private int dp(int x)'
        s=s.replace(marker,method+'\n'+marker)
p.write_text(s,encoding='utf-8')