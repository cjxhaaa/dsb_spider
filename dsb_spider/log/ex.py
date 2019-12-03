'''
所有exception，都要继承DsbException，并注明ex_code以作区分
'''


class DsbException(Exception):
    ex_code = 1
    ex_msg = 'error~~'
    
    def __init__(self, ex_msg=None):
        self.ex_msg = ex_msg or self.ex_msg
        super().__init__(ex_msg)
    
    def __str__(self):
        return self.ex_msg


class InvalidProduct(DsbException):
    ex_code = 2
    ex_msg = 'Product Not Found'


class EndTask(DsbException):
    ex_code = 3
    
    def __init__(self, msg=''):
        msg = 'end this task. {}'.format(msg)
        super().__init__(msg)


class CustomMadeProduct(DsbException):
    ex_code = 4
    ex_msg = 'it is a custom-made product, which we can not sell now'


class OutOfStock(DsbException):
    ex_code = 5
    ex_msg = 'Out Of Stock'


class TemporarilyOutOfStock(DsbException):
    ex_code = 6
    ex_msg = 'TemporarilyOutOfStock'


class EmptyResponse(DsbException):
    ex_code = 7
    ex_msg = 'EmptyResponse, please try again later.'


class NeedProxy(DsbException):
    ex_code = 8
    ex_msg = 'Access denied,need proxy'


class NeedProxyPool(DsbException):
    ex_code = 9
    ex_msg = 'Connection error,proxy pool need run'


class NotGood(DsbException):
    ex_code = 10
    ex_msg = 'Something wrong'


class CategoryNotFound(DsbException):
    ex_code = 11
    ex_msg = 'category not found'


class NeedLocalInsert(DsbException):
    ex_code = 12
    ex_msg = '这类商品需要本地手动入库'


class RedirectError(DsbException):
    ex_code = 13
    ex_msg = 'redirect error'


class NeedVPN(DsbException):
    ex_code = 14
    ex_msg = 'Need VPN!!'


class InvalidCategory(DsbException):
    ex_code = 15
    ex_msg = '违禁类目'


class CanNotFindImage(DsbException):
    ex_code = 16
    ex_msg = '图片未找到'


class CanNotFindSize(DsbException):
    ex_code = 17
    ex_msg = 'size未找到'


class AccessDenied(DsbException):
    ex_code = 18
    ex_msg = 'ip被封'


class TooManyRequestRetries(DsbException):
    ex_code = 19
    
    def __init__(self, msg=''):
        msg = '请求重试过多: {}'.format(msg)
        super().__init__(msg)


class OnceProduct(DsbException):
    ex_code = 20
    ex_msg = '这种商品只做一次入库，不需要再入了'


class CrmError(DsbException):
    ex_code = 21
    ex_msg = '从CRM 取任务 出了问题?'