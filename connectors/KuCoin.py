import ccxt.async_support as ccxt
import os.path
import time
import json
import asyncio
import marvin_console
import hypers
import interface.push_notifications
from helpers import virtual_tx

except_count = 0
while except_count < hypers.HTTP_API_retry_count:
	try:
		KuCoin = ccxt.kucoin({
			'enableRateLimit': True
		})
		# Switching to sandbox
		# KuCoin.urls['api'] = KuCoin.urls['test']
		with open(os.path.dirname(__file__) + '/../keys/KuCoin_LIVE.json', 'r') as json_file:
			keys = json.load(json_file)
			KuCoin.apiKey = keys['Public']
			KuCoin.secret = keys['Private']
			KuCoin.password = keys['Password']
		keys = None
		except_count = 0
		break
	except Exception as e:
		except_count += 1
		marvin_console.warning(f'Unable to initialise KuCoin connector ({except_count}. try).')
		if except_count >= hypers.HTTP_API_retry_count:
			marvin_console.error(f'KuCoin connector was unable to initialise {except_count} times. Error: {e}')
			raise

async def create_market(pairs):
	pairs = pairs.split(', ')
	objs = []
	for pair in pairs:
		obj = market(pair)
		await obj._init()
		objs.append(obj)
	if len(objs) == 1:	
		return objs[0]
	else:
		return objs

class market:
	def __init__(self, pair):
		self.pair = pair
		self.ex = KuCoin
		self.base = pair.split('/')[0]
		self.quote = pair.split('/')[1]

	async def _init(self):
		await self.ex.load_markets()

	async def create_price_store(self, dp_count, res, pair, loop):
		obj = self.price_store()
		await obj._init(dp_count, res, pair)
		loop.create_task(obj.activate())
		return obj

	class price_store:
		async def _init(self, dp_count, res, pair):
			self.ex = KuCoin
			self.pair = pair
			self.__is_active = True
			self.__res = res
			self.dp_count = dp_count
			self.__time_increment = {
				's' in self.__res : [1,'s'],
				'm' in self.__res : [60,'m'],
				'h' in self.__res : [3600, 'h']
			}
			self.__res_in_s = self.__time_increment[True][0] * int( self.__res.split( self.__time_increment[True][1] )[0] )
			since = ( time.time() - (self.__res_in_s*self.dp_count) )* 1000

			self.__historical = await self.__get_historical_OHLCV(since,res=self.__res)
			if self.__historical:
				self.__prices = [x[0:2] for x in self.__historical]
			else:
				marvin_console.info('Unable to get OHLCV, used current prices instead.')
				except_count = 0
				while except_count < hypers.HTTP_API_retry_count:
					try:
						self.__current = await self.ex.fetchTicker(self.pair)
						self.__prices = [[self.__current['timestamp'], (self.__current['bid'] + self.__current['ask']) / 2] for x in range(len(self.dp_count))]
						except_count = 0
						break
					except Exception as e:
						except_count += 1
						marvin_console.warning(f'KuCoin Unable to get current price at init. ({except_count}. try).')
						if except_count >= hypers.HTTP_API_retry_count:
							marvin_console.error(f'KuCoin Get current price at init. {except_count} times. Error: {e}')
							raise

			# remove additional dps
			if len(self.__prices) > dp_count:
				del self.__prices[0:(len(self.__prices)-dp_count)]
			# add temporary dps if needed
			self.temporary_dps_added = 0
			while len(self.__prices) < dp_count:
				self.temporary_dps_added += 1
				self.__prices.append([time.time()*1000,sum([x[1] for x in self.__prices])/len(self.__prices)])

		async def activate(self):
			# wait until next candle is arrived
			await asyncio.sleep( max([self.__res_in_s - (time.time() - (self.__prices[-1][0] / 1000)),0]) )
			except_count = 0
			while(self.__is_active):
				# update prices
				try:
					self.__current_ticker = await self.ex.fetchTicker(self.pair)
					except_count = 0
					# delete temporary dps if added
					if self.temporary_dps_added:
						del self.__prices[-self.temporary_dps_added:]
						self.temporary_dps_added = False
					
					if not None in self.__current_ticker.values():
						self.__prices.append([self.__current_ticker['timestamp'],(self.__current_ticker['bid']+self.__current_ticker['ask'])/2])
					else:
						self.__prices.append(self.__prices[-1])

					del self.__prices[0]
					marvin_console.info('Price store updated.', custom_field={'current value':self.__prices})
					await asyncio.sleep(self.__res_in_s)
				except Exception as e:
					except_count += 1
					marvin_console.warning(f'KuCoin Price store is unable to update prices ({except_count}. try).')
					await asyncio.sleep(hypers.HTTP_API_retry_sleep_s)
					if except_count >= hypers.HTTP_API_retry_count:
						marvin_console.error(f'KuCoin Price store was unable to update prices {except_count} times. Error: {e}')
						raise

		async def __get_historical_OHLCV(self, since,til='now',res='5m'):
			data, current_last_stamp = [], since
			except_count = 0
			# translating res to ms
			self.__time_increment = {
					's' in res : [1000,'s'],
					'm' in res : [60000,'m'],
					'h' in res : [3600000, 'h']
				}
			self.__res_in_ms = self.__time_increment[True][0] * int( res.split( self.__time_increment[True][1] )[0] )
			while (current_last_stamp+self.__res_in_ms < (til if til != 'now' else time.time()*1000)):
				await asyncio.sleep(self.ex.rateLimit / 1000)
				try:
					current_data = await self.ex.fetch_ohlcv(symbol=self.pair, timeframe=res, since=current_last_stamp)
					if len(data) and current_data[-1] == data[-1]:
						marvin_console.warning('fetchOHLCV last candle delay!')
						break
					if len(data) and current_data[0] == data[0]:
						marvin_console.warning('Accidental FetchOHLCV datapoint duplication!')
					data += current_data
					current_last_stamp = data[-1][0]
					except_count = 0
				except Exception as e:
					except_count += 1
					marvin_console.warning(f'KuCoin Unable to fetch historical OHLCV ({except_count}. try).')
					if except_count >= hypers.HTTP_API_retry_count:
						marvin_console.error(f'Kucoin was unable to fetch historical OHLCV {except_count} times. Error: {e}')
						#raise
			return data

		def get_past_prices(self):
			return self.__prices


		def last_candle_age(self):
			# in ms
			return time.time()*1000 - self.__prices[-1][0]

		def deactivate(self):
			self.__is_active = False

	async def get_current_price(self,side):
		except_count = 0
		while except_count < hypers.HTTP_API_retry_count:
			try:
				self.__current = await self.ex.fetchTicker(self.pair)
				marvin_console.info('Current rates',custom_field={'rates':self.__current})
				except_count = 0
				break
			except Exception as e:
				except_count += 1
				marvin_console.warning(f'KuCoin Unable to get current mid price ({except_count}. try).')
				if except_count >= hypers.HTTP_API_retry_count:
					marvin_console.error(f'KuCoin Get current mid price failed {except_count} times. Error: {e}')
					raise
		if side == 'mid':
			return (self.__current['bid']+self.__current['ask'])/2
		elif side == 'ask':
			return self.__current['ask']
		elif side == 'bid':
			return self.__current['bid']
		elif side == 'both':
			return {'bid':self.__current['bid'],'ask':self.__current['ask']}

	async def get_current_book(self):
		except_count = 0
		while except_count < hypers.HTTP_API_retry_count:
			try:
				# format: {'bids':[[rate,size],...],'asks':[[rate,size],...]}
				val= await self.ex.fetch_l2_order_book(self.pair)
				except_count = 0
				return val
			except Exception as e:
				except_count += 1
				marvin_console.warning(f'KuCoin Unable to get current orderbook ({except_count}. try).')
				if except_count >= hypers.HTTP_API_retry_count:
					marvin_console.error(f'KuCoin Get current mid price failed {except_count} times. Error: {e}')
					raise

	async def get_balance(self, funds_type, currency=False):
		except_count = 0
		while except_count < hypers.HTTP_API_retry_count:
			try:
				# funds_type: free/used/total
				fetched_bal = await self.ex.fetch_balance()
				if currency:
					if currency in fetched_bal[funds_type]:
						balance = fetched_bal[funds_type][currency]
					else:
						balance = 0
				else:
					balance = fetched_bal[funds_type]
					if self.base not in fetched_bal[funds_type]:
						fetched_bal[funds_type][self.base] = 0
					if self.quote not in fetched_bal[funds_type]:
						fetched_bal[funds_type][self.quote] = 0
				except_count = 0
				return balance
			except Exception as e:
				except_count += 1
				marvin_console.warning(f'KuCoin Unable to get balance ({except_count}. try).')
				if except_count >= hypers.HTTP_API_retry_count:
					marvin_console.error(f'KuCoin Get balance failed {except_count} times. Error: {e}')
					raise

	# magától cutolja az orderbook végénél, tehát nem biztos, hogy hogy annyit swapol, mint mondva van neki
	async def swap_to(self, currency_to_buy,order_type,swap_to_amount=False,swap_from_amount=False,cut_overspending=True,limit_rate=False):

		# checking if amount given
		if not swap_to_amount and not swap_from_amount:
			raise ValueError('Unkown amount to swap, either swap_to_amount or swap_from_amount must be specified.')

		# deciding whether it's a buy or a sell order
		if currency_to_buy == self.pair.split('/')[0]:
			direction = 'buy'
		elif currency_to_buy == self.pair.split('/')[1]:
			direction = 'sell'
		else:
			raise ValueError(f'{currency_to_buy.capitalize()} cannot be traded on {self.pair} market.')
		
		# transforming amount to array format
		amount = []
		if swap_to_amount:
			amount += [swap_to_amount,'to']
		if swap_from_amount:
			amount += [swap_from_amount,'from']

		# logic for market orders!
		if order_type == 'market':
			# at market orders, there can only be one of swap_to_amount and swap_from_amount specified
			if bool(swap_to_amount) == bool(swap_from_amount):
				raise ValueError('Swap is supposed to happen at market price, cannot be both swap_to_amount and swap_from_amount specified.')
			
			# calculating amount, creating order
			except_count = 0
			while except_count < hypers.HTTP_API_retry_count:
				try:
					# verified, checking for overspending
					if cut_overspending:
						book = await self.get_current_book()
						# if spending quote
						if direction == 'buy':
							# if amount was given is base
							if amount[1] == 'to':
								amount[0] = min([amount[0], virtual_tx(book, 'buy', await self.get_balance('total',self.quote), 'from', dismiss_liquidity_error=True)])
							# if amount was given in quote
							else:
								amount[0] = min([amount[0], await self.get_balance('total',self.quote)])
						# if spending base
						else:
							# if amount was given in quote
							if amount[1] == 'to':
								amount[0] =  min([virtual_tx(book, 'sell', amount[0], 'to', dismiss_liquidity_error=True) , await self.get_balance('total',self.base)])
								amount[1] = 'from'
							# if amount was given in base
							else:
								amount[0] = min([amount[0], await self.get_balance('total',self.base)])

					# Changing amount to be in base currency
					if direction == 'buy':
						amount_in_base = amount[0] if amount[1] == 'to' else virtual_tx(book,'buy',amount[0],'from',dismiss_liquidity_error=True)
					elif direction == 'sell':
						amount_in_base = amount[0] if amount[1] == 'from' else virtual_tx(book,'sell',amount[0],'to',dismiss_liquidity_error=True)

					await self.ex.create_order(self.pair, order_type, direction, amount_in_base)
					except_count = 0
					break
				except Exception as e:
					except_count += 1
					marvin_console.warning(f'KuCoin Unable to create order ({except_count}. try). Error: {e}')
					if except_count >= hypers.HTTP_API_retry_count:
						marvin_console.error(f'KuCoin order creation failed {except_count} times. Error: {e}')
						raise
		# logic for limit orders!
		# TODO ez még itt nincs letesztelve
		elif order_type == 'limit':
			# calculating amount, creating order
			while except_count < hypers.HTTP_API_retry_count:
				try:
					if swap_from_amount and swap_to_amount:
						limit_rate = swap_from_amount/swap_to_amount if direction == 'buy' else swap_to_amount/swap_from_amount
						amount_in_base = swap_to_amount if direction == 'buy' else swap_from_amount
					elif limit_rate and swap_to_amount:
						amount_in_base = swap_to_amount if direction == 'buy' else swap_to_amount/limit_rate
					elif limit_rate and swap_from_amount:
						amount_in_base = swap_from_amount/limit_rate if direction == 'buy' else swap_from_amount
					else:
						raise ValueError('Not enough information given to execute limit order.')
					
					# cut overspending
					if cut_overspending:
						if direction == 'sell':
							base_bal = await self.get_balance('free',currency=self.pair.split('/')[0])
							amount_in_base = min([amount_in_base, base_bal])
						else:
							quote_bal = await self.get_balance('free',currency=self.pair.split('/')[1])
							amount_in_base = min([amount_in_base, quote_bal/limit_rate ])

					# Sanity check & order creation
					# Assumptions: direction is correct
					current_rates = await self.get_current_price('both')
					if self.pair in hypers.limit_order_accepted_rate_range:
						if ((direction == 'buy' and hypers.limit_order_accepted_rate_range[self.pair][1] >= limit_rate and
						current_rates['ask'] >= limit_rate) or
						(direction == 'sell' and hypers.limit_order_accepted_rate_range[self.pair][0] <= limit_rate and
						current_rates['bid'] <= limit_rate)):
							await self.ex.create_order(self.pair, order_type, direction, amount_in_base, limit_rate)
							# TODO küldjön üzit, hogy ordert csinált (marketnél is)
						else:
							raise ValueError('Nínónínó Sanity check failed!!')
					else:
						"""if ((direction == 'buy' and current_rates['ask'] >= limit_rate) or
						(direction == 'sell' and current_rates['bid'] <= limit_rate)):
							await self.ex.create_order(self.pair, order_type, direction, amount_in_base, limit_rate)
							# TODO küldjön üzit, hogy ordert csinált (marketnél is)
						else:
							raise ValueError('Nínónínó Sanity check failed!!')"""
						raise NotImplementedError('Placing limit orders without accepted rate range hyper is currently unsupported.')

					except_count = 0
					break
				except Exception as e:
					except_count += 1
					marvin_console.warning(f'KuCoin Unable to create limit order ({except_count}. try). Error: {e}')
					if except_count >= hypers.HTTP_API_retry_count:
						marvin_console.error(f'KuCoin limit order creation failed {except_count} times. Error: {e}')
						raise



	async def get_trading_fees(self):
		return {'taker': self.ex.fees['trading']['taker'],'maker': self.ex.fees['trading']['maker']}

	async def get_min_amount(self):
		except_count = 0
		while except_count < hypers.HTTP_API_retry_count:
			try:
				markets = await self.ex.fetch_markets()
				min_amount = list(filter(lambda x: (x['symbol'] == self.pair), markets))[0]['limits']['amount']['min']
				return min_amount
			except Exception as e:
				except_count += 1
				marvin_console.warning(f'KuCoin Unable to get min amounts ({except_count}. try).')
				await asyncio.sleep(hypers.HTTP_API_retry_sleep_s)
				if except_count >= hypers.HTTP_API_retry_count:
					marvin_console.error(f'KuCoin get min amount failed {except_count} times. Error: {e}')
					raise

	async def drop_exchange(self):
		self.ex.close()