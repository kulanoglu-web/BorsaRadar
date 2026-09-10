package com.kulanoglu.borsaradar;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.content.Context;
import android.content.ClipboardManager;
import android.content.ClipData;
import android.graphics.Color;
import android.text.InputType;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Space;
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
    private static final int NAVY = Color.rgb(11, 31, 58);
    private static final int RED = Color.rgb(200, 16, 46);
    private static final int GREEN = Color.rgb(0, 128, 96);
    private static final String[] PORTFOLIO_SYMBOLS = BistUniverse.symbols(true);
    private static final String[] RADAR_SYMBOLS = BistUniverse.symbols(false);

    private final List<Holding> holdings = new ArrayList<>();
    private final Map<String, IndicatorEngine.Snapshot> latest = new HashMap<>();
    private final List<Ranked> lastRadarResults = new ArrayList<>();
    private LinearLayout content;
    private final ExecutorService io = Executors.newFixedThreadPool(3);
    private final Handler main = new Handler(Looper.getMainLooper());
    private String currentSection = "portfolio";
    private Runnable detailBackAction;
    private boolean detailOpen = false;

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
        b.setTextColor(Color.WHITE);
        b.setBackgroundColor(NAVY);
        b.setAllCaps(false);
        return b;
    }

    private TextView coloredText(String t, int sp, int color) {
        TextView v = title(t, sp);
        v.setTextColor(color);
        return v;
    }

    private String decision(IndicatorEngine.Snapshot s) {
        if (s.score >= 13 && s.trendUp && s.cmf20 > 0.05 && s.trendEfficiency20 > 0.28 && !s.trap) return "ÇOK GÜÇLÜ FIRSAT • AL";
        if ("AL".equals(s.signal)) return "AL";
        if ("ERKEN".equals(s.signal)) return "KADEMELİ AL";
        if ("SAT/RİSK".equals(s.signal)) return "SAT / RİSKİ AZALT";
        if ("KOVALAMA".equals(s.signal)) return "YENİ ALIM YAPMA";
        if ("İZLE".equals(s.signal)) return "TUT / YENİ ALIM İÇİN BEKLE";
        return "BEKLE / TUT";
    }

    private int decisionColor(IndicatorEngine.Snapshot s) {
        String d = decision(s);
        if (d.startsWith("ÇOK GÜÇLÜ FIRSAT")) return GREEN;
        if (d.equals("AL") || d.equals("KADEMELİ AL")) return GREEN;
        if (d.contains("SAT") || d.contains("YAPMA")) return RED;
        return Color.rgb(225, 145, 0);
    }

    private String decisionWhy(IndicatorEngine.Snapshot s) {
        List<String> why = new ArrayList<>();
        why.add(s.trendUp ? "yükseliş trendi güçlü" : (s.close < s.ema50 ? "fiyat EMA50 altında" : "trend henüz net değil"));
        why.add("RSI " + IndicatorEngine.fmt(s.rsi14));
        why.add(s.macd > s.macdSignal ? "MACD olumlu" : "MACD zayıf");
        why.add(s.relVolume >= 1.15 ? "hacim destekli" : "hacim desteği düşük");
        why.add(s.cmf20 > 0.05 ? "para girişi var" : (s.cmf20 < -0.08 ? "para çıkışı var" : "para akışı nötr"));
        if (s.breakout20) why.add("20 günlük kırılım");
        else if (s.preBreakout) why.add("kırılıma yakın");
        if (s.trap) why.add("yukarı yönlü tuzak riski");
        why.add("CCI " + IndicatorEngine.fmt(s.cci20));
        why.add("Stokastik " + IndicatorEngine.fmt(s.stochastic14));
        why.add("ADX " + IndicatorEngine.fmt(s.adx14));
        why.add("BorsaRadar trend verimi " + IndicatorEngine.fmt(s.trendEfficiency20));
        why.add("ATR momentum " + IndicatorEngine.fmt(s.momentumAtr20));
        why.add("hacim yön baskısı " + IndicatorEngine.fmt(s.volumePressure20));
        return "Neye göre: " + android.text.TextUtils.join(" • ", why) + ".";
    }

    private String indicatorConsensus(IndicatorEngine.Snapshot s) {
        int buy = 0, sell = 0, neutral = 0;
        if (s.trendUp) buy++; else if (s.close < s.ema50) sell++; else neutral++;
        if (s.rsi14 >= 45 && s.rsi14 <= 68) buy++; else if (s.rsi14 > 72) sell++; else neutral++;
        if (s.macd > s.macdSignal) buy++; else sell++;
        if (s.cmf20 > 0.05) buy++; else if (s.cmf20 < -0.08) sell++; else neutral++;
        if (s.breakout20 || s.preBreakout) buy++; else neutral++;
        if (s.trap) sell++; else neutral++;
        if (s.cci20 >= 50 && s.cci20 <= 180) buy++; else if (s.cci20 < -100) sell++; else neutral++;
        if (s.stochastic14 >= 55 && s.stochastic14 <= 88) buy++; else if (s.stochastic14 > 94 || s.stochastic14 < 18) sell++; else neutral++;
        if (s.adx14 >= 20 && s.trendUp) buy++; else if (s.adx14 >= 20 && s.close < s.ema50) sell++; else neutral++;
        if (s.trendEfficiency20 > 0.28) buy++; else if (s.trendEfficiency20 < -0.22) sell++; else neutral++;
        if (s.momentumAtr20 > 0.80) buy++; else if (s.momentumAtr20 < -0.80) sell++; else neutral++;
        if (s.volumePressure20 > 0.08) buy++; else if (s.volumePressure20 < -0.08) sell++; else neutral++;
        return "İndikatör uzlaşması: " + buy + " AL • " + neutral + " NÖTR • " + sell + " SAT";
    }

    private TextView decisionBanner(IndicatorEngine.Snapshot s) {
        TextView v = coloredText(decision(s), 22, Color.WHITE);
        v.setGravity(android.view.Gravity.CENTER);
        v.setTypeface(null, android.graphics.Typeface.BOLD);
        v.setBackgroundColor(decisionColor(s));
        v.setPadding(20, 22, 20, 22);
        return v;
    }

    private void shell(String page) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(14, 14, 14, 14);
        root.setBackgroundColor(Color.rgb(247, 249, 252));

        TextView brand = coloredText("BORSA RADAR", 27, Color.WHITE);
        brand.setBackgroundColor(NAVY);
        brand.setPadding(24, 22, 24, 22);
        root.addView(brand);

        LinearLayout nav = new LinearLayout(this);
        nav.setOrientation(LinearLayout.HORIZONTAL);
        Button p = btn("Portföyüm"), r = btn("BIST Radar"), a = btn("3 Strateji");
        p.setBackgroundColor(RED);
        r.setBackgroundColor(RED);
        a.setBackgroundColor(RED);
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
        TextView credit = coloredText("Programcı: Erdoğan Kulanoğlu", 12, Color.rgb(95, 105, 118));
        credit.setGravity(android.view.Gravity.CENTER);
        root.addView(credit);
        setContentView(root);
    }

    private void showPortfolio() {
        currentSection = "portfolio"; detailOpen = false;
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

        LinearLayout backup = new LinearLayout(this);
        Button copy = btn("Portföyü Kopyala");
        Button restore = btn("Panodan Geri Yükle");
        backup.addView(copy, new LinearLayout.LayoutParams(0, -2, 1));
        backup.addView(restore, new LinearLayout.LayoutParams(0, -2, 1));
        content.addView(backup);
        copy.setOnClickListener(v -> copyPortfolio());
        restore.setOnClickListener(v -> restorePortfolio());

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
            row.addView(coloredText("Son: " + money(s.close) + " • P/L: " + money(pnl) + " (%" + IndicatorEngine.fmt(pnlPct) + ")", 15, pnl >= 0 ? GREEN : RED));
            row.addView(decisionBanner(s));
            row.addView(coloredText(indicatorConsensus(s), 15, decisionColor(s)));
            row.addView(coloredText(decisionWhy(s), 14, decisionColor(s)));
            row.addView(title("Teknik ayrıntı: " + s.signal + " • " + s.reason, 13));
            row.addView(title("ATR stop referansı: " + money(Math.max(s.close - 2.2 * s.atr14, s.ema50 * 0.985)), 13));
        }

        LinearLayout buttons = new LinearLayout(this);
        Button edit = btn("Düzenle"), bt = btn("1Y Backtest"), del = btn("Sil");
        del.setBackgroundColor(RED);
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
        AutoCompleteTextView s = new AutoCompleteTextView(this);
        s.setHint("Hisse kodu veya şirket adı yaz (örn. BIMAS)");
        s.setThreshold(1);
        s.setSingleLine(true);
        s.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_dropdown_item_1line, BistUniverse.ENTRIES));
        EditText q = new EditText(this);
        q.setHint("Lot / adet");
        q.setInputType(InputType.TYPE_CLASS_NUMBER);
        EditText c = new EditText(this);
        c.setHint("Ortalama alış fiyatı (örn. 287,87)");
        c.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        if (edit != null) {
            s.setText(edit.symbol, false);
            q.setText(String.valueOf(edit.qty));
            c.setText(String.valueOf(edit.cost));
        }
        box.addView(s); box.addView(q); box.addView(c);
        new AlertDialog.Builder(this)
                .setTitle(edit == null ? "Portföye ekle" : "Pozisyonu düzenle")
                .setView(box)
                .setPositiveButton("Kaydet", (d, w) -> {
                    try {
                        String sym = BistUniverse.symbolFromEntry(s.getText().toString());
                        if (!Arrays.asList(PORTFOLIO_SYMBOLS).contains(sym)) throw new IllegalArgumentException();
                        int qty = Integer.parseInt(q.getText().toString());
                        String rawCost = c.getText().toString().trim();
                        double cost = Double.parseDouble(rawCost.replace(',', '.'));
                        // Bazı Android sayısal klavyeleri virgül tuşunu metne eklemeden
                        // kuruşları bitişik yazabiliyor: 28787 -> 287,87.
                        if (!rawCost.contains(",") && !rawCost.contains(".") && cost >= 10000) cost /= 100.0;
                        if (qty <= 0 || cost <= 0) throw new IllegalArgumentException();
                        if (edit == null) holdings.add(new Holding(sym, qty, cost));
                        else { edit.symbol = sym; edit.qty = qty; edit.cost = cost; }
                        save();
                        refreshPortfolio();
                    } catch (Exception ex) {
                        Toast.makeText(this, "Lot ve fiyatı kontrol et", Toast.LENGTH_LONG).show();
                    }
                })
                .setNegativeButton("İptal", null)
                .show();
    }

    private void showRadar() {
        currentSection = "radar"; detailOpen = false;
        shell("BIST Radar");
        content.addView(title("Radar portföyden bağımsız çalışır. Günlük Yahoo Finance verisini anahtarsız çeker; veri gecikmeli olabilir.", 15));
        content.addView(title("Skor: EMA20/50 + RSI14 + MACD + RVOL + CMF + Bollinger + CCI + Stokastik + ADX + BRTV + BRM + BRH + breakout/trap + ATR", 14));
        Button scan = btn("Tüm BIST Hisselerini Tara");
        content.addView(scan);
        scan.setOnClickListener(v -> scanRadar());
    }

    private void scanRadar() {
        shell("Tüm BIST Taranıyor");
        ProgressBar bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(RADAR_SYMBOLS.length);
        content.addView(bar);
        TextView status = title("0/" + RADAR_SYMBOLS.length + " • veri alınıyor", 16);
        content.addView(status);

        final List<Ranked> results = Collections.synchronizedList(new ArrayList<>());
        final int[] done = {0};
        final int[] failed = {0};
        for (String sym : RADAR_SYMBOLS) {
            io.execute(() -> {
                try {
                    List<MarketDataService.Candle> data = MarketDataService.fetchDaily(sym, "1y");
                    IndicatorEngine.Snapshot s = IndicatorEngine.analyze(data);
                    BacktestEngine.Result bt = BacktestEngine.run(data);
                    results.add(new Ranked(sym, s, bt));
                } catch (Exception ignored) { synchronized (failed) { failed[0]++; } }
                main.post(() -> {
                    done[0]++;
                    bar.setProgress(done[0]);
                    status.setText(done[0] + "/" + RADAR_SYMBOLS.length + " • başarılı " + results.size() + " • başarısız " + failed[0]);
                    if (done[0] >= RADAR_SYMBOLS.length) renderRadarResults(results);
                });
            });
        }
    }

    private void renderRadarResults(List<Ranked> results) {
        currentSection = "radar"; detailOpen = false;
        shell("Radar Sonuçları");
        List<Ranked> copy = new ArrayList<>(results);
        copy.sort((a, b) -> {
            int s = Integer.compare(b.s.score, a.s.score);
            if (s != 0) return s;
            return Double.compare(b.bt.netPct, a.bt.netPct);
        });
        lastRadarResults.clear();
        lastRadarResults.addAll(copy);
        content.addView(title(RADAR_SYMBOLS.length + " hisse tarandı; veri alınabilen " + copy.size() + " hisse arasından yalnızca en güçlü 30 teknik aday gösteriliyor.", 14));
        content.addView(title("Diğer hisseler düşük skor, zayıf trend, yetersiz hacim veya tuzak riski nedeniyle tavsiye listesine alınmadı.", 13));
        if (copy.isEmpty()) { content.addView(title("Veri alınamadı. İnternet bağlantısı veya veri kaynağı geçici olarak engellemiş olabilir.", 16)); return; }

        int limit = Math.min(30, copy.size());
        for (int i = 0; i < limit; i++) {
            Ranked r = copy.get(i);
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setPadding(18, 10, 18, 10);
            card.setBackgroundColor(Color.rgb(244,247,250));
            int radarColor = (r.s.signal.contains("AL") || r.s.signal.contains("ERKEN")) ? GREEN : (r.s.signal.contains("SAT") || r.s.signal.contains("RİSK") || r.s.signal.contains("KOVALAMA")) ? RED : NAVY;
            card.addView(coloredText((i + 1) + ". " + r.symbol + " • " + decision(r.s) + " • skor " + r.s.score + "/15", 18, radarColor));
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
        final String returnSection = currentSection;
        detailBackAction = () -> {
            if ("radar".equals(returnSection) && !lastRadarResults.isEmpty())
                renderRadarResults(new ArrayList<>(lastRadarResults));
            else if ("radar".equals(returnSection)) showRadar();
            else if ("strategies".equals(returnSection)) showStrategies();
            else showPortfolio();
        };
        detailOpen = true;
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
                    Button back = btn("← Geri");
                    back.setOnClickListener(v -> detailBackAction.run());
                    content.addView(back);
                    addStockNavigation(symbol);
                    TextView currentPrice = coloredText("GÜNCEL FİYAT: " + money(s.close), 24, NAVY);
                    currentPrice.setGravity(android.view.Gravity.CENTER);
                    currentPrice.setTypeface(null, android.graphics.Typeface.BOLD);
                    currentPrice.setPadding(20, 24, 20, 24);
                    content.addView(currentPrice);
                    content.addView(new PriceChartView(this, data), new LinearLayout.LayoutParams(-1, 760));
                    content.addView(decisionBanner(s));
                    content.addView(coloredText(indicatorConsensus(s), 16, decisionColor(s)));
                    content.addView(coloredText(decisionWhy(s), 15, decisionColor(s)));
                    content.addView(title("Teknik sinyal: " + s.signal + " • Teknik skor: " + s.score + " • Ölçek: -14…+15", 16));
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

    private void addStockNavigation(String symbol) {
        if (lastRadarResults.size() < 2) return;
        int index = -1;
        for (int i = 0; i < lastRadarResults.size(); i++) if (lastRadarResults.get(i).symbol.equals(symbol)) { index = i; break; }
        if (index < 0) return;
        final String previous = lastRadarResults.get((index - 1 + lastRadarResults.size()) % lastRadarResults.size()).symbol;
        final String next = lastRadarResults.get((index + 1) % lastRadarResults.size()).symbol;
        LinearLayout nav = new LinearLayout(this);
        Button prev = btn("← " + previous);
        Button nxt = btn(next + " →");
        nav.addView(prev, new LinearLayout.LayoutParams(0, -2, 1));
        nav.addView(nxt, new LinearLayout.LayoutParams(0, -2, 1));
        prev.setOnClickListener(v -> runSingleBacktest(previous));
        nxt.setOnClickListener(v -> runSingleBacktest(next));
        content.addView(nav);
    }

    private void copyPortfolio() {
        String data = getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("items", "[]");
        ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        cm.setPrimaryClip(ClipData.newPlainText("BorsaRadar Portföy", data));
        Toast.makeText(this, "Portföy panoya kopyalandı", Toast.LENGTH_LONG).show();
    }

    private void restorePortfolio() {
        try {
            ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            if (!cm.hasPrimaryClip()) throw new IllegalArgumentException();
            String data = cm.getPrimaryClip().getItemAt(0).coerceToText(this).toString();
            JSONArray a = new JSONArray(data);
            List<Holding> restored = new ArrayList<>();
            for (int i = 0; i < a.length(); i++) {
                JSONObject o = a.getJSONObject(i);
                restored.add(new Holding(o.getString("s"), o.getInt("q"), o.getDouble("c")));
            }
            holdings.clear(); holdings.addAll(restored); save(); showPortfolio();
            Toast.makeText(this, "Portföy geri yüklendi", Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "Panoda geçerli BorsaRadar portföyü yok", Toast.LENGTH_LONG).show();
        }
    }

    private void showStrategies() {
        currentSection = "strategies"; detailOpen = false;
        shell("100.000 TL • 3 Strateji");
        if (lastRadarResults.isEmpty()) {
            content.addView(title("Aktif tavsiye üretmek için önce tüm BIST radarını tara.", 17));
            Button go = btn("BIST Radarına Git");
            go.setOnClickListener(v -> showRadar());
            content.addView(go);
            return;
        }

        List<Ranked> shortTerm = new ArrayList<>();
        List<Ranked> longTerm = new ArrayList<>();
        List<Ranked> dividend = new ArrayList<>();
        List<String> dividendWatch = Arrays.asList("AKBNK","AYGAZ","BIMAS","ENKAI","EREGL","FROTO","ISDMR","SISE","TCELL","TOASO","TTKOM","TTRAK");
        for (Ranked r : lastRadarResults) {
            if (r.s.score >= 5 && !r.s.trap) shortTerm.add(r);
            if (r.s.trendUp && r.s.cmf20 > 0 && !r.s.trap) longTerm.add(r);
            if (dividendWatch.contains(r.symbol) && r.s.score >= 2 && !r.s.trap) dividend.add(r);
        }
        longTerm.sort((a, b) -> Double.compare(b.bt.netPct, a.bt.netPct));
        dividend.sort((a, b) -> Integer.compare(b.s.score, a.s.score));
        addStrategyGroup("KISA VADE / AL-SAT", 33333, shortTerm, "Teknik skor, hacim, kırılım ve backtest öncelikli.");
        addStrategyGroup("TEMETTÜ TEKNİK ÖN ELEME", 33333, dividend, "Temettü verimi ve bilanço doğrulanmadan kesin alım önerisi değildir.");
        addStrategyGroup("UZUN VADE TEKNİK ADAY", 33334, longTerm, "Trend, para akışı ve geçmiş strateji dayanıklılığı öncelikli.");
        content.addView(title("Dağılım örnektir; canlı derinlik ve aracı kurum dağılımı mevcut veri kaynağında yoktur.", 13));
    }

    private void addStrategyGroup(String heading, int budget, List<Ranked> candidates, String note) {
        TextView h = coloredText(heading + " • " + budget + " TL", 19, Color.WHITE);
        h.setBackgroundColor(NAVY);
        h.setTypeface(null, android.graphics.Typeface.BOLD);
        content.addView(h);
        content.addView(title(note, 13));
        int count = Math.min(3, candidates.size());
        if (count == 0) {
            content.addView(coloredText("Şu an ölçütleri karşılayan aday yok; nakitte bekle.", 15, RED));
            return;
        }
        int perStock = budget / count;
        for (int i = 0; i < count; i++) {
            Ranked r = candidates.get(i);
            int lots = Math.max(0, (int) Math.floor(perStock / r.s.close));
            Button pick = btn((i + 1) + ". " + r.symbol + " • " + decision(r.s));
            pick.setOnClickListener(v -> runSingleBacktest(r.symbol));
            content.addView(pick);
            content.addView(title("Fiyat " + money(r.s.close) + " • yaklaşık " + lots + " lot / " + perStock + " TL • skor " + r.s.score + " (-14…+15)", 14));
            content.addView(title(indicatorConsensus(r.s), 13));
        }
    }

    @Override public void onBackPressed() {
        if (detailOpen && detailBackAction != null) detailBackAction.run();
        else super.onBackPressed();
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
