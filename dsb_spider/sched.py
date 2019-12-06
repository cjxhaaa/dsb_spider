import queue
import traceback
import threading
from dsb_spider import log

logger = log.getLogger('dsb')



class TaskListener():
    def __init__(self, queue, concurrent:int=3):
        self.queue = queue
        self.concurrent = concurrent
    
    def enqueue(self, record):
        self.queue.put_nowait(record)
    
    def dequeue(self, block:bool=True):
        task = self.queue.get(block)
        return task
    
    def work(self):
        q = self.queue
        has_task_done = hasattr(q, 'task_done')
        while True:
            try:
                task = self.dequeue()
            except queue.Empty:
                break
            
            try:
                if not task:
                    break
                self.handle(task)
            except Exception as ex:
                traceback.print_exc()
                logger.errorx(ex)
            finally:
                task.finish()
                if has_task_done:
                    q.task_done()
    
    def handle(self, task):
        logger.debug(f'start: {task}')
        task.run()
    
    def start(self):
        for i in range(self.concurrent):
            t = threading.Thread(target=self.work)
            t.daemon = True
            t.start()