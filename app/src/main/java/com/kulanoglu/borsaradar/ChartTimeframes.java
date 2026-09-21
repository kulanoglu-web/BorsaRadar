package com.kulanoglu.borsaradar;
/** Tek kaynak: grafik zaman dilimleri. */
public final class ChartTimeframes {
 public static final String[] LABELS={"5 dk","15 dk","30 dk","1 saat","4 saat","1 gün","1 hafta","1 ay","3 ay","6 ay","1 yıl","2 yıl"};
 public static final String[] INTERVAL={"1m","1m","1m","5m","15m","5m","30m","1d","1d","1d","1d","1d"};
 public static final String[] RANGE={"1d","1d","1d","1d","1d","1d","5d","1mo","3mo","6mo","1y","2y"};
 public static int clamp(int i){return Math.max(0,Math.min(i,LABELS.length-1));}
 public static String label(int i){return LABELS[clamp(i)];}
 private ChartTimeframes(){}
}
