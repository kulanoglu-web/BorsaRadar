package com.kulanoglu.borsaradar;

public final class GlobalStockUniverse {
    private GlobalStockUniverse(){}

    public static final String[] GERMANY={
        "ADS • Adidas","AIR • Airbus","ALV • Allianz","BAS • BASF","BAYN • Bayer","BEI • Beiersdorf",
        "BMW • BMW","BNR • Brenntag","CBK • Commerzbank","CON • Continental","DB1 • Deutsche Boerse",
        "DBK • Deutsche Bank","DHL • DHL Group","DTE • Deutsche Telekom","EOAN • E.ON","FRE • Fresenius",
        "HEI • Heidelberg Materials","HEN3 • Henkel","IFX • Infineon","MBG • Mercedes-Benz Group",
        "MRK • Merck KGaA","MTX • MTU Aero Engines","MUV2 • Munich Re","P911 • Porsche AG",
        "PAH3 • Porsche SE","QIA • Qiagen","RHM • Rheinmetall","SAP • SAP","SIE • Siemens",
        "ENR • Siemens Energy","SHL • Siemens Healthineers","SY1 • Symrise","VOW3 • Volkswagen",
        "VNA • Vonovia","ZAL • Zalando","S92 • SMA Solar","NCH2 • Thyssenkrupp Nucera",
        "TKA • Thyssenkrupp","EVT • Evotec","AFX • Carl Zeiss Meditec","G1A • GEA Group"
    };

    public static final String[] USA={
        "AAPL • Apple","ABBV • AbbVie","ABNB • Airbnb","AMD • AMD","AMGN • Amgen","AMZN • Amazon",
        "AVGO • Broadcom","BA • Boeing","BAC • Bank of America","BRK-B • Berkshire Hathaway",
        "CAT • Caterpillar","COST • Costco","CRM • Salesforce","CSCO • Cisco","CVX • Chevron",
        "DIS • Walt Disney","GE • GE Aerospace","GOOG • Alphabet C","GOOGL • Alphabet A",
        "HD • Home Depot","IBM • IBM","INTC • Intel","JNJ • Johnson & Johnson","JPM • JPMorgan",
        "KO • Coca-Cola","LLY • Eli Lilly","MA • Mastercard","META • Meta Platforms","MMM • 3M",
        "MRK • Merck & Co","MSFT • Microsoft","NFLX • Netflix","NKE • Nike","NVDA • NVIDIA",
        "ORCL • Oracle","PEP • PepsiCo","PFE • Pfizer","PG • Procter & Gamble","PLTR • Palantir",
        "PYPL • PayPal","QCOM • Qualcomm","SBUX • Starbucks","T • AT&T","TSLA • Tesla",
        "TXN • Texas Instruments","UNH • UnitedHealth","V • Visa","VZ • Verizon","WMT • Walmart",
        "XOM • Exxon Mobil","XWEL • XWELL"
    };

    public static String code(String entry){
        if(entry==null)return "";
        int k=entry.indexOf(" • ");
        return (k>0?entry.substring(0,k):entry).trim().toUpperCase();
    }
}
