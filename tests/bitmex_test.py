import asyncio

import pytest

from octobot_websockets import L2_BOOK, TRADES
from octobot_websockets.bitmex.bitmex import Bitmex
from octobot_websockets.callback import TradeCallback, BookCallback

pytestmark = pytest.mark.asyncio

test_book = False
test_trade = False


def book(feed, symbob, asks, bids):
    global test_book
    test_book = True


def trade(feed, symbob, timestamp, side, amount, price):
    global test_trade
    test_trade = True


async def test_bitmex_ticker():
    b = Bitmex(pairs=['BTC/USD'], channels=[TRADES, L2_BOOK], callbacks={
        TRADES: TradeCallback(trade),
        L2_BOOK: BookCallback(book)
    })
    b.start()
    await asyncio.sleep(5)
    assert test_book
    assert test_trade
    b.close()
