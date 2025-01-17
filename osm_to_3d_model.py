__author__ = "Johannes Hechtl"
__email__ = "johannes.hechtl@tum.de"
__version__ = "1.0"

import os
from PySide import QtGui
import FreeCAD, FreeCADGui

from osm_map.BuildingObject import makeBuilding
from osm_map.Map import Map


class OSMtoCAD:
    """This command loads a .osm file and adds 3d models of all buildings to the currently active workspace"""

    def GetResources(self):
        resource_path = FreeCAD.getHomePath() + "Mod/OSM-Buildings/resources/"
        if not os.path.exists(resource_path):
            resource_path = FreeCAD.getUserAppDataDir() + "Mod/OSM-Buildings/resources/"
        return {'Pixmap': resource_path + "map.svg",  # the name of a svg file available in the resources
                'Accel': "Shift+S",  # a default shortcut (optional)
                'MenuText': "OSM to CAD",
                'ToolTip': "Load .osm file"}

    def Activated(self):

        doc = FreeCAD.activeDocument()

        filename = QtGui.QFileDialog().getOpenFileName()[0]

        map = Map(filename)

        doc = FreeCAD.activeDocument()

        # add buildings to FreeCad Document
        for building in map.buildings:
            makeBuilding(building)

        doc.recompute()
        return

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


FreeCADGui.addCommand('OSMtoCAD', OSMtoCAD())
