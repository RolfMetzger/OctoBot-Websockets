from octobot_websockets import TRADES, TICKER, L2_BOOK, CANDLE
from octobot_websockets.binance.binance import Binance
from octobot_websockets.bitfinex.bitfinex import Bitfinex
from octobot_websockets.bitmex.bitmex import Bitmex
from octobot_websockets.callback import TradeCallback, BookCallback, TickerCallback, CandleCallback
from octobot_websockets.feedhandler import FeedHandler
from octobot_websockets.kraken.kraken import Kraken
from octobot_websockets import BID, ASK


async def ticker(feed, pair, bid, ask, close, volume, high, low, opn):
    print(f'Feed: {feed} Pair: {pair} Bid: {bid} Ask: {ask}')


async def trade(feed, pair, order_id, timestamp, side, amount, price):
    print(
        f"Timestamp: {timestamp} Feed: {feed} Pair: {pair} ID: {order_id} Side: {side} Amount: {amount} Price: {price}")


async def book(feed, pair, book, timestamp):
    print(f'Timestamp: {timestamp} Feed: {feed} Pair: {pair} Book Bid Size is {len(book[BID])} Ask Size is {len(book[ASK])}')


async def candle(feed, pair, timestamp, close, volume, high, low, opn):
    print(f'Feed: {feed} Pair: {pair} Close: {close} Volume: {volume} High: {high} Low: {low} Open: {opn}')


async def funding(**kwargs):
    print(f"Funding Update for {kwargs['feed']}")
    print(kwargs)


def main():
    f = FeedHandler()
    # f.add_feed(Binance(pairs=['BTC/USDT'], channels=[TRADES, TICKER, L2_BOOK], callbacks={L2_BOOK: BookCallback(book),
    #                                                                                       TRADES: TradeCallback(trade),
    #                                                                                       TICKER: TickerCallback(ticker)}))
    # f.add_feed(Bitfinex(pairs=['BTC/USD'], channels=[L2_BOOK], callbacks={L2_BOOK: BookCallback(book)}))
    # f.add_feed(Bitmex(pairs=['BTC/USD'], channels=[TRADES], callbacks={TRADES: TradeCallback(trade)}))
    # f.add_feed(Kraken(config={TRADES: ['BTC/USD'], TICKER: ['ETH/USD']}, callbacks={TRADES: TradeCallback(trade),
    #                                                                                 TICKER: TickerCallback(ticker)}))
    f.add_feed(Bitfinex(pairs=['BTC/USD'], channels=[CANDLE], callbacks={CANDLE: CandleCallback(candle)}))
    f.run()


if __name__ == '__main__':
    main()
