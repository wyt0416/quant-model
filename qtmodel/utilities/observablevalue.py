from qtmodel.patterns.observable import Observable


class ObservableValue:

    def __init__(self, value=None):
        self._value = value
        self.observable = Observable()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v
        self.observable.notify_observers()
