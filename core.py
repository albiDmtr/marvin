# ő lesz lefuttatva, amikor elindul
import time
import importlib
import json
import asyncio
import hypers
from termcolor import colored, cprint
import logging
import marvin_console
import interface.push_notifications
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# parameters
strat_name = 'stablecoin_depeg'
ex_name = 'KuCoin'
#pair = 'USDT/USDC, USDT/DAI, USDT/TUSD, USDT/PAX, SUSD/USDT, USDN/USDT' # Format: "/" separated
pair = 'USDJ/USDT'
tick_time_s = 2
strat_specific_params = {
	'ma_dp_count':25,
	'ma_res':'5m',
	'threshold':0.3
}
"""strat_specific_params = [{
	'ma_dp_count':25,
	'ma_res':'5m',
	'threshold':0.3
},
{
	'ma_dp_count':25,
	'ma_res':'5m',
	'threshold':0.3
},
{
	'ma_dp_count':25,
	'ma_res':'5m',
	'threshold':0.3
},
{
	'ma_dp_count':25,
	'ma_res':'5m',
	'threshold':0.3
},
{
	'ma_dp_count':25,
	'ma_res':'5m',
	'threshold':0.3
},
{
	'ma_dp_count':25,
	'ma_res':'5m',
	'threshold':0.3
}]"""

# logic
if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	#loop.set_exception_handler(push_notifications.exception)

async def import_modules():
		logging.info(colored('Initialising market and strategy...','cyan','on_yellow'))
		global market
		global strat
		market = await importlib.import_module(f'connectors.{ex_name}').create_market(pair)
		strat = await importlib.import_module('strat.'+strat_name).create_strat(market, loop, strat_specific_params=strat_specific_params)
		logging.info(colored('Finisihed initialising. Marvin is now active.','cyan','on_yellow'))
		print(marvin_console.marvin_ascii)
		# !!!!TANULSÁG: NE OLVASGASS, HANEM TESZTELJ MINDENT, ÚGY DERÜLNEK KI A DOLGOK!!
		# 

async def main():
	i = 0
	await import_modules()
	while True:
		print(f'Tick no. {i}                        ', end="\r")
		await strat.exec()
		i +=1
		await asyncio.sleep(tick_time_s)

if __name__ == '__main__':
	loop.create_task(main())
	loop.run_forever()