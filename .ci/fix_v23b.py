from pathlib import Path
p=Path('build-v23/BorsaRadar/app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
s=s.replace('content.addView(title("BorsaPulse-2W canlı değerlendirme • " + s.reason, 17));','content.addView(title("BorsaPulse-2W kısa dönem değerlendirme tamamlandı.", 17));')
p.write_text(s,encoding='utf-8')
print('v2.3 final compile fix applied')
