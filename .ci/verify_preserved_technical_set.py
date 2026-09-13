from pathlib import Path
root=Path('app/src/main/java/com/kulanoglu/borsaradar')
files={p.name:p.read_text(encoding='utf-8') for p in root.glob('*.java')}
joined='\n'.join(files.values())
required=[
    'EMA','RSI','MACD','ATR','CMF','CCI','Stochastic','ADX','BRTV','BRM','BRH',
    'MOST','QQE','Fibonacci','MFI','Williams','Donchian','Ichimoku',
    'BR-Pulse','FlowBreak','TrendGuard','V30-Live','ShortPulse','V35-Hybrid'
]
missing=[x for x in required if x.lower() not in joined.lower()]
engine_files=['IndicatorEngine.java','MethodEngine.java','ShortPulseEngine.java','V35HybridEngine.java','LegacyTechnicalEnsemble.java','AdditionalIndicatorEngine.java','AdvancedIndicatorEngine.java','RadarTechnicalEngine.java']
missing_files=[x for x in engine_files if x not in files]
if missing or missing_files:
    raise SystemExit('Preserved technical regression: missing names=%s missing files=%s' % (missing,missing_files))
print('Preserved technical regression guard OK: %d names, %d engine files' % (len(required),len(engine_files)))
