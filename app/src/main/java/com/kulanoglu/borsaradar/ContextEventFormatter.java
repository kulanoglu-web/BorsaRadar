package com.kulanoglu.borsaradar;

public final class ContextEventFormatter {
    private ContextEventFormatter(){}
    public static String top(CatalystContextEngine.Result c,int max){
        if(c==null||c.topEvents==null||c.topEvents.isEmpty())return "Onemli olay bulunamadi.";
        StringBuilder b=new StringBuilder(); int n=Math.min(max,c.topEvents.size());
        for(int i=0;i<n;i++){if(i>0)b.append('\n');b.append("• ").append(trim(c.topEvents.get(i),150));}
        return b.toString();
    }
    private static String trim(String s,int n){if(s==null)return "";return s.length()<=n?s:s.substring(0,n-1)+"…";}
}
