from abc import ABCMeta, abstractmethod
from typing import Set

from qtmodel.error import QTError
from qtmodel.patterns.singleton import SingletonType


class Observable:
    """ Object that notifies its changes to a set of observers """
    def __init__(self):
        self.observers_ = set()
        self.settings_ = ObservableSettings()

    def register_observer(self, observer):
        """
        :param observer: Observer
        :return:
        """
        self.observers_.add(observer)

    def unregister_observer(self, observer):
        if self.settings_.updates_deferred():
            self.settings_.unregister_deferred_observer(observer=observer)

        return self.observers_.discard(observer)

    def notify_observers(self):
        # if updates are only deferred, flag this for later notification
        # these are held centrally by the settings singleton
        if not self.settings_.updates_enabled():
            self.settings_.register_deferred_observers(observers=self.observers_)
        elif self.observers_:
            successful = True
            err_msg = None
            for observer in self.observers_:
                try:
                    observer.update()
                except Exception as e:
                    # quite a dilemma. If we don't catch the exception,
                    # other observers will not receive the notification
                    # and might be left in an incorrect state. If we do
                    # catch it and continue the loop (as we do here) we
                    # lose the exception. The least evil might be to try
                    # and notify all observers, while raising an
                    # exception if something bad happened.
                    successful = False
                    err_msg = e.__repr__()

            if not successful:
                raise QTError(f"could not notify one or more observers: {err_msg}")


class Observer(metaclass=ABCMeta):

    def __init__(self):
        self.observables_ = []

    def register_with(self, observable: Observable):
        """
        :param observable: Observable
        :return:
        """
        if observable is not None:
            observable.register_observer(observer=self)
            return self.observables_.append(observable)
        return (self.observables_, False)

    def register_with_observables(self, observer):
        """
        :param observer: Observer
        :return:
        """
        observables = observer.observables_
        for observable in observables:
            self.register_with(observable=observable)

    def unregister_with(self, observable: Observable):
        observable.unregister_observer(observer=self)
        if observable in self.observables_:
            self.observables_.remove(observable)

    def unregister_with_all(self):
        for observable in self.observables_:
            observable.unregister_observer(observer=self)
        self.observables_.clear()

    @abstractmethod
    def update(self):
        pass

    def deep_update(self):
        self.update()

    def __del__(self):
        for observable in self.observables_:
            observable.unregister_observer(observer=self)


class ObservableSettings(metaclass=SingletonType):
    """ global repository for run-time library settings """

    def __init__(self):
        self.deferred_observers_ = set()
        self.updates_enabled_ = True
        self.updates_deferred_ = False

    def disable_updates(self, deferred: bool = False):
        self.updates_enabled_ = False
        self.updates_deferred_ = deferred

    def enable_updates(self):
        self.updates_enabled_ = True
        self.updates_deferred_ = False

        # if there are outstanding deferred updates, do the notification
        if self.deferred_observers_:
            successful = True
            err_msg = None

            for deferred_observer in self.deferred_observers_:
                try:
                    deferred_observer.update()
                except Exception as e:
                    successful = False
                    err_msg = e.__repr__()

            self.deferred_observers_.clear()

            if not successful:
                raise QTError(f"could not notify one or more observers: {err_msg}")

    def updates_enabled(self):
        return self.updates_enabled_

    def updates_deferred(self):
        return self.updates_deferred_

    def register_deferred_observers(self, observers: Set[Observer]):
        if self.updates_deferred():
            self.deferred_observers_.update(observers)

    def unregister_deferred_observer(self, observer: Observer):
        self.deferred_observers_.discard(observer)
