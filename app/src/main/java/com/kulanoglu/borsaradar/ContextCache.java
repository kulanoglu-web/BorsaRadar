package com.kulanoglu.borsaradar;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Kısa süreli bağlam cache'i + geçici kaynak arızalarında kontrollü eski veri yedeği. */
public final class ContextCache {
    private ContextCache(){}
    private static final long FRESH_TTL_MS=10*60*1000L;
    private static final long STALE_MAX_MS=6*60*60*1000L;
    private static final Map<String,Entry> MAP=new ConcurrentHashMap<>();
    static final class Entry { final long at; final UnifiedContextService.Result value; Entry(long a,UnifiedContextService.Result v){at=a;value=v;} }
    public static UnifiedContextService.Result get(String symbol){
        Entry e=MAP.get(key(symbol));
        if(e==null)return null;
        long age=System.currentTimeMillis()-e.at;
        if(age>STALE_MAX_MS){MAP.remove(key(symbol));return null;}
        return age<=FRESH_TTL_MS?e.value:null;
    }
    public static UnifiedContextService.Result getStale(String symbol){
        Entry e=MAP.get(key(symbol)); if(e==null)return null;
        long age=System.currentTimeMillis()-e.at;
        if(age>STALE_MAX_MS){MAP.remove(key(symbol));return null;}
        return e.value;
    }
    public static long ageMinutes(String symbol){Entry e=MAP.get(key(symbol));return e==null?-1:Math.max(0,(System.currentTimeMillis()-e.at)/60000L);}
    public static void put(String symbol,UnifiedContextService.Result value){if(value!=null&&value.hasContext)MAP.put(key(symbol),new Entry(System.currentTimeMillis(),value));}
    public static void clear(String symbol){MAP.remove(key(symbol));}
    private static String key(String s){return s==null?"":s.trim().toUpperCase();}
}
