'''
Copyright (C) 2017-2019  Bryant Moscon - bmoscon@gmail.com

Please see the LICENSE file for the terms and conditions
associated with this software.
'''
import json
import time
from collections import defaultdict
from decimal import Decimal
from math import nan

from sortedcontainers import SortedDict as sd

from octobot_websockets import UNSUPPORTED, TICKER, FUNDING, TRADES, BUY, SELL, BID, ASK, L3_BOOK, L2_BOOK, CANDLE
from octobot_websockets.feed import Feed

"""
Bitfinex configuration flags
DEC_S: Enable all decimal as strings.
TIME_S: Enable all times as date strings.
TIMESTAMP: Timestamp in milliseconds.
SEQ_ALL: Enable sequencing BETA FEATURE
CHECKSUM: Enable checksum for every book iteration.
          Checks the top 25 entries for each side of book.
          Checksum is a signed int.
          
https://docs.bitfinex.com/v2/reference
"""
DEC_S = 8
TIME_S = 32
TIMESTAMP = 32768
SEQ_ALL = 65536
CHECKSUM = 131072


class Bitfinex(Feed):
    def __init__(self, pairs=None, channels=None, callbacks=None, **kwargs):
        super().__init__('wss://api.bitfinex.com/ws/2', pairs=pairs, channels=channels, callbacks=callbacks, **kwargs)
        self.__reset()

    def __reset(self):
        self.l2_book = {}
        self.l3_book = {}
        '''
        channel map maps channel id (int) to a dict of
           symbol: channel's currency
           channel: channel name
           handler: the handler for this channel type
        '''
        self.channel_map = {}
        self.order_map = defaultdict(dict)
        self.seq_no = 0

    # [
    #   CHANNEL_ID,
    #   [
    #     BID,
    #     BID_SIZE,
    #     ASK,
    #     ASK_SIZE,
    #     DAILY_CHANGE,
    #     DAILY_CHANGE_PERC,
    #     LAST_PRICE,
    #     VOLUME,
    #     HIGH,
    #     LOW
    #   ]
    # ]
    # https://docs.bitfinex.com/v2/reference#ws-public-ticker
    async def _ticker(self, msg):
        chan_id = msg[0]
        if msg[1] == 'hb':
            # ignore heartbeats
            pass
        else:
            # bid, bid_size, ask, ask_size, daily_change, daily_change_percent,
            # last_price, volume, high, low
            bid, _, ask, _, _, _, close, volume, high, low = msg[1]
            pair = self.channel_map[chan_id]['symbol']
            pair = self.get_pair_from_exchange(pair)
            await self.callbacks[TICKER](feed=self.get_name(),
                                         pair=pair,
                                         bid=bid,
                                         ask=ask,
                                         close=close,
                                         volume=volume,
                                         high=high,
                                         low=low,
                                         opn=nan)

    # TRADING
    # [
    #   CHANNEL_ID,
    #   [
    #     [
    #       ID,
    #       MTS,
    #       AMOUNT,
    #       PRICE
    #     ],
    #     ...
    #   ]
    # ]
    # FUNDING
    # [
    #   CHANNEL_ID,
    #   [
    #     [
    #       ID,
    #       MTS,
    #       AMOUNT,
    #       RATE,
    #       PERIOD
    #     ],
    #     ...
    #   ]
    # ]
    # https://docs.bitfinex.com/v2/reference#ws-public-trades
    async def _trades(self, msg):
        chan_id = msg[0]
        pair = self.channel_map[chan_id]['symbol']
        funding = pair[0] == 'f'
        pair = self.get_pair_from_exchange(pair)

        async def _trade_update(trade):
            if funding:
                order_id, timestamp, amount, price, period = trade
            else:
                order_id, timestamp, amount, price = trade
                period = None
            side = SELL if amount < 0 else BUY
            amount = abs(amount)
            if period:
                await self.callbacks[FUNDING](feed=self.get_name(),
                                              pair=pair,
                                              side=side,
                                              amount=amount,
                                              price=price,
                                              order_id=order_id,
                                              timestamp=timestamp,
                                              period=period)
            else:
                await self.callbacks[TRADES](feed=self.get_name(),
                                             pair=pair,
                                             side=side,
                                             amount=amount,
                                             price=price,
                                             order_id=order_id,
                                             timestamp=timestamp)

        if isinstance(msg[1], list):
            # snapshot
            for trade_update in msg[1]:
                await _trade_update(trade_update)
        else:
            # update
            if msg[1] == 'te' or msg[1] == 'fte':
                await _trade_update(msg[2])
            elif msg[1] == 'tu' or msg[1] == 'ftu':
                # ignore trade updates
                pass
            elif msg[1] == 'hb':
                # ignore heartbeats
                pass
            else:
                self.logger.warning("%s: Unexpected trade message %s", self.get_name(), msg)

    # [
    #   CHANNEL_ID,
    #   [
    #     [
    #       MTS,
    #       OPEN,
    #       CLOSE,
    #       HIGH,
    #       LOW,
    #       VOLUME
    #     ],
    #     ...
    #   ]
    # ]
    # https://docs.bitfinex.com/v2/reference#ws-public-candle
    async def _candles(self, msg):
        chan_id = msg[0]
        timestamp, opn, close, high, low, volume = msg[1]
        pair = self.channel_map[chan_id]['symbol']
        pair = self.get_pair_from_exchange(pair)
        await self.callbacks[CANDLE](feed=self.get_name(),
                                     pair=pair,
                                     timestamp=timestamp,
                                     close=close,
                                     volume=volume,
                                     high=high,
                                     low=low,
                                     opn=opn)

    # TRADING
    # [
    #   CHANNEL_ID,
    #   [
    #     [
    #       PRICE,
    #       COUNT,
    #       AMOUNT
    #     ],
    #     ...
    #   ]
    # ]
    #
    # FUNDING
    # [
    #   CHANNEL_ID,
    #   [
    #     [
    #       RATE,
    #       PERIOD,
    #       COUNT,
    #       AMOUNT
    #     ],
    #     ...
    #   ]
    # ]
    # https://docs.bitfinex.com/v2/reference#ws-public-order-books
    async def _book(self, msg):
        """
        For L2 book updates
        """
        timestamp = time.time() * 1000
        chan_id = msg[0]
        pair = self.channel_map[chan_id]['symbol']
        pair = self.get_pair_from_exchange(pair)
        delta = {BID: [], ASK: []}
        forced = False

        if isinstance(msg[1], list):
            if isinstance(msg[1][0], list):
                # snapshot so clear book
                self.l2_book[pair] = {BID: sd(), ASK: sd()}
                for update in msg[1]:
                    price, _, amount = update
                    price = Decimal(price)
                    amount = Decimal(amount)

                    if amount > 0:
                        side = BID
                    else:
                        side = ASK
                        amount = abs(amount)
                    self.l2_book[pair][side][price] = amount
                forced = True
            else:
                # book update
                price, count, amount = msg[1]
                price = Decimal(price)
                amount = Decimal(amount)

                if amount > 0:
                    side = BID
                else:
                    side = ASK
                    amount = abs(amount)

                if count > 0:
                    # change at price level
                    delta[side].append((price, amount))
                    self.l2_book[pair][side][price] = amount
                else:
                    # remove price level
                    del self.l2_book[pair][side][price]
                    delta[side].append((price, 0))
        elif msg[1] == 'hb':
            pass
        else:
            self.logger.warning("%s: Unexpected book msg %s", self.get_name(), msg)

        await self.book_callback(pair, L2_BOOK, forced, delta, timestamp)

    # TRADING
    # [
    #   CHANNEL_ID,
    #   [
    #     [
    #       ORDER_ID,
    #       PRICE,
    #       AMOUNT
    #     ],
    #     ...
    #   ]
    # ]
    #
    # FUNDING
    # [
    #   CHANNEL_ID,
    #   [
    #     [
    #       OFFER_ID,
    #       PERIOD,
    #       RATE,
    #       AMOUNT
    #     ],
    #     ...
    #   ]
    # ]
    # https://docs.bitfinex.com/v2/reference#ws-public-raw-order-books
    async def _raw_book(self, msg):
        """
        For L3 book updates
        """
        timestamp = time.time() * 1000

        def add_to_book(pair, side, price, order_id, amount):
            if price in self.l3_book[pair][side]:
                self.l3_book[pair][side][price][order_id] = amount
            else:
                self.l3_book[pair][side][price] = {order_id: amount}

        def remove_from_book(pair, side, order_id):
            price = self.order_map[pair][side][order_id]['price']
            del self.l3_book[pair][side][price][order_id]
            if len(self.l3_book[pair][side][price]) == 0:
                del self.l3_book[pair][side][price]

        delta = {BID: [], ASK: []}
        forced = False
        chan_id = msg[0]
        pair = self.channel_map[chan_id]['symbol']
        pair = self.get_pair_from_exchange(pair)

        if isinstance(msg[1], list):
            if isinstance(msg[1][0], list):
                # snapshot so clear orders
                self.order_map[pair] = {BID: {}, ASK: {}}
                self.l3_book[pair] = {BID: sd(), ASK: sd()}

                for update in msg[1]:
                    order_id, price, amount = update
                    price = Decimal(price)
                    amount = Decimal(amount)

                    if amount > 0:
                        side = BID
                    else:
                        side = ASK
                        amount = abs(amount)

                    self.order_map[pair][side][order_id] = {'price': price, 'amount': amount}
                    add_to_book(pair, side, price, order_id, amount)
                forced = True
            else:
                # book update
                order_id, price, amount = msg[1]
                price = Decimal(price)
                amount = Decimal(amount)

                if amount > 0:
                    side = BID
                else:
                    side = ASK
                    amount = abs(amount)

                if price == 0:
                    price = self.order_map[pair][side][order_id]['price']
                    remove_from_book(pair, side, order_id)
                    del self.order_map[pair][side][order_id]
                    delta[side].append((order_id, price, 0))
                else:
                    if order_id in self.order_map[pair][side]:
                        del_price = self.order_map[pair][side][order_id]['price']
                        delta[side].append((order_id, del_price, 0))
                        # remove existing order before adding new one
                        delta[side].append((order_id, price, amount))
                        remove_from_book(pair, side, order_id)
                    else:
                        delta[side].append((order_id, price, amount))
                    add_to_book(pair, side, price, order_id, amount)
                    self.order_map[pair][side][order_id] = {'price': price, 'amount': amount}

        elif msg[1] == 'hb':
            return
        else:
            self.logger.warning("%s: Unexpected book msg %s", self.get_name(), msg)
            return

        await self.book_callback(pair, L3_BOOK, forced, delta, timestamp)

    async def message_handler(self, msg):
        msg = json.loads(msg, parse_float=Decimal)

        if isinstance(msg, list):
            chan_id = msg[0]
            if chan_id in self.channel_map:
                seq_no = msg[-1]
                if self.seq_no + 1 != seq_no:
                    self.logger.warning("%s: missing sequence number. Received %d, expected %d", self.get_name(), seq_no, self.seq_no + 1)
                    raise ValueError
                self.seq_no = seq_no

                await self.channel_map[chan_id]['handler'](msg)
            else:
                self.logger.warning("%s: Unexpected message on unregistered channel %s", self.get_name(), msg)
        elif 'event' in msg and msg['event'] == 'error':
            self.logger.error("%s: Error message from exchange: %s", self.get_name(), msg['msg'])
        elif 'chanId' in msg and 'symbol' in msg:
            handler = None
            if msg['channel'] == 'ticker':
                handler = self._ticker
            elif msg['channel'] == 'trades':
                handler = self._trades
            elif msg['channel'] == 'candles':
                handler = self._candles
            elif msg['channel'] == 'book':
                if msg['prec'] == 'R0':
                    handler = self._raw_book
                else:
                    handler = self._book
            else:
                self.logger.warning('%s: Invalid message type %s', self.get_name(), msg)
                return

            self.channel_map[msg['chanId']] = {'symbol': msg['symbol'],
                                               'channel': msg['channel'],
                                               'handler': handler}

    async def subscribe(self, websocket):
        self.__reset()
        await websocket.send(json.dumps({
            'event': "conf",
            'flags': SEQ_ALL
        }))

        for channel in self.channels if not self.config else self.config:
            for pair in self.pairs if not self.config else self.config[channel]:
                message = {'event': 'subscribe',
                           'channel': channel,
                           'symbol': pair
                           }
                if 'book' in channel:
                    parts = channel.split('-')
                    if len(parts) != 1:
                        message['channel'] = 'book'
                        try:
                            message['prec'] = parts[1]
                            message['freq'] = parts[2]
                            message['len'] = parts[3]
                        except IndexError:
                            # any non specified params will be defaulted
                            pass

                if 'candles' in channel:
                    parts = channel.split('-')
                    if len(parts) != 1:
                        message['channel'] = 'candles'
                        try:
                            message['prec'] = parts[1]
                            message['freq'] = parts[2]
                            message['len'] = parts[3]
                        except IndexError:
                            # any non specified params will be defaulted
                            pass

                await websocket.send(json.dumps(message))

    @classmethod
    def get_name(cls):
        return 'bitfinex2'

    @classmethod
    def get_L2_book_feed(cls):
        return 'book-P0-F0-100'

    @classmethod
    def get_L3_book_feed(cls):
        return 'book-R0-F0-100'

    @classmethod
    def get_trades_feed(cls):
        return 'trades'

    @classmethod
    def get_ticker_feed(cls):
        return 'ticker'

    @classmethod
    def get_volume_feed(cls):
        return UNSUPPORTED

    @classmethod
    def get_funding_feed(cls):
        return 'trades'

    @classmethod
    def get_candle_feed(cls):
        return 'candles'
