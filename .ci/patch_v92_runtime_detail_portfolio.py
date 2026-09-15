from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v92 runtime stability: never leave single-stock detail permanently locked after a failed/slow request.
s=s.replace('''        if(!singleStockLoading.add(symbol)) return;''','''        // Do not block a new explicit detail request behind a stale loading lock.
        singleStockLoading.remove(symbol);
        singleStockLoading.add(symbol);''')
# Ensure every posted success/error path releases the per-symbol loading marker.
s=s.replace('''main.post(()->renderFastTechnicalDetail(symbol,data));''','''main.post(()->{singleStockLoading.remove(symbol);renderFastTechnicalDetail(symbol,data);});''')
s=s.replace('''main.post(()->{try{renderFastTechnicalDetail(symbol,data);''','''main.post(()->{singleStockLoading.remove(symbol);try{renderFastTechnicalDetail(symbol,data);''')
s=s.replace('''main.post(()->{try{renderStockDetail(symbol,a,chart,"10G");''','''main.post(()->{singleStockLoading.remove(symbol);try{renderStockDetail(symbol,a,chart,"10G");''')
# Legacy-safe Fake portfolio reader. Old installations may contain non-String SharedPreferences values.
old='''        String raw=getSharedPreferences("paper_portfolio",MODE_PRIVATE).getString(symbol,null); if(raw==null) return "Henüz Fake pozisyon yok";
        try{String[] z=raw.split("\\\\|"); double buy=Double.parseDouble(z[0]); int qty=Integer.parseInt(z[1]); long at=Long.parseLong(z[2]);'''
new='''        Object rawObj=getSharedPreferences("paper_portfolio",MODE_PRIVATE).getAll().get(symbol); if(rawObj==null) return "Henüz Fake pozisyon yok";
        try{String raw=String.valueOf(rawObj); String[] z=raw.split("\\\\|"); if(z.length<3)return "Fake portföy kaydı okunamadı"; double buy=Double.parseDouble(z[0]); int qty=Integer.parseInt(z[1]); long at=Long.parseLong(z[2]); if(!Double.isFinite(buy)||buy<=0||qty<=0)return "Fake portföy kaydı okunamadı";'''
if old in s:s=s.replace(old,new,1)
# v90 percentage reader: tolerate legacy preference types too.
s=s.replace('''try{String rr=getSharedPreferences("paper_portfolio",MODE_PRIVATE).getString(symbol,null); if(rr!=null){String[] pp=rr.split("\\\\|");''','''try{Object ro=getSharedPreferences("paper_portfolio",MODE_PRIVATE).getAll().get(symbol); String rr=ro==null?null:String.valueOf(ro); if(rr!=null){String[] pp=rr.split("\\\\|");''')
# Make the detail portfolio section unambiguous: real and fake are separate stores/actions.
s=s.replace('''collapsible("🧪 Portföy / Fake Portföy",pfBody,false)''','''collapsible("📁 Gerçek Portföy + 🧪 Fake Portföy (ayrı)",pfBody,false)''')
# Avoid an endless-looking fast screen message when deep detail is delayed.
s=s.replace('''"Son fiyat hemen gösterildi • Derin teknik analiz aşağıda tamamlanacak"''','''"Güncel fiyat/grafik • Detay hazırlanırken ekran kullanılabilir"''')
p.write_text(s,encoding='utf-8')
