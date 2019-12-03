from .color_codes import parse_colors
import logging
import re

__all__ = ('ColorFormatter')

LOG_LEVEL_COLORS = {
    logging.DEBUG: 'white',
    logging.INFO: 'green',
    logging.WARNING: 'yellow',
    logging.ERROR: 'red',
    logging.CRITICAL: 'bold_red',
}


class ColorFormatter(logging.Formatter):
    def usesColor(self):
        return self._style._fmt.find('%(color') >= 0
    
    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        
        if self.usesColor():
            colors = re.findall(f'%\((color-.*?)\)s', self._style._fmt)
            for color in colors:
                if color == 'color-level':
                    setattr(record, color, parse_colors('bg_' + LOG_LEVEL_COLORS[record.levelno]))
                else:
                    setattr(record, color, parse_colors(color.split('-')[-1]))
            record.reset = parse_colors('reset')
        s = self.formatMessage(record)
        
        if hasattr(record, 'ex_msg'):
            record.exc_text = record.ex_msg + '\n'
        
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            else:
                record.exc_text += self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)
        return s