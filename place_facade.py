"""This Script is still work in progresss. It is the start of an implementation of a phtogrammetry algorithm."""

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

from facade_gui import FacadeGui
from place_image import place_image

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


class PlaceFacade:
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
        if len(self.fassade.corners) != 8:
            sys.exit("Corner size has to be 8")

        # todo determine which point is which (when they are disordered)
        top_left, top_right, bot_right, bot_left, depth_l1, depth_l2, depth_r1, depth_r2 = self.fassade.corners

        # draw rectangle along four points
        cv.line(img, (top_left[0], top_left[1]), (top_right[0], top_right[1]), (0, 255, 0), 3)
        cv.line(img, (top_right[0], top_right[1]), (bot_right[0], bot_right[1]), (0, 255, 0), 3)
        cv.line(img, (bot_right[0], bot_right[1]), (bot_left[0], bot_left[1]), (0, 255, 0), 3)
        cv.line(img, (bot_left[0], bot_left[1]), (top_left[0], top_left[1]), (0, 255, 0), 3)

        # draw depth lines
        cv.line(img, (depth_l1[0], depth_l1[1]), (depth_l2[0], depth_l2[1]), (0, 255, 0), 3)
        cv.line(img, (depth_r1[0], depth_r1[1]), (depth_r2[0], depth_r2[1]), (0, 255, 0), 3)

        # compute perspective transform
        fac_width = 500
        fac_height = 500
        matrix = cv.getPerspectiveTransform(np.float32([top_left, top_right, bot_right, bot_left]),
                                            np.float32([[0, 0], [fac_width - 1, 0], [fac_width - 1, fac_height - 1],
                                                        [0, fac_height - 1]]))
        transformed_img = cv.warpPerspective(self.fassade.src_img.copy(), matrix, (fac_width, fac_height))
        self.img_path = "facade_transformed.jpg"
        cv.imwrite(self.img_path, transformed_img)

        cv.imshow("window", img)
        wait_n_key()

        van_point_hor = line_line_intersection(top_left, top_right, bot_right, bot_left)
        van_point_ver = line_line_intersection(top_left, bot_left, top_right, bot_right)
        van_point_dep = line_line_intersection(depth_l1, depth_l2, depth_r1, depth_r2)

        # expand image
        scaling_factor = 8
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

        top_left = transform_point(top_left)
        top_right = transform_point(top_right)
        bot_left = transform_point(bot_left)
        bot_right = transform_point(bot_right)

        depth_l1 = transform_point(depth_l1)
        depth_r1 = transform_point(depth_r1)
        van_point_hor = transform_point(van_point_hor)
        van_point_ver = transform_point(van_point_ver)
        van_point_dep = transform_point(van_point_dep)

        cv.line(img, top_left, van_point_hor, (50, 50, 255), 3)
        cv.line(img, bot_left, van_point_hor, (50, 50, 255), 3)

        cv.line(img, top_left, van_point_ver, (50, 50, 255), 3)
        cv.line(img, top_right, van_point_ver, (50, 50, 255), 3)

        cv.line(img, depth_l1, van_point_dep, (50, 50, 255), 3)
        cv.line(img, depth_r1, van_point_dep, (50, 50, 255), 3)

        cv.imshow("window", img)
        wait_n_key()
        # connect vanishing points
        cv.line(img, van_point_hor, van_point_ver, (0, 255, 255), 3)
        cv.line(img, van_point_ver, van_point_dep, (0, 255, 255), 3)
        cv.line(img, van_point_dep, van_point_hor, (0, 255, 255), 3)

        cv.imshow("window", img)

        wait_n_key()
        # compute perpendiculars through vanishing points
        perpendicular_h = perpendicular_through_point(van_point_hor, van_point_ver, van_point_dep)
        cv.line(img, van_point_hor, perpendicular_h, (0, 255, 255), 3)
        perpendicular_v = perpendicular_through_point(van_point_ver, van_point_dep, van_point_hor)
        cv.line(img, van_point_ver, perpendicular_v, (0, 255, 255), 3)
        perpendicular_d = perpendicular_through_point(van_point_dep, van_point_hor, van_point_ver)
        cv.line(img, van_point_dep, perpendicular_d, (0, 255, 255), 3)
        cv.imshow("window", img)
        wait_n_key()
        # compute circles?
        ortho_center = line_line_intersection(van_point_hor, perpendicular_h, van_point_ver, perpendicular_v)
        circle_center = van_point_ver[0] + van_point_hor[0] / 2, van_point_ver[1] + van_point_hor[1] / 2
        # radius = geo.Point(*van_point_hor).distance(geo.Point)
        # circle = geo.Circle(circle_center, )

        # wait_n_key()
        cv.destroyAllWindows()
        # let user select facade segments
        FreeCAD.Console.PrintMessage("Creating Gui" + "\n")
        FacadeGui(self, self.img_path)

    def insertIntoCAD(self):
        # place image in 3d model
        place_image(self.doc, self.img_path, self.clicked_face)
        self.doc.recompute()
        return

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


FreeCADGui.addCommand('PlaceFacade', PlaceFacade())

if __name__ == '__main__':
    fassade = PlaceFacade()
    fassade.Activated()
