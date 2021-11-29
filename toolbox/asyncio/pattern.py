import asyncio
from typing import Awaitable, Callable, Optional


class ClassTask:
    def __init__(
        self,
        func: Awaitable,
        start_callback: Optional[Callable] = None,
        end_callback: Optional[Callable] = None,
        run_forever: bool = False,
        start: bool = False,
    ):
        """
        Adds start, stop, and async context manager functionality to a class.

        This is a useful pattern that can be used for any asyncio-based class with an
        awaitable entry-point that needs to be started/stopped via non-blocking code,
        and/or needs to be accessed via an async context manager.

        This is useful for large asynchronous operations that happens within a single
        class. See example below for how to use it.

        Args:
            func: The awaitable entry-point of the class.
            start_callback: A function to call when the class is started.
            end_callback: A function to call when the class is stopped.
            run_forever: Whether to run the class forever.
            start: Whether to start the class immediately on initialization.

        Example:

            .. code-block:: python

                from toolbox.asyncio.pattern import ClassTask
                import asyncio

                class AsyncClass(ClassTask):
                    def __init__(self, start: bool = False):
                        super().__init__(
                            self.run,
                            start_callback=lambda: print("Starting!"),
                            end_callback=lambda: print("Stopping!"),
                            run_forever=True,
                            start=start,
                        )

                    async def run(self):
                        # Some async functionality here.

                async def main():

                    # Use with __init__ start.
                    process = AsyncClass(start=True)
                    await asyncio.sleep(1)
                    process.stop()

                    # Use with functions to start/stop.
                    process = AsyncClass()
                    process.start()
                    await asyncio.sleep(1)
                    process.stop()

                    # Use with context manager to start/stop.
                    async with AsyncClass() as process:
                        ...

                asyncio.run(main())
        """

        self._func = func
        self._start_callback = start_callback
        self._end_callback = end_callback
        self._run_forever = run_forever
        self._task = None
        self._loop = asyncio.get_event_loop()
        if start:
            self.start()

    def start(self):
        """
        Starts the task without blocking.
        """
        if not self._task or self._task.cancelled():
            if self._start_callback:
                self._start_callback()
            self._task = self._loop.create_task(self._func())
            if self._run_forever:
                self._loop.run_forever()

    def stop(self):
        """
        Stops the task without blocking.
        """
        if self._task and not self._task.cancelled():
            if self._end_callback:
                self._end_callback()
            self._task.cancel()

    async def __aenter__(self) -> type:
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.stop()
        if self._task:
            return self._task.cancelled()
