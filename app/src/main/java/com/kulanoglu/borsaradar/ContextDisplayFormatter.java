package com.kulanoglu.borsaradar;

/** UI'da uzun motor ciktilarini kisa ve okunur metne cevirir. */
public final class ContextDisplayFormatter {
    private ContextDisplayFormatter(){}
    public static String headline(CatalystContextEngine.Result c){
        if(c==null||!c.hasContext)return "Bilgi akisi: veri yetersiz";
        return "Birlesik "+f(c.combinedScore)+"/8 • Bilgi gucu "+f0(c.informationStrength)+"/100 • "+c.strengthLabel;
    }
    public static String detail(CatalystContextEngine.Result c){
        if(c==null)return "";
        return "Haber "+f(c.newsScore)+" • KAP "+f(c.kapScore)+" • Kalite "+f0(c.qualityScore)+"/100 • Makro "+c.macroTag+" "+f(c.macroRisk)+"/10";
    }
    private static String f(double x){return String.format(java.util.Locale.US,"%.1f",x);}
    private static String f0(double x){return String.format(java.util.Locale.US,"%.0f",x);}
}
