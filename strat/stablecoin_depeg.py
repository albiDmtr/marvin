import time
import math
import hypers
import bisect
import asyncio
import os.path

async def create_strat(market, loop, strat_specific_params={'ma_dp_count':'25','ma_res':'5m','threshold':0.2}):
	obj = strat(market, strat_specific_params)
	await obj._init(loop)
	return obj

# !!! Pár percente vannak tradek, úgyhogy a botnak tudnia kell választani a market és a limit orderek közt
class strat():
	def __init__(self, market, strat_specific_params={'ma_dp_count':'25','ma_res':'5m','threshold':0.2}):
		self.threshold = strat_specific_params['threshold']
		self.ma_dp_count = strat_specific_params['ma_dp_count']
		self.ma_res = strat_specific_params['ma_res']
		self.market = market

	# ITTARTUNK a kód validálással, olyan sorrendben megyünk, ahogy tényleg történnek a dolgok
	async def _init(self, loop):
		self.price_store = await self.market.create_price_store(self.ma_dp_count, self.ma_res, self.market.pair, loop)
		self.fees = await self.market.get_trading_fees()
		self.min_amount = await self.market.get_min_amount()
		print({"type":"info","msg":"market initialized","balances":await self.market.get_balance("total")})

	# verified (legfeljebb 1 orderrel téved list slicing miatt, azt meg leszarjuk)
	async def calculate_max_order_size(self, side, threshold, past_prices):
			self.orders = await self.market.get_current_book()
			self.orders = self.orders[side]
			self.listed_orders = [x[0] for x in self.orders]
			self.average = sum(past_prices) / len(past_prices)
			print({"type":"calculating_size","side":side,"threshold":threshold,"average":self.average,"book":self.orders})

			def amount_above(limit, fees=False):
				# ez egyet téved
				if fees:
					self.applied_fees = self.fees['taker']
				else:
					self.applied_fees = 0

				if side == 'asks':
					self.limit_index = bisect.bisect(self.listed_orders, limit/(1+self.applied_fees))
				elif side == 'bids':
					self.reverse_orders = self.listed_orders.copy()
					self.reverse_orders.reverse()
					self.limit_index = len(self.reverse_orders) - bisect.bisect(self.reverse_orders, limit/(1-self.applied_fees))
				else:
					print({"type":"error","msg":"Side must be either asks or bids to calculate max order size."})
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
		current_rates = await self.market.get_current_price('both')
		print({"type":"current_rates","msg":current_rates})

		if current_rates['ask'] < self.lower_threshold:
			balance = await self.market.get_balance('total')
			if balance[self.market.quote] > hypers.min_stablecoin_trade_amount:
				print({"type":"examining_swap","to":"base"})
				# examine swap to base
				max_size = await self.calculate_max_order_size('asks', self.lower_threshold, self.past_prices)
				if max_size >= self.min_amount:
					print({"type":"executing_from_strat","to":"base"})
					await self.market.swap_to(self.market.base,'market',swap_to_amount=max_size,cut_overspending=True)
					print({"type":"executed_from_strat","to":"base","at":current_rates["ask"],"balances":balance})

		if current_rates['bid'] > self.upper_threshold:
			balance = await self.market.get_balance('total')
			if balance[self.market.base] > hypers.min_stablecoin_trade_amount:
				print({"type":"examining_swap","to":"quote"})
				# examine swap to quote
				max_size = await self.calculate_max_order_size('bids', self.upper_threshold, self.past_prices)
				# különben itt a min_amount nem teljesen jó, mert swap_from amountban van
				if max_size >= self.min_amount:
					print({"type":"executing_from_strat","to":"quote"})
					await self.market.swap_to(self.market.quote,'market',swap_to_amount=max_size,cut_overspending=True)
					print({"type":"executed_from_strat","to":"quote","at":current_rates["bid"],"balances":balance})