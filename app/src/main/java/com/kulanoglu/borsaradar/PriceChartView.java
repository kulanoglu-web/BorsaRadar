package com.kulanoglu.borsaradar;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;
import java.util.List;
import java.util.Locale;

public final class PriceChartView extends View {
    private final List<MarketDataService.Candle> data;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final String label;

    public PriceChartView(Context c,List<MarketDataService.Candle>d){this(c,d,"SON 10 İŞLEM GÜNÜ");}
    public PriceChartView(Context c,List<MarketDataService.Candle>d,String l){super(c);data=d;label=l;setMinimumHeight(dp(260));setBackgroundColor(Color.rgb(9,30,54));setPadding(dp(12),dp(18),dp(12),dp(18));}
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}

    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);
        if(data==null||data.size()<2)return;
        float left=getPaddingLeft()+dp(3),right=getWidth()-getPaddingRight()-dp(3),top=getPaddingTop()+dp(28),bottom=getHeight()-getPaddingBottom()-dp(28);
        double min=Double.MAX_VALUE,max=-Double.MAX_VALUE;
        for(MarketDataService.Candle c:data){min=Math.min(min,c.low);max=Math.max(max,c.high);}
        if(max<=min)max=min+1;
        paint.setStrokeWidth(dp(1));paint.setColor(Color.rgb(48,72,101));
        for(int i=0;i<=4;i++){float y=top+(bottom-top)*i/4f;canvas.drawLine(left,y,right,y,paint);}
        float step=(right-left)/Math.max(1,data.size()-1);
        for(int i=0;i<data.size();i++){
            MarketDataService.Candle c=data.get(i);float x=left+step*i;
            float yo=bottom-(float)((c.open-min)/(max-min))*(bottom-top),yc=bottom-(float)((c.close-min)/(max-min))*(bottom-top),yh=bottom-(float)((c.high-min)/(max-min))*(bottom-top),yl=bottom-(float)((c.low-min)/(max-min))*(bottom-top);
            paint.setColor(c.close>=c.open?Color.rgb(22,190,135):Color.rgb(235,65,85));paint.setStrokeWidth(dp(1));canvas.drawLine(x,yh,x,yl,paint);paint.setStrokeWidth(Math.max(dp(3),step*.48f));canvas.drawLine(x,yo,x,yc,paint);
        }
        paint.setTextSize(dp(12));paint.setColor(Color.WHITE);canvas.drawText(label,left,dp(24),paint);
        String last="Son "+fmt(data.get(data.size()-1).close)+" ₺";canvas.drawText(last,right-paint.measureText(last),dp(24),paint);
        String low="Düşük "+fmt(min),high="Yüksek "+fmt(max);canvas.drawText(low,left,getHeight()-dp(8),paint);canvas.drawText(high,right-paint.measureText(high),getHeight()-dp(8),paint);
    }
    private String fmt(double v){return String.format(Locale.US,"%.2f",v);}
}
