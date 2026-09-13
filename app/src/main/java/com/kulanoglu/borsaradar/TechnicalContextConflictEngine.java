package com.kulanoglu.borsaradar;

/** Teknik görünüm ile bilgi akışının aynı mı ters mi yönde olduğunu sınıflar. */
public final class TechnicalContextConflictEngine {
    private TechnicalContextConflictEngine(){}
    public enum State { CONFIRMED_POSITIVE, CONFIRMED_NEGATIVE, POSITIVE_CONTEXT_CONFLICT, NEGATIVE_CONTEXT_CONFLICT, NEUTRAL }
    public static State classify(double technical,double context,boolean hasContext){
        if(!hasContext)return State.NEUTRAL;
        if(technical>=1.3&&context>=2.5)return State.CONFIRMED_POSITIVE;
        if(technical<=-1.3&&context<=-2.5)return State.CONFIRMED_NEGATIVE;
        if(technical<=-1.3&&context>=2.5)return State.POSITIVE_CONTEXT_CONFLICT;
        if(technical>=1.3&&context<=-2.5)return State.NEGATIVE_CONTEXT_CONFLICT;
        return State.NEUTRAL;
    }
    public static String label(State s){
        switch(s){
            case CONFIRMED_POSITIVE:return "TEKNİK + BİLGİ POZİTİF";
            case CONFIRMED_NEGATIVE:return "TEKNİK + BİLGİ NEGATİF";
            case POSITIVE_CONTEXT_CONFLICT:return "TEKNİK ZAYIF / BİLGİ POZİTİF";
            case NEGATIVE_CONTEXT_CONFLICT:return "TEKNİK POZİTİF / BİLGİ NEGATİF";
            default:return "KARIŞIK / NÖTR";
        }
    }
}
