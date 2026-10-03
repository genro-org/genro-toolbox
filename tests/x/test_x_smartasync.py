# Copyright 2026 Softwell S.r.l. - Genro Team
# SPDX-License-Identifier: Apache-2.0

"""Implementation tests for AsyncHandler.current_thread_loop."""

import asyncio

from genro_toolbox.smartasync import AsyncHandler


def test_current_thread_loop_setter_stores_and_removes():
    handler = AsyncHandler()
    loop = asyncio.new_event_loop()
    try:
        handler.current_thread_loop = loop
        assert handler.current_thread_loop is loop
        handler.current_thread_loop = None
        assert handler.current_thread_loop is not loop
    finally:
        handler.reset()
        loop.close()
