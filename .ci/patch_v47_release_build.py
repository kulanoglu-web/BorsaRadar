from pathlib import Path
p=Path('app/build.gradle')
s=p.read_text(encoding='utf-8')
start=s.find('buildTypes')
if start>=0:
    brace=s.find('{',start)
    depth=0
    end=-1
    for i in range(brace,len(s)):
        if s[i]=='{': depth+=1
        elif s[i]=='}':
            depth-=1
            if depth==0:
                end=i+1
                break
    if end>0:
        block="""buildTypes {
        debug {
            signingConfig signingConfigs.stable
        }
        release {
            signingConfig signingConfigs.stable
            minifyEnabled false
            shrinkResources false
        }
    }"""
        s=s[:start]+block+s[end:]
p.write_text(s,encoding='utf-8')
