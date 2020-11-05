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
		# A botnak nem muszáj felhő tesztüzemben, de nagyon nem baj.
		# És vannak más dolgok, amiket szintén lehetne rajta csinálni tesztüzemben is, multimarket tipikusan ilyen.
		# Az van a felhővel hogy amúgy pár óra, csak nem értünk hozzá.
		# Egyelőre haggyuk a felhőt, upgradeket csinálunk.
		# Upgradek:
		#	Multimarket
		# 	Ezt hogyan tudjuk megoldani?
		#	Oké, több market instance lesz, ez tök egyértelmű
		# 	Sandbox tudja ezt kezelni?
		#	stratnál pedig összekötünk mindent mindennel, és a legjobb dealbe rakjuk a pízt
		#	viszont itt már kellhet gondolkodni, hogy mikor éri meg berakni, nem-e?
		#	
		# Order blacklisting vagy multimarket?
		#	Egyelőre nem tudni, megy-e a bot, a multimarketet érdemes lehet megcsinálni akkor is ha nem megy.
		#	Az order blacklisting pedig ameddig tesztüzemben van, egy biztosabb képet tud adni, megy-e.
		# 
		# Miért csinál ilyen kicsi ordereket? Tényleg vannak bent 1 centes orderek?
		# A mid árakat látva, tényleg addig tradel a bot, ameddig el nem viszi más az adott ordert?

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