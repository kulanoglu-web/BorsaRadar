package com.kulanoglu.borsaradar;

import java.util.Locale;

public final class MarketSymbol {
    private MarketSymbol(){}

    public static String manual(String raw,int market){
        String s=raw==null?"":raw.trim().toUpperCase(Locale.ROOT).replace(" ","");
        if(s.isEmpty()) return s;
        if(market==1){
            if(s.startsWith("DE:")) return s;
            if(s.endsWith(".DE")) s=s.substring(0,s.length()-3);
            return "DE:"+s;
        }
        if(market==2){
            if(s.startsWith("US:")) return s;
            return "US:"+s.replace(".US","");
        }
        if(s.startsWith("TR:")) s=s.substring(3);
        if(s.endsWith(".IS")) s=s.substring(0,s.length()-3);
        return s;
    }

    public static String yahoo(String stored){
        String s=stored==null?"":stored.trim().toUpperCase(Locale.ROOT);
        if(s.startsWith("US:")) return s.substring(3);
        if(s.startsWith("DE:")){
            String x=s.substring(3);
            return x.endsWith(".DE")?x:x+".DE";
        }
        if(s.startsWith("TR:")) s=s.substring(3);
        if(s.endsWith(".IS") || s.endsWith(".DE")) return s;
        return s+".IS";
    }

    public static int marketIndex(String stored){
        if(stored!=null && stored.startsWith("DE:")) return 1;
        if(stored!=null && stored.startsWith("US:")) return 2;
        return 0;
    }

    public static String label(String stored){
        if(stored==null) return "";
        if(stored.startsWith("DE:")) return stored.substring(3)+" • Almanya";
        if(stored.startsWith("US:")) return stored.substring(3)+" • ABD";
        if(stored.startsWith("TR:")) return stored.substring(3)+" • Türkiye";
        return stored+" • Türkiye";
    }

    public static String currency(String stored){
        if(stored!=null && stored.startsWith("DE:")) return "€";
        if(stored!=null && stored.startsWith("US:")) return "$";
        return "₺";
    }

    public static boolean isTurkey(String stored){
        return stored!=null && !stored.startsWith("DE:") && !stored.startsWith("US:");
    }
}
