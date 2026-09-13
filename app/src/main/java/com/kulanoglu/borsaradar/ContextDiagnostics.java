package com.kulanoglu.borsaradar;

/** Kaynak sorunlarini kullaniciya teknik hata yigmadan kisa tanilar. */
public final class ContextDiagnostics {
    private ContextDiagnostics(){}
    public static String label(UnifiedContextService.Result r){
        if(r==null)return "Baglam motoru sonucu yok";
        if(r.newsOk&&r.kapOk)return "Haber + KAP erisimi aktif";
        if(r.newsOk)return "Haber aktif • KAP erisimi yok/bos";
        if(r.kapOk)return "KAP aktif • haber erisimi yok/bos";
        return "Canli baglam kaynaklarina erisim yok";
    }
}
