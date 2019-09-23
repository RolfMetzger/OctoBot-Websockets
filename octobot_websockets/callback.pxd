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

cdef class Callback(object):
    cdef object callback

cdef class TradeCallback(Callback):
    pass

cdef class TickerCallback(Callback):
    pass

cdef class CandleCallback(Callback):
    pass

cdef class KlineCallback(Callback):
    pass

cdef class BookCallback(Callback):
    pass

cdef class OrdersCallback(Callback):
    pass

cdef class PositionCallback(Callback):
    pass

cdef class UpdatedBookCallback(Callback):
    pass

cdef class FundingCallback(Callback):
    pass

cdef class PortfolioCallback(Callback):
    pass
