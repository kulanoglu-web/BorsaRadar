from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
old='''                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                radarResults.add(new RadarItem(sym,r));'''
new='''                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                RadarTechnicalEngine.Result rt=RadarTechnicalEngine.analyze(d);
                RadarItem item=new RadarItem(sym,r);
                item.score=rt.score;
                item.rankedScore=rt.score;
                item.why=rt.summary+" • "+item.why;
                radarResults.add(item);'''
if old not in s:
    raise SystemExit('multi technical radar patch failed')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
