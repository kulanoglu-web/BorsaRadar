from pathlib import Path
import re
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
old='''                RadarItem item=new RadarItem(sym,r); item.score=rt.score; item.rankedScore=rt.score; item.why=rt.summary+" • "+item.why;\n                if(r.price>0)buffer.add(item);'''
new='''                RadarItem item=new RadarItem(sym,r); item.score=rt.score; item.rankedScore=rt.score; item.why=rt.summary+" • "+item.why;\n                if(rt.score>=4.2){HourlyRiskGate.Decision g=HourlyRiskGate.review(sym,rt.score,item.recommendation,item.confidence);item.recommendation=g.label;item.rankedScore=rt.score+g.adjustment;item.why=item.why+" • "+g.note;}\n                if(r.price>0)buffer.add(item);'''
if old not in s: raise SystemExit('hourly item anchor missing')
s=s.replace(old,new,1)
s=s.replace('main.post(this::showBaskets);','main.post(this::showHourlyRadar);',1)
p.write_text(s,encoding='utf-8')
b=Path('app/build.gradle');g=b.read_text(encoding='utf-8');g=re.sub(r'versionCode\s+\d+','versionCode 55',g);g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.7'",g);b.write_text(g,encoding='utf-8')
