from pathlib import Path
import re
p=Path('app/build.gradle')
s=p.read_text(encoding='utf-8')
s=re.sub(r'versionCode\s+\d+','versionCode 40',s)
s=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.9.0'",s)
p.write_text(s,encoding='utf-8')

# Keep the existing Android workflow stable; apply the v3.10 feature patch here.
feature_patch=Path('.ci/patch_v43_eur_info.py')
if feature_patch.exists():
    exec(compile(feature_patch.read_text(encoding='utf-8'),str(feature_patch),'exec'))
