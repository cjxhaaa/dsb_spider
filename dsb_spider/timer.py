import time
import datetime


class Timer(object):
    def __init__(self, name, timeout=0):
        self.name = name
        self.timeout = timeout
        self.start_ts = None
        
        self.status = "stop"
        self.amount_time = 0
        
        self.start()
    
    def __enter__(self, *args, **kwargs):
        pass
    
    def __exit__(self, type, value, trace):
        self.stop()
    
    def start(self):
        if self.status in ("stop",):
            self.amount_time = 0
        
        self.start_ts = time.time()  # 设置当前时间为开始时间
        
        self.status = "start"
    
    def pause(self):
        if self.status != "start":
            return
        
        self.status = "pause"
        now = time.time()
        self.amount_time += now - self.start_ts
    
    def resume(self):
        if self.status != "pause":
            return
        
        self.start()
    
    def stop(self, callback=None):
        now = time.time()
        if self.status == "pause":
            self.start_ts = now
        
        cost = (now - self.start_ts) + self.amount_time
        if callable(callback):
            callback(cost)
        
        else:
            if cost >= self.timeout:
                print("{} EXEC '{}' cost: {:.5f}s".format(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.name, cost))
        return cost