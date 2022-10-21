# -*- coding: utf-8 -*-

"""
file: utils.py
description: working with trajectories
author: Heather Kaths
date: 21-10-2022
"""

import shapely.geometry as SG

def checkIn(traj,poly):
    #return true if a trajectory starts or ends within a shapely polygone
    P0=obj.positions[0]
    PL=obj.positions[-1]
    if delete.contains(SG.Point(P0.x,P0.y)) == False and delete.contains(SG.Point(PL.x,PL.y)) == False:
        return False
    else:
        return True
      
def P_ave(p1,p2):
    #return the midpoint of a line / average of two points
    return SG.Point((p1[0]+p2[0])/2,(p1[1]+p2[1])/2)
