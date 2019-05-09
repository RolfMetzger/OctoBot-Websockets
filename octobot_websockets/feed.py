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
from abc import abstractmethod
from asyncio import Task, CancelledError
from datetime import datetime, timedelta
from typing import List, Dict

import ccxt
import websockets
from ccxt.base.exchange import Exchange as ccxtExchange

from octobot_websockets import TRADES, TICKER, L2_BOOK, L3_BOOK, BOOK_DELTA, UNSUPPORTED, FUNDING, CANDLE, POSITION, \
    ORDERS, PORTFOLIO, TimeFrames
from octobot_websockets.callback import Callback


class Feed:
    def __init__(self,
                 address: str,
                 pairs: List = None,
                 channels: List = None,
                 callbacks: Dict = None,
                 api_key: str = None,
                 api_secret: str = None,
                 time_frames: List[TimeFrames] = None,
                 book_interval: int = 1000,
                 timeout: int = 120,
                 timeout_interval: int = 5,
                 create_loop: bool = True):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

        self.create_loop: bool = create_loop
        if create_loop:
            self.loop = asyncio.new_event_loop()
        else:
            self.loop = asyncio.get_event_loop()

        self.api_key: str = api_key
        self.api_secret: str = api_secret
        self.address: str = address

        self.timeout: int = timeout
        self.timeout_interval: int = timeout_interval
        self.book_update_interval: int = book_interval
        self.updates: int = 0

        self.is_connected: bool = False
        self.do_deltas: bool = False

        self.pairs: List = []
        self.channels: List = []
        self.callbacks: Dict = {}
        self.time_frames = time_frames if time_frames is not None else []

        self.websocket = None
        self.ccxt_client = None

        self._watch_task: Task = None
        self._websocket_task: Task = None
        self.last_msg: datetime = datetime.utcnow()

        self.__initialize(pairs, channels, callbacks)

    def __initialize(self, pairs, channels, callbacks):
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

    def start(self):
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
        retries = 0
        delay = 1
        self.watch_task = None
        while retries <= retries:
            try:
                async with websockets.connect(self.address) as websocket:
                    self.websocket = websocket
                    await self.on_open()
                    self._watch_task = asyncio.create_task(self.__watch())
                    # connection was successful, reset retry count and delay
                    self.retries = 0
                    self.delay = 1
                    await self.subscribe()
                    await self._handler()
            except (websockets.ConnectionClosed,
                    ConnectionAbortedError,
                    ConnectionResetError,
                    CancelledError) as e:
                self.logger.warning(f"{self.get_name()} encountered connection issue ({e}) - reconnecting...")
                await asyncio.sleep(delay)
                retries += 1
                delay *= 2
            except Exception as e:
                self.logger.error(f"{self.get_name()} encountered an exception ({e}), reconnecting...")
                await asyncio.sleep(delay)
                retries += 1
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

    def on_close(self):
        self.logger.info('Websocket Closed')

    def stop(self):
        self.websocket.close()

    def close(self):
        self.stop()
        self._watch_task.cancel()
        self._websocket_task.cancel()

    def get_auth(self):
        return []  # to be overwritten

    @abstractmethod
    async def on_message(self, message):
        raise NotImplemented("on_message is not implemented")

    @abstractmethod
    async def subscribe(self):
        raise NotImplemented("subscribe is not implemented")

    @classmethod
    def get_name(cls):
        raise NotImplemented("get_name is not implemented")

    @classmethod
    def get_ccxt(cls):
        getattr(ccxt, cls.get_name())

    @classmethod
    @abstractmethod
    def get_L2_book_feed(cls):
        raise NotImplemented("get_L2_book_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_L3_book_feed(cls):
        raise NotImplemented("get_L3_book_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_trades_feed(cls):
        raise NotImplemented("get_trades_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_ticker_feed(cls):
        raise NotImplemented("get_ticker_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_candle_feed(cls):
        raise NotImplemented("get_candle_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_funding_feed(cls):
        raise NotImplemented("get_funding_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_portfolio_feed(cls):
        raise NotImplemented("get_portfolio_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_orders_feed(cls):
        raise NotImplemented("get_orders_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_position_feed(cls):
        raise NotImplemented("get_position_feed is not implemented")

    def get_pairs(self) -> List:
        return self.ccxt_client.symbols

    @staticmethod
    def timestamp_normalize(ts):
        return ts

    @classmethod
    def get_feeds(cls) -> Dict:
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

    def get_pair_from_exchange(self, pair) -> str:
        return self.ccxt_client.find_market(pair)["symbol"]

    def get_exchange_pair(self, pair) -> str:
        if pair in self.ccxt_client.symbols:
            try:
                return self.ccxt_client.find_market(pair)["id"]
            except KeyError:
                raise KeyError(f'{pair} is not supported on {self.get_name()}')
        else:
            raise ValueError(f'{pair} is not supported on {self.get_name()}')

    def feed_to_exchange(self, feed):
        ret = self.get_feeds()[feed]
        if ret == UNSUPPORTED:
            self.logger.error("{} is not supported on {}".format(feed, self.get_name()))
            raise ValueError(f"{feed} is not supported on {self.get_name()}")
        return ret

    @staticmethod
    def safe_float(dictionary, key, default_value=None):
        return ccxtExchange.safe_float(dictionary, key, default_value)
