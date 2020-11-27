# verified
def virtual_tx(orderbook,direction,amount,amount_in,dismiss_liquidity_error=False,fee=0.001):

    # substracting fee
    amount = amount*(1-fee) if amount_in == 'from' else amount
    exchanged_amount = 0
    left = amount if amount_in == 'from' else 0
    cost = 0
    liquidity_error = True
    if direction != 'buy' and direction != 'sell' or amount_in != 'from' and amount_in != 'to':
        raise ValueError()
    orders = orderbook['asks'] if direction == 'buy' else orderbook['bids']
    
    # looping through orderbook
    for current_order in orders:
        current_order_cost = current_order[1] if direction == 'sell' else current_order[1] * current_order[0]
        current_order_exchanged = current_order[1] * current_order[0] if direction == 'sell' else current_order[1]
        if amount_in == 'from':
            if current_order_cost < left:
                exchanged_amount += current_order_exchanged
                left -= current_order_cost
            else:
                exchanged_amount += left * current_order[0] if direction == 'sell' else left / current_order[0]
                left = 0
                liquidity_error = False
                break
        elif amount_in == 'to':
            if exchanged_amount + current_order_exchanged < amount:
                exchanged_amount += current_order_exchanged
                cost += current_order_cost
            else:
                cost += (amount - exchanged_amount)/current_order_exchanged * current_order_cost
                exchanged_amount = amount
                liquidity_error = False

    # check if there were enough liquidity to use up all
    if liquidity_error and not dismiss_liquidity_error:
        raise ValueError('Not enough liquidity to perform transaction.')
    # substracting fee
    cost = cost*(1+fee) if amount_in == 'to' else cost
    # returns the amount of destination currency if from amount is given, if to amount is given returns the cost in from amount
    return exchanged_amount if amount_in == 'from' else cost