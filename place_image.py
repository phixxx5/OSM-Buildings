__author__ = "Philip Zimmermann"
__email__ = "philip.zimmermann@tum.de"
__version__ = "1.0"

import FreeCAD, FreeCADGui
from PySide import QtGui

import math


def place_image(doc, image_path, clicked_face):
    # change draw style to flat lines to improve image display
    name = "Flat lines"
    mw = FreeCADGui.getMainWindow()
    for i in mw.findChildren(QtGui.QAction):
        if i.text() == name:
            i.activate(QtGui.QAction.Trigger)

    points = clicked_face.Vertexes
    face_normal = clicked_face.normalAt(0, 0)
    pitch_angle = 90  # TODO this only considers perfectly vertical building facades
    rot_1 = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), pitch_angle)
    ref_point = points[0].Point
    for point in points[1:]:
        if point.Point.z == ref_point.z:
            horiz_point = point.Point
        if point.Point.x == ref_point.x and point.Point.y == ref_point.y:
            verti_point = point.Point
    yaw_angle = math.degrees(FreeCAD.Vector(1, 0, 0).getAngle(face_normal))
    if face_normal.y < 0:
        yaw_angle = 90 - yaw_angle
    else:
        yaw_angle = 90 + yaw_angle
    rot_2 = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), yaw_angle)
    img_plane = doc.addObject("Image::ImagePlane", "ImagePlane")
    img_plane.ImageFile = image_path
    img_plane.XSize = ref_point.sub(horiz_point).Length
    img_plane.YSize = ref_point.sub(verti_point).Length
    img_plane.Placement = FreeCAD.Placement(clicked_face.CenterOfMass, rot_2.multiply(rot_1))


class PlaceImage:

    def Activated(self):
        """ This code gets executed when the corresponding button is pressed."""
        doc = FreeCAD.activeDocument()
        clicked_face = FreeCADGui.Selection.getSelectionEx()[0].SubObjects[0]
        file_path = QtGui.QFileDialog().getOpenFileName()[0]
        place_image(doc, file_path, clicked_face)
        doc.recompute()

    def GetResources(self):
        """ Return resources for GUI"""
        return {'Pixmap': 'path_to_an_icon/myicon.png', 'MenuText': 'Place image',
                'ToolTip': 'Place an image in the 3D model on a selected building facade.'}
        # Pixmap is a png icon that is the face of the button.
        # The tooltip gets displayed when hovering over the button


FreeCADGui.addCommand('PlaceImage', PlaceImage())
