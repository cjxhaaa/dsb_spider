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
