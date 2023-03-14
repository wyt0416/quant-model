

class Fdm1dMesher:

    def __init__(self, size: int):
        self._locations = [0] * size
        self._dplus = [0] * size
        self._dminus = [0] * size

    def size(self):
        return len(self._locations)

    def dplus(self, index: int):
        return self._dplus[index]

    def dminus(self, index: int):
        return self._dminus[index]

    def location(self, index: int):
        return self._locations[index]

    def locations(self):
        return self._locations
