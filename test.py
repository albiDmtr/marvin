import bisect
import time
import ccxt.async_support as ccxt
import asyncio
# Switching to sandbox
kucoin = ccxt.kucoin()

#kucoin.urls['api'] = kucoin.urls['test']

#kucoin.apiKey = "5f8874a0b654b6000630d9b6"
#kucoin.secret = "cf0a60d6-6d44-437e-8f68-f635efea4e22"
#kucoin.password = "marvin_sandbox"
"""
async def vau(loop):
	# mi van az idővel?
	# Meg van adva a res és a datapoint count
	await kucoin.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(vau(loop))"""

def test(a, b=False):
    print(b)

test('heló',True)