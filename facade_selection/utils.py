__author__ = "Philip Zimmermann"
__email__ = "philip.zimmermann@tum.de"
__version__ = "1.0"

from collections import namedtuple
import enum

Point = namedtuple('Point', 'x y')


class FacObjTypes(enum.Enum):
    WINDOW = 0
    BALCONY = 1
