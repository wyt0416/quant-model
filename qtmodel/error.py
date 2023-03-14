from loguru import logger


class QTError(Exception):
    def __init__(self,
                 message: str):
        """ Create QTError object by passing a message string. """
        self.message = message

    def __str__(self):
        return f'"QTError:" {self.message}'


class TestError(Exception):
    def __init__(self,
                 message: str):
        """ Create TestError object by passing a message string. """
        self.message = message

    def __str__(self):
        return f'"TestError:" {self.message}'


class NotCatchError(Exception):
    def __init__(self,
                 message: str):
        """ Create NotCatchError object used in 'try' sentence which will not be caught by trying. """
        self.message = message

    def __str__(self):
        return f'"TestError:" {self.message}'


def qt_require(condition, message):
    if not condition:
        raise QTError(message=message)


def qt_ensure(condition, message):
    if not condition:
        raise QTError(message=message)


def qt_assert(condition, message):
    if not condition:
        raise QTError(message=message)


def qt_require_no_throw(expression: str, globals=None, locals=None):
    try:
        exec(expression, globals, locals)
        logger.info("successful")
    except Exception as e:
        logger.error(e)
