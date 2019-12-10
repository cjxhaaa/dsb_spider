from dsb_spider.log import getLogger,DEBUG
from dsb_spider.log.ex import DsbException
logger = getLogger('dsb')
# logger.setLevel(DEBUG)
from dsb_spider.utils import hash_args

class TaskStateError(DsbException):
    ex_msg = 'haha~'

class TaskAlreadyReadyError(TaskStateError):
    ex_msg = 'Already ready'


class TaskNotReadyError(TaskStateError):
    ex_msg = 'Not ready'


class TaskAlreadyStopedError(TaskStateError):
    ex_msg = 'Already stoped'

# 注册
_TASK_FUNC_REGISTERS = {}

def default(self, _ex , *args, **kwargs):
    logger.errorx(_ex)

class _FuncRegistry():
    def __init__(self, name:str):
        self.name = name
        self.funcs = {}
        if name == 'ex':
            self['default'] = default
        
    def update(self, funcs_iter):
        if hasattr(funcs_iter, 'items'):
            funcs_iter = funcs_iter.items()
        for key, value in funcs_iter:
            self[key] = value
            
    def __setitem__(self, key, value):
        if not callable(value):
            raise DsbException(f'func {key} register failed')
        if not key:
            raise ValueError('func name must not be none')
        self.funcs[key] = value
        
    def __getitem__(self, item):
        return self.funcs[item]
    
    def __delitem__(self, key):
        del self.funcs[key]
        
    def __iter__(self):
        return iter(self.funcs)
    
    def items(self):
        return list(self.funcs.items())
    
    def iteritems(self):
        return iter(self.funcs.items())
    
    def clear(self):
        self.funcs.clear()
        
    def __call__(self, obj):
        self[obj.__name__] = obj
        return obj
    
    def __repr__(self):
        return f'<{self.__class__.__name__}|{self.name}>'
    
    def __str__(self):
        return f'<{self.__class__.__name__}|{self.name}>'

def getTaskFuncRegister(name: str):
    try:
        return _TASK_FUNC_REGISTERS[name]
    except KeyError:
        register = _TASK_FUNC_REGISTERS[name] = _FuncRegistry(name)
        return register

exRegistry = getTaskFuncRegister('ex')

def exhandler(ignore:bool=True, interrupt:bool=False):
    def deco_func(func):
        def deco_args(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except TaskStateError as _ex:
                logger.debug(_ex)
            except Exception as _ex:
                if hasattr(_ex, 'handle_name'):
                    ex_handler = exRegistry[_ex.handle_name]
                else:
                    ex_handler = exRegistry['default']
                callable(ex_handler) and ex_handler(self, _ex, *args, *kwargs)

                if interrupt:
                    self.finish()
                if not ignore:
                    raise
        return deco_args
    return deco_func
    

# 使用单例保证相同任务运行的唯一性
class TaskSingleton(type):
    _instances = {}
    
    def __call__(cls,*args, **kwargs):
        key = hash_args(*args, **kwargs)
        if key in cls._instances:
            return cls._instances[key]
        instance = super().__call__(*args, **kwargs)
        instance.hash_key = key
        cls._instances[key] = instance
        return instance
    
    @classmethod
    def clear(cls, key):
        try:
            del cls._instances[key]
        except KeyError:
            pass

# 定义任务状态: ready -> running -> stoped , 只有ready状态可run
# ready:

class ReadyState():
    @staticmethod
    def ready(task):
        task.new_state(RunningState)
    
    @staticmethod
    def run(task):
        raise TaskNotReadyError
    
    @staticmethod
    def stop(task):
        task.new_state(StopedState)

class RunningState():
    @staticmethod
    def ready(task):
        raise TaskAlreadyReadyError

    @staticmethod
    def run(task):
        logger.info(f'start {task}')

    @staticmethod
    def stop(task):
        task.new_state(StopedState)

class StopedState():
    @staticmethod
    def ready(task):
        raise TaskAlreadyStopedError

    @staticmethod
    def run(task):
        raise TaskAlreadyStopedError

    @staticmethod
    def stop(task):
        raise TaskAlreadyStopedError
    
# 定义任务阶段： ready -> run -> finish

class Task(object, metaclass=TaskSingleton):
    def __new__(cls, _name, *args, **kwargs):
        for key, value in getTaskFuncRegister(_name).items():
            setattr(cls, key, value)
        return super().__new__(cls)
    
    def __init__(self,_name, listener=None, **kwargs):
        self._name = _name
        self.listener=listener
        self.new_state(ReadyState)
        
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._dead = False
    
    def new_state(self, state):
        self._state = state
    
    @exhandler(interrupt=True)
    def ready(self):
        self._state.ready(self)
        if self.listener is not None:
            self.listener.enqueue(self)
        if hasattr(self, 'do_ready'):
            self.do_ready()

    @exhandler(interrupt=True)
    def run(self):
        self._state.run(self)
        if hasattr(self, 'do_task'):
            self.do_task()

    @exhandler()
    def finish(self):
        self._state.stop(self)
        if hasattr(self, 'hash_key'):
            TaskSingleton.clear(self.hash_key)
        if hasattr(self, 'do_finish'):
            self.do_finish()

    def __repr__(self):
        if hasattr(self, '_repr'):
            return self._repr()
        return super().__repr__()

    def __str__(self):
        if hasattr(self, '_str'):
            return self._str()
        return super().__str__()
    
if __name__ == '__main__':
    haha = getTaskFuncRegister('haha')
    
    @haha
    def do_ready(self):
        raise Exception('hehe')
        
    @haha
    def do_task(self):
        raise Exception('hehe')
        print('run')
        
    @haha
    def do_finish(self):
        raise Exception('hehe')

    @haha
    def _repr(self):
        return 'haha'

    task = Task('haha')
    task.ready()
    task.run()
    task.finish()


