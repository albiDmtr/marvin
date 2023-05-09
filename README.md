<img src="https://raw.githubusercontent.com/albiDmtr/marvin/main/logo_long.png"  width="800" height="auto">

<h1 style="font-family: Roboto;">◤¯¯◥ marvin</h1>

**A trading bot for trading stablecoins on the KuCoin exchange**

This is a project I started in 2020 when I became interested in automated cryptocurrency trading and that's when the bulk of the code was written. It was written in Python and uses a strategy that profits off instances when stablecoin pairs such as `DAI/USDC` or `USDT/USDC` depeg, that is the rate goes significantly below or above the 1:1 ratio. Given this is a simple strategy, I was able to achieve some success with it but nothing crazy.

The bot is also easily extendable, so new exchanges and strategies can be added effortlessly.

# The strategy
The bot trades on stablecoin pairs, which are cryptocurrencies that have their value pegged to the dollar either because they are backed by the dollar or because of a central bank algorithm. Because of this, the exchange rate of all stablecoin pairs should be 1, but in the short term there is some fluctuation from the 1:1 ratio. We assume that, in the long run, the price will revert near it's intended value. That's what the bot uses to spot opportunities when the price is unusually low or high and uses it to make profitable trades.<br>**Here is how it's intended to work:**
<img src="https://raw.githubusercontent.com/albiDmtr/marvin/main/example.png"  width="800" height="auto">



# Setup and usage

<div style="background-color:#ed736b; color:white; padding:5px; border-radius:4px; border:solid 3px #c94f47;">**DISCLAIMER: The bot hasn't been tested thoroughly. Bugs and crashes are possible hence I don't recommend using it live without understanding the code.**</div>

## Setup
1. **Clone this repository to have a copy of the files locally**
2. **Get API keys from KuCoin (and setup your account if needed):**
> More information about this can be found on **[this](https://www.kucoin.com/support/360015102174 "this")** page
3. **In the project root directory, there is a folder called `keys`. Paste your API credentials there in the form provided by the example file` KuCoin.json`.**
4. **Setup the email account to get notifications to**
> [As Google changed its policy in 2022, apps can no longer sign in to Google accounts using only username and password](https://support.google.com/accounts/answer/6010255?hl=en "As Google changed its policy in 2022, apps can no longer sign in to Google accounts using only username and password"). The bot is currently unable to send you notifications about events, but a solution that uses Telegram is on the way.
5. **Configure ``core.py``**
You can edit the parameters of the strategy by setting the following global variables:
- `strat_name`: The name of the file inside the strat folder that contains the strategy being used. Currently the only option is `stablecoin_depeg`.
- `ex_name`: Specifies what exchange connector should the bot look for. Currently only `KuCoin` connector is implemented.
- `pair`: The market the bot should trade on, in a slash-separated format, e.g.: `"DAI/USDT"`.
- `tick_time_s`: Specifies how often should the bot run the strategy to check if there are opportunities. It's not recommended to change it as it can cause problems with API rate limits.
- `strat_specific_params`: A JSON object specifying parameters specific to the strategy being used. For the `stablecoin_depeg` strategy, these are the following:
- `ma_dp_count`: The number of datapoints the bot should use to calculate the moving average of the price. The default value is `25`.
- `ma_res`: Specifies the time intervals at which the bot should take a new datapoints into the calculation of the moving average. Default value is `"5m"`, other values are in the format: `<integer><s/m/h>`, where `s` stands for second, `m` for minutes, and `h` for hours.

> For example, an `ma_dp_count` of `25` and an `ma_res` of `"5m"` means that the strategy calculates the moving average based on the last 25 snapshots of the price that were recorded at 5 minute intervals

- `threshold`: A float between 0 and 1. A lower number means that the bot will make an order only if the price is very extreme, while a higher number means that the bot will make orders more frequently. The default value is `0.3`, which means that the bot will only buy if the current price is lower than 70% of the price snapshots in its memory, and sell if the price is higher than 70% of the price snapshots is its memory.

## Usage
Once everything is set up just run core.py:
```
python -u ./core.py
```
Or you can also build a Docker image from it, there is a `Dockerfile` to help with that.