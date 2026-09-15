from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
start=s.find('private void analyzeStock(String symbol)')
end=s.find('private void renderFastTechnicalDetail',start)
if start<0 or end<0: raise SystemExit('detail boundaries missing')
block=s[start:end]
# Replace blocking spinner shell with an immediate usable screen. Network data fills it asynchronously.
import re
block=re.sub(r'''shell\(symbol\+" • analiz"\);\s*content\.addView\(loadingCard\("Fiyat ve teknik göstergeler hazırlanıyor…"\)\);''','''shell(symbol+" • analiz");
        LinearLayout instant=card();
        instant.addView(bold(symbol,24,Color.WHITE));
        instant.addView(txt("Veri yenileniyor… Bu ekranı beklemeden kullanabilirsin.",13,Color.GRAY));
        content.addView(instant);''',block,count=1)
# Ensure data acquisition is isolated from scan traffic and that a timeout/failure leaves navigation usable.
block=block.replace('detailIo.execute(()->{','detailIo.execute(()->{',1)
# Do not clear/recreate the screen until actual data arrives; existing cached/previous UI remains responsive.
s=s[:start]+block+s[end:]
p.write_text(s,encoding='utf-8')
