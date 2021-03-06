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
from octobot_websockets.feeds.feed cimport Feed
from octobot_websockets.data.candle cimport Candle

cdef class CandleConstructor:
    cdef double time_frame_delta
    cdef double time_frame_seconds
    cdef bint should_stop
    cdef str symbol

    cdef Feed feed
    cdef Candle candle

    cdef object time_frame
    cdef object candle_task
