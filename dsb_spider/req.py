from dsb_spider.utils import str_to_dict
from dsb_spider.timer import Timer
from dsb_spider.log.ex import DsbException
from urllib.parse import urljoin, urlparse
from lxml import etree
from requests.exceptions import (ConnectTimeout, ConnectionError, ReadTimeout)
from requests.adapters import HTTPAdapter
from functools import partial
from typing import List, Set, Union
from collections import Counter
from dsb_spider.tasker import getTaskFuncRegister
import requests
import time
import traceback
import re
import json

__ALL__ = ['request', 'get', 'post', 'tranResponse','HTTPSSortHeaderAdapter']

default_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.3',
}

SESSIONS_MAP = {}

_Paths = Union[str, List[str], Set[str]]
_Content = _Patten = Union[str, bytes]
_Pattens = Union[_Patten, List[_Patten], Set[_Patten]]
_XpathElems =  Union[List[etree._Element], List[str]]
_Resp = Union[requests.Response, _Content]


class TooManyRequestRetries(DsbException):
    def __init__(self, msg=''):
        msg = 'Too many request retries: {}'.format(msg)
        super().__init__(msg)

ns = etree.FunctionNamespace(None)

@ns
def trim(context, result):  # 新增: //a[trim(text()) = "Dsb"]
    return [text.strip() for text in result]

@ns
def lower(context, result): # 新增：//a[lower(text()) = "dsb"]
    return [text.lower() for text in result]

@ns
def upper(context, result): #新增：//a[upper(text()) = "DSB"]
    return [text.upper() for text in result]


class _Response(object):
    def __init__(self, text: _Content):
        if isinstance(text, bytes):
            self._content = text
        else:
            self._content = bytes(text, 'utf8')
            
_RE_COMPILE_CACHE = {}
        
class NewResponse(requests.Response):
    def __init__(self):
        super().__init__()
        self.element = None
        
    def xpath(self, paths:_Paths) -> _XpathElems:
        if self.element is None:
            try:
                try:
                    self.element = etree.HTML(self.text)
                except ValueError:
                    self.element = etree.HTML(self.text.encode('utf8'))
            except etree.XMLSyntaxError as e:
                encoding2 = self.apparent_encoding
                print('change encoding', self.encoding, 'to', encoding2)
                self.encoding = encoding2
                self.element = etree.HTML(self.text)
                
        if self.element is None:
            return []
        
        try:
            if isinstance(paths, str):
                paths = [paths, ]
        
            for _path in paths:
                nodes = self.element.xpath(_path)
                if len(nodes) > 0:
                    return nodes
            return []
    
        except AttributeError as e:
            traceback.print_exc()
            return []
    
    def regex(self, paths:_Pattens, flags=0) ->  List[_Content]:
        if isinstance(paths, (str, bytes)):
            paths = [paths]
            
        for path in paths:
            if isinstance(path, str):
                result = re.findall(path, self.text, flags)
            else:
                result = re.findall(path, self.content, flags)
            if len(result) > 0:
                return result
        return []
    
    def regex_json(self, paths:_Paths, flags=0) -> List[dict]:
        results = []
        for _result in self.regex(paths, flags):
            results.append(json.loads(_result))
        return results
        
    def save_self(self, path:str='/tmp/t.html'):
        with open(path, 'w') as fb:
            print(path)
            fb.write(self.text)
    
def tranResponse(response: _Resp) -> Union[NewResponse, _Response]:
    if isinstance(response, (str, bytes)):
        response = _Response(response)
    newResp = NewResponse()
    newResp.__dict__.update(response.__dict__)
    return newResp

# 头部排序
class HTTPSSortHeaderConnection():
    def putheader(self, header, *values):
        self._get_headers_buffer().append((header, values))
    
    def _get_headers_buffer(self):
        if hasattr(self, "_headers_buffer"):
            return self._headers_buffer
        
        else:
            self._headers_buffer = []
            return self._headers_buffer
    
    def endheaders(self, *args, **kwargs):
        headers_scores = [
            "Host",
            "User-Agent",
            "Accept",
            "Accept-Language",
            "Accept-Encoding",
            "Content-Type",
            "Referer",
            "Content-Length",
            "Cookie"
            "Connection",
            "Upgrade-Insecure-Requests",
            "Pragma",
            "Cache-Control",
        ]
        hdr_kvs = sorted(self._get_headers_buffer(),
                         key=lambda kv: headers_scores.index(kv[0]) if kv[0] in headers_scores else len(headers_scores))
        self._headers_buffer = []
        for k, vs in hdr_kvs:
            super(HTTPSSortHeaderConnection, self).putheader(k, *vs)
        
        return super(HTTPSSortHeaderConnection, self).endheaders(*args, **kwargs)


class HTTPSSortHeaderAdapter(HTTPAdapter):
    def get_connection(self, url, proxies=None):
        conn = super(HTTPSSortHeaderAdapter, self).get_connection(url, proxies)
        if not issubclass(conn.ConnectionCls, HTTPSSortHeaderConnection):
            conn.ConnectionCls = type("HTTPSSortHeaderConnection", (HTTPSSortHeaderConnection, conn.ConnectionCls), {})
            conn.ConnectionCls._headers_buffer = []
        return conn

def get_dict_headers(headers):
    return {str: str_to_dict,
            dict: lambda x: x}[type(headers)](headers)


def get_session_by_url(url):
    netloc = urlparse(url).netloc
    return SESSIONS_MAP.get(netloc, requests.session())

def clear_session_by_url(url):
    netloc = urlparse(url).netloc
    SESSIONS_MAP.pop(netloc, None)


_SESSION_COUNTER = Counter()


def counter_session(netloc, max_count):
    max_count = max_count or 10000
    _SESSION_COUNTER[netloc] += 1
    
    if _SESSION_COUNTER[netloc] > max_count:
        _SESSION_COUNTER[netloc] = 0
        s = SESSIONS_MAP.pop(netloc, None)
        if s:
            s.close()
            
def default_get_proxies():
    return None

def request(method:str, url:str, adapter:HTTPAdapter=None, max_count:int=None,retry:int=3,
            proxies=None,use_default_proxy:bool=False,proxy_port:int=None,proxy:str=None, **kwargs) -> NewResponse:
    '''
    :param method:
    :param url:
    :param kwargs:
    adapter: 适配器
    max_count: session使用最大计数
    retry: 请求重试最大次数
    timeout: 请求超时
    allow_redirects: 是否允许重定向
    proxies: 完整格式代理
    proxy_port: socks5代理端口
    proxy: 代理地址
    use_default_proxy: 直接使用默认代理
    session: 使用自定义session
    headers: 头部
    以及其他若干requests.request参数
    :return:
    '''
    kwargs.setdefault('timeout', 30)
    kwargs.setdefault('allow_redirects', True)
    kwargs.setdefault('verify', False)
    
    # headers
    dict_headers = get_dict_headers(kwargs.pop('headers', {}))
    headers = default_headers.copy()
    headers.update(dict_headers)
    kwargs['headers'] = headers
    
    # proxies
    if proxy_port:
        proxies = {
            'http': f'socks5://localhost:{proxy_port}',
            'https': f'socks5://localhost:{proxy_port}'
        }
    if proxy:
        proxies = {'http': proxy, 'https': proxy}
        
    
    netloc = urlparse(url).netloc
    retry_count = 0
    while True:
        try:
            if use_default_proxy:
                try:
                    get_proxy_func = getTaskFuncRegister('proxy')['get_proxy']
                    proxy = get_proxy_func()
                    print(proxy)
                    if proxy:
                        proxies = {'http': proxy, 'https': proxy}
                except KeyError:
                    pass
            
            kwargs['proxies'] = proxies

            with Timer(method + ' request: ' + url, timeout=5):
                session = kwargs.pop('session', None) or SESSIONS_MAP.get(netloc, None)  # 根据每一个主机名来取一个session
                
                if not session:
                    session = requests.session()
                    if adapter:
                        session.mount("http://", adapter)
                        session.mount("https://", adapter)
                    
                    SESSIONS_MAP[netloc] = session
                
                response = session.request(method, url, **kwargs)
            break
        except (ConnectTimeout, ReadTimeout, ConnectionError) as e:
            print(e, ' retry')
            if retry_count >= retry:
                err_url = url
                if hasattr(e, 'request') and hasattr(e.request, 'url'):
                    err_url = e.request.url
                raise TooManyRequestRetries(err_url)
            time.sleep(2)
            retry_count+=1
    
    counter_session(netloc, max_count)
    
    def _urlsjoin(urls):
        assert isinstance(urls, list)
        return [_urljoin(i) for i in urls]
    
    def _urljoin(url):
        assert isinstance(url, str)
        return urljoin(response.url, url)
    
    # Binding a html parser to response
    
    response = tranResponse(response)
    response.urljoin = _urljoin
    response.urlsjoin = _urlsjoin
    response.url_original = url
    return response

get = partial(request, 'GET')
post = partial(request, 'post')
delete = partial(request, 'delete')
head = partial(request, 'head')
put = partial(request, 'PUT')


if __name__ == '__main__':
    resp = tranResponse('''<html>
  <head>
    <link href="great.css" rel="stylesheet" type="text/css">
    <title>Best Page Ever</title>
  </head>
  <body>
    <h1 class="heading">Top News</h1>
    <p style="font-size: 200%">World News only on this page</p>
    Ah, and here's some more text, by the way.
    <p>... and this is a parsed fragment ...</p>
  </body>
</html>''')
    print(resp.xpath('//head'))
    # resp = request('GET','http://m.fine3q.com/home-w/index.html')
    # hh = resp.xpath('//node()')
    # import ipdb
    # ipdb.set_trace()