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
