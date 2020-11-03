import time
import math
import hypers
import bisect
import logging
import asyncio
import os.path

# configuring logger
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
trades_logger = logging.getLogger('trades')
trades_hdlr = logging.FileHandler(f'{os.path.dirname(__file__)}/../logs/results/trades.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
trades_hdlr.setFormatter(formatter)
trades_logger.addHandler(trades_hdlr)

async def create_strat(market, loop, strat_specific_params={'ma_dp_count':'25','ma_res':'5m','threshold':0.2}):
	obj = strat(market, strat_specific_params)
	await obj._init(loop)
	return obj

class strat():
	def __init__(self, market, strat_specific_params={'ma_dp_count':'25','ma_res':'5m','threshold':0.2}):
		self.threshold = strat_specific_params['threshold']
		self.ma_dp_count = strat_specific_params['ma_dp_count']
		self.ma_res = strat_specific_params['ma_res']
		self.market = market
		self.money_in_base = self.market.balance
		self.money_in_base = self.money_in_base['base'] if self.money_in_base['base'] > self.money_in_base['quote'] else self.money_in_base['quote']

	# ITTARTUNK a kód validálással, olyan sorrendben megyünk, ahogy tényleg történnek a dolgok
	async def _init(self, loop):
		self.price_store = await self.market.create_price_store(self.ma_dp_count, self.ma_res, self.market.pair, loop)
		self.fees = await self.market.get_trading_fees()
		trades_logger.info(f'Market initialised, balances: {self.market.balance}')

	# verified (legfeljebb 1 orderrel téved list slicing miatt, azt meg leszarjuk)
	async def calculate_max_order_size(self, side, threshold, past_prices):
			self.orders = await self.market.get_current_book()
			self.orders = self.orders[side]
			self.listed_orders = [x[0] for x in self.orders]
			self.average = sum(past_prices) / len(past_prices)

			def amount_above(limit, fees=False):
				if fees:
					self.applied_fees = fees['taker']
				else:
					self.applied_fees = 0

				if side == 'asks':
					self.limit_index = bisect.bisect(self.listed_orders, limit/(1+self.applied_fees))
				elif side == 'bids':
					self.listed_orders.reverse()
					self.limit_index = len(self.listed_orders) - bisect.bisect(self.listed_orders, limit/(1-self.applied_fees))
				else:
					logging.error('Side must be either asks or bids to calculate max order size.')
					raise ValueError()
				return sum([x[1] for x in self.orders][0:self.limit_index])

			# always returns in swap_to_amount, order price with fee should be above average price
			return min([amount_above(self.average,fees=True), amount_above(threshold)])


	async def exec(self):
		self.past_prices = [x[1] for x in self.price_store.get_past_prices()]
		self.past_prices.sort()
		# biztosamibiztos counting len of prices, even though dp_count is given
		self.prices_len = len(self.past_prices)
		self.lower_threshold = self.past_prices[math.floor( self.prices_len*self.threshold )]
		self.upper_threshold = self.past_prices[self.prices_len - math.floor( self.prices_len*self.threshold )]
		current_rate = await self.market.get_current_mid_price()	
		print(f'Current rate is {current_rate}.', end="\r")
		if current_rate < self.lower_threshold and self.market.balance['quote'] > hypers.min_stabelcoin_trade_amount:
			logging.info(f'Examining swap to {self.market.base}.')
			# examine swap to base
			max_size = await self.calculate_max_order_size('asks', self.lower_threshold, self.past_prices)
			if max_size:
				logging.info(f'Executing swap to {self.market.base}.')
				# TODO csekkolja, hogy minimum order size felett legyen
				await self.market.swap_to(self.market.base,'market',swap_to_amount=min([max_size,self.market.balance['quote']]))
				trades_logger.info(f'Swapped to {self.market.base} at {current_rate}, balances: {self.market.balance}')

		if current_rate > self.upper_threshold and self.market.balance['base'] > hypers.min_stabelcoin_trade_amount:
			logging.info(f'Examining swap to {self.market.quote}.')
			# examine swap to quote
			max_size = await self.calculate_max_order_size('bids', self.upper_threshold, self.past_prices)
			if max_size:
				logging.info(f'Executing swap to {self.market.quote}.')
				# TODO csekkolja, hogy minimum order size felett legyen
				await self.market.swap_to(self.market.quote,'market',swap_to_amount=min([max_size,self.market.balance['base']]))
				trades_logger.info(f'Swapped to {self.market.quote} at {current_rate}, balances: {self.market.balance}')