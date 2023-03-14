from abc import ABCMeta, abstractmethod

from qtmodel.patterns.observable import Observable, Observer


class LazyObject(metaclass=ABCMeta):

    def __init__(self):
        super(LazyObject, self).__init__()
        self._calculated = False
        self._frozen = False
        self._always_forward = False

    def update(self):
        # forwards notifications only the first time
        if self._calculated or self._always_forward:
            # set to False early
            # 1) to prevent infinite recursion
            # 2) otherways non-lazy observers would be served obsolete
            #    data because of self._calculated being still True
            self._calculated = False
            # observers don't expect notifications from frozen objects
            if not self._frozen:
                self.notify_observers()
                # exiting notifyObservers() self._calculated could be
                # already True because of non-lazy observers

    def recalculate(self):
        was_frozen = self._frozen
        self._calculated = self._frozen = False
        try:
            self.calculate()
        except Exception as e:
            self._frozen = was_frozen
            self.notify_observers()
            raise e
        self._frozen = was_frozen
        self.notify_observers()

    def freeze(self):
        self._frozen = True

    def unfreeze(self):
        # send notifications, just in case we lost any,
        # but only once, i.e. if it was frozen
        if self._frozen:
            self._frozen = False
            self.notify_observers()

    def always_forward_notifications(self):
        self._always_forward = True

    def calculate(self):
        if not self._calculated and not self._frozen:
            self._calculated = True  # prevent infinite recursion in case of bootstrapping
            try:
                self.perform_calculations()
            except Exception as e:
                self._calculated = False
                raise e

    @abstractmethod
    def perform_calculations(self):
        """
        This method must implement any calculations which must be
        (re)done in order to calculate the desired results.
        :return:
        """
        pass




        

