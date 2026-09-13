from pathlib import Path
import re
p=Path('app/build.gradle')
s=p.read_text(encoding='utf-8')
s=re.sub(r'versionCode\s+\d+','versionCode 40',s)
s=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.9.0'",s)
p.write_text(s,encoding='utf-8')
