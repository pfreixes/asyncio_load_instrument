============================
Asyncio loop load instrument
============================

*Disclaimer* this feature does not work with the official Python Asyncio module, it is built on top of
an Asyncio `modification <https://github.com/pfreixes/cpython/commit/adc3ba46979394997c40aa89178b4724442b28eb>`, still a proposal.

Measure how busy is your loop and make your code adaptative for different level of performance saturation.
The following snippet shows how the instrument can be used to reject coroutines when the load factor is greater
than **0.9**:

.. code-block:: python

	import asyncio
	import time
	import random

	from asyncio_load_instrument import LoadInstrument, load


	async def coro(loop, idx):
		await asyncio.sleep(idx % 10)
		if load() > 0.9:
			return False
		start = loop.time()
		while loop.time() - start < 0.02:
			pass
		return True

	async def run(loop, n):
		tasks = [coro(loop, i) for i in range(n)]
		results = await asyncio.gather(*tasks)
		abandoned = len([r for r in results if not r])
		print("Load reached for {} coros/seq: {}, abandoned {}/{}".format(n/10, load(), abandoned))

	async def main(loop):
		await run(loop, 800)

	loop = asyncio.get_event_loop()
	loop.add_instrument(LoadInstrument)
	loop.run_until_complete(main(loop))

.. _modificaiton: 
