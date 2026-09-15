from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/PriceChartView.java')
s=p.read_text(encoding='utf-8')
old='private final String label;'
new='private final String label;\n    private double tradeEntry=Double.NaN,tradeTarget1=Double.NaN,tradeTarget2=Double.NaN,tradeTarget3=Double.NaN,tradeStop=Double.NaN;'
if old in s and 'tradeTarget1' not in s:s=s.replace(old,new,1)
anchor='    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}'
method='''    public PriceChartView setTradeLevels(double entry,double target1,double target2,double stop){
        tradeEntry=entry;tradeTarget1=target1;tradeTarget2=target2;tradeStop=stop;
        tradeTarget3=Double.isFinite(target2)&&Double.isFinite(target1)?target2+(target2-target1):Double.NaN;
        invalidate();return this;
    }
    private void drawTradeLevels(Canvas canvas,float left,float right,double min,double max,float top,float bottom,String symbol){
        double[] v={tradeTarget1,tradeTarget2,tradeTarget3,tradeStop};String[] n={"H1","H2","H3","STOP"};
        int[] col={Color.rgb(46,204,113),Color.rgb(38,198,218),Color.rgb(255,193,7),Color.rgb(235,65,85)};
        paint.setTextSize(dp(10));paint.setStrokeWidth(dp(1));
        for(int i=0;i<v.length;i++){if(!Double.isFinite(v[i])||v[i]<min||v[i]>max)continue;float yy=y(v[i],min,max,top,bottom);paint.setColor(col[i]);paint.setStyle(Paint.Style.STROKE);canvas.drawLine(left,yy,right,yy,paint);paint.setStyle(Paint.Style.FILL);String t=n[i]+" "+fmt(displayValue(v[i],symbol))+" "+currencySymbol(symbol);canvas.drawText(t,left+dp(4),yy-dp(3),paint);}
    }
'''
if anchor in s and 'private void drawTradeLevels' not in s:s=s.replace(anchor,anchor+'\n'+method,1)
old='drawSupportResistance(canvas,start,count,left,right,min,max,top,priceBottom);'
if old in s and 'drawTradeLevels(canvas' not in s:s=s.replace(old,old+'drawTradeLevels(canvas,left,right,min,max,top,priceBottom,symbol);',1)
p.write_text(s,encoding='utf-8')

m=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
x=m.read_text(encoding='utf-8')
# Attach calculated short-term levels to every stock detail PriceChartView creation that uses chart data.
old='PriceChartView chartView=new PriceChartView(this,chart,ChartTimeframes.LABELS[tf]);'
new='PriceChartView chartView=new PriceChartView(this,chart,ChartTimeframes.LABELS[tf]); ShortTermTargetEngine.Target chartTarget=ShortTermTargetEngine.calculate(chart,ChartTimeframes.INTERVAL[tf]); if(chartTarget!=null)chartView.setTradeLevels(chartTarget.entry,chartTarget.target1,chartTarget.target2,chartTarget.stop);'
if old in x:x=x.replace(old,new)
m.write_text(x,encoding='utf-8')
