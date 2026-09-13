package com.kulanoglu.borsaradar;

/** Portfoy icin teknik emri tekrar etmek yerine pozisyon yonetim etiketi uretir. */
public final class PositionActionLabelEngine {
    private PositionActionLabelEngine(){}
    public static String label(ShortPulseEngine.Result t,CatalystContextEngine.Result c,double cost){
        if(t==null)return "VERI BEKLE";
        DecisionContextEngine.Result d=DecisionContextEngine.evaluate(t,c);
        double pnl=cost>0?(t.price/cost-1)*100:0;
        if("CIFT TEYIT NEGATIF".equals(d.state))return "RISKI AZALTMA ADAYI";
        if("SATIS SINYALI TEYITSIZ".equals(d.state))return "ACELE SATMA / TEYIT BEKLE";
        if("CIFT TEYIT POZITIF".equals(d.state)&&pnl<15)return "KORU / GUCLU";
        if("ALIS SINYALI TEYITSIZ".equals(d.state))return "YENI ALIMDA BEKLE";
        return "KORU / IZLE";
    }
}
