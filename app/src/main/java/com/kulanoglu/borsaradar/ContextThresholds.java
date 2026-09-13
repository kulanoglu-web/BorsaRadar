package com.kulanoglu.borsaradar;

/** Baglam esiklerini tek yerde tutar; ileride backtest ile optimize edilebilir. */
public final class ContextThresholds {
    private ContextThresholds(){}
    public static final double POSITIVE=3.0;
    public static final double NEGATIVE=-3.0;
    public static final double HIGH_MACRO_RISK=7.0;
    public static final double GOOD_QUALITY=60.0;
    public static final double LOW_QUALITY=45.0;
    public static final double TECH_STRONG=2.7;
    public static final double TECH_WEAK=-1.3;
}
