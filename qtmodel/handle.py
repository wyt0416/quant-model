from qtmodel.error import qt_require
from qtmodel.patterns.observable import Observable, Observer


class Link(Observable, Observer):

    def __init__(self, h, register_as_observer: bool):
        Observable.__init__(self)
        Observer.__init__(self)
        self._h = None
        self._is_observer = False
        self.link_to(h, register_as_observer)

    def link_to(self, h, register_as_observer: bool):
        if (h != self._h) or (self._is_observer != register_as_observer):
            if self._h and self._is_observer:
                self.unregister_with(self._h)
            self._h = h
            self._is_observer = register_as_observer
            if self._h and self._is_observer:
                self.register_with(self._h)
            self.notify_observers()

    def empty(self):
        return self._h is None

    def current_link(self):
        return self._h

    def update(self):
        self.notify_observers()


class Handle:
    """
    Shared handle to an observable
    All copies of an instance of this class refer to the same
    observable by means of a relinkable smart pointer. When such
    pointer is relinked to another observable, the change will be
    propagated to all the copies.
    """

    def __init__(self, p=None, register_as_observer: bool = True):
        self._link = Link(p, register_as_observer)

    def current_link(self):
        qt_require(not self.empty(), "empty Handle cannot be dereferenced")
        return self._link.current_link()

    def empty(self):
        return self._link.empty()

    def __getattribute__(self, attr):
        if 'link' not in attr and '__dict__' not in attr and "empty" not in attr:
            return object.__getattribute__(self._link.current_link(), attr)
        return object.__getattribute__(self, attr)

    def __eq__(self, other):
        """
        self==other.
        :param other:
        :return: Handle
        """
        return self._link == other._link

    def __ne__(self, other):
        """
        self!=other.
        :param other:
        :return:
        """
        return self._link != other._link

    def __lt__(self, other):
        """
        self<other.
        :param other:
        :return:
        """
        return id(self._link) > id(other._link)


class RelinkableHandle(Handle):
    """
    Relinkable handle to an observable
    An instance of this class can be relinked so that it points to
    another observable. The change will be propagated to all
    handles that were created as copies of such instance.
    """

    def __init__(self, p=None, register_as_observer: bool = True):
        super().__init__(p, register_as_observer)

    def link_to(self, h, register_as_observer: bool = True):
        self._link.link_to(h, register_as_observer)
