from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Interactive stock detail must never wait behind hundreds of background radar jobs.
# Accept the current bulk executor size (it may be tuned independently for scan speed).
if 'detailIo' not in s:
    pat=r'(    private final ExecutorService io = Executors\.newFixedThreadPool\(\d+\);)'
    s,n=re.subn(pat,r'\1\n    private final ExecutorService detailIo = Executors.newFixedThreadPool(2);',s,count=1)
    if n!=1: raise SystemExit('executor anchor missing')

# Route the single-stock analysis to the dedicated interactive executor.
start=s.find('private void analyzeStock(String symbol)')
end=s.find('private void renderStockDetail',start)
if start<0 or end<0: raise SystemExit('analyzeStock boundaries missing')
block=s[start:end]
if 'detailIo.execute' not in block:
    if 'io.execute' not in block: raise SystemExit('analyzeStock io.execute missing')
    block=block.replace('io.execute','detailIo.execute',1)
s=s[:start]+block+s[end:]

# Timeframe changes are interactive too; they should not queue behind the bulk scan.
start=s.find('private void loadFullChartFrame(String symbol,FullAnalysisEngine.Result a,String frame)')
if start<0: raise SystemExit('loadFullChartFrame missing')
end=s.find('\n    private ',start+20)
if end<0: end=len(s)
block=s[start:end]
if 'detailIo.execute' not in block and 'io.execute' in block:
    block=block.replace('io.execute','detailIo.execute',1)
    s=s[:start]+block+s[end:]

# Shut down both executors.
if 'detailIo.shutdownNow();' not in s:
    s=s.replace('''        io.shutdownNow();\n        super.onDestroy();''','''        io.shutdownNow();\n        detailIo.shutdownNow();\n        super.onDestroy();''',1)

# Improve loading text so it is clear this is an interactive priority request.
s=s.replace('Teknik + eski metodlar + haber/KAP + makro analiz ediliyor…','Teknik analiz öncelikli çalışıyor • haber/KAP/makro bağlamı ekleniyor…',1)

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 53',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.5'",g)
b.write_text(g,encoding='utf-8')
p.write_text(s,encoding='utf-8')
