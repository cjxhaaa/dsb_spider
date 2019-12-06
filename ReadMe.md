## 安装
```text
pip3 install dsb_spider
```
## 使用

####基本请求
```python
from dsb_spider.req import request
  
resp = request('GET', 'https://www.macys.com/shop/product?ID=10442340')
 
# 默认保存当前resp.text到/tmp/t.html
resp.save_self() 
 
# 默认支持xpath, 且支持多项xpath规则
title1 = resp.xpath('//head/title/text()')
title2 = resp.xpath(['//head/title/text()', '//meta[@name="twitter:title"]/text()'])
# 输出： ["Origins 5-Pc. Plantscription Nourish, Renew & Hydrate Set & Reviews - Macy's"]
  
# 扩展少量xpath比较字符函数:
# trim() 清空两侧, lower() 小写, upper() 大写
resp.xpath('//head/meta[trim(@value) = "Product"]')
resp.xpath('//head/meta[lower(@value) = "product"]')
resp.xpath('//head/meta[upper(@value) = "PRODUCT"]')

```
####日志打印格式化
```python
from dsb_spider import getLogger

logger = getLogger('dsb')
logger.error('haha')
# 输出： [dsb] 2019-12-06 10:48:12 |  ERROR  | haha

```

#### 快速实现基于多线程简单的生产者消费者任务
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
