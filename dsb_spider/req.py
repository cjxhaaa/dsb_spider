from dsb_spider.utils import str_to_dict
from dsb_spider.timer import Timer
from dsb_spider.log.ex import TooManyRequestRetries
from urllib.parse import urljoin, urlparse
from lxml import etree
from requests.exceptions import (ConnectTimeout, ConnectionError, ReadTimeout)
from requests.adapters import HTTPAdapter
import requests
import time
import traceback
import chardet

__ALL__ = ['request', 'get', 'post', 'response2selector','HTTPSSortHeaderAdapter']

default_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.3',
}

SESSIONS_MAP = {}


class _Response(object):
    def __init__(self, content):
        self.content = content
        if isinstance(self.content, bytes):
            self._encoding = chardet.detect(self.content)["encoding"]
        else:
            self._encoding = "utf8"
    
    @property
    def apparent_encoding(self):
        return self.encoding
    
    @property
    def encoding(self):
        return self._encoding
    
    @encoding.setter
    def encoding(self, value):
        self._encoding = value
    
    @property
    def text(self):
        if isinstance(self.content, bytes):
            return self.content.decode(self.encoding)
        
        else:
            return self.content


def response2selector(response):
    if isinstance(response, (str, bytes)):
        response = _Response(response)
    
    element = None
    
    def _xpath(_paths):
        nonlocal element  # lxml被动解析
        if element is None:
            try:
                try:
                    element = etree.HTML(response.text)
                except ValueError:
                    pass
                
                if element is None:
                    element = etree.HTML(response.text.encode('utf8'))
            except etree.XMLSyntaxError as e:
                encoding2 = response.apparent_encoding
                # print(e)
                print('change encoding', response.encoding, 'to', encoding2)
                response.encoding = encoding2
                element = etree.HTML(response.text)
        try:
            if not isinstance(_paths, (tuple, list)):
                _paths = [_paths, ]
            
            result_list = []
            for _path in _paths:
                result_list = element.xpath(_path)
                if len(result_list) > 0:
                    break
            return result_list
        
        except AttributeError as e:
            traceback.print_exc()
            return []
    
    return _xpath

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


SESSION_NUM = {}


def counter_session(netloc, max_count):
    max_count = max_count or 10000
    if SESSION_NUM.get(netloc):
        SESSION_NUM[netloc] += 1
    else:
        SESSION_NUM[netloc] = 1
    
    if SESSION_NUM[netloc] > max_count:
        s = SESSIONS_MAP.pop(netloc, None)
        if s:
            s.close()
            
def default_get_proxies():
    return None

def request(method, url, **kwargs):
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
    adapter = kwargs.pop("adapter", None)
    max_count = kwargs.pop('max_count', None)
    retry = kwargs.pop('retry', 3)
    kwargs.setdefault('timeout', 30)
    kwargs.setdefault('allow_redirects', True)
    kwargs.setdefault('verify', False)
    
    # headers
    dict_headers = get_dict_headers(kwargs.pop('headers', {}))
    headers = default_headers.copy()
    headers.update(dict_headers)
    kwargs['headers'] = headers
    
    # proxies
    proxies = kwargs.pop('proxies', None)
    use_default_proxy = kwargs.pop('use_default_proxy', False)
    proxy_port = kwargs.pop('proxy_port', None)
    proxy = kwargs.pop("proxy", None)
        
    if not proxies and proxy_port:
        proxies = {
            'http': f'socks5://localhost:{proxy_port}',
            'https': f'socks5://localhost:{proxy_port}'
        }
    if not proxies and proxy:
        proxies = {'http': proxy, 'https': proxy}
        
    
    netloc = urlparse(url).netloc
    retry_count = 0
    while True:
        try:
            if use_default_proxy:
                proxy = default_get_proxies()
                print(proxy)
                if proxy:
                    proxies = {'http': proxy, 'https': proxy}
            
            if proxies:
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
    response.xpath = response2selector(response)
    response.urljoin = _urljoin
    response.urlsjoin = _urlsjoin
    response.url_original = url
    return response

def get(url, params=None, **kwargs):
    """Sends a GET request.

    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """
    return request('get', url, params=params, **kwargs)


def post(url, data=None, json=None, **kwargs):
    # print(kwargs)
    """Sends a POST request.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
    :param json: (optional) json data to send in the body of the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """
    
    # **kwargs (dict kwargs被解包成了 参数 传入)
    return request('post', url, data=data, json=json, **kwargs)