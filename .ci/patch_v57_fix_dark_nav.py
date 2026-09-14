from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
s=s.replace('Button p=button("⌂\n"+L("Portföy","Portfolio","Portfolio"),Color.rgb(42,47,54));','Button p=button("⌂ / "+L("Portföy","Portfolio","Portfolio"),Color.rgb(42,47,54));')
s=s.replace('Button r=button("↗\n"+L("Radar","Radar","Radar"),ACCENT);','Button r=button("↗ / "+L("Radar","Radar","Radar"),ACCENT);')
s=s.replace('Button one=button("⌕\n"+L("Tek Hisse","Einzeltitel","Single"),Color.rgb(42,47,54));','Button one=button("⌕ / "+L("Tek Hisse","Einzeltitel","Single"),Color.rgb(42,47,54));')
s=s.replace('Button three=button("▦\n"+L("3 Sepet","3 Körbe","3 Baskets"),Color.rgb(42,47,54));','Button three=button("▦ / "+L("3 Sepet","3 Körbe","3 Baskets"),Color.rgb(42,47,54));')
p.write_text(s,encoding='utf-8')
