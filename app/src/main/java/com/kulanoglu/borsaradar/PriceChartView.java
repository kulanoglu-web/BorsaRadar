package com.kulanoglu.borsaradar;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.View;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public final class PriceChartView extends View {
    private final List<MarketDataService.Candle> data;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final String label;
    public PriceChartView(Context c,List<MarketDataService.Candle>d){this(c,d,"1 GÜN");}
    public PriceChartView(Context c,List<MarketDataService.Candle>d,String l){super(c);data=d;label=l;setMinimumHeight(dp(330));setBackgroundColor(Color.rgb(9,30,54));setPadding(dp(12),dp(18),dp(12),dp(18));}
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onDraw(Canvas canvas){super.onDraw(canvas);if(data==null||data.size()<2)return;int start=0,count=data.size();float left=getPaddingLeft()+dp(3),right=getWidth()-getPaddingRight()-dp(3),top=getPaddingTop()+dp(30),priceBottom=getHeight()-getPaddingBottom()-dp(92),volTop=priceBottom+dp(12),volBottom=getHeight()-getPaddingBottom()-dp(35);double min=Double.MAX_VALUE,max=-Double.MAX_VALUE,maxVol=0;for(int i=start;i<data.size();i++){MarketDataService.Candle c=data.get(i);min=Math.min(min,c.low);max=Math.max(max,c.high);maxVol=Math.max(maxVol,c.volume);}if(max<=min)max=min+1;
        paint.setStrokeWidth(dp(1));paint.setColor(Color.rgb(48,72,101));for(int i=0;i<=4;i++){float y=top+(priceBottom-top)*i/4f;canvas.drawLine(left,y,right,y,paint);}
        float slot=(right-left)/Math.max(1,count);float body=Math.max(dp(2),slot*.55f);for(int j=0;j<count;j++){MarketDataService.Candle c=data.get(start+j);float x=left+slot*(j+.5f);float yh=y(c.high,min,max,top,priceBottom),yl=y(c.low,min,max,top,priceBottom),yo=y(c.open,min,max,top,priceBottom),yc=y(c.close,min,max,top,priceBottom);int col=c.close>=c.open?Color.rgb(22,190,135):Color.rgb(235,65,85);paint.setColor(col);paint.setStrokeWidth(dp(1));canvas.drawLine(x,yh,x,yl,paint);paint.setStyle(Paint.Style.FILL);canvas.drawRect(x-body/2,Math.min(yo,yc),x+body/2,Math.max(Math.min(yo,yc)+dp(1),Math.max(yo,yc)),paint);if(maxVol>0){float vh=(float)(c.volume/maxVol)*(volBottom-volTop);paint.setColor(Color.argb(150,Color.red(col),Color.green(col),Color.blue(col)));canvas.drawRect(x-body/2,volBottom-vh,x+body/2,volBottom,paint);}}
        drawEma(canvas,5,start,count,left,right,min,max,top,priceBottom,Color.rgb(255,193,7));drawEma(canvas,9,start,count,left,right,min,max,top,priceBottom,Color.rgb(77,208,225));drawEma(canvas,20,start,count,left,right,min,max,top,priceBottom,Color.rgb(186,104,200));
        paint.setTextSize(dp(12));paint.setColor(Color.WHITE);paint.setFakeBoldText(true);canvas.drawText(label+"  •  Mum + Hacim + EMA 5/9/20",left,dp(24),paint);paint.setFakeBoldText(false);String symbol=data.get(data.size()-1).symbol,cur=currencySymbol(symbol);double last=data.get(data.size()-1).close;String latest="Son "+fmt(displayValue(last,symbol))+" "+cur;canvas.drawText(latest,right-paint.measureText(latest),dp(24),paint);SimpleDateFormat sdf=new SimpleDateFormat("dd.MM",Locale.getDefault());paint.setTextSize(dp(11));paint.setColor(Color.rgb(190,207,226));String d1=sdf.format(new Date(data.get(start).time*1000L)),d2=sdf.format(new Date(data.get(data.size()-1).time*1000L));canvas.drawText(d1,left,getHeight()-dp(8),paint);canvas.drawText(d2,right-paint.measureText(d2),getHeight()-dp(8),paint);
    }
    private float y(double v,double min,double max,float top,float bottom){return bottom-(float)((v-min)/(max-min))*(bottom-top);}
    private void drawEma(Canvas canvas,int period,int start,int count,float left,float right,double min,double max,float top,float bottom,int color){if(count<period)return;double k=2.0/(period+1),e=data.get(start).close;Path p=new Path();float slot=(right-left)/Math.max(1,count);for(int j=0;j<count;j++){double c=data.get(start+j).close;e=j==0?c:c*k+e*(1-k);float x=left+slot*(j+.5f),yy=y(e,min,max,top,bottom);if(j==0)p.moveTo(x,yy);else p.lineTo(x,yy);}paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(dp(1));paint.setColor(color);canvas.drawPath(p,paint);paint.setStyle(Paint.Style.FILL);}
    private double displayValue(double v,String symbol){String n=MarketDataService.normalizeSymbol(symbol);if(n.endsWith(".IS")||n.endsWith(".DE"))return v;double rate=CurrencyService.usdToEur();return Double.isFinite(rate)?v*rate:v;}
    private String currencySymbol(String symbol){String n=MarketDataService.normalizeSymbol(symbol);return n.endsWith(".IS")?"₺":"€";}
    private String fmt(double v){return String.format(Locale.US,"%.2f",v);}
}
