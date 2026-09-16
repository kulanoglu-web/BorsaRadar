from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v120: scanUniverse is local to scanRadar. Older patches accidentally changed a
# completion check in the following method. Keep scanRadar immutable, restore all
# out-of-method checks to the selected radar universe.
a=s.find('private void scanRadar()')
b=s.find('private void enrichRadarTopCandidates',a)
if a<0 or b<0: raise SystemExit('radar method anchors missing')
pre=s[:a]
scan=s[a:b]
post=s[b:]
# scanRadar owns a local immutable universe.
if 'final String[] scanUniverse=radarUniverse();' not in scan:
    brace=scan.find('{')+1
    scan=scan[:brace]+'\n        final String[] scanUniverse=radarUniverse();'+scan[brace:]
scan=scan.replace('radarUniverse().length','scanUniverse.length')
# No method after scanRadar may reference its local variable.
post=post.replace('scanUniverse.length','radarUniverse().length')
s=pre+scan+post
p.write_text(s,encoding='utf-8')
