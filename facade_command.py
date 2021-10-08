"""This Script is still work in progresss. It is the start of an implementation of a photogrammetry algorithm."""

__author__ = "Philip Zimmermann"
__email__ = "philip.zimmermann@tum.de"
__version__ = "1.0"

import os
import FreeCAD, FreeCADGui
from PySide import QtGui
from PySide.QtGui import QApplication
import cv2 as cv
import sys
from collections import namedtuple
import numpy as np
from sympy import Point, Circle, intersection, Line, Segment

from facade_selection.facade_gui import FacadeGui
from place_in_cad import place_image, place_facade_objects

IMAGE_MAX_WIDTH = 1200
IMAGE_MAX_HEIGHT = 800


def resize_image(img):
    height, width = img.shape[:2]
    width_factor = IMAGE_MAX_WIDTH / width
    height_factor = IMAGE_MAX_HEIGHT / height
    image_factor = min(width_factor, height_factor)
    new_width = int(width * image_factor)
    new_height = int(height * image_factor)
    img = cv.resize(img, (new_width, new_height))
    return img


def line_line_intersection(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denominator == 0:
        raise Exception('lines do not intersect')
    x = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator
    y = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator
    return int(x), int(y)


def perpendicular_through_point(ortho_point_1, line_point_1, line_point_2):
    g1 = line_point_2[0] - line_point_1[0], line_point_2[1] - line_point_1[1]
    g2 = g1[1], -g1[0]
    ortho_point_2 = ortho_point_1[0] + g2[0], ortho_point_1[1] + g2[1]
    return line_line_intersection(ortho_point_1, ortho_point_2, line_point_1, line_point_2)


def wait_n_key():
    while True:
        key = cv.waitKeyEx()
        if key == 110:
            break


class FacadeCommand:
    """Command that lets the user select vanishing points in an image and places the facade on selected face in CAD
    model """

    def __init__(self):
        self.fassade = namedtuple("fassade", "src_img corners windows")
        self.fassade.corners = []

    def GetResources(self):
        resource_path = FreeCAD.getHomePath() + "Mod/OSM-Buildings/resources/"
        if not os.path.exists(resource_path):
            resource_path = FreeCAD.getUserAppDataDir() + "Mod/OSM-Buildings/resources/"
        return {'Pixmap': resource_path + "place_facade.svg",  # the name of a svg file available in the resources
                'Accel': "Shift+S",  # a default shortcut (optional)
                'MenuText': "Add a Fassade",
                'ToolTip': "Select an image to add a fassade"}

    def draw_circle(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDBLCLK:
            point = np.array([x, y])
            self.fassade.corners.append(point)
            self.update_image()

    def empty_method(self, *args):
        pass

    def update_image(self):
        img = self.fassade.src_img.copy()
        for i in self.fassade.corners:
            x = i[0]
            y = i[1]
            cv.circle(img, (x, y), 3, (0, 255, 0), -1)

        cv.imshow("window", img)

    def Activated(self):
        """Do something here"""
        try:
            self.clicked_face = FreeCADGui.Selection.getSelectionEx()[0].SubObjects[0]
            self.clicked_building = FreeCADGui.Selection.getSelection()[0]
        except:
            FreeCAD.Console.PrintMessage("Select facade in 3D model first (left-click)." + "\n")
            return

        self.fassade = namedtuple("fassade", "src_img corners windows")
        self.fassade.corners = []
        self.doc = FreeCAD.activeDocument()

        filename = QtGui.QFileDialog().getOpenFileName()[0]

        # Loading the image
        img = cv.imread(filename)
        if img is None:
            sys.exit("Could not read the image.")

        img = resize_image(img)
        self.fassade.src_img = img

        cv.namedWindow('window')

        # mark points
        FreeCAD.Console.PrintMessage("Mark facade corners and two depth lines. To continue press N" + "\n")
        cv.setMouseCallback('window', self.draw_circle)
        cv.imshow("window", img)

        wait_n_key()
        cv.setMouseCallback('window', self.empty_method)

        img = self.fassade.src_img.copy()
        if len(self.fassade.corners) != 4:
            sys.exit("Corner size has to be 4")

        # todo determine which point is which (when they are disordered)
        top_left, top_right, bot_right, bot_left = self.fassade.corners

        # draw rectangle along four points
        cv.line(img, (top_left[0], top_left[1]), (top_right[0], top_right[1]), (0, 255, 0), 3)
        cv.line(img, (top_right[0], top_right[1]), (bot_right[0], bot_right[1]), (0, 255, 0), 3)
        cv.line(img, (bot_right[0], bot_right[1]), (bot_left[0], bot_left[1]), (0, 255, 0), 3)
        cv.line(img, (bot_left[0], bot_left[1]), (top_left[0], top_left[1]), (0, 255, 0), 3)

        van_point_hor = line_line_intersection(top_left, top_right, bot_right, bot_left)
        van_point_ver = line_line_intersection(top_left, bot_left, top_right, bot_right)
        # van_point_dep = line_line_intersection(depth_l1, depth_l2, depth_r1, depth_r2)

        # expand image
        scaling_factor = 16
        old_img = img
        img = cv.resize(img, (img.shape[1] // scaling_factor, img.shape[0] // scaling_factor))
        side_border = (old_img.shape[0] - img.shape[0]) // 2
        top_border = (old_img.shape[1] - img.shape[1]) // 2
        img = cv.copyMakeBorder(img, side_border, side_border,
                                top_border, top_border,
                                cv.BORDER_CONSTANT)

        def transform_point(point):
            scaled = point[0] // scaling_factor, point[1] // scaling_factor
            return scaled[0] + top_border, scaled[1] + side_border

        top_left = Point(*transform_point(top_left))
        top_right = Point(*transform_point(top_right))
        bot_left = Point(*transform_point(bot_left))
        bot_right = Point(*transform_point(bot_right))
        van_point_hor = Point(*transform_point(van_point_hor))
        van_point_ver = Point(*transform_point(van_point_ver))

        cv.line(img, top_left.coordinates, van_point_hor.coordinates, (50, 50, 255))
        cv.line(img, bot_left.coordinates, van_point_hor.coordinates, (50, 50, 255))
        cv.line(img, top_left.coordinates, van_point_ver.coordinates, (50, 50, 255))
        cv.line(img, top_right.coordinates, van_point_ver.coordinates, (50, 50, 255))

        # connect vanishing points
        van_point_connecting_line = Line(van_point_hor, van_point_ver)
        cv.line(img, van_point_hor.coordinates, van_point_ver.coordinates, (0, 255, 255))

        cv.imshow("window", img)
        wait_n_key()

        # perpendicular through image center and vanishing point connecting line
        img_center = Point(img.shape[1] // 2, img.shape[0] // 2)
        perpendicular_point = Point(*perpendicular_through_point(img_center.coordinates, van_point_ver.coordinates,
                                                                 van_point_hor.coordinates))
        perpendicular_line = Line(img_center, perpendicular_point)
        circle_center = Segment(van_point_ver, van_point_hor).midpoint
        radius = van_point_ver.distance(van_point_hor) / 2
        circle = Circle(circle_center, radius)
        intersections = intersection(circle, perpendicular_line)
        # find the correct intersection point
        if len(intersections) != 2:
            raise Exception("There should be two intersections with the circle.")
        if len(intersection(Segment(img_center, intersections[0]), van_point_connecting_line)) == 1:
            circle_intersection = intersections[0]
        elif len(intersection(Segment(img_center, intersections[1]), van_point_connecting_line)) == 1:
            circle_intersection = intersections[1]
        else:
            raise Exception("One of the points should be on other side of the vanishing point line")

        cv.circle(img, circle_center.coordinates, radius, (50, 255, 50))
        cv.line(img, circle_intersection.coordinates, van_point_hor.coordinates, (255, 255, 255))
        cv.line(img, circle_intersection.coordinates, van_point_ver.coordinates, (255, 255, 255))
        cv.line(img, circle_intersection.coordinates, img_center.coordinates, (255, 50, 50))

        cv.imshow("window", img)
        wait_n_key()

        # compute mirror line
        mirror_slope = van_point_ver - van_point_hor
        bottom_center = Segment(bot_right, bot_left).midpoint
        mirror_line_origin = bottom_center + (bottom_center - van_point_hor)
        mirror_line = Line(mirror_line_origin, mirror_line_origin + mirror_slope)
        cv.line(img, (mirror_line_origin - 10 * mirror_slope).coordinates,
                (mirror_line_origin + 10 * mirror_slope).coordinates,
                (255, 150, 150), 3)

        # compute mirror line meeting points
        top_mirror_point = intersection(Line(top_left, top_right), mirror_line)[0]
        bot_mirror_point = intersection(Line(bot_left, bot_right), mirror_line)[0]
        right_mirror_point = intersection(Line(top_right, bot_right), mirror_line)[0]
        left_mirror_point = intersection(Line(top_left, bot_left), mirror_line)[0]

        # compute projected points
        vertical_projection_slope = Line(circle_intersection, van_point_ver).direction
        horizontal_projection_slope = Line(circle_intersection, van_point_hor).direction

        top_projection_line = Line(top_mirror_point, top_mirror_point + horizontal_projection_slope)
        bot_projection_line = Line(bot_mirror_point, bot_mirror_point + horizontal_projection_slope)
        right_projection_line = Line(right_mirror_point, right_mirror_point + vertical_projection_slope)
        left_projection_line = Line(left_mirror_point, left_mirror_point + vertical_projection_slope)

        top_left_projected = intersection(top_projection_line, left_projection_line)[0]
        top_right_projected = intersection(top_projection_line, right_projection_line)[0]
        bot_left_projected = intersection(bot_projection_line, left_projection_line)[0]
        bot_right_projected = intersection(bot_projection_line, right_projection_line)[0]

        # draw projection computation
        cv.line(img, top_right.coordinates, top_mirror_point.coordinates, (50, 50, 255))
        cv.line(img, bot_right.coordinates, bot_mirror_point.coordinates, (50, 50, 255))
        cv.line(img, bot_right.coordinates, right_mirror_point.coordinates, (50, 50, 255))
        cv.line(img, bot_left.coordinates, left_mirror_point.coordinates, (50, 50, 255))

        cv.line(img, top_mirror_point.coordinates, top_left_projected.coordinates, (50, 255, 50))
        cv.line(img, bot_mirror_point.coordinates, bot_left_projected.coordinates, (50, 255, 50))
        cv.line(img, right_mirror_point.coordinates, top_right_projected.coordinates, (50, 255, 50))
        cv.line(img, left_mirror_point.coordinates, top_left_projected.coordinates, (50, 255, 50))

        width = top_left_projected.distance(top_right_projected)
        height = top_left_projected.distance(bot_left_projected)
        facade_ratio = height / width

        cv.imshow("window", img)
        wait_n_key()

        cv.destroyAllWindows()

        # compute perspective transform and save for later
        fac_width = 800
        fac_height = int(facade_ratio * fac_width)
        matrix = cv.getPerspectiveTransform(np.float32(self.fassade.corners),
                                            np.float32([[0, 0], [fac_width - 1, 0], [fac_width - 1, fac_height - 1],
                                                        [0, fac_height - 1]]))
        transformed_img = cv.warpPerspective(self.fassade.src_img.copy(), matrix, (fac_width, fac_height))
        self.img_path = "facade_transformed.jpg"
        cv.imwrite(self.img_path, transformed_img)

        # adjust building size in CAD model
        self.adjust_building_height(facade_ratio)
        self.clicked_face = FreeCADGui.Selection.getSelectionEx()[0].SubObjects[0]

        # let user select facade segments
        FreeCAD.Console.PrintMessage("Creating Gui" + "\n")
        FacadeGui(self, self.img_path)

    def insertIntoCAD(self, fac_objects):
        # place image in 3d model
        place_image(self.doc, self.img_path, self.clicked_face)
        place_facade_objects(self.doc, fac_objects, self.clicked_face)
        self.doc.recompute()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

    def adjust_building_height(self, facade_ratio):
        width = self.clicked_face.Vertexes[0].Point.sub(self.clicked_face.Vertexes[1].Point).Length
        height = width * facade_ratio
        height_vector = FreeCAD.Vector(0, 0, height)
        point_vectors_top = []
        for top_corner in self.clicked_building.corners_bottom:
            top_corner = top_corner.add(height_vector)
            point_vectors_top.append(top_corner)
        self.clicked_building.corners_top = point_vectors_top
        self.doc.recompute()


FreeCADGui.addCommand('FacadeCommand', FacadeCommand())

if __name__ == '__main__':
    fassade = FacadeCommand()
    fassade.Activated()
