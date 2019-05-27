# cython: language_level=3
import asyncio
import calendar
import hashlib
import hmac
import json
import time
import urllib
from collections import defaultdict
from datetime import datetime as dt

from ccxt.async_support import bitmex

from octobot_websockets.constants import TRADES, BUY, SELL, L2_BOOK, FUNDING, UNSUPPORTED, POSITION, ORDERS, TimeFrames, \
    TimeFramesMinutes, MSECONDS_TO_MINUTE, MSECONDS_TO_SECONDS
from octobot_websockets.data.book import Book
from octobot_websockets.feeds.feed import Feed
from octobot_websockets.constructors.candle_constructor import CandleConstructor
from octobot_websockets.constructors.ticker_constructor import TickerConstructor


class Bitmex(Feed):
    api = 'https://www.bitmex.com/api/v1'
    MAX_TABLE_LEN = 200
    CANDLE_RETRY_TIME = 30

    def __init__(self, pairs=None, channels=None, callbacks=None, **kwargs):
        super().__init__('wss://www.bitmex.com/realtime', pairs=pairs, channels=channels, callbacks=callbacks, **kwargs)
        self.ticker_constructors = {}
        self.candle_constructors = {}
        self._reset()

    def _reset(self):
        self.partial_received = False
        self.order_id = {}
        self.l3_book = {}
        for pair in self.pairs:
            self.l3_book[pair] = Book()
            self.order_id[pair] = defaultdict(dict)

    async def _trade(self, msg: dict):
        for data in msg['data']:
            await self.callbacks[TRADES](feed=self.get_name(),
                                         symbol=self.get_pair_from_exchange(data['symbol']),
                                         side=BUY if data['side'] == 'Buy' else SELL,
                                         amount=data['size'],
                                         price=data['price'],
                                         timestamp=data['timestamp'])
        last_data: dict = msg['data'][-1]
        last_symbol: str = self.get_pair_from_exchange(last_data['symbol'])
        try:
            await self.ticker_constructors[last_symbol].handle_recent_trade(last_data['price'])
        except KeyError:
            self.ticker_constructors[last_symbol] = TickerConstructor(self, last_symbol)
            await self.ticker_constructors[last_symbol].handle_recent_trade(last_data['price'])

        # await self.__update_candles(last_data, last_symbol)

    async def __update_candles(self, last_data, last_symbol):
        for time_frame in self.time_frames:
            try:
                await self.candle_constructors[last_symbol][time_frame].handle_recent_trade(last_data['price'],
                                                                                            last_data['size'])
            except KeyError:
                if last_symbol not in self.candle_constructors:
                    self.candle_constructors[last_symbol] = {}

                if time_frame not in self.candle_constructors[last_symbol]:
                    started_candle = await self.get_last_candle_from_ccxt(last_symbol, time_frame)
                    print(f"start = {started_candle}")
                    self.candle_constructors[last_symbol][time_frame] = CandleConstructor(self, last_symbol,
                                                                                          time_frame,
                                                                                          started_candle)

                await self.candle_constructors[last_symbol][time_frame].handle_recent_trade(last_data['price'],
                                                                                            last_data['size'])

    async def get_last_candle_from_ccxt(self, last_symbol: str, time_frame: TimeFrames) -> list:
        while True:
            since: int = self.async_ccxt_client.milliseconds() - MSECONDS_TO_MINUTE * TimeFramesMinutes[time_frame]
            candle: list = (await self.async_ccxt_client.fetch_ohlcv(last_symbol, time_frame.value, since, 1))
            if candle:
                candle[0][0] = self.fix_timestamp(candle[0][0])
                return candle[0]
            else:
                self.logger.warning("Failed to synchronize candles, retrying...")
                await asyncio.sleep(self.CANDLE_RETRY_TIME)

    async def _l2_book(self, msg: dict):
        book: Book = Book()
        book.handle_book_update(msg['data'][0]['bids'], msg['data'][0]['asks'])
        await self.callbacks[L2_BOOK](feed=self.get_name(),
                                      symbol=self.get_pair_from_exchange(msg['data'][0]['symbol']),
                                      asks=book.asks,
                                      bids=book.bids,
                                      timestamp=book.timestamp)

    async def _quote(self, msg: dict):
        """Return a ticker object. Generated from quote and trade."""
        ticker_data: dict = msg['data'][0]
        ticker_symbol: str = self.get_pair_from_exchange(ticker_data['symbol'])
        try:
            await self.ticker_constructors[ticker_symbol].handle_quote(ticker_data['bidPrice'], ticker_data['askPrice'])
        except KeyError:
            self.ticker_constructors[ticker_symbol] = TickerConstructor(self, ticker_symbol)
            await self.ticker_constructors[ticker_symbol].handle_quote(ticker_data['bidPrice'], ticker_data['askPrice'])

    async def _order(self, msg: dict):
        is_canceled: int = 'ordStatus' in msg['data'] and msg['data']['ordStatus'] == 'Canceled'
        is_filled: int = 'ordStatus' in msg['data'] and msg['data']['ordStatus'] == 'Filled'
        await self.callbacks[ORDERS](feed=self.get_name(),
                                     symbol=self.get_pair_from_exchange(msg['data']['symbol']),
                                     price=msg['data']['avgEntryPrice'],
                                     quantity=msg['data']['cumQty'],
                                     order_id=msg['data']['orderID'],
                                     is_canceled=is_canceled,
                                     is_filled=is_filled)

    async def _position(self, msg: dict):
        await self.callbacks[POSITION](feed=self.get_name(),
                                       symbol=self.get_pair_from_exchange(msg['data']['symbol']),
                                       entry_price=msg['data']['avgEntryPrice'],
                                       cost=msg['data']['simpleCost'],
                                       quantity=msg['data']['simpleQty'],
                                       pnl_percent=msg['data']['simplePnlPcnt'],
                                       mark_price=msg['data']['markPrice'],
                                       liquidation_price=msg['data']['liquidationPrice'],
                                       timestamp=msg['data']['timestamp'])

    async def _funding(self, msg: dict):
        for data in msg['data']:
            await self.callbacks[FUNDING](feed=self.get_name(),
                                          symbol=self.get_pair_from_exchange(data['symbol']),
                                          timestamp=data['timestamp'],
                                          interval=data['fundingInterval'],
                                          rate=data['fundingRate'],
                                          rate_daily=data['fundingRateDaily'])

    async def on_message(self, json_message: str):
        """Handler for parsing WS messages."""
        parsed_message: dict = json.loads(json_message)

        table: str = parsed_message['table'] if 'table' in parsed_message else None
        action: str = parsed_message['action'] if 'action' in parsed_message else None

        try:
            if 'info' in parsed_message:
                self.logger.info(f"{self.get_name()}: info message : {parsed_message}")
            elif 'subscribe' in parsed_message:
                if not parsed_message['success']:
                    self.logger.error(f"{self.get_name()}: subscribed failed : {parsed_message}")
            elif 'status' in parsed_message:
                if parsed_message['status'] == 400:
                    self.logger.error(parsed_message['error'])
                if parsed_message['status'] == 401:
                    self.logger.error("API Key incorrect, please check and restart.")
            elif 'error' in parsed_message:
                self.logger.error(f"{self.get_name()}: Error message from exchange: {parsed_message}")
            elif action:
                if table == self.get_trades_feed():
                    await self._trade(parsed_message)

                elif table == self.get_funding_feed():
                    await self._funding(parsed_message)

                elif table == self.get_ticker_feed():
                    await self._quote(parsed_message)

                elif table == self.get_margin_feed():
                    await self._position(parsed_message)

                elif table == self.get_position_feed():
                    await self._position(parsed_message)

                elif table == self.get_orders_feed():
                    await self._order(parsed_message)

                elif table == self.get_execution_feed():
                    await self._order(parsed_message)

                # elif table == self.get_L3_book_feed():
                #     await self.handle_book_update(message)

                elif table == self.get_L2_book_feed():
                    await self._l2_book(parsed_message)
                else:
                    raise Exception(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"Error when handling message {e}")
            raise e

    # async def handle_book_update(self, msg):
    #     delta = {BID: [], ASK: []}
    #     pair = None
    #     # if we reset the book, force a full update
    #     forced = False
    #     is_partial = msg['action'] == 'partial'
    #     if not self.partial_received:
    #         # per bitmex documentation messages received before partial
    #         # should be discarded
    #         if not is_partial:
    #             print("return")
    #             return
    #         else:
    #             self.partial_received = True
    #         forced = True
    #
    #     if is_partial or msg['action'] == 'insert':
    #         for data in msg['data']:
    #             side = BID if data['side'] == 'Buy' else ASK
    #             price = data['price']
    #             pair = data['symbol']
    #             size = data['size']
    #             order_id = data['id']
    #
    #             if price in self.l3_book[pair][side]:
    #                 self.l3_book[pair][side][price][order_id] = size
    #             else:
    #                 self.l3_book[pair][side][price] = {order_id: size}
    #             self.order_id[pair][side][order_id] = (price, size)
    #             delta[side].append((order_id, price, size))
    #     elif msg['action'] == 'update':
    #         for data in msg['data']:
    #             side = BID if data['side'] == 'Buy' else ASK
    #             pair = data['symbol']
    #             update_size = data['size']
    #             order_id = data['id']
    #
    #             price, _ = self.order_id[pair][side][order_id]
    #
    #             self.l3_book[pair][side][price][order_id] = update_size
    #             self.order_id[pair][side][order_id] = (price, update_size)
    #             delta[side].append((order_id, price, update_size))
    #     elif msg['action'] == 'delete':
    #         for data in msg['data']:
    #             pair = data['symbol']
    #             side = BID if data['side'] == 'Buy' else ASK
    #             order_id = data['id']
    #
    #             delete_price, _ = self.order_id[pair][side][order_id]
    #             del self.order_id[pair][side][order_id]
    #             del self.l3_book[pair][side][delete_price][order_id]
    #
    #             if len(self.l3_book[pair][side][delete_price]) == 0:
    #                 del self.l3_book[pair][side][delete_price]
    #
    #             delta[side].append((order_id, delete_price, 0))
    #
    #     else:
    #         self.logger.warning(f"{self.get_nane()}: Unexpected L3 Book message {msg}")
    #         return
    #
    #     await self.callbacks[L3_BOOK](feed=self.get_name(),
    #                                   symbol=self.get_pair_from_exchange(pair),
    #                                   asks=self.l3_book[pair][ASK],
    #                                   bids=self.l3_book[pair][BID],
    #                                   forced=forced)

    async def subscribe(self):
        chans: list = []
        for channel in self.channels:
            for pair in self.pairs:
                chans.append("{}:{}".format(channel, pair))

        await self.__send_command("subscribe", chans)

    async def __send_command(self, command, args):
        await self.websocket.send(json.dumps({"op": command, "args": args or []}))

    def get_auth(self):
        """Return auth headers. Will use API Keys if present in settings."""
        if self.api_key:
            self.logger.info("Authenticating with API Key.")
            # To auth to the WS using an API key, we generate a signature of a nonce and
            # the WS API endpoint.
            expires = self.generate_nonce()
            return [
                "api-expires: " + str(expires),
                "api-signature: " + self.generate_signature(self.api_secret, 'GET', '/realtime', expires, ''),
                "api-key:" + self.api_key
            ]
        else:
            self.logger.info("Not authenticating.")
            return []

    @classmethod
    def get_name(cls):
        return 'bitmex'

    @classmethod
    def get_ccxt_async_client(cls):
        return bitmex

    @classmethod
    def get_L2_book_feed(cls):
        return 'orderBook10'

    @classmethod
    def get_L3_book_feed(cls):
        return UNSUPPORTED  #  'orderBookL2'

    @classmethod
    def get_trades_feed(cls):
        return 'trade'

    @classmethod
    def get_ticker_feed(cls):
        return 'quote'

    @classmethod
    def get_candle_feed(cls):
        return 'candle'

    @classmethod
    def get_kline_feed(cls):
        return 'kline'

    @classmethod
    def get_funding_feed(cls):
        return 'funding'

    @classmethod
    def get_margin_feed(cls):
        return 'margin'

    @classmethod
    def get_position_feed(cls):
        return 'position'

    @classmethod
    def get_portfolio_feed(cls):
        return UNSUPPORTED

    @classmethod
    def get_orders_feed(cls):
        return 'order'

    @classmethod
    def get_execution_feed(cls):
        return 'execution'

    def fix_timestamp(self, ts):
        return ts / MSECONDS_TO_SECONDS

    def timestamp_normalize(self, ts):
        return calendar.timegm(dt.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").utctimetuple())

    # From https://github.com/BitMEX/api-connectors/blob/master/official-ws/python/util/api_key.py
    def generate_nonce(self):
        return int(round(time.time() + 3600))

    # Generates an API signature.
    # A signature is HMAC_SHA256(secret, verb + path + nonce + data), hex encoded.
    # Verb must be uppercased, url is relative, nonce must be an increasing 64-bit integer
    # and the data, if present, must be JSON without whitespace between keys.
    #
    # For example, in psuedocode (and in real code below):
    #
    # verb=POST
    # url=/api/v1/order
    # nonce=1416993995705
    # data={"symbol":"XBTZ14","quantity":1,"price":395.01}
    # signature = HEX(HMAC_SHA256(secret, 'POST/api/v1/order1416993995705{"symbol":"XBTZ14","quantity":1,"price":395.01}'))
    def generate_signature(self, secret, verb, url, nonce, data):
        """Generate a request signature compatible with BitMEX."""
        # Parse the url so we can remove the base and extract just the path.
        parsedURL = urllib.parse.urlparse(url)
        path: str = parsedURL.path
        if parsedURL.query:
            path += '?' + parsedURL.query

        # print "Computing HMAC: %s" % verb + path + str(nonce) + data
        message: str = (verb + path + str(nonce) + data).encode('utf-8')

        return hmac.new(secret.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()