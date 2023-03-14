from qtmodel.methods.lattices.lattice import TreeLattice
from qtmodel.timegrid import TimeGrid
from qtmodel.types import Real


class TreeLattice1D(TreeLattice):

    def __init__(self, time_grid: TimeGrid, n: int):
        super(TreeLattice1D, self).__init__(time_grid=time_grid, n=n)

    def grid(self, t: Real):
        i = self.time_grid().index(t)
        grid = [None] * self.impl().size(i)
        for j in range(len(grid)):
            grid[j] = self.impl().underlying(i, j)
        return grid

    def underlying(self, i: int, index: int):
        return self.impl().underlying(i, index)
