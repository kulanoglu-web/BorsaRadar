from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
s=s.replace('bt.setEnabled(hourly||!scanRunning);','bt.setEnabled(true);')
s=s.replace('b.setEnabled(hourly||!scanRunning);','b.setEnabled(true);')
a=s.find('private void scanRadar()')
if a<0: raise SystemExit('scanRadar missing')
b=s.find('\n    private ',a+30)
if b<0:b=len(s)
q=s[a:b]
q=q.replace('scanRunning=false;radarRunningByMarket[ownedMarket]=false;','scanRunning=false;radarRunningByMarket[ownedMarket]=false;saveRadarMarketSnapshot(ownedMarket);')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
