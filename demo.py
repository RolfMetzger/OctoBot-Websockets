from octobot_websockets import TRADES, TICKER, L2_BOOK
from octobot_websockets.bitmex.bitmex import Bitmex
from octobot_websockets.callback import TradeCallback, TickerCallback, BookCallback


def ticker(feed, symbol, bid, ask, last):
    print(f'[TICKER] Feed: {feed} Pair: {symbol} Bid: {bid} Ask: {ask} Last : {last}')


def trade(feed, symbol, timestamp, side, amount, price):
    print(
        f"[TRADE] Timestamp: {timestamp} Feed: {feed} Pair: {symbol} Side: {side} Amount: {amount} Price: {price}")


def book(feed, symbol, asks, bids):
    print(f'[ORDER BOOK] Feed: {feed} Pair: {symbol} '
          f'Last Book Bid is {bids[-1]} with {bids[-1]}'
          f'Last Book Ask is {asks[0]} with {asks[0]}')


def candle(feed, symbol, timestamp, close, volume, high, low, opn):
    print(f'Feed: {feed} Pair: {symbol} Close: {close} Volume: {volume} High: {high} Low: {low} Open: {opn}')


def funding(**kwargs):
    print(f"Funding Update for {kwargs['feed']}")
    print(kwargs)


def main():
    b = Bitmex(pairs=['BTC/USD', 'ETH/USD'], channels=[TRADES, TICKER, L2_BOOK], callbacks={
        TRADES: TradeCallback(trade),
        TICKER: TickerCallback(ticker),
        L2_BOOK: BookCallback(book)
    })
    b.start()


if __name__ == '__main__':
    main()
