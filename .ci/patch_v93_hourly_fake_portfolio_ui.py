from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Hourly radar: manual refresh must not stay blocked by a stale running flag.
old='''private void scanShortTerm(String mode){
        if(shortScanRunning)return;
        shortScanRunning=true;shortScanMode=mode;shortScanDone.set(0);shortScanFailed.set(0);'''
new='''private void scanShortTerm(String mode){
        if(shortScanRunning && shortScanDone.get()>0 && shortScanDone.get()<marketSymbols(primaryMarket()).length){shortScanRunning=false;}
        if(shortScanRunning)return;
        shortScanRunning=true;shortScanMode=mode;shortScanDone.set(0);shortScanFailed.set(0);'''
if old in s:s=s.replace(old,new,1)
s=s.replace('''b.setEnabled(!shortScanRunning);b.setOnClickListener(v->scanShortTerm("1S"));''','''b.setEnabled(true);b.setOnClickListener(v->{shortScanRunning=false;scanShortTerm("1S");});''',1)

# Production navigation intentionally has no Fake/Paper portfolio tab.
# Paper portfolio support added by earlier patches may remain available internally,
# but it must not occupy the main bottom navigation.

p.write_text(s,encoding='utf-8')
