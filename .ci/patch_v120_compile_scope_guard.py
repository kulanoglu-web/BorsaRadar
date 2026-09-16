from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v121 compile guard: scanUniverse may only exist inside scanRadar.
a=s.find('private void scanRadar()')
if a<0: raise SystemExit('scanRadar missing')
# Find the actual next method instead of relying on a method name that may have moved.
b=s.find('\n    private ',a+30)
if b<0:b=len(s)
pre=s[:a]; scan=s[a:b]; post=s[b:]
# Ensure method-local immutable universe exists.
brace=scan.find('{')+1
if 'final String[] scanUniverse=radarUniverse();' not in scan:
    scan=scan[:brace]+'\n        final String[] scanUniverse=radarUniverse();'+scan[brace:]
# Only scanRadar completion checks may use the local variable.
scan=scan.replace('radarUniverse().length','scanUniverse.length')
# Every reference outside scanRadar is invalid and must use a non-local expression.
post=post.replace('scanUniverse.length','radarUniverse().length')
pre=pre.replace('scanUniverse.length','radarUniverse().length')
s=pre+scan+post
p.write_text(s,encoding='utf-8')
