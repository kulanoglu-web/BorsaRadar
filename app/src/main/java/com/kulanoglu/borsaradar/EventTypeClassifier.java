package com.kulanoglu.borsaradar;

import java.util.Locale;

public final class EventTypeClassifier {
    private EventTypeClassifier(){}
    public enum Type { EARNINGS, GUIDANCE, CONTRACT, PARTNERSHIP, M_AND_A, CAPITAL, DIVIDEND, BUYBACK, REGULATORY, LEGAL, PRODUCT, MACRO, MANAGEMENT, OTHER }
    public static Type classify(String title){
        String t=title==null?"":title.toLowerCase(Locale.ROOT);
        if(has(t,"earnings","revenue","net income","bilanço","finansal sonuç"))return Type.EARNINGS;
        if(has(t,"guidance","beklenti","forecast","outlook"))return Type.GUIDANCE;
        if(has(t,"contract","sözleşme","ihale","order","sipariş"))return Type.CONTRACT;
        if(has(t,"partnership","ortaklık","collaboration","iş birliği"))return Type.PARTNERSHIP;
        if(has(t,"acquisition","merger","satın alma","birleşme"))return Type.M_AND_A;
        if(has(t,"sermaye","bedelli","bedelsiz","rights issue"))return Type.CAPITAL;
        if(has(t,"dividend","temettü","kar pay"))return Type.DIVIDEND;
        if(has(t,"buyback","geri alım"))return Type.BUYBACK;
        if(has(t,"ban","restriction","regulator","spk","sec","rekabet","export control"))return Type.REGULATORY;
        if(has(t,"lawsuit","dava","investigation","soruşturma","ceza"))return Type.LEGAL;
        if(has(t,"launch","product","ürün","platform"))return Type.PRODUCT;
        if(has(t,"faiz","interest rate","inflation","enflasyon","oil","petrol","war","savaş","election","seçim"))return Type.MACRO;
        if(has(t,"ceo","cfo","yönetim","board","istifa","resign"))return Type.MANAGEMENT;
        return Type.OTHER;
    }
    private static boolean has(String t,String... k){for(String x:k)if(t.contains(x))return true;return false;}
}
