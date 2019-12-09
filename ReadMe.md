## 安装
```text
pip3 install dsb_spider==0.2.12
```
## 使用

#### 基本请求
```python
from dsb_spider.req import request
  
resp = request('GET', 'https://www.macys.com/shop/product?ID=10442340')
 
# 默认保存当前resp.text到/tmp/t.html
resp.save_self() 
 
# 默认支持xpath, 且支持多项xpath规则直到匹配命中
title1 = resp.xpath('//head/title/text()')
title2 = resp.xpath(['//head/title/text()', '//meta[@name="twitter:title"]/text()'])
# 输出： ["Origins 5-Pc. Plantscription Nourish, Renew & Hydrate Set & Reviews - Macy's"]

# 支持正则
result1 = resp.regex('.*?')

# 正则后转json
result2 = resp.regex_json('.*?')

# 扩展少量xpath比较字符函数:
# trim() 清空两侧, lower() 小写, upper() 大写
resp.xpath('//head/meta[trim(@value) = "Product"]')
resp.xpath('//head/meta[lower(@value) = "product"]')
resp.xpath('//head/meta[upper(@value) = "PRODUCT"]')

# 注册默认获取代理函数，方便使用request的use_default_proxy参数
from dsb_spider import getTaskFuncRegister

def get_proxy():
    return 'XXX.XX.X.X'

proxyRegistry = getTaskFuncRegister('proxy')
proxyRegistry.update({'get_proxy', get_proxy}) # 注册的函数名必须为get_proxy

```
#### 日志打印格式化
```python
from dsb_spider import getLogger

logger = getLogger('dsb')
logger.error('haha')
# 输出： [dsb] 2019-12-06 10:48:12 |  ERROR  | haha

```

#### 快速实现基于多线程简单的生产者消费者任务

Task对象是基于传入的参数实现的单例，task会有Ready，Running，Stoped三种状态。task初始为Ready状态
 
自动去重：通过单例+状态，保证了任务执行的原子性。
 
因为同一时间只能有一个task实例存在，当处于running状态时，其他任务变量执行该任务实例的ready方法会失败
 
* Ready态，此时可进行ready，stop, 不可run。
* Running态，此时可run, stop, 不可ready。
* Stop态，任务结束，啥都干不了。

可以注册do_ready, do_task, do_finish方法，方法均在task状态改变后被调用

```text
                  do_ready               do_task
+------+  init +------------+  ready  +--------------+
| task +-------> ReadyState +---------> RunningState |run
+------+       +------------+         +-------+------+
                     |stop                    |
                     |  +-------------+ stop  |
                     +--> StopedState <-------+
                        +-------------+
                            do_finish

```


```python
from dsb_spider import getTaskFuncRegister, Task, TaskListener,getLogger
import queue
import time
logger = getLogger('dsb')
 
TASK_NAME = 'task'
task = getTaskFuncRegister(TASK_NAME) # 注册器
 
# 定义task阶段: ready -> do -> stop

@task
def do_ready(self):
    logger.info(f'{self.id} ready')
 
@task
def do_task(self):
    logger.info(f'{self.id} running')
 
@task
def do_stop(self):
    logger.info(f'{self.id} stop')
    
@task
def _repr(self):
    return f'<task| {self.id}>'
    

def run():
    q = queue.Queue(-1)
    tl = TaskListener(q, 5)
    tl.start()
    while True:
        tasks = [x for x in range(10)] # 取到任务0~9
        logger.info(f'get tasks: {len(tasks)}')

        for t in tasks:
            task = Task(TASK_NAME, listener=tl, id=t)
            task.ready()
        time.sleep(5)
        
if __name__ == "__main__":
    run()
    
'''
[dsb] 2019-12-06 11:00:45 |   INFO  | get tasks: 10
[dsb] 2019-12-06 11:00:45 |   INFO  | 0 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 1 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 0 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 2 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 3 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 4 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 5 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 6 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 7 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 8 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 9 ready
[dsb] 2019-12-06 11:00:45 |   INFO  | 0 stop
[dsb] 2019-12-06 11:00:45 |   INFO  | 2 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 2 stop
[dsb] 2019-12-06 11:00:45 |   INFO  | 3 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 1 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 1 stop
[dsb] 2019-12-06 11:00:45 |   INFO  | 5 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 5 stop
[dsb] 2019-12-06 11:00:45 |   INFO  | 6 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 6 stop
[dsb] 2019-12-06 11:00:45 |   INFO  | 7 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 7 stop
[dsb] 2019-12-06 11:00:45 |   INFO  | 3 stop
[dsb] 2019-12-06 11:00:45 |   INFO  | 8 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 8 stop
[dsb] 2019-12-06 11:00:45 |   INFO  | 4 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 4 stop
[dsb] 2019-12-06 11:00:45 |   INFO  | 9 running
[dsb] 2019-12-06 11:00:45 |   INFO  | 9 stop
'''

```

#### 异常处理分离
异常处理函数注册表名为ex，使用getTaskFuncRegister('ex')直接注册即可

```python
from dsb_spider import getTaskFuncRegister, Task, TaskListener,getLogger
from dsb_spider.log.ex import DsbException
import queue
import time
logger = getLogger('dsb')
 
class TestExError(DsbException):
    handle_name = 'testExHandler' # handle_name即为处理此异常函数名 
 
exRegistry = getTaskFuncRegister('ex')
 
@exRegistry
def testExHandler(self, _ex, *args, **kwargs):
    '''
    self: 即当前task对象
    _ex: 当前捕获的异常对象
    '''
    logger.error('test success')


 
TASK_NAME = 'errtask'
errtask = getTaskFuncRegister(TASK_NAME) # 注册器
 
# 定义task阶段: ready -> do -> stop
@errtask
def do_ready(self):
    logger.info(f'{self.id} ready')
 
@errtask
def do_task(self):
    logger.info(f'{self.id} running')
    raise TestExError   # 假装出现了异常
 
@errtask
def do_finish(self):
    logger.info(f'{self.id} stop')
    
@errtask
def _repr(self):
    return f'<errtask| {self.id}>'
    

    
def run():
    q = queue.Queue(-1)
    tl = TaskListener(q, 5)
    tl.start()
    while True:
        tasks = [x for x in range(10)] # 取到任务0~9
        logger.info(f'get tasks: {len(tasks)}')

        for t in tasks:
            task = Task(TASK_NAME, listener=tl, id=t)
            task.ready()
        time.sleep(5)
        
if __name__ == "__main__":
    run()
    
'''
[dsb] 2019-12-06 17:52:27 |   INFO  | get tasks: 10
[dsb] 2019-12-06 17:52:27 |   INFO  | 0 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 1 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 2 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 3 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 4 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 5 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 6 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 7 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 8 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 9 ready
[dsb] 2019-12-06 17:52:27 |   INFO  | 0 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 0 stop
[dsb] 2019-12-06 17:52:27 |   INFO  | 1 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 1 stop
[dsb] 2019-12-06 17:52:27 |   INFO  | 2 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 2 stop
[dsb] 2019-12-06 17:52:27 |   INFO  | 3 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 3 stop
[dsb] 2019-12-06 17:52:27 |   INFO  | 4 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 4 stop
[dsb] 2019-12-06 17:52:27 |   INFO  | 5 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 5 stop
[dsb] 2019-12-06 17:52:27 |   INFO  | 6 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 6 stop
[dsb] 2019-12-06 17:52:27 |   INFO  | 7 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 7 stop
[dsb] 2019-12-06 17:52:27 |   INFO  | 8 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 8 stop
[dsb] 2019-12-06 17:52:27 |   INFO  | 9 running
[dsb] 2019-12-06 17:52:27 |  ERROR  | test success
[dsb] 2019-12-06 17:52:27 |   INFO  | 9 stop
'''
```
