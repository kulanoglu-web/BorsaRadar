package com.kulanoglu.borsaradar;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Makro hareketleri hisse/sector duyarliligina gore agirliklandirir. */
public final class SectorMacroSensitivityEngine {
    private SectorMacroSensitivityEngine(){}
    private static final Set<String> AIRLINES=new HashSet<>(Arrays.asList("THYAO","PGSUS","LHA","UAL","DAL","AAL"));
    private static final Set<String> ENERGY=new HashSet<>(Arrays.asList("TUPRS","PETKM","AKSEN","AYDEM","GWIND","ENJSA","ZOREN","XOM","CVX"));
    private static final Set<String> BANKS=new HashSet<>(Arrays.asList("AKBNK","GARAN","ISCTR","YKBNK","HALKB","VAKBN","TSKB","ALBRK","JPM","BAC","DBK","CBK"));
    private static final Set<String> EXPORTERS=new HashSet<>(Arrays.asList("FROTO","TOASO","ARCLK","VESTL","SISE","EREGL","KRDMD","TTRAK","OTKAR"));
    private static final Set<String> IMPORT_HEAVY=new HashSet<>(Arrays.asList("THYAO","PGSUS","PETKM","TUPRS","ARCLK","VESTL"));
    private static final Set<String> GROWTH=new HashSet<>(Arrays.asList("NVDA","AMD","AVGO","PLTR","TSLA","S92","NCH2"));

    private static String clean(String raw){
        return raw==null?"":raw.toUpperCase(Locale.ROOT).replace(".IS","").replace(".DE","");
    }
    public static String group(String raw){
        String s=clean(raw);
        if(AIRLINES.contains(s))return "HAVAYOLU";
        if(BANKS.contains(s))return "BANKA";
        if(ENERGY.contains(s))return "ENERJI";
        if(EXPORTERS.contains(s))return "IHRACATCI";
        if(GROWTH.contains(s))return "BUYUME";
        return "GENEL";
    }
    public static double multiplier(String rawSymbol,String macroTag){
        String s=clean(rawSymbol),tag=macroTag==null?"NONE":macroTag;
        if("PETROL".equals(tag)){if(AIRLINES.contains(s))return 1.35;if(ENERGY.contains(s))return .80;}
        if("FAIZ".equals(tag)){if(BANKS.contains(s))return 1.20;if(GROWTH.contains(s))return 1.30;}
        if("KUR".equals(tag)){if(EXPORTERS.contains(s))return .75;if(IMPORT_HEAVY.contains(s))return 1.30;}
        if("GEOPOLITIK".equals(tag)){if(AIRLINES.contains(s))return 1.30;if(ENERGY.contains(s))return 1.10;}
        if("POLITIK".equals(tag)&&!MarketDataService.isGlobalSymbol(rawSymbol))return 1.25;
        return 1.0;
    }
}
