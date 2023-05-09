import ccxt.async_support as ccxt
import os.path
import logging
from helpers import virtual_tx
slippage_logger = logging.getLogger('slippage')
slippage_hdlr = logging.FileHandler(f'{os.path.dirname(__file__)}/../logs/slippages.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
slippage_hdlr.setFormatter(formatter)
slippage_logger.addHandler(slippage_hdlr)

class sandbox_kucoin(ccxt.kucoin):
    def __init__(self, balance=None, config={}):
        super().__init__(config=config)
        # use test balance if available else use real balance on exchange
        self.test_balance = balance if balance else self.__fetch_real_balance()
    
    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        if type != 'market':
            raise ValueError()
        self.base = symbol.split('/')[0]
        self.quote = symbol.split('/')[1]

        # checking if amount bigger than minimum
        markets = await self.fetch_markets()
        min_amount = list(filter(lambda x: (x['symbol'] == symbol), markets))[0]['limits']['amount']['min']
        if amount < min_amount:
            raise ValueError('Amount is under min amount.')

        # logging
        book = await self.fetch_l2_order_book(symbol)
        slippage_logger.info(f"Orderbook is: {book['asks'] if side == 'buy' else book['bids']}")
        slippage_logger.info(f'{amount} {self.base} {side} transaction on {symbol} market at KuCoin.')

        # updating balances
        amount_in = 'to' if side == 'buy' else 'from'
        quote_amount = virtual_tx(book,side,amount,amount_in)
        if side == 'buy' and self.test_balance['free'][self.quote] >= quote_amount:
            self.test_balance['free'][self.base] += amount
            self.test_balance['total'][self.base] += amount
            self.test_balance['free'][self.quote] -= quote_amount
            self.test_balance['total'][self.quote] -= quote_amount
        elif side == 'sell' and self.test_balance['free'][self.base] >= amount :
            self.test_balance['free'][self.base] -= amount
            self.test_balance['total'][self.base] -= amount
            self.test_balance['free'][self.quote] += quote_amount
            self.test_balance['total'][self.quote] += quote_amount
        else:
            raise ValueError('Insufficient fund or incorrect side.')
    
    async def fetch_balance(self):
        return self.test_balance
    
    def __fetch_real_balance(self, params={}):
        self.load_markets()
        type = None
        request = {}
        if 'type' in params:
            type = params['type']
            if type is not None:
                request['type'] = type
            params = self.omit(params, 'type')
        else:
            options = self.safe_value(self.options, 'fetchBalance', {})
            type = self.safe_string(options, 'type', 'trade')
        response = self.privateGetAccounts(self.extend(request, params))
        data = self.safe_value(response, 'data', [])
        result = {'info': response}
        for i in range(0, len(data)):
            balance = data[i]
            balanceType = self.safe_string(balance, 'type')
            if balanceType == type:
                currencyId = self.safe_string(balance, 'currency')
                code = self.safe_currency_code(currencyId)
                account = self.account()
                account['total'] = self.safe_float(balance, 'balance')
                account['free'] = self.safe_float(balance, 'available')
                account['used'] = self.safe_float(balance, 'holds')
                result[code] = account
        return self.parse_balance(result)

