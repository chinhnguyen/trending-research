from collections.abc import Awaitable, Callable

ProgressCallback = Callable[[str, int], Awaitable[None] | None]


async def report_progress(callback: ProgressCallback | None, stage: str, percent: int) -> None:
    if callback is None:
        return
    result = callback(stage, percent)
    if result is not None:
        await result
