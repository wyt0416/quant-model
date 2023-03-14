from abc import ABCMeta, abstractmethod


# class AcyclicVisitor:
#     """ degenerate base class for the Acyclic %Visitor pattern """
#     pass


class Visitor(metaclass=ABCMeta):
    """ Visitor for a specific class """

    @abstractmethod
    def visit(self, p):
        pass
