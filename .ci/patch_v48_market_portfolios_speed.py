from pathlib import Path

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Keep the speed improvement, but do not create a second market/profile state.
# Exchange separation, persistence and switching are owned by patch_v54_exchange_profiles.py.
s=s.replace('Executors.newFixedThreadPool(5)','Executors.newFixedThreadPool(10)')

p.write_text(s,encoding='utf-8')
