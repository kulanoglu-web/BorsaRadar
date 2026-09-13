package com.kulanoglu.borsaradar;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Makro olayın her hisseyi aynı etkilemesini engelleyen kaba sektör duyarlılığı. */
public final class SectorMacroSensitivityEngine {
    private SectorMacroSensitivityEngine(){}
    private static final Set<String> AIRLINES=new HashSet<>(Arrays.asList("THYAO","PGSUS","LHA","UAL","DAL","AAL"));
    private static final Set<String> ENERGY=new HashSet<>(Arrays.asList("TUPRS","PETKM","AKSEN","AYDEM","GWIND","XOM","CVX"));
    private static final Set<String> BANKS=new HashSet<>(Arrays.asList("AKBNK","GARAN","ISCTR","YKBNK","HALKB","VAKBN","JPM","BAC","DBK","CBK"));
    private static final Set<String> GROWTH=new HashSet<>(Arrays.asList("NVDA","AMD","AVGO","PLTR","TSLA","S92","NCH2"));
    public static double multiplier(String rawSymbol,String macroTag){
        String s=rawSymbol==null?"":rawSymbol.toUpperCase(Locale.ROOT).replace(".IS","").replace(".DE","");
        String tag=macroTag==null?"NONE":macroTag;
        if("PETROL".equals(tag)){if(AIRLINES.contains(s))return 1.35;if(ENERGY.contains(s))return .80;}
        if("FAIZ".equals(tag)){if(BANKS.contains(s))return 1.20;if(GROWTH.contains(s))return 1.30;}
        if("GEOPOLITIK".equals(tag)){if(AIRLINES.contains(s))return 1.30;if(ENERGY.contains(s))return 1.10;}
        if("POLITIK".equals(tag)&&!MarketDataService.isGlobalSymbol(rawSymbol))return 1.25;
        return 1.0;
    }
}
