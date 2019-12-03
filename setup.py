from setuptools import setup,find_packages



setup(
    name='dsb_spider',
    version='0.0.12',
    author='cjxh',
    author_email='chenjianxihang@duoshoubang.cn',
    url='http://m.fine3q.com/home-w/index.html',
    description=u'一个轻量的爬虫工具',
    packages=find_packages(exclude=['log']),
    install_requires=['requests>=2.21.0', 'pip>=19.0.3', 'lxml>=4.4.1', 'chardet==3.0.4'],
    python_requires='>=3.6'
)