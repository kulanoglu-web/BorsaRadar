from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# First-run mandatory acceptance before normal use.
s=s.replace('''        setupAlerts();
        showPortfolio();
        handleNotificationIntent(getIntent());''','''        setupAlerts();
        if(!getSharedPreferences(PREFS,Context.MODE_PRIVATE).getBoolean("terms_accepted_v1",false)){
            showTermsAcceptance();
        } else {
            showPortfolio();
            handleNotificationIntent(getIntent());
        }''')

terms='''
    private void showTermsAcceptance(){
        ScrollView scroll=new ScrollView(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(8),dp(18),dp(18));
        box.addView(bold("BorsaRadar • Kullanım Şartları",21,NAVY));
        box.addView(bold("© 2026 Erdoğan Kulanoğlu • Tüm hakları saklıdır",15,NAVY2));
        box.addView(txt("Devam etmek için aşağıdaki şartları okuyup kabul etmeniz gerekir.",14,Color.DKGRAY));
        box.addView(bold("Türkçe",16,RED));
        box.addView(txt("BorsaRadar yalnızca teknik analiz ve karar destek amacıyla sunulur; yatırım danışmanlığı, kişisel yatırım tavsiyesi veya kazanç garantisi değildir. AL/TUT/SAT, hedef, stop, güven yüzdesi ve diğer göstergeler kesin sonuç vermez. Hisse senedi ve diğer piyasa işlemleri önemli zarar ve sermaye kaybı riski taşır. Tüm yatırım ve işlem kararlarının sorumluluğu tamamen kullanıcıya aittir. Kullanıcı, uygulamadaki bilgi ve sinyalleri kendi değerlendirmesiyle kullanır ve doğabilecek doğrudan veya dolaylı finansal kayıplardan geliştirici Erdoğan Kulanoğlu'nu sorumlu tutmayacağını kabul eder. Uygulama üçüncü taraf otomatik emir, işlem robotu, kopya işlem, sinyal aktarma veya benzeri harici programlarla birlikte kullanılmak üzere tasarlanmamıştır ve bu tür kullanım yasaktır. Üçüncü taraf uygulama, veri servisi, bağlantı, gecikme, hata veya kesintilerinden geliştirici sorumlu değildir. Kişisel portföy verileri geliştiriciye gönderilmez; cihaz üzerinde tutulur. Piyasa verileri üçüncü taraf veri servislerinden alınabilir ve bu servislerin kendi koşulları geçerlidir.",13,Color.DKGRAY));
        box.addView(bold("Deutsch",16,RED));
        box.addView(txt("BorsaRadar dient ausschließlich der technischen Analyse und Entscheidungsunterstützung. Es handelt sich weder um Anlageberatung noch um eine persönliche Empfehlung oder Gewinngarantie. Kauf-/Halten-/Verkaufssignale, Ziele, Stops und Konfidenzwerte garantieren kein Ergebnis. Wertpapiergeschäfte können zu erheblichen Verlusten bis hin zum Verlust des eingesetzten Kapitals führen. Sämtliche Anlage- und Handelsentscheidungen liegen allein in der Verantwortung des Nutzers. Der Nutzer erklärt sich damit einverstanden, den Entwickler Erdoğan Kulanoğlu nicht für direkte oder indirekte finanzielle Verluste haftbar zu machen. Die App ist nicht zur Nutzung mit externen Auto-Trading-Systemen, Bots, Copy-Trading-, Signalweiterleitungs- oder ähnlichen Drittprogrammen bestimmt; eine solche Nutzung ist untersagt. Für Fehler, Verzögerungen, Ausfälle oder Daten von Drittanbietern übernimmt der Entwickler keine Haftung. Persönliche Portfoliodaten werden nicht an den Entwickler übertragen und verbleiben auf dem Gerät.",13,Color.DKGRAY));
        box.addView(bold("English",16,RED));
        box.addView(txt("BorsaRadar is provided solely for technical analysis and decision support. It is not investment advice, a personal recommendation, or a guarantee of profit. Buy/hold/sell signals, targets, stops, confidence values and other indicators do not guarantee any result. Trading shares and other market instruments involves substantial risk, including loss of invested capital. All investment and trading decisions are solely the user's responsibility. By using the app, the user agrees not to hold developer Erdoğan Kulanoğlu liable for direct or indirect financial losses. The app is not designed for use with external automated trading systems, bots, copy-trading, signal-forwarding tools or similar third-party programs; such use is prohibited. The developer is not responsible for third-party data, delays, errors, outages or connectivity issues. Personal portfolio data is not sent to the developer and remains on the device.",13,Color.DKGRAY));
        box.addView(txt("Kabul ederek uygulamayı bu şartlarla kullanmayı kabul ediyorum. / Mit der Annahme stimme ich diesen Bedingungen zu. / By accepting, I agree to use the app under these terms.",12,Color.GRAY));
        scroll.addView(box);
        AlertDialog dlg=new AlertDialog.Builder(this)
                .setTitle("Şartları kabul et / Bedingungen akzeptieren / Accept terms")
                .setView(scroll)
                .setCancelable(false)
                .setPositiveButton("KABUL EDİYORUM",null)
                .setNegativeButton("ÇIKIŞ",null)
                .create();
        dlg.setOnShowListener(x->{
            dlg.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
                getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putBoolean("terms_accepted_v1",true).apply();
                dlg.dismiss();
                showPortfolio();
                handleNotificationIntent(getIntent());
            });
            dlg.getButton(AlertDialog.BUTTON_NEGATIVE).setOnClickListener(v->finish());
        });
        dlg.show();
    }
'''
marker='    private void showInfo(){'
if 'private void showTermsAcceptance()' not in s:
    s=s.replace(marker,terms+'\n'+marker)

# Make the copyright owner visible on every screen footer.
s=s.replace('© 2026 Erdoğan Kulanoğlu • BorsaRadar • Tüm hakları saklıdır','© 2026 Erdoğan Kulanoğlu • BorsaRadar • Tüm hakları saklıdır • ⓘ şartlar')

# Strengthen Info text with user responsibility and no third-party automation.
s=s.replace('''Bu uygulama yatırım danışmanlığı değildir. AL, TUT, SAT, erken kırılım, hedef, stop, güven yüzdesi ve benzeri göstergeler yalnızca teknik karar desteğidir; doğruluk, kazanç veya sonuç garantisi yoktur.''','''Bu uygulama yatırım danışmanlığı değildir. AL, TUT, SAT, erken kırılım, hedef, stop, güven yüzdesi ve benzeri göstergeler yalnızca teknik karar desteğidir; doğruluk, kazanç veya sonuç garantisi yoktur. Tüm yatırım ve işlem kararlarının sorumluluğu kullanıcıya aittir. Uygulamanın üçüncü taraf otomatik işlem, bot, kopya işlem veya sinyal aktarma programlarıyla kullanılması yasaktır.''')

# Info screen offers a button to re-open mandatory terms text by resetting acceptance and showing it.
s=s.replace('''box.addView(txt("Sürüm 3.10 • Teknik karar destek uygulaması",11,Color.GRAY));''','''Button termsBtn=button("Kullanım şartlarını tekrar göster",NAVY2); box.addView(termsBtn); termsBtn.setOnClickListener(v->{
            getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putBoolean("terms_accepted_v1",false).apply();
            showTermsAcceptance();
        });
        box.addView(txt("Sürüm 3.10.2 • Teknik karar destek uygulaması",11,Color.GRAY));''')

p.write_text(s,encoding='utf-8')

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 43',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.10.2'",g)
b.write_text(g,encoding='utf-8')
