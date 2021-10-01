""" The code in this file is used to initialize the OSM-Buildings addon with the FreeCAD GUI."""

__author__ = "Johannes Hechtl"
__email__ = "johannes.hechtl@tum.de"
__version__ = "1.0"

class OSM_Buildings(Workbench):

    MenuText = "OSM-Buildings"
    ToolTip = "A description of my workbench"
    resource_path = FreeCAD.getHomePath() + "Mod/OSM-Buildings/resources/"
    import os
    if not os.path.exists(resource_path):
        resource_path = FreeCAD.getUserAppDataDir() + "Mod/OSM-Buildings/resources/"
    Icon = resource_path + "house.svg"

    def Initialize(self):
        """This function is executed when FreeCAD starts"""
        # import MyModuleA, MyModuleB # import here all the needed files that create your FreeCAD commands

        # if you have command classes in other files, they need to be imported EXACTLY here
        from facade_command import FacadeCommand
        from osm_to_3d_model import OSMtoCAD

        self.list = ['OSMtoCAD',
                     'FacadeCommand',
                     # 'PlaceImage'
                     ]  # A list of the command names created
        # commands, that are not listed here, will not show up in the GUI

        self.appendToolbar("My Commands", self.list)  # creates a new toolbar with your commands
        self.appendMenu("My New Menu", self.list)  # creates a new menu
        self.appendMenu(["An existing Menu", "My submenu"], self.list)  # appends a submenu to an existing menu

    def Activated(self):
        """This function is executed when the workbench is activated"""
        return

    def Deactivated(self):
        """This function is executed when the workbench is deactivated"""
        return

    def ContextMenu(self, recipient):
        """This is executed whenever the user right-clicks on screen"""
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu("My commands", self.list)  # add commands to the context menu

    def GetClassName(self):
        # This function is mandatory if this is a full python workbench
        # This is not a template, the returned string should be exactly "Gui::PythonWorkbench"
        return "Gui::PythonWorkbench"


Gui.addWorkbench(OSM_Buildings())
