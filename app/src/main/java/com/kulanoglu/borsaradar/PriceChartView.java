package com.kulanoglu.borsaradar;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.View;

import java.util.List;
import java.util.Locale;

public final class PriceChartView extends View {
    private final List<MarketDataService.Candle> data;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);

    public PriceChartView(Context context, List<MarketDataService.Candle> data) {
        super(context);
        this.data = data;
        setMinimumHeight(dp(280));
        setBackgroundColor(Color.rgb(11, 31, 58));
        setPadding(dp(12), dp(18), dp(12), dp(18));
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (data == null || data.size() < 2) return;
        float left = getPaddingLeft() + dp(4);
        float right = getWidth() - getPaddingRight() - dp(4);
        float top = getPaddingTop() + dp(28);
        float bottom = getHeight() - getPaddingBottom() - dp(30);
        double min = Double.MAX_VALUE, max = -Double.MAX_VALUE;
        for (MarketDataService.Candle candle : data) {
            min = Math.min(min, candle.close);
            max = Math.max(max, candle.close);
        }
        if (max <= min) max = min + 1.0;
        paint.setStrokeWidth(dp(1));
        paint.setColor(Color.rgb(55, 76, 105));
        for (int i = 0; i <= 4; i++) {
            float y = top + (bottom - top) * i / 4f;
            canvas.drawLine(left, y, right, y, paint);
        }
        Path path = new Path();
        for (int i = 0; i < data.size(); i++) {
            float x = left + (right - left) * i / (data.size() - 1f);
            float y = bottom - (float) ((data.get(i).close - min) / (max - min)) * (bottom - top);
            if (i == 0) path.moveTo(x, y); else path.lineTo(x, y);
        }
        double first = data.get(0).close;
        double last = data.get(data.size() - 1).close;
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(dp(3));
        paint.setColor(last >= first ? Color.rgb(22, 190, 135) : Color.rgb(235, 65, 85));
        canvas.drawPath(path, paint);
        paint.setStyle(Paint.Style.FILL);
        paint.setTextSize(dp(13));
        paint.setColor(Color.WHITE);
        canvas.drawText("1 YILLIK FİYAT GRAFİĞİ", left, dp(24), paint);
        canvas.drawText("En yüksek: " + fmt(max) + " ₺", left, getHeight() - dp(10), paint);
        String low = "En düşük: " + fmt(min) + " ₺";
        canvas.drawText(low, right - paint.measureText(low), getHeight() - dp(10), paint);
        String latest = "Son: " + fmt(last) + " ₺";
        canvas.drawText(latest, right - paint.measureText(latest), dp(24), paint);
    }

    private String fmt(double value) {
        return String.format(Locale.US, "%.2f", value);
    }
}

