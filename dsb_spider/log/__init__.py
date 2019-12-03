'''
to start:
import log

logger = log.getLogger('dsb')
logger.info('hah')
console output 'hah'

logger = log.getLogger('dsb.mongo')
logger.error('hah')
mongo will save log 'hah'
'''
from dsb_spider.log.formatter import ColorFormatter
from dsb_spider.log import ex
from functools import wraps
import logging

__all__ = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DATE_FMT', 'ColorFormatter', 'getLogger', 'ex')

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# **加色规则：
# 如果要添加color，标志必须为 %(color)s-----  %(reset)s的格式，
# 粗体：color-bold  红色：color-red  粗体红色：color-bold_red  背景红色：color-bg_red
# 如：%(color-red)s 内容 %(reset)s 或者 %(color-bg_blue)s 内容 %(reset)s
DATE_FMT = "%Y-%m-%d %H:%M:%S"
_LEVEL_COLOR_FMT = '[dsb] %(asctime)s | %(color-level)s %(levelname)5s %(reset)s | %(message)s'
_LEVEL_FMT = '[dsb] %(asctime)s | %(levelname)5s | %(message)s'


def exLogger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs.setdefault('extra', {})
        if args and isinstance(args[0], Exception):
            if not isinstance(args[0], ex.DsbException):
                kwargs['exc_info'] = args[0]
            kwargs['extra'].update({
                'ex_code': getattr(args[0], 'ex_code', 0),
                'ex_name': args[0].__class__.__name__,
                'ex_msg': args[0].__str__()
            })
            
            url = kwargs.pop('url', '')
            if url:
                args = (f'{args[0].__class__.__name__} : {url}',)  # 这样直接改，有待商榷
                kwargs['extra'].update({'url': url})
        
        return func(*args, **kwargs)
    
    return wrapper


def getLogger(name=None):
    logger = logging.getLogger(name)
    setattr(logger, 'debugx', exLogger(logger.debug))
    setattr(logger, 'infox', exLogger(logger.info))
    setattr(logger, 'warningx', exLogger(logger.warning))
    setattr(logger, 'errorx', exLogger(logger.error))
    setattr(logger, 'criticalx', exLogger(logger.critical))
    return logger


def initColorlog():
    colorFormatter = ColorFormatter(_LEVEL_COLOR_FMT, datefmt=DATE_FMT)
    
    logger = getLogger('dsb')
    logger.propagate = False  # 阻止record向root节点传播
    logger.setLevel(INFO)
    
    # color console log
    colorStreamHandler = logging.StreamHandler()
    colorStreamHandler.setFormatter(colorFormatter)
    logger.addHandler(colorStreamHandler)

initColorlog()