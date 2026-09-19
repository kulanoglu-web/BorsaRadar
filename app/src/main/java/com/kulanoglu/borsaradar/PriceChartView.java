package com.kulanoglu.borsaradar;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.View;
import android.view.MotionEvent;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public final class PriceChartView extends View {
    private final List<MarketDataService.Candle> data;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final String label;
    private int selectedIndex=-1;
    private float touchX=-1;
    public PriceChartView(Context c,List<MarketDataService.Candle>d){this(c,d,"1 GÜN");}
    public PriceChartView(Context c,List<MarketDataService.Candle>d,String l){super(c);data=d;label=l;setMinimumHeight(dp(350));setBackgroundColor(Color.rgb(9,30,54));setPadding(dp(12),dp(18),dp(12),dp(18));}
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onDraw(Canvas canvas){super.onDraw(canvas);if(data==null||data.size()<2)return;int start=0,count=data.size();String symbol=data.get(data.size()-1).symbol,cur=currencySymbol(symbol);float left=getPaddingLeft()+dp(3),right=getWidth()-getPaddingRight()-dp(55),top=getPaddingTop()+dp(30),priceBottom=getHeight()-getPaddingBottom()-dp(105),volTop=priceBottom+dp(12),volBottom=getHeight()-getPaddingBottom()-dp(48);double min=Double.MAX_VALUE,max=-Double.MAX_VALUE,maxVol=0;for(int i=start;i<data.size();i++){MarketDataService.Candle c=data.get(i);min=Math.min(min,c.low);max=Math.max(max,c.high);maxVol=Math.max(maxVol,c.volume);}if(max<=min)max=min+1;
        paint.setStrokeWidth(dp(1));paint.setTextSize(dp(10));paint.setColor(Color.rgb(48,72,101));for(int i=0;i<=4;i++){float yy=top+(priceBottom-top)*i/4f;canvas.drawLine(left,yy,right,yy,paint);double raw=max-(max-min)*i/4.0;String pv=fmt(displayValue(raw,symbol))+" "+cur;paint.setColor(Color.rgb(190,207,226));canvas.drawText(pv,right+dp(5),yy+dp(4),paint);paint.setColor(Color.rgb(48,72,101));}
        float slot=(right-left)/Math.max(1,count);float body=Math.max(dp(2),slot*.55f);for(int j=0;j<count;j++){MarketDataService.Candle c=data.get(start+j);float x=left+slot*(j+.5f);float yh=y(c.high,min,max,top,priceBottom),yl=y(c.low,min,max,top,priceBottom),yo=y(c.open,min,max,top,priceBottom),yc=y(c.close,min,max,top,priceBottom);int col=c.close>=c.open?Color.rgb(22,190,135):Color.rgb(235,65,85);paint.setColor(col);paint.setStrokeWidth(dp(1));canvas.drawLine(x,yh,x,yl,paint);paint.setStyle(Paint.Style.FILL);canvas.drawRect(x-body/2,Math.min(yo,yc),x+body/2,Math.max(Math.min(yo,yc)+dp(1),Math.max(yo,yc)),paint);if(maxVol>0){float vh=(float)(c.volume/maxVol)*(volBottom-volTop);paint.setColor(Color.argb(150,Color.red(col),Color.green(col),Color.blue(col)));canvas.drawRect(x-body/2,volBottom-vh,x+body/2,volBottom,paint);}}
        drawEma(canvas,5,start,count,left,right,min,max,top,priceBottom,Color.rgb(255,193,7));drawEma(canvas,9,start,count,left,right,min,max,top,priceBottom,Color.rgb(77,208,225));drawEma(canvas,20,start,count,left,right,min,max,top,priceBottom,Color.rgb(186,104,200));drawEma(canvas,50,start,count,left,right,min,max,top,priceBottom,Color.rgb(255,138,101));drawBollinger(canvas,20,start,count,left,right,min,max,top,priceBottom);drawVwap(canvas,start,count,left,right,min,max,top,priceBottom);drawSupportResistance(canvas,start,count,left,right,min,max,top,priceBottom);drawHighLowLabels(canvas,left,right,top,priceBottom,min,max,symbol,cur);
        paint.setTextSize(dp(11));paint.setColor(Color.WHITE);paint.setFakeBoldText(true);canvas.drawText(label+" • Mum/Hacim • EMA 5/9/20/50 • BB • VWAP",left,dp(24),paint);paint.setFakeBoldText(false);double last=data.get(data.size()-1).close;String latest="Son "+fmt(displayValue(last,symbol))+" "+cur;canvas.drawText(latest,right-paint.measureText(latest),dp(40),paint);
        drawLastPrice(canvas,left,right,top,priceBottom,min,max,symbol,cur);
        if(selectedIndex>=start && selectedIndex<data.size())drawCrosshair(canvas,left,right,top,volBottom,start,count,min,max,symbol,cur);
        drawTimeScale(canvas,left,right,volBottom,start,count);
    }
    @Override public boolean onTouchEvent(MotionEvent e){
        if(data==null||data.isEmpty())return false;
        if(e.getAction()==MotionEvent.ACTION_DOWN||e.getAction()==MotionEvent.ACTION_MOVE){
            touchX=e.getX();
            float left=getPaddingLeft()+dp(3),right=getWidth()-getPaddingRight()-dp(55);
            float slot=(right-left)/Math.max(1,data.size());
            selectedIndex=Math.max(0,Math.min(data.size()-1,(int)((touchX-left)/Math.max(1f,slot))));
            invalidate();return true;
        }
        if(e.getAction()==MotionEvent.ACTION_UP){performClick();return true;}
        return true;
    }
    @Override public boolean performClick(){super.performClick();return true;}
    private void drawLastPrice(Canvas canvas,float left,float right,float top,float bottom,double min,double max,String symbol,String cur){
        double last=data.get(data.size()-1).close;float yy=y(last,min,max,top,bottom);
        paint.setColor(Color.rgb(240,180,40));paint.setStrokeWidth(dp(1));canvas.drawLine(left,yy,right,yy,paint);
        paint.setTextSize(dp(10));String t=fmt(displayValue(last,symbol))+" "+cur;paint.setColor(Color.rgb(240,180,40));canvas.drawText(t,right+dp(4),yy-dp(3),paint);
    }
    private void drawCrosshair(Canvas canvas,float left,float right,float top,float volBottom,int start,int count,double min,double max,String symbol,String cur){
        MarketDataService.Candle c=data.get(selectedIndex);float slot=(right-left)/Math.max(1,count);float x=left+slot*((selectedIndex-start)+.5f);float yy=y(c.close,min,max,top,volBottom-dp(117));
        paint.setColor(Color.argb(180,210,220,230));paint.setStrokeWidth(dp(1));canvas.drawLine(x,top,x,volBottom,paint);canvas.drawLine(left,yy,right,yy,paint);
        paint.setTextSize(dp(10));paint.setColor(Color.WHITE);
        String info="O "+fmt(displayValue(c.open,symbol))+"  H "+fmt(displayValue(c.high,symbol))+"  L "+fmt(displayValue(c.low,symbol))+"  C "+fmt(displayValue(c.close,symbol))+" "+cur+"  Vol "+compact(c.volume);
        canvas.drawText(info,left,top-dp(8),paint);
        SimpleDateFormat sdf=new SimpleDateFormat("dd.MM.yy HH:mm",Locale.getDefault());String dt=sdf.format(new Date(c.time*1000L));float tw=paint.measureText(dt);canvas.drawText(dt,Math.max(left,Math.min(x-tw/2,right-tw)),getHeight()-dp(25),paint);
    }
    private String compact(double v){if(v>=1000000)return String.format(Locale.US,"%.1fM",v/1000000d);if(v>=1000)return String.format(Locale.US,"%.1fK",v/1000d);return String.format(Locale.US,"%.0f",v);}
    private void drawTimeScale(Canvas canvas,float left,float right,float volBottom,int start,int count){paint.setTextSize(dp(10));paint.setColor(Color.rgb(190,207,226));int ticks=Math.min(5,Math.max(2,count));long span=Math.max(0,data.get(data.size()-1).time-data.get(start).time);String pattern=span<=2*86400L?"HH:mm":span<=120*86400L?"dd.MM":"MM.yy";SimpleDateFormat sdf=new SimpleDateFormat(pattern,Locale.getDefault());for(int i=0;i<ticks;i++){int idx=start+Math.round((count-1)*i/(float)(ticks-1));float x=left+(right-left)*i/(float)(ticks-1);String t=sdf.format(new Date(data.get(idx).time*1000L));float tw=paint.measureText(t);if(i==0)canvas.drawText(t,x,getHeight()-dp(8),paint);else if(i==ticks-1)canvas.drawText(t,x-tw,getHeight()-dp(8),paint);else canvas.drawText(t,x-tw/2,getHeight()-dp(8),paint);paint.setColor(Color.rgb(36,58,82));canvas.drawLine(x,volBottom+dp(2),x,getHeight()-dp(23),paint);paint.setColor(Color.rgb(190,207,226));}}
    private void drawHighLowLabels(Canvas canvas,float left,float right,float top,float bottom,double min,double max,String symbol,String cur){paint.setTextSize(dp(10));paint.setColor(Color.rgb(210,220,232));String hi="Y "+fmt(displayValue(max,symbol))+" "+cur,lo="D "+fmt(displayValue(min,symbol))+" "+cur;canvas.drawText(hi,left,top+dp(11),paint);canvas.drawText(lo,left,bottom-dp(5),paint);}\n    private float y(double v,double min,double max,float top,float bottom){return bottom-(float)((v-min)/(max-min))*(bottom-top);}
    private void drawEma(Canvas canvas,int period,int start,int count,float left,float right,double min,double max,float top,float bottom,int color){if(count<period)return;double k=2.0/(period+1),e=data.get(start).close;Path p=new Path();float slot=(right-left)/Math.max(1,count);for(int j=0;j<count;j++){double c=data.get(start+j).close;e=j==0?c:c*k+e*(1-k);float x=left+slot*(j+.5f),yy=y(e,min,max,top,bottom);if(j==0)p.moveTo(x,yy);else p.lineTo(x,yy);}paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(dp(1));paint.setColor(color);canvas.drawPath(p,paint);paint.setStyle(Paint.Style.FILL);}
    private void drawBollinger(Canvas canvas,int period,int start,int count,float left,float right,double min,double max,float top,float bottom){if(count<period)return;Path up=new Path(),lo=new Path();float slot=(right-left)/Math.max(1,count);boolean begun=false;for(int j=period-1;j<count;j++){double sum=0,sq=0;for(int k=j-period+1;k<=j;k++){double v=data.get(start+k).close;sum+=v;sq+=v*v;}double mean=sum/period,sd=Math.sqrt(Math.max(0,sq/period-mean*mean));float x=left+slot*(j+.5f),yu=y(mean+2*sd,min,max,top,bottom),yl=y(mean-2*sd,min,max,top,bottom);if(!begun){up.moveTo(x,yu);lo.moveTo(x,yl);begun=true;}else{up.lineTo(x,yu);lo.lineTo(x,yl);}}paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(dp(1));paint.setColor(Color.rgb(120,144,156));canvas.drawPath(up,paint);canvas.drawPath(lo,paint);paint.setStyle(Paint.Style.FILL);}
    private void drawVwap(Canvas canvas,int start,int count,float left,float right,double min,double max,float top,float bottom){double pv=0,vol=0;Path p=new Path();float slot=(right-left)/Math.max(1,count);boolean begun=false;for(int j=0;j<count;j++){MarketDataService.Candle c=data.get(start+j);double v=Math.max(0,c.volume);if(v<=0)continue;pv+=((c.high+c.low+c.close)/3.0)*v;vol+=v;double vw=pv/vol;float x=left+slot*(j+.5f),yy=y(vw,min,max,top,bottom);if(!begun){p.moveTo(x,yy);begun=true;}else p.lineTo(x,yy);}if(!begun)return;paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(dp(1));paint.setColor(Color.rgb(38,198,218));canvas.drawPath(p,paint);paint.setStyle(Paint.Style.FILL);}
    private void drawSupportResistance(Canvas canvas,int start,int count,float left,float right,double min,double max,float top,float bottom){int n=Math.min(count,40);double support=Double.MAX_VALUE,resistance=-Double.MAX_VALUE;for(int j=count-n;j<count;j++){MarketDataService.Candle c=data.get(start+j);support=Math.min(support,c.low);resistance=Math.max(resistance,c.high);}paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(dp(1));paint.setColor(Color.rgb(46,204,113));canvas.drawLine(left,y(support,min,max,top,bottom),right,y(support,min,max,top,bottom),paint);paint.setColor(Color.rgb(255,99,71));canvas.drawLine(left,y(resistance,min,max,top,bottom),right,y(resistance,min,max,top,bottom),paint);paint.setStyle(Paint.Style.FILL);}
    private double displayValue(double v,String symbol){String n=MarketDataService.normalizeSymbol(symbol);if(n.endsWith(".IS")||n.endsWith(".DE"))return v;double rate=CurrencyService.usdToEur();return Double.isFinite(rate)?v*rate:v;}
    private String currencySymbol(String symbol){String n=MarketDataService.normalizeSymbol(symbol);return n.endsWith(".IS")?"₺":"€";}
    private String fmt(double v){return String.format(Locale.US,"%.2f",v);}
}
