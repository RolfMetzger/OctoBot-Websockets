import calendar
import hashlib
import hmac
import json
import time
import urllib
from collections import defaultdict
from datetime import datetime as dt

from octobot_websockets.constants import TRADES, BUY, SELL, L2_BOOK, FUNDING, UNSUPPORTED, POSITION, ORDERS
from octobot_websockets.book import Book
from octobot_websockets.candle_constructor import CandleConstructor
from octobot_websockets.feed cimport Feed
from octobot_websockets.ticker_constructor import TickerConstructor

cdef class Bitmex(Feed):
    api = 'https://www.bitmex.com/api/v1'
    MAX_TABLE_LEN = 200

    cdef dict ticker_constructors
    cdef dict candle_constructors

    cdef int partial_received

    cdef dict order_id # TODO remove
    cdef dict l3_book # TODO remove

    def __init__(self, pairs=None, channels=None, callbacks=None, **kwargs):
        super().__init__('wss://www.bitmex.com/realtime', pairs=pairs, channels=channels, callbacks=callbacks, **kwargs)
        self.ticker_constructors = {}
        self.candle_constructors = {}
        self._reset()

    cdef _reset(self):
        self.partial_received = False
        self.order_id = {}
        self.l3_book = {}
        for pair in self.pairs:
            self.l3_book[pair] = Book()
            self.order_id[pair] = defaultdict(dict)

    async def _trade(self, dict msg):
        """
        trade msg example

        {
            'timestamp': '2018-05-19T12:25:26.632Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 40,
            'price': 8335,
            'tickDirection': 'PlusTick',
            'trdMatchID': '5f4ecd49-f87f-41c0-06e3-4a9405b9cdde',
            'grossValue': 479920,
            'homeNotional': Decimal('0.0047992'),
            'foreignNotional': 40
        }
        """
        for data in msg['data']:
            await self.callbacks[TRADES](feed=self.get_name(),
                                         symbol=self.get_pair_from_exchange(data['symbol']),
                                         side=BUY if data['side'] == 'Buy' else SELL,
                                         amount=data['size'],
                                         price=data['price'],
                                         timestamp=data['timestamp'])
        cdef dict last_data = msg['data'][-1]
        cdef str symbol = self.get_pair_from_exchange(last_data['symbol'])
        try:
            await self.ticker_constructors[symbol].handle_recent_trade(last_data['price'])
        except KeyError:
            self.ticker_constructors[symbol] = TickerConstructor(self, symbol)
            await self.ticker_constructors[symbol].handle_recent_trade(last_data['price'])

        await self.__update_candles(last_data, symbol)

    async def __update_candles(self, last_data, symbol):
        for time_frame in self.time_frames:
            try:
                await self.candle_constructors[symbol][time_frame].handle_recent_trade(last_data['price'],
                                                                                       last_data['size'])
            except KeyError:
                if symbol not in self.candle_constructors:
                    self.candle_constructors[symbol] = {}

                if time_frame not in self.candle_constructors[symbol]:
                    self.candle_constructors[symbol][time_frame] = CandleConstructor(self, symbol, time_frame)

                await self.candle_constructors[symbol][time_frame].handle_recent_trade(last_data['price'],
                                                                                       last_data['size'])

    async def _l2_book(self, dict msg):
        cdef object book = Book()
        book.handle_book_update(msg['data'][0]['bids'], msg['data'][0]['asks'])
        await self.callbacks[L2_BOOK](feed=self.get_name(),
                                      symbol=self.get_pair_from_exchange(msg['data'][0]['symbol']),
                                      asks=book.asks,
                                      bids=book.bids,
                                      timestamp=book.timestamp)

    async def _quote(self, dict msg):
        """Return a ticker object. Generated from quote and trade."""
        cdef dict data = msg['data'][0]
        cdef str symbol = self.get_pair_from_exchange(data['symbol'])
        try:
            await self.ticker_constructors[symbol].handle_quote(data['bidPrice'], data['askPrice'])
        except KeyError:
            self.ticker_constructors[symbol] = TickerConstructor(self, symbol)
            await self.ticker_constructors[symbol].handle_quote(data['bidPrice'], data['askPrice'])

    async def _order(self, dict msg):
        """
        {
           "table":"execution",
           "action":"insert",
           "data":[
              {
                 "execID":"0193e879-cb6f-2891-d099-2c4eb40fee21",
                 "orderID":"00000000-0000-0000-0000-000000000000",
                 "clOrdID":"",
                 "clOrdLinkID":"",
                 "account":2,
                 "symbol":"XBTUSD",
                 "side":"Sell",
                 "lastQty":1,
                 "lastPx":1134.37,
                 "underlyingLastPx":null,
                 "lastMkt":"XBME",
                 "lastLiquidityInd":"RemovedLiquidity",
                 "simpleOrderQty":null,
                 "orderQty":1,
                 "price":1134.37,
                 "displayQty":null,
                 "stopPx":null,
                 "pegOffsetValue":null,
                 "pegPriceType":"",
                 "currency":"USD",
                 "settlCurrency":"XBt",
                 "execType":"Trade",
                 "ordType":"Limit",
                 "timeInForce":"ImmediateOrCancel",
                 "execInst":"",
                 "contingencyType":"",
                 "exDestination":"XBME",
                 "ordStatus":"Filled",
                 "triggered":"",
                 "workingIndicator":false,
                 "ordRejReason":"",
                 "simpleLeavesQty":0,
                 "leavesQty":0,
                 "simpleCumQty":0.001,
                 "cumQty":1,
                 "avgPx":1134.37,
                 "commission":0.00075,
                 "tradePublishIndicator":"DoNotPublishTrade",
                 "multiLegReportingType":"SingleSecurity",
                 "text":"Liquidation",
                 "trdMatchID":"7f4ab7f6-0006-3234-76f4-ae1385aad00f",
                 "execCost":88155,
                 "execComm":66,
                 "homeNotional":-0.00088155,
                 "foreignNotional":1,
                 "transactTime":"2017-04-04T22:07:46.035Z",
                 "timestamp":"2017-04-04T22:07:46.035Z"
              }
           ]
        }
        """
        cdef int is_canceled = 'ordStatus' in msg['data'] and msg['data']['ordStatus'] == 'Canceled'
        cdef int is_filled = 'ordStatus' in msg['data'] and msg['data']['ordStatus'] == 'Filled'
        await self.callbacks[ORDERS](feed=self.get_name(),
                                     symbol=self.get_pair_from_exchange(msg['data']['symbol']),
                                     price=msg['data']['avgEntryPrice'],
                                     quantity=msg['data']['cumQty'],
                                     order_id=msg['data']['orderID'],
                                     is_canceled=is_canceled,
                                     is_filled=is_filled)

    async def _position(self, dict msg):
        """
        {
           "table":"position",
           "action":"update",
           "data":[
              {
                 "account":2,
                 "symbol":"XBTUSD",
                 "currency":"XBt",
                 "deleveragePercentile":null,
                 "rebalancedPnl":-2171150,
                 "prevRealisedPnl":2172153,
                 "execSellQty":2001,
                 "execSellCost":172394155,
                 "execQty":0,
                 "execCost":-2259128,
                 "execComm":87978,
                 "currentTimestamp":"2017-04-04T22:16:38.547Z",
                 "currentQty":0,
                 "currentCost":-2259128,
                 "currentComm":87978,
                 "realisedCost":-2259128,
                 "unrealisedCost":0,
                 "grossExecCost":0,
                 "isOpen":false,
                 "markPrice":null,
                 "markValue":0,
                 "riskValue":0,
                 "homeNotional":0,
                 "foreignNotional":0,
                 "posState":"",
                 "posCost":0,
                 "posCost2":0,
                 "posInit":0,
                 "posComm":0,
                 "posMargin":0,
                 "posMaint":0,
                 "maintMargin":0,
                 "realisedGrossPnl":2259128,
                 "realisedPnl":2171150,
                 "unrealisedGrossPnl":0,
                 "unrealisedPnl":0,
                 "unrealisedPnlPcnt":0,
                 "unrealisedRoePcnt":0,
                 "simpleQty":0,
                 "simpleCost":0,
                 "simpleValue":0,
                 "simplePnl":0,
                 "simplePnlPcnt":0,
                 "avgCostPrice":null,
                 "avgEntryPrice":null,
                 "breakEvenPrice":null,
                 "marginCallPrice":null,
                 "liquidationPrice":null,
                 "bankruptPrice":null,
                 "timestamp":"2017-04-04T22:16:38.547Z"
              }
           ]
        }
        """
        await self.callbacks[POSITION](feed=self.get_name(),
                                       symbol=self.get_pair_from_exchange(msg['data']['symbol']),
                                       entry_price=msg['data']['avgEntryPrice'],
                                       cost=msg['data']['simpleCost'],
                                       quantity=msg['data']['simpleQty'],
                                       pnl_percent=msg['data']['simplePnlPcnt'],
                                       mark_price=msg['data']['markPrice'],
                                       liquidation_price=msg['data']['liquidationPrice'],
                                       timestamp=msg['data']['timestamp'])

    async def _funding(self, dict msg):
        """
        {'table': 'funding',
         'action': 'partial',
         'keys': ['timestamp', 'symbol'],
         'types': {
             'timestamp': 'timestamp',
             'symbol': 'symbol',
             'fundingInterval': 'timespan',
             'fundingRate': 'float',
             'fundingRateDaily': 'float'
            },
         'foreignKeys': {
             'symbol': 'instrument'
            },
         'attributes': {
             'timestamp': 'sorted',
             'symbol': 'grouped'
            },
         'filter': {'symbol': 'XBTUSD'},
         'data': [{
             'timestamp': '2018-08-21T20:00:00.000Z',
             'symbol': 'XBTUSD',
             'fundingInterval': '2000-01-01T08:00:00.000Z',
             'fundingRate': Decimal('-0.000561'),
             'fundingRateDaily': Decimal('-0.001683')
            }]
        }
        """
        for data in msg['data']:
            await self.callbacks[FUNDING](feed=self.get_name(),
                                          symbol=self.get_pair_from_exchange(data['symbol']),
                                          timestamp=data['timestamp'],
                                          interval=data['fundingInterval'],
                                          rate=data['fundingRate'],
                                          rate_daily=data['fundingRateDaily'])

    async def on_message(self, str json_message):
        """Handler for parsing WS messages."""
        cdef dict message = json.loads(json_message)

        cdef str table = message['table'] if 'table' in message else None
        cdef str action = message['action'] if 'action' in message else None

        try:
            if 'info' in message:
                self.logger.info(f"{self.get_name()}: info message : {message}")
            elif 'subscribe' in message:
                if not message['success']:
                    self.logger.error(f"{self.get_name()}: subscribed failed : {message}")
            elif 'status' in message:
                if message['status'] == 400:
                    self.logger.error(message['error'])
                if message['status'] == 401:
                    self.logger.error("API Key incorrect, please check and restart.")
            elif 'error' in message:
                self.logger.error(f"{self.get_name()}: Error message from exchange: {message}")
            elif action:
                if table == self.get_trades_feed():
                    await self._trade(message)

                elif table == self.get_funding_feed():
                    await self._funding(message)

                elif table == self.get_ticker_feed():
                    await self._quote(message)

                elif table == self.get_margin_feed():
                    await self._position(message)

                elif table == self.get_position_feed():
                    await self._position(message)

                elif table == self.get_orders_feed():
                    await self._order(message)

                elif table == self.get_execution_feed():
                    await self._order(message)

                # elif table == self.get_L3_book_feed():
                #     await self.handle_book_update(message)

                elif table == self.get_L2_book_feed():
                    await self._l2_book(message)
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
        cdef list chans = []
        for channel in self.channels:
            for pair in self.pairs:
                chans.append("{}:{}".format(channel, pair))

        await self.__send_command("subscribe", chans)

    async def __send_command(self, command, args):
        await self.websocket.send(json.dumps({"op": command, "args": args or []}))

    cdef list get_auth(self):
        """Return auth headers. Will use API Keys if present in settings."""
        if self.api_key:
            self.logger.info("Authenticating with API Key.")
            # To auth to the WS using an API key, we generate a signature of a nonce and
            # the WS API endpoint.
            expires = generate_nonce()
            return [
                "api-expires: " + str(expires),
                "api-signature: " + generate_signature(self.api_secret, 'GET', '/realtime', expires, ''),
                "api-key:" + self.api_key
            ]
        else:
            self.logger.info("Not authenticating.")
            return []

    @classmethod
    def get_name(cls):
        return 'bitmex'

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

    cdef int timestamp_normalize(self, ts):
        return calendar.timegm(dt.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").utctimetuple())

# From https://github.com/BitMEX/api-connectors/blob/master/official-ws/python/util/api_key.py
cdef int generate_nonce():
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
cdef str generate_signature(secret, verb, url, nonce, data):
    """Generate a request signature compatible with BitMEX."""
    # Parse the url so we can remove the base and extract just the path.
    cdef object parsedURL = urllib.parse.urlparse(url)
    cdef str path = parsedURL.path
    if parsedURL.query:
        path += '?' + parsedURL.query

    # print "Computing HMAC: %s" % verb + path + str(nonce) + data
    cdef str message = (verb + path + str(nonce) + data).encode('utf-8')

    return hmac.new(secret.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()
