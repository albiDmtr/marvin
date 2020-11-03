# ő lesz lefuttatva, amikor elindul
import time
import importlib
import json
import asyncio
import hypers
from termcolor import colored, cprint
import logging
import marvin_console
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# parameters
strat_name = 'stablecoin_depeg'
ex_name = 'KuCoin'
pair = 'USDT/DAI' # Format: "/" separated
tick_time_s = 2
strat_specific_params = {
	'ma_dp_count':25,
	'ma_res':'5m',
	'threshold':0.2
}

# logic
if __name__ == '__main__':
	loop = asyncio.get_event_loop()

async def import_modules():
		logging.info(colored('Initialising market and strategy...','cyan','on_yellow'))
		global market
		global strat
		market = await importlib.import_module(f'connectors.{ex_name}').create_market(pair)
		strat = await importlib.import_module('strat.'+strat_name).create_strat(market, loop, strat_specific_params=strat_specific_params)
		logging.info(colored('Finisihed initialising. Marvin is now active.','cyan','on_yellow'))
		print(marvin_console.marvin_ascii)
		# TODO:
		# kód végigolvasás, nagyjából oké? (core.py megvan, )
		# csinál ez a bot tradeket? (menjen, oszt majd kiderül)
		# menjen fel píz a kucoinra, menjen a bot cloudba
		# csináljuk meg a sanity checkeket
		#
		# Nem megy ez a geci. Mi van? Lehet, hogy az árakat nem jól kapja, meg lehet, hogy a logic szar
		# (külön lehet, hogy egy kicsivel szigorúbb).
		# Vagy egy balance emulátort csinálunk, vagy már csak élesben fog tudni menni.
		# Írjuk meg gyorsbaokosba a tesztet

async def main():
	i = 0
	await import_modules()
	while True:
		print(f'Tick no. {i}                        ', end="\r")
		await strat.exec()
		i +=1
		await asyncio.sleep(tick_time_s)

if __name__ == '__main__':
	loop.run_until_complete(main())