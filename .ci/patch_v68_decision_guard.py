from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

old='''        LinearLayout action=new LinearLayout(this); action.setOrientation(LinearLayout.HORIZONTAL);
        String rec=r.recommendation==null?"BEKLE":r.recommendation;
        int recColor=rec.contains("SAT")||rec.contains("RİSK")?RED:rec.contains("AL")?GREEN:AMBER;
        Button signal=button(rec,recColor); signal.setTextSize(19);
        Button add=button("Portföye Ekle",Color.rgb(49,55,63)); add.setTextSize(15);
        action.addView(signal,new LinearLayout.LayoutParams(0,dp(58),1.15f)); action.addView(add,new LinearLayout.LayoutParams(0,dp(58),1));
        content.addView(action); add.setOnClickListener(v->portfolioDialog(null,symbol)); spacer(7);

        LinearLayout decision=card(); decision.addView(bold("Karar Özeti",18,Color.WHITE));
        decision.addView(bold(a.decision.state,18,a.decision.caution?AMBER:recColor));
        decision.addView(txt(a.decision.note,14,Color.DKGRAY));
'''
new='''        LinearLayout action=new LinearLayout(this); action.setOrientation(LinearLayout.HORIZONTAL);
        String rawRec=r.recommendation==null?"BEKLE":r.recommendation;
        double frameLow=Double.POSITIVE_INFINITY,frameHigh=Double.NEGATIVE_INFINITY;
        for(MarketDataService.Candle c:chart){frameLow=Math.min(frameLow,c.low);frameHigh=Math.max(frameHigh,c.high);}
        double supportDistance=(Double.isFinite(frameLow)&&r.price>0)?((r.price-frameLow)/r.price*100.0):99.0;
        boolean nearSupport=supportDistance<=3.5;
        boolean sellLike=rawRec.contains("SAT")||rawRec.contains("RİSK");
        boolean unconfirmed=a.decision!=null&&a.decision.caution;
        String rec=rawRec;
        String guardNote="";
        if(sellLike&&(nearSupport||unconfirmed)){
            rec=nearSupport?"BEKLE • DÖNÜŞ TEYİDİ":"RİSK ARTTI • TEYİT BEKLE";
            if(nearSupport) guardNote="Fiyat seçili zaman dilimindeki desteğe yaklaşık %"+fmt(Math.max(0,supportDistance))+" mesafede. Destek kırılmadan satış sinyali kesinleştirilmedi.";
            else guardNote="Teknik zayıflık var; ancak haber/bağlam veya çoklu sinyal teyidi yetersiz olduğu için doğrudan SAT yerine teyit bekleniyor.";
        }
        int recColor=rec.contains("SAT")?RED:rec.contains("AL")?GREEN:AMBER;
        Button signal=button(rec,recColor); signal.setTextSize(17);
        Button add=button("Portföye Ekle",Color.rgb(49,55,63)); add.setTextSize(15);
        action.addView(signal,new LinearLayout.LayoutParams(0,dp(58),1.25f)); action.addView(add,new LinearLayout.LayoutParams(0,dp(58),1));
        content.addView(action); add.setOnClickListener(v->portfolioDialog(null,symbol)); spacer(7);

        LinearLayout decision=card(); decision.addView(bold("Karar Özeti",18,Color.WHITE));
        decision.addView(bold(a.decision.state,18,a.decision.caution?AMBER:recColor));
        if(!guardNote.isEmpty()) decision.addView(txt(guardNote,14,AMBER));
        decision.addView(txt(a.decision.note,14,Color.DKGRAY));
'''
if old not in s:
    raise SystemExit('decision action block not found')
s=s.replace(old,new,1)

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 57',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.9'",g)
b.write_text(g,encoding='utf-8')
p.write_text(s,encoding='utf-8')
