from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# 5 workers make a 645-symbol US scan look frozen while the first network calls wait.
s=s.replace('private final ExecutorService io = Executors.newFixedThreadPool(5);','private final ExecutorService io = Executors.newFixedThreadPool(12);')
s=s.replace('private final ExecutorService io=Executors.newFixedThreadPool(5);','private final ExecutorService io=Executors.newFixedThreadPool(12);')
# Publish progress immediately instead of waiting for the first 8/20 symbols.
s=s.replace('if(done%8==0 || done>=universe.length){','if(done<=12 || done%4==0 || done>=universe.length){')
s=s.replace('}else if(done%20==0)main.post(this::showHourlyRadar);','}else if(done<=12 || done%4==0)main.post(this::showHourlyRadar);')
# If an old scan flag survived a screen rebuild but has no completed work, allow a fresh scan.
needle='private void scanShortTerm(String mode){\n        if(shortScanRunning)return;'
if needle in s:
    s=s.replace(needle,'private void scanShortTerm(String mode){\n        if(shortScanRunning && shortScanDone.get()>0)return;\n        if(shortScanRunning && shortScanDone.get()==0)shortScanRunning=false;',1)
p.write_text(s,encoding='utf-8')
