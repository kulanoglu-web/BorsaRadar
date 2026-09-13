package com.kulanoglu.borsaradar;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/** Ayni olayin farkli kaynaklarda tekrar tekrar puanlanmasini engeller. */
public final class EventDeduplicator {
    private EventDeduplicator(){}
    public static List<MultiSourceContextEngine.Event> unique(List<MultiSourceContextEngine.Event> in){
        List<MultiSourceContextEngine.Event> out=new ArrayList<>(); if(in==null)return out;
        Set<String> seen=new HashSet<>();
        for(MultiSourceContextEngine.Event e:in){
            String key=key(e.title); if(key.length()<8||seen.add(key))out.add(e);
        }
        return out;
    }
    static String key(String s){
        if(s==null)return ""; String x=Normalizer.normalize(s.toLowerCase(Locale.ROOT),Normalizer.Form.NFD).replaceAll("\\p{M}","");
        x=x.replaceAll("[^a-z0-9 ]"," ").replaceAll("\\b(a|the|ve|ile|icin|for|to|of|and|bir)\\b"," ").replaceAll("\\s+"," ").trim();
        String[] p=x.split(" "); StringBuilder b=new StringBuilder(); int n=Math.min(8,p.length); for(int i=0;i<n;i++)b.append(p[i]).append(' '); return b.toString().trim();
    }
}
