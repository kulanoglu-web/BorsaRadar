package com.kulanoglu.borsaradar;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Kisa sureli baglam cache'i: ayni hisse icin gereksiz ag isteklerini azaltir. */
public final class ContextCache {
    private ContextCache(){}
    private static final long TTL_MS=10*60*1000L;
    private static final Map<String,Entry> MAP=new ConcurrentHashMap<>();
    static final class Entry { final long at; final UnifiedContextService.Result value; Entry(long a,UnifiedContextService.Result v){at=a;value=v;} }
    public static UnifiedContextService.Result get(String symbol){
        Entry e=MAP.get(key(symbol));
        if(e==null||System.currentTimeMillis()-e.at>TTL_MS){if(e!=null)MAP.remove(key(symbol));return null;}
        return e.value;
    }
    public static void put(String symbol,UnifiedContextService.Result value){if(value!=null)MAP.put(key(symbol),new Entry(System.currentTimeMillis(),value));}
    public static void clear(String symbol){MAP.remove(key(symbol));}
    private static String key(String s){return s==null?"":s.trim().toUpperCase();}
}
