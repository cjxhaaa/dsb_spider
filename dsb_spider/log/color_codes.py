__all__ = ('escape_codes', 'parse_colors')

def esc(*x):
    return f"\033[{';'.join(x)}m"


escape_codes = {
    'reset': esc('0'),
    'bold': esc('01'),
    'thin': esc('02')
}

COLORS = [
    'black',
    'red',
    'green',
    'yellow',
    'blue',
    'purple',
    'cyan',
    'white'
]

PREFIXES = [
    ('3', ''), ('01;3', 'bold_'), ('02;3', 'thin_'),
    ('3', 'fg_'), ('01;3', 'fg_bold_'), ('02;3', 'fg_thin_'),
    ('4', 'bg_'), ('10', 'bg_bold_')
]

for prefix, prefix_name in PREFIXES:
    for code, name in enumerate(COLORS):
        escape_codes[prefix_name + name] = esc(prefix + str(code))


def parse_colors(name):
    return escape_codes[name]