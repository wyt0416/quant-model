import threading

global_storage = threading.local()


class SingletonType(type):
    """ Meta class for the singleton pattern. """

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if getattr(global_storage, cls.__name__, None) is None:
            setattr(global_storage, cls.__name__, super().__call__(*args, **kwargs))
        return getattr(global_storage, cls.__name__, None)
