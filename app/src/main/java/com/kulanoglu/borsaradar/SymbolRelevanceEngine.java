package com.kulanoglu.borsaradar;

import java.util.Locale;

/** Haber sirketi gercekten ilgilendiriyor mu? Yanlis eslesmeleri azaltir. */
public final class SymbolRelevanceEngine {
    private SymbolRelevanceEngine(){}
    public static double relevance(String symbol,String companyName,String title,String summary){
        String s=symbol==null?"":symbol.replace(".IS","").replace(".DE","").toLowerCase(Locale.ROOT);
        String c=companyName==null?"":companyName.toLowerCase(Locale.ROOT);
        String text=((title==null?"":title)+" "+(summary==null?"":summary)).toLowerCase(Locale.ROOT);
        if(!s.isEmpty() && text.matches(".*\\b"+java.util.regex.Pattern.quote(s)+"\\b.*"))return 1.0;
        if(!c.isEmpty() && c.length()>=4 && text.contains(c))return .95;
        String first=c.split(" ")[0]; if(first.length()>=5&&text.contains(first))return .72;
        return .38;
    }
}
