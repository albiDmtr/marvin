import time
import importlib
import json
import asyncio
import hypers
import marvin_console
from termcolor import colored, cprint
import interface.push_notifications

# parameters
strat_name = 'stablecoin_depeg'
ex_name = 'KuCoin'
pair = 'USDJ/USDT' # Format: "/" separated
tick_time_s = 2
strat_specific_params = {
	'ma_dp_count':25,
	'ma_res':'5m',
	'threshold':0.3
}

# logic
if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.set_exception_handler(interface.push_notifications.exception)


async def import_modules():
		marvin_console.info("starting up")
		global market
		global strat
		market = await importlib.import_module(f'connectors.{ex_name}').create_market(pair)
		strat = await importlib.import_module('strat.'+strat_name).create_strat(market, loop, strat_specific_params=strat_specific_params)
		marvin_console.info("running")

async def main():
	i = 0
	await import_modules()
	while True:
		await strat.exec()
		i +=1
		await asyncio.sleep(tick_time_s)

if __name__ == '__main__':
	loop.create_task(main())
	loop.run_forever()