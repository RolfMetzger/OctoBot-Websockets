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

cdef class Ticker:
    cdef public int ready
    cdef public float bid_price
    cdef public float ask_price
    cdef public float last_price

    def __init__(self):
        self.ready = False
        self.ask_price = 0
        self.last_price = 0
        self.bid_price = 0

    cpdef int handle_quote(self, bid_price: float, ask_price: float):
        cdef int should_refresh = False

        if self.bid_price != bid_price:
            self.bid_price = bid_price
            should_refresh = True

        if self.ask_price != ask_price:
            self.ask_price = ask_price
            should_refresh = True

        return should_refresh

    cpdef int handle_recent_trade(self, last_price: float):
        if self.last_price != last_price:
            self.last_price = last_price
            return True
        return False

    cpdef int is_ready(self):
        if not self.ready:
            self.ready = self.last_price != 0 and self.bid_price != 0 and self.ask_price != 0
        return self.ready
