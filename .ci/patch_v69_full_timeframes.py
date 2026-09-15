from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
old='''        LinearLayout tf1=new LinearLayout(this); tf1.setOrientation(LinearLayout.HORIZONTAL);
        String[] frames={"1S","4S","1G","1Hf","1Ay","3Ay","6Ay","1Y"};
        for(String x:frames){Button b=button(x,x.equals(frame)?RED:Color.rgb(49,55,63)); b.setTextSize(12); tf1.addView(b,new LinearLayout.LayoutParams(0,-2,1)); b.setOnClickListener(v->loadFullChartFrame(symbol,a,x));}
        content.addView(tf1); spacer(5);
'''
new='''        LinearLayout tf1=new LinearLayout(this); tf1.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout tf2=new LinearLayout(this); tf2.setOrientation(LinearLayout.HORIZONTAL);
        String[] frames=ChartTimeframes.LABELS;
        for(int i=0;i<frames.length;i++){String x=frames[i]; Button b=button(x,x.equals(frame)?RED:Color.rgb(49,55,63)); b.setTextSize(10); (i<6?tf1:tf2).addView(b,new LinearLayout.LayoutParams(0,-2,1)); final int idx=i; b.setOnClickListener(v->{getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("chart_tf",idx).apply();loadFullChartFrame(symbol,a,idx);});}
        content.addView(tf1); content.addView(tf2); spacer(5);
'''
if old not in s: raise SystemExit('timeframe button block not found')
s=s.replace(old,new,1)
pat=r'''    private void loadFullChartFrame\(String symbol,FullAnalysisEngine\.Result a,String frame\)\{.*?\n    \}\n'''
rep='''    private void loadFullChartFrame(String symbol,FullAnalysisEngine.Result a,int index){
        final int idx=Math.max(0,Math.min(index,ChartTimeframes.LABELS.length-1));
        final String frame=ChartTimeframes.LABELS[idx];
        shell(symbol+" • "+frame+" yükleniyor");
        ProgressBar p=new ProgressBar(this); content.addView(p); content.addView(txt("Grafik verisi alınıyor…",14,Color.GRAY));
        io.execute(()->{try{final List<MarketDataService.Candle> out=DetailedChartController.fetch(symbol,idx);main.post(()->renderStockDetail(symbol,a,out,frame));}
        catch(Exception e){main.post(()->{shell(symbol+" • "+frame);content.addView(txt("Grafik verisi alınamadı: "+e.getMessage(),15,RED));});}});
    }
'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('loadFullChartFrame block not found')
# Initial detail keeps fast preview, but label follows saved choice only after user explicitly loads it.
p.write_text(s,encoding='utf-8')
