from dsb_spider import log

logger = log.getLogger('dsb')


# 用来去重
class TaskSingleton(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        operation, url = args[:2]
        if url not in cls._instances:
            cls._instances[url] = super().__call__(*args, **kwargs)
        return cls._instances[url]
    
    @classmethod
    def clear(cls, key):
        try:
            del cls._instances[key]
        except KeyError:
            pass


class ActivityTaskSingleton(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        task_id = args[0]  # task肯定有task_id, 且唯一
        if task_id not in cls._instances:
            print('need create:', task_id)
            cls._instances[task_id] = super().__call__(*args, **kwargs)
        return cls._instances[task_id]
    
    @classmethod
    def clear(cls, key):
        try:
            del cls._instances[key]
        except KeyError:
            pass


ImageTaskSingleton = ActivityTaskSingleton


class BaseTask(object):
    def new_state(self, state):
        self._state = state
    
    def ready(self):
        raise NotImplementedError()
    
    def do_task(self):
        return self._state.run(self)
    
    def finish(self):
        raise NotImplementedError()


# 可定义任务状态: stoped -> ready -> stoped , 只有ready状态可run

class TaskState():
    @staticmethod
    def ready(task):
        raise NotImplementedError()
    
    @staticmethod
    def run(task):
        raise NotImplementedError()
    
    @staticmethod
    def stop(task):
        raise NotImplementedError()