from pathlib import Path
import re
p=Path('app/build.gradle')
s=p.read_text(encoding='utf-8')
s=re.sub(r'versionCode\s+\d+','versionCode 40',s)
s=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.9.0'",s)
p.write_text(s,encoding='utf-8')

feature_patch=Path('.ci/patch_v43_eur_info.py')
if feature_patch.exists():
    exec(compile(feature_patch.read_text(encoding='utf-8'),str(feature_patch),'exec'))

m=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
t=m.read_text(encoding='utf-8')
t=re.sub(r'^\s*cost\.setHint\(pos==0\?.*?\);\s*$', '', t, flags=re.M)
t=t.replace('EditText cost=new EditText(this); cost.setHint("Alış fiyatı (₺)");','EditText cost=new EditText(this); cost.setHint("Alış fiyatı (TL / EUR)");')
m.write_text(t,encoding='utf-8')

fix_patch=Path('.ci/patch_v44_decision_fix.py')
if fix_patch.exists():
    exec(compile(fix_patch.read_text(encoding='utf-8'),str(fix_patch),'exec'))

q=Path('.ci/patch_v45_terms_acceptance.py')
if q.exists():
    exec(compile(q.read_text(encoding='utf-8'),str(q),'exec'))

v46=Path('.ci/patch_v46_terms_checkbox.py')
if v46.exists():
    exec(compile(v46.read_text(encoding='utf-8'),str(v46),'exec'))

v48=Path('.ci/patch_v48_international_mode.py')
if v48.exists():
    exec(compile(v48.read_text(encoding='utf-8'),str(v48),'exec'))

v55=Path('.ci/patch_v55_terms_fallback.py')
if v55.exists():
    exec(compile(v55.read_text(encoding='utf-8'),str(v55),'exec'))

# Ensure a normal signed release variant exists for device installation.
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
if 'release { signingConfig signingConfigs.stable' not in g:
    g=g.replace('buildTypes { debug { signingConfig signingConfigs.stable } }',
                'buildTypes { debug { signingConfig signingConfigs.stable } release { signingConfig signingConfigs.stable; minifyEnabled false; shrinkResources false } }')
b.write_text(g,encoding='utf-8')