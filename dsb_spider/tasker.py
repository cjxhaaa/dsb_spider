from dsb_spider.log import getLogger
from dsb_spider.log.ex import DsbException
logger = getLogger('dsb')
from dsb_spider.utils import hash_args
from types import MethodType,FunctionType

# 注册
_TASK_FUNC_REGISTERS = {}

class _FuncRegistry():
    def __init__(self, name:str):
        self.name = name
        self.funcs = {}
        
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

# 定义任务状态: stoped -> ready -> stoped , 只有ready状态可run
# ready:

class StopedState():
    @staticmethod
    def ready(task):
        task.new_state(ReadyState)
        task.do_ready()
    
    @staticmethod
    def run(task):
        raise RuntimeError('Not ready')
    
    @staticmethod
    def stop(task):
        raise RuntimeError('Already stoped')

class ReadyState():
    @staticmethod
    def ready(task):
        raise RuntimeError('Already ready')

    @staticmethod
    def run(task):
        task.do_task()

    @staticmethod
    def stop(task):
        task.new_state(StopedState)
        task.do_stop()
    
# 定义任务阶段： ready -> run -> finish

class Task(object, metaclass=TaskSingleton):
    # def __new__(cls, _name, *args, **kwargs):
    #     registry = getTaskFuncRegister(_name)
    #     for key, value in registry.items():
    #         setattr(cls, key, value)
    #     return super().__new__(cls)
    
    def __init__(self,_name, listener=None, **kwargs):
        self.task_name = _name
        self.listener=listener
        self.new_state(StopedState)
        registry = getTaskFuncRegister(_name)
        for key, value in registry.items():
            setattr(self, key, MethodType(value, self))
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def new_state(self, state):
        self._state = state
    
    def ready(self):
        try:
            self._state.ready(self)
            if self.listener is not None:
                self.listener.enqueue(self)
        except RuntimeError as ex:
            logger.debug(ex)
    
    def run(self):
        self._state.run(self)
    
    def finish(self):
        if hasattr(self, 'hash_key'):
            TaskSingleton.clear(self.hash_key)
        self._state.stop(self)

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
        print('ready')
        
    @haha
    def do_task(self):
        print(self)

    @haha
    def do_stop(self):
        print('stop')


    @haha
    def _repr(self):
        return 'haha'

    task = Task('haha')
    task.ready()
    task.run()
    task.finish()
    print(isinstance(do_stop, FunctionType))
    print(isinstance(haha, ))


