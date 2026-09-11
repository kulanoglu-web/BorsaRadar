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
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final String label;

    public PriceChartView(Context c, List<MarketDataService.Candle> d) {
        this(c, d, "1 GÜN • SON 10 İŞLEM GÜNÜ");
    }

    public PriceChartView(Context c, List<MarketDataService.Candle> d, String l) {
        super(c);
        data = d;
        label = l;
        setMinimumHeight(dp(260));
        setBackgroundColor(Color.rgb(9, 30, 54));
        setPadding(dp(12), dp(18), dp(12), dp(18));
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (data == null || data.size() < 2) return;
        int start = Math.max(0, data.size() - 10);
        int count = data.size() - start;
        float left = getPaddingLeft() + dp(3);
        float right = getWidth() - getPaddingRight() - dp(3);
        float top = getPaddingTop() + dp(34);
        float bottom = getHeight() - getPaddingBottom() - dp(34);

        double min = Double.MAX_VALUE, max = -Double.MAX_VALUE;
        for (int i = start; i < data.size(); i++) {
            min = Math.min(min, data.get(i).close);
            max = Math.max(max, data.get(i).close);
        }
        if (max <= min) max = min + 1.0;

        paint.setStrokeWidth(dp(1));
        paint.setColor(Color.rgb(48, 72, 101));
        for (int i = 0; i <= 4; i++) {
            float y = top + (bottom - top) * i / 4f;
            canvas.drawLine(left, y, right, y, paint);
        }

        Path path = new Path();
        for (int j = 0; j < count; j++) {
            MarketDataService.Candle c = data.get(start + j);
            float x = left + (right - left) * j / Math.max(1f, count - 1f);
            float y = bottom - (float)((c.close - min) / (max - min)) * (bottom - top);
            if (j == 0) path.moveTo(x, y); else path.lineTo(x, y);
        }
        double first = data.get(start).close;
        double last = data.get(data.size() - 1).close;
        int lineColor = last >= first ? Color.rgb(22, 190, 135) : Color.rgb(235, 65, 85);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(dp(3));
        paint.setColor(lineColor);
        canvas.drawPath(path, paint);
        paint.setStyle(Paint.Style.FILL);

        for (int j = 0; j < count; j++) {
            MarketDataService.Candle c = data.get(start + j);
            float x = left + (right - left) * j / Math.max(1f, count - 1f);
            float y = bottom - (float)((c.close - min) / (max - min)) * (bottom - top);
            canvas.drawCircle(x, y, dp(2), paint);
        }

        paint.setTextSize(dp(12));
        paint.setColor(Color.WHITE);
        paint.setFakeBoldText(true);
        canvas.drawText("ZAMAN DİLİMİ: " + label, left, dp(24), paint);
        paint.setFakeBoldText(false);
        String latest = "Son " + fmt(last) + " ₺";
        canvas.drawText(latest, right - paint.measureText(latest), dp(24), paint);

        SimpleDateFormat sdf = new SimpleDateFormat("dd.MM", Locale.getDefault());
        String d1 = sdf.format(new Date(data.get(start).time * 1000L));
        String d2 = sdf.format(new Date(data.get(data.size() - 1).time * 1000L));
        paint.setTextSize(dp(11));
        paint.setColor(Color.rgb(190, 207, 226));
        canvas.drawText(d1, left, bottom + dp(20), paint);
        canvas.drawText(d2, right - paint.measureText(d2), bottom + dp(20), paint);

        paint.setColor(Color.WHITE);
        paint.setTextSize(dp(11));
        String low = "Düşük " + fmt(min);
        String high = "Yüksek " + fmt(max);
        canvas.drawText(low, left, getHeight() - dp(7), paint);
        canvas.drawText(high, right - paint.measureText(high), getHeight() - dp(7), paint);
    }

    private String fmt(double v) { return String.format(Locale.US, "%.2f", v); }
}
