package com.kulanoglu.borsaradar;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.content.Context;
import android.graphics.Color;
import android.text.InputType;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Space;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final String PREFS = "portfolio";
    private static final String[] BIST = {
            "ADEL","AEFES","AGHOL","AKBNK","AKCNS","AKSA","AKSEN","ALARK","ALBRK","ALFAS",
            "ARCLK","ASELS","ASTOR","BERA","BIMAS","BRSAN","BRYAT","BTCIM","CANTE","CCOLA",
            "CIMSA","DOAS","DOHOL","ECILC","EGEEN","EKGYO","ENJSA","ENKAI","EREGL","EUPWR",
            "FROTO","GARAN","GESAN","GUBRF","GWIND","HALKB","HEKTS","ISCTR","ISMEN","KARSN",
            "KCHOL","KONTR","KONYA","KOZAA","KOZAL","KRDMD","KLRHO","MAVI","MGROS","MIATK",
            "ODAS","OTKAR","OYAKC","PETKM","PGSUS","QUAGR","SAHOL","SASA","SISE","SKBNK",
            "SMRTG","SOKM","TAVHL","TCELL","THYAO","TKFEN","TOASO","TSKB","TTKOM","TTRAK",
            "ULKER","VAKBN","VESTL","YEOTK","YKBNK","ZOREN","AAGYO","ANSGR","BRSAN",
            "CWENE","DEVA","DOCO","ECZYT","GENIL","IPEKE","KCAER","KMPUR","MPARK","NTHOL",
            "PASEU","REEDR","TABGD","TATGD","TMSN","TURSG","VESBE","AKFGY","AKFYE","ALARK"
    };

    private final List<Holding> holdings = new ArrayList<>();
    private final Map<String, IndicatorEngine.Snapshot> latest = new HashMap<>();
    private LinearLayout content;
    private final ExecutorService io = Executors.newFixedThreadPool(4);
    private final Handler main = new Handler(Looper.getMainLooper());

    static class Holding {
        String symbol;
        int qty;
        double cost;
        Holding(String s, int q, double c) { symbol = s; qty = q; cost = c; }
    }

    static class Ranked {
        String symbol;
        IndicatorEngine.Snapshot s;
        BacktestEngine.Result bt;
        Ranked(String symbol, IndicatorEngine.Snapshot s, BacktestEngine.Result bt) { this.symbol=symbol; this.s=s; this.bt=bt; }
    }

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        load();
        showPortfolio();
    }

    @Override protected void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }

    private TextView title(String t, int sp) {
        TextView v = new TextView(this);
        v.setText(t);
        v.setTextSize(sp);
        v.setTextColor(Color.rgb(20, 28, 38));
        v.setPadding(24, 14, 24, 10);
        return v;
    }

    private Button btn(String t) {
        Button b = new Button(this);
        b.setText(t);
        return b;
    }

    private void shell(String page) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(14, 14, 14, 14);

        LinearLayout nav = new LinearLayout(this);
        nav.setOrientation(LinearLayout.HORIZONTAL);
        Button p = btn("Portföyüm"), r = btn("BIST Radar"), a = btn("3 Strateji");
        nav.addView(p, new LinearLayout.LayoutParams(0, -2, 1));
        nav.addView(r, new LinearLayout.LayoutParams(0, -2, 1));
        nav.addView(a, new LinearLayout.LayoutParams(0, -2, 1));
        p.setOnClickListener(v -> showPortfolio());
        r.setOnClickListener(v -> showRadar());
        a.setOnClickListener(v -> showStrategies());
        root.addView(nav);
        root.addView(title("BorsaRadar • " + page, 24));

        ScrollView s = new ScrollView(this);
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        s.addView(content);
        root.addView(s, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
    }

    private void showPortfolio() {
        shell("Portföyüm");
        content.addView(title("Elindeki hisseleri burada ayrı tut. TUPRS portföyde değerlendirilir, bağımsız radar taramasına alınmaz.", 15));
        LinearLayout actions = new LinearLayout(this);
        Button add = btn("+ Hisse Ekle");
        Button refresh = btn("Fiyatları / Sinyalleri Yenile");
        actions.addView(add, new LinearLayout.LayoutParams(0, -2, 1));
        actions.addView(refresh, new LinearLayout.LayoutParams(0, -2, 1));
        content.addView(actions);
        add.setOnClickListener(v -> portfolioDialog(null));
        refresh.setOnClickListener(v -> refreshPortfolio());

        if (holdings.isEmpty()) content.addView(title("Henüz portföy girişi yok.", 16));
        for (Holding h : new ArrayList<>(holdings)) renderHolding(h);
    }

    private void renderHolding(Holding h) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.VERTICAL);
        row.setPadding(18, 12, 18, 12);
        row.setBackgroundColor(Color.rgb(244, 247, 250));
        row.addView(title(h.symbol + " • " + h.qty + " lot • Ort. " + money(h.cost), 18));

        IndicatorEngine.Snapshot s = latest.get(h.symbol);
        if (s == null) {
            row.addView(title("Canlı/gecikmeli veri henüz alınmadı.", 14));
        } else {
            double pnl = (s.close - h.cost) * h.qty;
            double pnlPct = h.cost == 0 ? 0 : (s.close / h.cost - 1.0) * 100.0;
            row.addView(title("Son: " + money(s.close) + " • P/L: " + money(pnl) + " (%" + IndicatorEngine.fmt(pnlPct) + ")", 15));
            row.addView(title("Sinyal: " + s.signal + " • " + s.reason, 14));
            row.addView(title("ATR stop referansı: " + money(Math.max(s.close - 2.2 * s.atr14, s.ema50 * 0.985)), 13));
        }

        LinearLayout buttons = new LinearLayout(this);
        Button edit = btn("Düzenle"), bt = btn("1Y Backtest"), del = btn("Sil");
        buttons.addView(edit, new LinearLayout.LayoutParams(0, -2, 1));
        buttons.addView(bt, new LinearLayout.LayoutParams(0, -2, 1));
        buttons.addView(del, new LinearLayout.LayoutParams(0, -2, 1));
        row.addView(buttons);
        edit.setOnClickListener(v -> portfolioDialog(h));
        bt.setOnClickListener(v -> runSingleBacktest(h.symbol));
        del.setOnClickListener(v -> { holdings.remove(h); save(); showPortfolio(); });
        content.addView(row);
        Space sp = new Space(this);
        content.addView(sp, new LinearLayout.LayoutParams(1, 10));
    }

    private void refreshPortfolio() {
        if (holdings.isEmpty()) { Toast.makeText(this, "Önce portföye hisse ekle", Toast.LENGTH_SHORT).show(); return; }
        shell("Portföy Güncelleniyor");
        ProgressBar bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(holdings.size());
        content.addView(bar);
        TextView status = title("Veri alınıyor...", 16);
        content.addView(status);

        final int[] done = {0};
        for (Holding h : new ArrayList<>(holdings)) {
            io.execute(() -> {
                try {
                    List<MarketDataService.Candle> data = MarketDataService.fetchDaily(h.symbol, "6mo");
                    IndicatorEngine.Snapshot s = IndicatorEngine.analyze(data);
                    synchronized (latest) { latest.put(h.symbol, s); }
                } catch (Exception ignored) { }
                main.post(() -> {
                    done[0]++;
                    bar.setProgress(done[0]);
                    status.setText(done[0] + "/" + holdings.size() + " tamamlandı");
                    if (done[0] >= holdings.size()) showPortfolio();
                });
            });
        }
    }

    private void portfolioDialog(Holding edit) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(24, 10, 24, 0);
        Spinner s = new Spinner(this);
        s.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, BIST));
        EditText q = new EditText(this);
        q.setHint("Lot / adet");
        q.setInputType(InputType.TYPE_CLASS_NUMBER);
        EditText c = new EditText(this);
        c.setHint("Ortalama alış fiyatı (örn. 287,87)");
        c.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        if (edit != null) {
            int idx = Arrays.asList(BIST).indexOf(edit.symbol);
            if (idx >= 0) s.setSelection(idx);
            q.setText(String.valueOf(edit.qty));
            c.setText(String.valueOf(edit.cost));
        }
        box.addView(s); box.addView(q); box.addView(c);
        new AlertDialog.Builder(this)
                .setTitle(edit == null ? "Portföye ekle" : "Pozisyonu düzenle")
                .setView(box)
                .setPositiveButton("Kaydet", (d, w) -> {
                    try {
                        String sym = (String) s.getSelectedItem();
                        int qty = Integer.parseInt(q.getText().toString());
                        String rawCost = c.getText().toString().trim();
                        double cost = Double.parseDouble(rawCost.replace(',', '.'));
                        // Bazı Android sayısal klavyeleri virgül tuşunu metne eklemeden
                        // kuruşları bitişik yazabiliyor: 28787 -> 287,87.
                        if (!rawCost.contains(",") && !rawCost.contains(".") && cost >= 10000) cost /= 100.0;
                        if (qty <= 0 || cost <= 0) throw new IllegalArgumentException();
                        if (edit == null) holdings.add(new Holding(sym, qty, cost));
                        else { edit.symbol = sym; edit.qty = qty; edit.cost = cost; }
                        save(); showPortfolio();
                    } catch (Exception ex) {
                        Toast.makeText(this, "Lot ve fiyatı kontrol et", Toast.LENGTH_LONG).show();
                    }
                })
                .setNegativeButton("İptal", null)
                .show();
    }

    private void showRadar() {
        shell("BIST Radar");
        content.addView(title("Radar portföyden bağımsız çalışır. Günlük Yahoo Finance verisini anahtarsız çeker; veri gecikmeli olabilir.", 15));
        content.addView(title("Skor: EMA20/50 + RSI14 + MACD + RVOL + CMF + Bollinger + breakout + trap + ATR", 14));
        Button scan = btn("BIST100 Radarını Tara");
        content.addView(scan);
        scan.setOnClickListener(v -> scanRadar());
    }

    private void scanRadar() {
        shell("BIST100 Taranıyor");
        ProgressBar bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(BIST.length);
        content.addView(bar);
        TextView status = title("0/" + BIST.length + " • veri alınıyor", 16);
        content.addView(status);

        final List<Ranked> results = Collections.synchronizedList(new ArrayList<>());
        final int[] done = {0};
        for (String sym : BIST) {
            io.execute(() -> {
                try {
                    List<MarketDataService.Candle> data = MarketDataService.fetchDaily(sym, "1y");
                    IndicatorEngine.Snapshot s = IndicatorEngine.analyze(data);
                    BacktestEngine.Result bt = BacktestEngine.run(data);
                    results.add(new Ranked(sym, s, bt));
                } catch (Exception ignored) { }
                main.post(() -> {
                    done[0]++;
                    bar.setProgress(done[0]);
                    status.setText(done[0] + "/" + BIST.length + " • başarılı " + results.size());
                    if (done[0] >= BIST.length) renderRadarResults(results);
                });
            });
        }
    }

    private void renderRadarResults(List<Ranked> results) {
        shell("Radar Sonuçları");
        List<Ranked> copy = new ArrayList<>(results);
        copy.sort((a, b) -> {
            int s = Integer.compare(b.s.score, a.s.score);
            if (s != 0) return s;
            return Double.compare(b.bt.netPct, a.bt.netPct);
        });
        content.addView(title("En güçlü teknik skorlar • backtest sonucu geçmiş performanstır, garanti değildir.", 14));
        if (copy.isEmpty()) { content.addView(title("Veri alınamadı. İnternet bağlantısı veya veri kaynağı geçici olarak engellemiş olabilir.", 16)); return; }

        int limit = Math.min(30, copy.size());
        for (int i = 0; i < limit; i++) {
            Ranked r = copy.get(i);
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setPadding(18, 10, 18, 10);
            card.setBackgroundColor(Color.rgb(244,247,250));
            card.addView(title((i + 1) + ". " + r.symbol + " • " + r.s.signal + " • skor " + r.s.score, 18));
            card.addView(title("Fiyat " + money(r.s.close) + " • " + r.s.reason, 14));
            card.addView(title("1Y backtest: " + r.bt.summary, 13));
            Button bt = btn("Detaylı backtest yenile");
            card.addView(bt);
            bt.setOnClickListener(v -> runSingleBacktest(r.symbol));
            content.addView(card);
            Space sp = new Space(this);
            content.addView(sp, new LinearLayout.LayoutParams(1, 8));
        }
    }

    private void runSingleBacktest(String symbol) {
        shell(symbol + " Backtest");
        ProgressBar p = new ProgressBar(this);
        content.addView(p);
        TextView t = title("1 yıllık günlük veri indiriliyor ve strateji geriye dönük çalıştırılıyor...", 16);
        content.addView(t);
        io.execute(() -> {
            try {
                List<MarketDataService.Candle> data = MarketDataService.fetchDaily(symbol, "1y");
                IndicatorEngine.Snapshot s = IndicatorEngine.analyze(data);
                BacktestEngine.Result r = BacktestEngine.run(data);
                main.post(() -> {
                    shell(symbol + " Backtest Sonucu");
                    content.addView(title("Güncel teknik sinyal: " + s.signal + " • skor " + s.score, 18));
                    content.addView(title(r.summary, 17));
                    content.addView(title("Mantık: güçlü AL/ERKEN sinyaliyle giriş; ATR + EMA50 tabanlı ilk stop; ATR trailing ve trend/MACD bozulmasında çıkış.", 14));
                    content.addView(title("Not: komisyon, kayma, vergi ve gün içi gerçekleşme farkları dahil değildir. Sonuç yatırım garantisi değildir.", 13));
                });
            } catch (Exception e) {
                main.post(() -> {
                    shell(symbol + " Backtest");
                    content.addView(title("Veri alınamadı: " + e.getMessage(), 16));
                });
            }
        });
    }

    private void showStrategies() {
        shell("100.000 TL • 3 Strateji");
        content.addView(title("Kısa vade / al-sat: 33.333 TL", 18));
        content.addView(title("• Radar skoru ≥ 7 öncelik • ATR stop • tek pozisyonda sermayenin tamamı kullanılmaz.", 14));
        content.addView(title("Temettü: 33.333 TL", 18));
        content.addView(title("• Bu sürümde teknik trend filtresi aktif. Temettü verimi/bilanço verisi sonraki temel analiz modülüne ayrıldı.", 14));
        content.addView(title("Uzun vade: 33.334 TL", 18));
        content.addView(title("• EMA50 üstü trend, para akışı ve geri çekilme disiplini öncelikli.", 14));
        content.addView(title("Radar sinyalleri karar desteğidir; otomatik alım-satım emri göndermez.", 13));
    }

    private String money(double x) {
        return String.format(Locale.US, "%.2f ₺", x);
    }

    private void save() {
        JSONArray a = new JSONArray();
        try {
            for (Holding h : holdings) {
                JSONObject o = new JSONObject();
                o.put("s", h.symbol); o.put("q", h.qty); o.put("c", h.cost); a.put(o);
            }
        } catch (Exception ignored) { }
        getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString("items", a.toString()).apply();
    }

    private void load() {
        holdings.clear();
        String x = getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("items", "[]");
        try {
            JSONArray a = new JSONArray(x);
            for (int i = 0; i < a.length(); i++) {
                JSONObject o = a.getJSONObject(i);
                double savedCost = o.getDouble("c");
                // v0.9.0'da virgülsüz kaydedilmiş olası fiyatları bir kez düzelt.
                if (savedCost >= 10000) savedCost /= 100.0;
                holdings.add(new Holding(o.getString("s"), o.getInt("q"), savedCost));
            }
        } catch (Exception ignored) { }
    }
}
