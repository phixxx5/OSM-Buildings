__author__ = "Philip Zimmermann"
__email__ = "philip.zimmermann@tum.de"
__version__ = "1.0"

from facade_selection.utils import Point, FacObjTypes


class FacadeObject:
    def __init__(self, p1: Point, p2: Point, type: FacObjTypes):
        self.p1 = Point(min(p1.x, p2.x), min(p1.y, p2.y))
        self.p2 = Point(max(p1.x, p2.x), max(p1.y, p2.y))
        self.type = type

    def width(self) -> int:
        return abs(self.p1.x - self.p2.x)

    def height(self) -> int:
        return abs(self.p1.y - self.p2.y)

    def center(self) -> Point:
        return Point((self.p1.x + self.p2.x) / 2, (self.p1.y + self.p2.y) / 2)

    def set_width(self, value: float):
        center = self.center()
        self.p1 = Point(center.x - value / 2, self.p1.y)
        self.p2 = Point(center.x + value / 2, self.p2.y)

    def set_height(self, value: float):
        center = self.center()
        self.p1 = Point(self.p1.x, center.y - value / 2)
        self.p2 = Point(self.p2.x, center.y + value / 2)
