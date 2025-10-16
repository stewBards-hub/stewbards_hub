import asyncio, aiosqlite 

DB_PATH = "alexandria.db"

class Librarian: 
    def __init__(self, path=DB_PATH): 
        self.path = path
        self.queue = asyncio.Queue()
        self._writer_task = None 

    async def start_writer(self): 
        self._writer_task = asyncio.create_task(self._writer())
    
    async def stop_writer(self): 
        await self.queue.put(None)
        if self._writer_task: 
            await self._writer_task

    #writes to the database
    async def _writer(self): 
        async with aiosqlite.connect(self.path) as db: 
            while True: 
                job = await self.queue.get()
                if job is None: 
                    break 
                query, params = job 
                await db.execute(query, params)
                await db.commit()

    async def enqueue_to_write(self, query, params=()):
        await self.queue.put(query, params)
