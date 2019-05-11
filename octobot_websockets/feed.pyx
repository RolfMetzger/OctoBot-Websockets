#  Drakkar-Software OctoBot-Websockets
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.

import asyncio
import logging
from asyncio import CancelledError
from datetime import datetime, timedelta
from typing import List

import ccxt
import websockets
from ccxt.base.exchange import Exchange as ccxtExchange

from octobot_websockets.constants import TRADES, TICKER, L2_BOOK, L3_BOOK, BOOK_DELTA, UNSUPPORTED, FUNDING, CANDLE, POSITION, \
    ORDERS, PORTFOLIO, TimeFrames, HOURS_TO_SECONDS
from octobot_websockets.callback import Callback

cdef class Feed:
    MAX_DELAY = HOURS_TO_SECONDS

    def __init__(self,
                 address: str,
                 pairs: list = None,
                 channels: list = None,
                 callbacks: dict = None,
                 api_key: str = None,
                 api_secret: str = None,
                 time_frames: List[TimeFrames] = None,
                 book_interval: int = 1000,
                 timeout: int = 120,
                 timeout_interval: int = 5,
                 create_loop: bool = True):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

        self.create_loop = create_loop
        if create_loop:
            self.loop = asyncio.new_event_loop()
        else:
            self.loop = asyncio.get_event_loop()

        self.api_key = api_key
        self.api_secret = api_secret
        self.address = address

        self.timeout = timeout
        self.timeout_interval = timeout_interval
        self.book_update_interval = book_interval
        self.updates = 0

        self.is_connected = False
        self.do_deltas = False
        self.should_stop = False

        self.pairs = []
        self.channels = []
        self.callbacks = {}
        self.time_frames = time_frames if time_frames is not None else []

        self.websocket = None
        self.ccxt_client = None
        self._watch_task = None
        self._websocket_task = None
        self.last_msg = datetime.utcnow()

        self.__initialize(pairs, channels, callbacks)

    cdef __initialize(self, pairs, channels, callbacks):
        self.ccxt_client = getattr(ccxt, self.get_name())()
        self.ccxt_client.load_markets()

        self.pairs = [self.get_exchange_pair(pair) for pair in pairs] if pairs else []
        self.channels = [self.feed_to_exchange(chan) for chan in channels] if channels else []

        self.callbacks = {TRADES: Callback(None),
                          TICKER: Callback(None),
                          L2_BOOK: Callback(None),
                          L3_BOOK: Callback(None),
                          CANDLE: Callback(None),
                          PORTFOLIO: Callback(None),
                          ORDERS: Callback(None),
                          POSITION: Callback(None)}

        if callbacks:
            for cb_type, cb_func in callbacks.items():
                self.callbacks[cb_type] = cb_func
                if cb_type == BOOK_DELTA:
                    self.do_deltas = True

    cpdef start(self):
        if self.create_loop:
            self._websocket_task = self.loop.run_until_complete(self.__connect())
        else:
            self._websocket_task = self.loop.create_task(self.__connect())

    async def __watch(self):
        if self.last_msg:
            if datetime.utcnow() - timedelta(seconds=self.timeout) > self.last_msg:
                self.logger.warning("No messages received within timeout, restarting connection")
                print("reconnect")
                await self.__reconnect()
        await asyncio.sleep(self.timeout_interval)

    async def __on_error(self, error):
        self.logger.error(f"Error : {error}")

    async def __connect(self):
        """ Connect to websocket feeds """
        cdef int delay = 1
        self._watch_task = None
        while not self.should_stop:
            # manage max delay
            if delay >= self.MAX_DELAY:
                delay = self.MAX_DELAY

            try:
                async with websockets.connect(self.address) as websocket:
                    self.websocket = websocket
                    await self.on_open()
                    self._watch_task = asyncio.create_task(self.__watch())
                    # connection was successful, reset retry count and delay
                    delay = 1
                    await self.subscribe()
                    await self._handler()
            except (websockets.ConnectionClosed,
                    ConnectionAbortedError,
                    ConnectionResetError,
                    CancelledError) as e:
                self.logger.warning(f"{self.get_name()} encountered connection issue ({e}) - reconnecting...")
                await asyncio.sleep(delay)
                delay *= 2
            except Exception as e:
                self.logger.error(f"{self.get_name()} encountered an exception ({e}), reconnecting...")
                await asyncio.sleep(delay)
                delay *= 2

    async def _handler(self):
        async for message in self.websocket:
            self.last_msg = datetime.utcnow()
            try:
                await self.on_message(message)
            except Exception:
                self.logger.error(f"{self.get_name()}: error handling message {message}")
                # exception will be logged with traceback when connection handler
                # retries the connection
                raise

    async def __reconnect(self):
        self.stop()
        await self.__connect()

    async def on_open(self):
        self.logger.info("Connected")

    cdef on_close(self):
        self.logger.info('Websocket Closed')

    cpdef stop(self):
        self.websocket.close()

    cpdef close(self):
        self.stop()
        self._watch_task.cancel()
        self._websocket_task.cancel()

    cdef list get_auth(self):
        return []  # to be overwritten

    async def on_message(self, message):
        raise NotImplemented("on_message is not implemented")

    async def subscribe(self):
        raise NotImplemented("subscribe is not implemented")

    @classmethod
    def get_name(cls) -> str:
        raise NotImplemented("get_name is not implemented")

    @classmethod
    def get_ccxt(cls) -> object:
        getattr(ccxt, cls.get_name())

    @classmethod
    def get_L2_book_feed(cls) -> str:
        raise NotImplemented("get_L2_book_feed is not implemented")

    @classmethod
    def get_L3_book_feed(cls) -> str:
        raise NotImplemented("get_L3_book_feed is not implemented")

    @classmethod
    def get_trades_feed(cls) -> str:
        raise NotImplemented("get_trades_feed is not implemented")

    @classmethod
    def get_ticker_feed(cls) -> str:
        raise NotImplemented("get_ticker_feed is not implemented")

    @classmethod
    def get_candle_feed(cls) -> str:
        raise NotImplemented("get_candle_feed is not implemented")

    @classmethod
    def get_funding_feed(cls) -> str:
        raise NotImplemented("get_funding_feed is not implemented")

    @classmethod
    def get_portfolio_feed(cls) -> str:
        raise NotImplemented("get_portfolio_feed is not implemented")

    @classmethod
    def get_orders_feed(cls) -> str:
        raise NotImplemented("get_orders_feed is not implemented")

    @classmethod
    def get_position_feed(cls) -> str:
        raise NotImplemented("get_position_feed is not implemented")

    cdef list get_pairs(self):
        return self.ccxt_client.symbols

    cdef int timestamp_normalize(self, ts):
        return ts

    @classmethod
    def get_feeds(cls) -> dict:
        return {
            FUNDING: cls.get_funding_feed(),
            L2_BOOK: cls.get_L2_book_feed(),
            L3_BOOK: cls.get_L3_book_feed(),
            TRADES: cls.get_trades_feed(),
            CANDLE: cls.get_candle_feed(),
            TICKER: cls.get_ticker_feed(),
            POSITION: cls.get_position_feed(),
            ORDERS: cls.get_orders_feed(),
            PORTFOLIO: cls.get_portfolio_feed()
        }

    cdef str get_pair_from_exchange(self, pair):
        return self.ccxt_client.find_market(pair)["symbol"]

    cdef str get_exchange_pair(self, pair):
        if pair in self.ccxt_client.symbols:
            try:
                return self.ccxt_client.find_market(pair)["id"]
            except KeyError:
                raise KeyError(f'{pair} is not supported on {self.get_name()}')
        else:
            raise ValueError(f'{pair} is not supported on {self.get_name()}')

    cdef str feed_to_exchange(self, feed):
        ret = self.get_feeds()[feed]
        if ret == UNSUPPORTED:
            self.logger.error("{} is not supported on {}".format(feed, self.get_name()))
            raise ValueError(f"{feed} is not supported on {self.get_name()}")
        return ret

    cdef float safe_float(self, dictionary, key, default_value):
        return ccxtExchange.safe_float(dictionary, key, default_value)
