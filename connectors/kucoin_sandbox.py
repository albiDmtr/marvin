import ccxt.async_support as ccxt
import os.path
import logging
slippage_logger = logging.getLogger('slippage')
slippage_hdlr = logging.FileHandler(f'{os.path.dirname(__file__)}/../logs/slippages.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
slippage_hdlr.setFormatter(formatter)
slippage_logger.addHandler(slippage_hdlr)

class sandbox_kucoin(ccxt.kucoin):
    def __init__(self, balance=None, config={}):
        super().__init__(config=config)
        # nézze meg initkor a valódi balanceot, majd tradekkor változtassa
        self.test_balance = balance if balance else self.__fetch_real_balance()
    
    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        if type != 'market':
            raise ValueError()
        self.base = symbol.split('/')[0]
        self.quote = symbol.split('/')[1]

        # verified
        async def base_to_quote(base_amount):
            quote_amount = 0
            base_left = base_amount
            # quotet akarunk venni, sellelni akarunk, tehát mi askolnánk ha ez limit lenne, bidet veszünk
            orders = await self.fetch_l2_order_book(symbol)
            orders = orders['bids']
            slippage_logger.info(f'Orderbook is: {orders[0:3]}')
            starting_price = orders[0][0]
            for current_order in orders:
                # total price of order in base
                current_order_base_price = current_order[1]
                if current_order_base_price < base_left:
                    quote_amount += current_order[0]*current_order[1]
                    base_left -= current_order_base_price
                else:
                    quote_amount += base_left*current_order[0]
                    ending_price = current_order[0]
                    base_left = 0
                    break
            # check if there were enough liquidity to use up all base
            if base_left != 0:
                raise ValueError('Not enough liquidity.')
            slippage_logger.info(f'{amount} {self.base} {side} transaction on {symbol} market at KuCoin, starting price was {starting_price}, ending price was {ending_price}, slippage is {starting_price - ending_price}.')
            return quote_amount

        # checking if amount bigger than minimum
        markets = await self.fetch_markets()
        min_amount = list(filter(lambda x: (x['symbol'] == symbol), markets))[0]['limits']['amount']['min']
        if amount < min_amount:
            raise ValueError('Amount is under min amount.')
        
        # TERV order blacklisting
        # Vagy l3 orderbook alapján konkrét orderekkel megoldva, vagy l2-vel úgy, hogy feljegyezzük, milyen
        # ordereket használtunk fel, viszont a mennyiségeik szépen lassan fogynak, és amikor átszámolunk, ha adott
        # áron van ezen a listán, akkor csak akkorának tekintjük az ordert, amennyivel nagyobb annál, mint ami a listán van
        # 
        # Vannak orderek a bookban. Mi elhasználjuk a legjobbakat. Mások is használják őket, meg cancelelik is őket.
        # Azt kéne tudnunk megoldani, hogy kétszer ne tudjuk elhasználni ugyanazt az ordert. <- ezt az
        # Viszont idővel visszafolyna a likviditás. Igen, viszont ezt mi leszarjuk
        # Itt annyit csinál a cucc, hogy átszámol baset quoteba és levonja/hozzáadja a balancehoz
        # ÁÁCSI
        # Mindegy, melyik oldaláról fogyasztunk a booknak? Miért a bideket nézi akkor is ha venni akarunk?
        # Normális esetben azt mondod buy 1000, az exchange fogja magát, és az askokat addig pörgeti, ameddig meg
        # nincs az 1000.
        # Ez a szar viszont a bideket pörgeti addig.
        # Az orderbook asszimetrikus
        # Tényleg szar az egész?
        # Attól függően, hogy baseből váltasz át quoteba vagy quoteból basebe, más lesz a slippage
        # 

        # updating balances
        quote_amount = await base_to_quote(amount)
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
        #
        #     {
        #         "code":"200000",
        #         "data":[
        #             {"balance":"0.00009788","available":"0.00009788","holds":"0","currency":"BTC","id":"5c6a4fd399a1d81c4f9cc4d0","type":"trade"},
        #             {"balance":"3.41060034","available":"3.41060034","holds":"0","currency":"SOUL","id":"5c6a4d5d99a1d8182d37046d","type":"trade"},
        #             {"balance":"0.01562641","available":"0.01562641","holds":"0","currency":"NEO","id":"5c6a4f1199a1d8165a99edb1","type":"trade"},
        #         ]
        #     }
        #
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

