# Copyright 2026 Softwell S.r.l. - Genro Team
# SPDX-License-Identifier: Apache-2.0

"""Contract tests for smartawait, smartcontinuation, SmartLock and is_awaitable."""

import asyncio

import pytest

from genro_toolbox import SmartLock, is_awaitable, smartawait, smartcontinuation


async def value_after_yield(value):
    await asyncio.sleep(0)
    return value


async def nested_coroutine(value):
    return value_after_yield(value)


def test_is_awaitable():
    coroutine = value_after_yield(1)
    assert is_awaitable(coroutine)
    assert not is_awaitable(1)
    coroutine.close()


@pytest.mark.asyncio
async def test_smartawait_plain_value():
    assert await smartawait(5) == 5


@pytest.mark.asyncio
async def test_smartawait_resolves_nested_awaitables():
    assert await smartawait(nested_coroutine(7)) == 7


def test_smartcontinuation_plain_value_is_immediate():
    assert smartcontinuation(3, lambda value, extra: value + extra, 10) == 13


@pytest.mark.asyncio
async def test_smartcontinuation_awaitable_returns_continuation():
    result = smartcontinuation(
        value_after_yield(3), lambda value, extra=0: value * 2 + extra, extra=1
    )
    assert is_awaitable(result)
    assert await result == 7


@pytest.mark.asyncio
async def test_smartlock_runs_once_for_concurrent_callers():
    calls = []

    async def load(value):
        calls.append(value)
        await asyncio.sleep(0.01)
        return value * 10

    lock = SmartLock()
    results = await asyncio.gather(*(lock.run_once(load, 4) for _ in range(5)))
    assert results == [40] * 5
    assert calls == [4]


@pytest.mark.asyncio
async def test_smartlock_runs_again_after_completion():
    calls = []

    async def load():
        calls.append(1)
        return len(calls)

    lock = SmartLock()
    assert await lock.run_once(load) == 1
    assert await lock.run_once(load) == 2


@pytest.mark.asyncio
async def test_smartlock_shares_exception():
    async def fail():
        await asyncio.sleep(0.01)
        raise KeyError("boom")

    lock = SmartLock()
    results = await asyncio.gather(*(lock.run_once(fail) for _ in range(3)), return_exceptions=True)
    assert all(isinstance(result, KeyError) for result in results)


@pytest.mark.asyncio
async def test_smartlock_reset_cancels_waiters():
    started = asyncio.Event()

    async def slow():
        started.set()
        await asyncio.sleep(1)
        return 1

    lock = SmartLock()
    first = asyncio.create_task(lock.run_once(slow))
    await started.wait()
    waiter = asyncio.create_task(lock.run_once(slow))
    await asyncio.sleep(0)
    lock.reset()
    with pytest.raises(asyncio.CancelledError):
        await waiter
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first


def test_smartlock_reset_without_future():
    SmartLock().reset()
