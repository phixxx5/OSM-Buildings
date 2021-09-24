__author__ = "Philip Zimmermann"
__email__ = "philip.zimmermann@tum.de"
__version__ = "1.0"

import FreeCAD, FreeCADGui
from PySide import QtGui
from typing import List
import math

from facade_selection.facade_gui import FacadeObject
from facade_selection.utils import FacObjTypes



def place_image(doc, image_path: str, clicked_face) -> None:
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


def place_facade_objects(doc, fac_objects: List[FacadeObject], clicked_face) -> None:
    points = clicked_face.Vertexes
    face_normal = clicked_face.normalAt(0, 0)
    # points are always ordered this way
    ref_point = points[0].Point
    horiz_point = points[1].Point
    verti_point = points[3].Point
    yaw_angle = math.degrees(FreeCAD.Vector(1, 0, 0).getAngle(face_normal))
    if face_normal.y < 0:
        yaw_angle = - yaw_angle
    else:
        yaw_angle = + yaw_angle
    rot_2 = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), yaw_angle)
    for fac_object in fac_objects:
        box_object = doc.addObject("Part::Box", "Box")
        box_object.Width = ref_point.sub(horiz_point).Length * abs(fac_object.p1.x - fac_object.p2.x)
        box_object.Height = ref_point.sub(verti_point).Length * abs(fac_object.p1.y - fac_object.p2.y)
        box_object.Length = 100  # mm
        position = ref_point.add(horiz_point.sub(ref_point).multiply(min(fac_object.p1.x, fac_object.p2.x)
                                                                     )).add(
            verti_point.sub(ref_point).multiply(1 - max(fac_object.p1.y, fac_object.p2.y)
                                                ))
        box_object.Placement = FreeCAD.Placement(position, rot_2)
        if fac_object.type == FacObjTypes.WINDOW:
            box_object.ViewObject.ShapeColor = (0.67, 1.00, 1.00)
        if fac_object.type == FacObjTypes.BALCONY:
            box_object.Length = 1500  # mm
            box_object.ViewObject.ShapeColor = (1.00, 0.67, 0.00)
    FreeCAD.ActiveDocument.recompute()  # if nothing appears recompute


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
