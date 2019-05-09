from octobot_websockets import TRADES, TICKER, L2_BOOK, CANDLE, TimeFrames
from octobot_websockets.bitmex.bitmex import Bitmex
from octobot_websockets.callback import TradeCallback, TickerCallback, BookCallback, CandleCallback


async def ticker(feed, symbol, bid, ask, last, timestamp):
    print(f'[{timestamp}][TICKER] Feed: {feed} Pair: {symbol} Bid: {bid} Ask: {ask} Last : {last}')


async def trade(feed, symbol, timestamp, side, amount, price):
    print(
        f"[{timestamp}][TRADE] Feed: {feed} Pair: {symbol} Side: {side} Amount: {amount} Price: {price}")


async def book(feed, symbol, asks, bids, timestamp):
    print(f'[{timestamp}][ORDER BOOK] Feed: {feed} Pair: {symbol} Book Bids are {bids}')
    print(f'[{timestamp}][ORDER BOOK] Feed: {feed} Pair: {symbol} Book Asks are {asks}')


async def candle(feed, symbol, timestamp, time_frame, close, volume, high, low, opn):
    print(f'[{timestamp}][CANDLE] Feed: {feed} TimeFrame: {time_frame} Pair: {symbol} Close: {close} Volume: {volume} High: {high} Low: {low} Open: {opn}')


async def funding(**kwargs):
    print(f"Funding Update for {kwargs['feed']}")
    print(kwargs)


def main():
    b = Bitmex(pairs=['BTC/USD', 'ETH/USD'], channels=[TRADES, TICKER, L2_BOOK, CANDLE], callbacks={
        TRADES: TradeCallback(trade),
        TICKER: TickerCallback(ticker),
        L2_BOOK: BookCallback(book),
        CANDLE: CandleCallback(candle)
    }, time_frames=[TimeFrames.ONE_MINUTE])
    b.start()


if __name__ == '__main__':
    main()
