from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v82: ensure quote card uses latest valid chart close whenever provider result price is absent.
s=s.replace('double visiblePrice=(chart!=null&&!chart.isEmpty()&&chart.get(chart.size()-1).close>0)\n  ? chart.get(chart.size()-1).close : r.price;', 'double visiblePrice=(chart!=null&&!chart.isEmpty()&&chart.get(chart.size()-1).close>0) ? chart.get(chart.size()-1).close : r.price;')
# Catch variants still rendering r.price directly.
s=s.replace('TextView px=bold(money(r.price,symbol),28,r.changePct>=0?GREEN:RED);', 'double visiblePrice=(chart!=null&&!chart.isEmpty()&&chart.get(chart.size()-1).close>0)?chart.get(chart.size()-1).close:r.price; TextView px=bold(money(visiblePrice,symbol),28,r.changePct>=0?GREEN:RED);')
# Do not display a percentage as authoritative when no usable visible price exists.
s=s.replace('TextView ch=txt(String.format(java.util.Locale.US,"%s %.2f%%",r.changePct>=0?"▲":"▼",r.changePct),18,r.changePct>=0?GREEN:RED);', 'TextView ch=txt(visiblePrice>0?String.format(java.util.Locale.US,"%s %.2f%%",r.changePct>=0?"▲":"▼",r.changePct):"Fiyat bekleniyor",18,r.changePct>=0?GREEN:RED);')
# Rename Takas to Alanlar/Satanlar to avoid ambiguity.
s=s.replace('"🏦 Takas"','"🏦 Alan/Satan"')
s=s.replace('"🏦 Kurumsal Alım / Satım"','"🏦 Büyük Alanlar / Satanlar"')
p.write_text(s,encoding='utf-8')
