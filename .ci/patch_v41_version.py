from pathlib import Path
import re
p=Path('app/build.gradle')
s=p.read_text(encoding='utf-8')
s=re.sub(r'versionCode\s+\d+','versionCode 40',s)
s=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.9.0'",s)
p.write_text(s,encoding='utf-8')

for name in ['patch_v43_eur_info.py','patch_v44_decision_fix.py','patch_v45_terms_acceptance.py','patch_v46_terms_checkbox.py','patch_v48_international_mode.py','patch_v55_terms_fallback.py','patch_v49_persistent_short_scan.py']:
    q=Path('.ci')/name
    if q.exists():
        exec(compile(q.read_text(encoding='utf-8'),str(q),'exec'))

m=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
t=m.read_text(encoding='utf-8')
t=re.sub(r'^\s*cost\.setHint\(pos==0\?.*?\);\s*$', '', t, flags=re.M)
t=t.replace('EditText cost=new EditText(this); cost.setHint("Alış fiyatı (₺)");','EditText cost=new EditText(this); cost.setHint("Alış fiyatı (TL / EUR)");')
m.write_text(t,encoding='utf-8')

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
if 'release { signingConfig signingConfigs.stable' not in g:
    g=g.replace('buildTypes { debug { signingConfig signingConfigs.stable } }','buildTypes { debug { signingConfig signingConfigs.stable } release { signingConfig signingConfigs.stable; minifyEnabled false; shrinkResources false } }')
b.write_text(g,encoding='utf-8')