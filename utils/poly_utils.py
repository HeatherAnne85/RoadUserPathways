# -*- coding: utf-8 -*-

#functions for creating and saving polygons

import cv2
from trafficintelligence import moving, cvutils
import shapely.geometry as SG
import pickle


def P_ave(p1,p2):
    #return the midpoint of a line / average of two points
    return SG.Point((p1[0]+p2[0])/2,(p1[1]+p2[1])/2)


def plotPoly(image, app_polys, mpp, out_file):
    #plot polygons on world image and save image
    #mpp is a meters per pixel value for the world image
    for app, poly in app_polys.items():
        point_list = [moving.Point(point[0]/mpp,point[1]/mpp) for point in poly.exterior.coords]
        t = moving.Trajectory.fromPointList(point_list)
        cvutils.cvPlot(image,t,(255, 0, 0),thickness=2)   
        cv2.imwrite(out_file, image)
        
        
def polys(center, arm_centers, directions = ['N','E','S','W'], save = False):
    #create polygons from points in the middle of the approach arms and the center of the intersection.
    #directions is input if it is not a four-approach intersection
    #save is a file pathways
    l = len(arm_centers)
    points = {}
    approaches = {}
    for c,row in enumerate(arm_centers):
        points[directions[c]]=SG.Point(row)
        points[directions[c]+directions[(c+1)%l]] = P_ave(row,arm_centers[(c+1)%l])
    for c,row in enumerate(arm_centers):
        vals = [value for key, value in points.items() if directions[c] in key]
        vals.append(SG.Point(center[0][0],center[0][1]))
        approaches[directions[c]]=SG.MultiPoint(vals).convex_hull
    if save !=False:
        with open(save, 'wb') as handle:
            pickle.dump(approaches, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return approaches


def checkIn(traj,poly):
    #return true if a trajectory starts or ends within a shapely polygone
    P0=traj[0]
    PL=traj[-1]
    if poly.contains(SG.Point(P0.x,P0.y)) == False and poly.contains(SG.Point(PL.x,PL.y)) == False:
        return False
    else:
        return True
    
def getApproach(traj_red, app_polys):
    P=traj_red[0]
    for app, poly in app_polys.items():
        if poly.contains(SG.Point(P.x,P.y)):
            return app
    return "fail"
