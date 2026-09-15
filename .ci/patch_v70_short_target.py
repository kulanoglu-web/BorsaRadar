from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
needle='''        content.addView(decision); spacer(7);

        LinearLayout meters=card();'''
rep='''        content.addView(decision); spacer(7);

        // Short-term positions must have an explicit price target and time horizon.
        ShortTermTargetEngine.Target st=ShortTermTargetEngine.calculate(chart, ChartTimeframes.INTERVAL[Math.max(0,Math.min(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("chart_tf",3),ChartTimeframes.INTERVAL.length-1))]);
        if(st!=null){
            String cur=MarketSymbol.marketIndex(symbol)==0?"TL":"€";
            LinearLayout target=card(); target.addView(bold("Kısa Vade Hedef Planı",17,Color.WHITE));
            target.addView(txt(st.summary(cur),14,Color.DKGRAY));
            target.addView(txt("Hedef süresi dolarsa ve fiyat/hacim teyidi gelmezse pozisyon yeniden değerlendirilmeli; kısa vade uzun vadeye çevrilmemeli.",12,AMBER));
            content.addView(target); spacer(7);
        }

        LinearLayout meters=card();'''
if needle not in s: raise SystemExit('decision insertion point not found')
s=s.replace(needle,rep,1)
p.write_text(s,encoding='utf-8')
