from setuptools import setup,find_packages

setup(
    name='dsb_spider',
    version='0.2.17',
    author='cjxh',
    author_email='cjxhaaa@gmail.com',
    url='https://github.com/cjxhaaa/dsb_spider',
    description='A lightweight web scraping tool.',
    long_description="https://github.com/cjxhaaa/dsb_spider",
    packages=find_packages(exclude=['log']),
    install_requires=['requests>=2.21.0', 'pip>=19.0.3', 'lxml>=4.4.1', 'chardet==3.0.4'],
    python_requires='>=3.6'
)