from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v124: completion belongs to scan owner. Preserve per-market done/fail/running and snapshot.
a=s.find('private void scanRadar()')
if a<0: raise SystemExit('scanRadar missing')
b=s.find('\n    private ',a+30)
if b<0:b=len(s)
q=s[a:b]
# Capture immutable owner/universe once.
brace=q.find('{')+1
if 'final int ownedMarket=' not in q[:1000]:
    q=q[:brace]+'\n        radarMarketChoice=radarMarketChoiceMain; final int ownedMarket=radarMarketChoice;'+q[brace:]
if 'final String[] scanUniverse=radarUniverse();' not in q:
    q=q[:brace]+'\n        final String[] scanUniverse=radarUniverse();'+q[brace:]
# Progress bookkeeping must be written to owner whenever counters advance.
q=q.replace('scanDone++;','scanDone++;radarDoneByMarket[ownedMarket]=scanDone;')
q=q.replace('scanFailed++;','scanFailed++;radarFailByMarket[ownedMarket]=scanFailed;')
# Completion must never depend on currently visible market.
q=q.replace('if(done>=radarUniverse().length)','if(done>=scanUniverse.length)')
q=q.replace('if(done>=scanUniverse.length){','if(done>=scanUniverse.length){radarDoneByMarket[ownedMarket]=done;radarFailByMarket[ownedMarket]=scanFailed;',1)
# Finalization: always mark owner complete and persist its rows before any redraw.
for old in ['scanRunning=false;radarRunningByMarket[ownedMarket]=false;saveRadarMarketSnapshot(ownedMarket);','scanRunning=false;radarRunningByMarket[ownedMarket]=false;']:
    if old in q:
        q=q.replace(old,'scanRunning=false;radarRunningByMarket[ownedMarket]=false;radarDoneByMarket[ownedMarket]=scanUniverse.length;saveRadarMarketSnapshot(ownedMarket);',1)
        break
s=s[:a]+q+s[b:]
# Rendering: distinguish never-scanned from completed-zero-result.
a=s.find('private void showRadar()')
if a>=0:
    b=s.find('\n    private ',a+30)
    if b<0:b=len(s)
    q=s[a:b]
    old='"Henüz "+radarMarketTitle()+" radar sonucu yok. Tara düğmesine basarak bu piyasayı tara."'
    new='(radarDoneByMarket[radarMarketChoice]>0&&!radarRunningByMarket[radarMarketChoice]?"Tarama tamamlandı; kriterlere uyan hisse bulunamadı.":"Henüz "+radarMarketTitle()+" radar sonucu yok. Tara düğmesine basarak bu piyasayı tara.")'
    q=q.replace(old,new)
    s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
