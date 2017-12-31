import asyncio

__all__ = ('LoadInstrument', 'load')

# Frequency in seconds, of how often the load is updated.
_LOAD_FREQ = 1

class Instrument(asyncio.LoopInstrument):

    def __init__(self):
        self._load = 0.0
        self._load_last_update = None
        self._load_sleeping_time = None

    def _update_load(self, loop):
        """Update the load of the loop"""
        # The load of the loop is calculated as the
        # percentage of the time waiting for IO events
        # vs the total time from the last update.

        # Use a decay function to represent the load of the system.
        # where each decay step is done at each _LOAD_FREQ
        # ex. load = t0/2 + t1/4 + t2/8 + ...

        # Decay as many times the _LOAD_FREQ has been reached,
        # where in regular situations just one, however when the reactor
        # had a spike of callbaks or there was a long sleeping time
        # it can be more than one.

        total_time = loop.time() - self._load_last_update

        while total_time >= _LOAD_FREQ:
            sleeping_time = min(self._load_sleeping_time, _LOAD_FREQ)
            load = 1 - (sleeping_time/_LOAD_FREQ)
            self._load = (load + self._load) / 2
            total_time -= _LOAD_FREQ
            self._load_sleeping_time =\
                max(0, self._load_sleeping_time - _LOAD_FREQ)

        # the leftovers will be used in the next _updated_load call
        self._load_last_update = loop.time() - total_time

    def load(self, loop=None):
        """Return the load of the loop. A float number between 0.0 and 1.0."""

        loop = loop if loop else asyncio.get_event_loop()

        if (loop.is_running()) and\
                (loop.time() - self._load_last_update >= _LOAD_FREQ):
            self._update_load(loop)

        return self._load

    # asyncio event loop signals

    def loop_start(self, loop):
        self._load_sleeping_time = 0
        self._load_last_update = loop.time()

    def tick_start(self, loop):
        pass

    def io_start(self, loop, timeout):
        self._io_start = loop.time()

    def io_end(self, loop, timeout):
        dt = loop.time() - self._io_start

        if timeout is not None:
            # Count only time spent sleeping, if OS decided to give
            # the CPU later dont count it as slept time.
            self._load_sleeping_time += min(dt, timeout)
        else:
            self._load_sleeping_time += dt

    def tick_end(self, loop, handles):
        if loop.time() - self._load_last_update >= _LOAD_FREQ:
            self._update_load(loop)


LoadInstrument = Instrument()
load = LoadInstrument.load
