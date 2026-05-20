import cv2
import numpy as np

def point_in_polygon(pt, polygon):
    """
    Check if a point pt (x, y) is inside the polygon.
    """
    return cv2.pointPolygonTest(np.array(polygon, np.int32), pt, False) >= 0


def get_side_of_line(p, line):
    """
    Determine which side of a line point p is on.
    """
    x1, y1, x2, y2 = line
    return (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1)


def shrink_bbox(x1, y1, x2, y2, factor):
    """
    Shrink the bounding box coordinates by a given factor.
    """
    w = x2 - x1
    h = y2 - y1
    dw = int(w * factor)
    dh = int(h * factor)

    return int(x1 + dw), int(y1 + dh), int(x2 - dw), int(y2 - dh)
