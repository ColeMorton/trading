import vectorbt as vbt

price = vbt.YFData.download("BTC-USD").get("Close")

pf = vbt.Portfolio.from_holding(price, init_cash=100)
print(pf.total_profit())

ema_fast = vbt.MA.run(price, window=11, ewm=True)
ema_slow = vbt.MA.run(price, window=17, ewm=True)
entries = ema_fast.ma_crossed_above(ema_slow)
exits = ema_fast.ma_crossed_below(ema_slow)

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100)
print(pf.total_profit())
