from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Tune the bulk/general + intraday scan executor only after all UI/feature patches
# have finished, so earlier patch anchors remain stable.
pat=r'private final ExecutorService io = Executors\.newFixedThreadPool\(\d+\);'
s,n=re.subn(pat,'private final ExecutorService io = Executors.newFixedThreadPool(12);',s,count=1)
if n!=1: raise SystemExit('bulk executor tuning anchor missing')

p.write_text(s,encoding='utf-8')
