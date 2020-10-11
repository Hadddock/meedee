import pygame.font
'''
Created on Oct 11, 2020

@author: justi
'''


def update_fps(FramePerSec):
    """Return current FPS"""
    FPS = str(int(FramePerSec.get_fps()))
    font = pygame.font.SysFont("freesansbold.ttf", 18)
    FPS_DISPLAY = font.render(FPS, 1, (0, 0, 0))
    return FPS_DISPLAY


def segments_intersect(A, B, C, D):
    """
    Return whether or not the segment formed by A and B
    intersects the segment formed by C and D
    
    """

    def ccw(A, B, C):
        return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x) 

    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


def line_intersection(line1, line2):
    """Return the intersection point of line1 and line2"""
    determinant_one = determinant(line1[0], line1[1])
    determinant_two = determinant((line1[0][0], 1), (line1[1][0], 1))
    determinant_three = determinant (line2[0], line2[1])
    determinant_four = determinant((line2[0][0], 1), (line2[1][0], 1))
    determinant_five = determinant((line1[0][1], 1), (line1[1][1], 1))
    determinant_six = determinant((line2[0][1], 1), (line2[1][1], 1))
    
    denominator = determinant((determinant_two, determinant_five), (determinant_four, determinant_six))
    xNumerator = determinant((determinant_one, determinant_two), (determinant_three, determinant_four))
    yNumerator = determinant((determinant_one, determinant_five), (determinant_three, determinant_six))
    
    return(xNumerator / denominator, yNumerator / denominator)


def determinant(pointA, pointB):
    """Return the determinant point of pointA and pointB"""
    return pointA[0] * pointB[1] - pointA[1] * pointB[0]    