from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# V35'i portfoy risk/firsat bildirimlerinin ana karar katmani yap.
old='''ShortPulseEngine.Result sr=ShortPulseEngine.analyze(d);
                holdingSignals.put(h.symbol,sr);
                double pnlPct=h.cost>0?(sr.price/h.cost-1)*100:0;
                if(sr.price<=sr.stopReference || sr.recommendation.contains("SAT") || sr.recommendation.contains("RİSK"))
                    notifyAlert("Zarar önleme: "+h.symbol, sr.recommendation+" • fiyat "+money(sr.price)+" • stop "+money(sr.stopReference));
                else if(pnlPct>=8 && !sr.recommendation.contains("AL"))
                    notifyAlert("Kâr koruma: "+h.symbol, "Pozisyon +%"+fmt(pnlPct)+" • momentum zayıflayabilir, kâr korumayı değerlendir.");'''
new='''ShortPulseEngine.Result sr=ShortPulseEngine.analyze(d);
                holdingSignals.put(h.symbol,sr);
                V35HybridEngine.Result v35=V35HybridEngine.analyze(d,h.cost);
                double pnlPct=h.cost>0?(v35.price/h.cost-1)*100:0;
                if(v35.risk || v35.price<=v35.stopPrice)
                    notifyAlert("V35 zarar önleme: "+h.symbol, v35.action+" • fiyat "+money(v35.price)+" • stop "+money(v35.stopPrice));
                else if(pnlPct>=6 && (v35.action.contains("TUT") || v35.action.contains("İZLE")))
                    notifyAlert("V35 kâr koruma: "+h.symbol, "Pozisyon +%"+fmt(pnlPct)+" • stop "+money(v35.stopPrice)+" • "+v35.phase);'''
if old in s: s=s.replace(old,new)

# Detay ekranında V35 canlı karar kartını ekle.
needle='''content.addView(txt("Emir burada hazırlanır; nihai onay Ziraat Trader içinde verilir.",12,Color.GRAY));'''
replacement='''try {
            V35HybridEngine.Result v35=V35HybridEngine.analyze(data,0);
            int vc=v35.risk?RED:(v35.opportunity?GREEN:Color.rgb(225,145,0));
            content.addView(bold("V35 HYBRID • "+v35.action+" • %"+(int)v35.confidence,17,vc));
            content.addView(txt(v35.reason,12,Color.DKGRAY));
        } catch(Exception ignored) {}
        content.addView(txt("Emir burada hazırlanır; nihai onay Ziraat Trader içinde verilir.",12,Color.GRAY));'''
if needle in s: s=s.replace(needle,replacement)

# Radar bitisinde sadece eski en iyi satira degil, V35 uyumlu erken AL mantigina vurgu yapan metin.
s=s.replace('"Erken kırılım + güçlü adaylar"','"V35 Hybrid • erken kırılım + güçlü adaylar"')
s=s.replace('"BorsaRadar Alarmları"','"BorsaRadar V35 Alarmları"')
s=s.replace('"Fırsat, kâr koruma ve zarar önleme uyarıları"','"V35 fırsat, kâr koruma ve zarar önleme uyarıları"')

p.write_text(s,encoding='utf-8')

# Sürüm 3.8
b=Path('app/build.gradle')
t=b.read_text(encoding='utf-8')
t=re.sub(r'versionCode\s+\d+','versionCode 38',t)
t=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.8.0'",t)
b.write_text(t,encoding='utf-8')
