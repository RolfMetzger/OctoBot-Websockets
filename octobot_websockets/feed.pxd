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

cdef class Feed:
    cdef str api_key
    cdef str api_secret
    cdef str address

    cdef int timeout
    cdef int timeout_interval
    cdef int book_update_interval
    cdef int updates

    # booleans
    cdef int create_loop
    cdef int is_connected
    cdef int do_deltas
    cdef int should_stop

    cdef list pairs
    cdef list time_frames
    cdef list channels

    cdef public dict callbacks

    # objects
    cdef object loop
    cdef object logger
    cdef object websocket
    cdef object ccxt_client
    cdef object _watch_task
    cdef object _websocket_task
    cdef object last_msg

    cdef __initialize(self, pairs, channels, callbacks)
    cpdef start(self)
    cdef on_close(self)
    cpdef stop(self)
    cpdef close(self)
    cdef list get_auth(self)
    cdef list get_pairs(self)
    cdef int timestamp_normalize(self, ts)
    cdef str get_pair_from_exchange(self, pair)
    cdef str get_exchange_pair(self, pair)
    cdef str feed_to_exchange(self, feed)
    cdef float safe_float(self, dictionary, key, default_value)
