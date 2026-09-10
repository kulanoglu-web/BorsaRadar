package com.kulanoglu.borsaradar;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;

public final class MarketDataService {
    private static final Object RATE_LOCK = new Object();
    private static long lastRequestAt = 0L;
    private MarketDataService() {}

    public static final class Candle {
        public final long time;
        public final double open;
        public final double high;
        public final double low;
        public final double close;
        public final double volume;

        public Candle(long time, double open, double high, double low, double close, double volume) {
            this.time = time;
            this.open = open;
            this.high = high;
            this.low = low;
            this.close = close;
            this.volume = volume;
        }
    }

    public static List<Candle> fetchDaily(String bistSymbol, String range) throws Exception {
        String symbol = bistSymbol.endsWith(".IS") ? bistSymbol : bistSymbol + ".IS";
        Exception last = null;
        String[] hosts = {"query1.finance.yahoo.com", "query2.finance.yahoo.com"};
        for (int attempt = 0; attempt < 4; attempt++) {
            String url = "https://" + hosts[attempt % hosts.length] + "/v8/finance/chart/" + symbol
                    + "?range=" + range + "&interval=1d&includePrePost=false&events=div%2Csplits";
            try {
                throttle();
                return fetch(url);
            } catch (Exception e) {
                last = e;
                try { Thread.sleep(700L * (attempt + 1)); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw interrupted; }
            }
        }
        throw last == null ? new Exception("Veri alınamadı") : last;
    }

    private static void throttle() throws InterruptedException {
        synchronized (RATE_LOCK) {
            long wait = 260L - (System.currentTimeMillis() - lastRequestAt);
            if (wait > 0) Thread.sleep(wait);
            lastRequestAt = System.currentTimeMillis();
        }
    }

    private static List<Candle> fetch(String address) throws Exception {
        HttpURLConnection conn = null;
        try {
            conn = (HttpURLConnection) new URL(address).openConnection();
            conn.setConnectTimeout(10000);
            conn.setReadTimeout(12000);
            conn.setRequestMethod("GET");
            conn.setRequestProperty("User-Agent", "Mozilla/5.0 BorsaRadar/0.9");
            conn.setRequestProperty("Accept", "application/json");

            int code = conn.getResponseCode();
            if (code < 200 || code >= 300) throw new Exception("HTTP " + code);

            StringBuilder sb = new StringBuilder();
            BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
            br.close();

            JSONObject root = new JSONObject(sb.toString());
            JSONObject chart = root.getJSONObject("chart");
            if (!chart.isNull("error")) throw new Exception("Veri kaynağı hatası");
            JSONArray result = chart.getJSONArray("result");
            if (result.length() == 0) throw new Exception("Veri yok");
            JSONObject r = result.getJSONObject(0);
            JSONArray ts = r.getJSONArray("timestamp");
            JSONObject q = r.getJSONObject("indicators").getJSONArray("quote").getJSONObject(0);
            JSONArray o = q.getJSONArray("open");
            JSONArray h = q.getJSONArray("high");
            JSONArray l = q.getJSONArray("low");
            JSONArray c = q.getJSONArray("close");
            JSONArray v = q.getJSONArray("volume");

            List<Candle> out = new ArrayList<>();
            int n = Math.min(ts.length(), c.length());
            for (int i = 0; i < n; i++) {
                if (c.isNull(i) || h.isNull(i) || l.isNull(i) || o.isNull(i)) continue;
                double close = c.optDouble(i, Double.NaN);
                double high = h.optDouble(i, Double.NaN);
                double low = l.optDouble(i, Double.NaN);
                double open = o.optDouble(i, Double.NaN);
                double volume = v.isNull(i) ? 0.0 : v.optDouble(i, 0.0);
                if (Double.isNaN(close) || Double.isNaN(high) || Double.isNaN(low) || Double.isNaN(open)) continue;
                out.add(new Candle(ts.getLong(i), open, high, low, close, volume));
            }
            if (out.size() < 30) throw new Exception("Yetersiz veri: " + out.size() + " gün");
            return out;
        } finally {
            if (conn != null) conn.disconnect();
        }
    }
}
