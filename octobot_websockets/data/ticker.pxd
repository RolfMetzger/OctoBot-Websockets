# cython: language_level=3
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
    cdef public timestamp
    cdef public bint ready
    cdef public double bid_price
    cdef public double ask_price
    cdef public double last_price

    cpdef bint handle_quote(self, double bid_price, double ask_price)
    cpdef bint handle_recent_trade(self, double last_price)
    cpdef bint is_ready(self)
