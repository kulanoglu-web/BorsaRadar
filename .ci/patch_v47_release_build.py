from pathlib import Path
import re
p=Path('app/build.gradle')
s=p.read_text(encoding='utf-8')
s=re.sub(
    r'buildTypes\s*\{\s*debug\s*\{\s*signingConfig\s+signingConfigs\.stable\s*\}\s*\}',
    "buildTypes {\n        debug {\n            signingConfig signingConfigs.stable\n        }\n        release {\n            signingConfig signingConfigs.stable\n            minifyEnabled false\n            shrinkResources false\n        }\n    }",
    s,
    count=1,
    flags=re.S
)
p.write_text(s,encoding='utf-8')
