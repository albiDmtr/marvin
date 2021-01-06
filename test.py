import ccxt

# stampből utc idő:
"""from datetime import datetime
datetime.utcfromtimestamp(1609911921339.3743/1000).strftime('%Y-%m-%d %H:%M:%S')"""



kcon = ccxt.kucoin()

# a fetch ohlcv csak régebbi adatokkal megy
print(kcon.fetchTicker('USDJ/USDT'))

# Jól számol a bot since-t.
