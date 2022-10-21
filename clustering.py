# -*- coding: utf-8 -*-

"""
file: clustering.py
description: import trajectories in Traffic Intelligence format, augment for clustering and cluster
author: Heather Kaths
date: 11-10-2022
"""

from sklearn.cluster import AffinityPropagation
from trafficintelligence import storage, cvutils, moving
import sklearn.metrics as m
import numpy as np
from numpy.linalg.linalg import inv    
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import cv2
import os
import shapely.geometry as SG
import pickle

from utils import poly_utils as PU
from utils import traj_utils as TU


def ml(pref, Traj):
    af = AffinityPropagation(preference=pref, random_state=1).fit(Traj)
    labels = af.labels_
    centers = af.cluster_centers_indices_
    n_clusters_ = len(af.cluster_centers_indices_) 
    return af, n_clusters_, labels, centers
    

def plotTrajectories(n_clusters_, labels, Full_traj, image_save_loc, approach):
    import matplotlib.colors as colors
    image_all = cv2.imread(Home+'Geometry/plan.png')
    image_dl = cv2.imread(Home+'Geometry/plan.png')
    jet = plt.get_cmap('jet') 
    cNorm  = colors.Normalize(vmin=0, vmax=n_clusters_)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)
    colors = []

    for idx in range(n_clusters_):
        colorVal = scalarMap.to_rgba(idx)
        colorVal = [C*250 for C in colorVal] 
        colors.append(colorVal)

    for cluster in labels:
        indicies = [i for i, D in enumerate(labels) if D == cluster]
        for i in indicies:
            t = Full_traj[i]
            cvutils.cvPlot(image_all,t,colors[cluster%len(colors)],t.length())  
            if i in centers:
                cvutils.cvPlot(image_dl,t,colors[cluster%len(colors)],t.length(), thickness=2)   
                cv2.arrowedLine(image_dl, t[t.length()-2].asint().astuple(), t[t.length()-1].asint().astuple(), colors[cluster%len(colors)], thickness=2, tipLength=5)
                
    cv2.imwrite(image_save_loc+"desire_lines_{}.jpg".format(approach), image_dl)
    cv2.imwrite(image_save_loc+"all_traj_{}.jpg".format(approach), image_all)
        
    
n=20    #number of x-y coordinates in reduced trajectory
traj_min_length = 100

Home='C:/Users/heath/Desktop/trajectory_data/TUM/Mars/'
homography=inv(np.loadtxt(Home+'Geometry/homography-rectified-2.txt'))
image_save_loc=Home+'clustering/'
mpp = np.loadtxt(Home+'Geometry/mpp.txt')
trim = SG.Polygon(np.load(Home+'Geometry/outerBoundary.npy'))
delete = SG.Polygon(np.load(Home+'Geometry/innerBoundary.npy'))
arm_centers = np.load(Home+'Geometry/armCenters.npy')
center = np.load(Home+'Geometry/intersectionCenter.npy')

try: 
    with open(Home+'Geometry/approach_polys.pickle', 'rb') as handle:
        app_polys = pickle.load(handle)   
except:
    app_polys = PU.polys(center, arm_centers, save=Home+'Geometry/approach_polys.pickle')
    
#PU.plotPoly(cv2.imread(Home+'Geometry/plan.png'),app_polys, mpp, image_save_loc+'polys.jpg')

Traj={'all':[]}
Full_traj={'all':[]}
lengths = {'all':[]}

count = 0
    
for traj_sql in os.listdir(Home+"SQLite"):
    
    SQL = Home+'SQLite/{}'.format(traj_sql)
    
    print('loading SQLite: {}'.format(SQL))
    try:
        objects = storage.loadTrajectoriesFromSqlite(SQL, 'object')
    except:
        print('fail')
        continue
    
    for obj in objects:
        traj_red = obj.positions.getTrajectoryInPolygon(trim)[0]  
        if obj.userType == 4 and PU.checkIn(obj.positions, delete) == False and traj_red.length() > traj_min_length:  
            approach = PU.getApproach(traj_red, app_polys)
            Full_traj['all'].append(traj_red.__mul__(1/mpp))
            if approach not in Full_traj:
                Full_traj[approach] = []
                Traj[approach] = []
                lengths[approach] = []
            Full_traj[approach].append(traj_red.__mul__(1/mpp))
            traj_red.computeCumulativeDistances()
            Length=np.floor(traj_red.getCumulativeDistance(len(traj_red)-1))
            reduced=[]
            for X in range(n):
                minimum=1000
                goal=X*Length/n
                for pos in range(len(obj.positions)-1):
                    dist=traj_red.getCumulativeDistance(pos)
                    app=np.abs(goal-dist)
                    if app<minimum:
                        minimum=app
                    else:
                        reduced.append(traj_red[pos].x)
                        reduced.append(traj_red[pos].y)    
                        break
            lengths[approach].append(traj_red.getTotalDistance())        
            Traj[approach].append(reduced)   
            lengths['all'].append(traj_red.getTotalDistance())        
            Traj['all'].append(reduced)
    #count+=1
    if count == 10:
        break
                   
for approach in Traj.keys():
    Traj_1=np.asarray(Traj[approach])
    
    if Traj_1.shape[0] < 10:
        continue
    
    lengths_1 = np.array(lengths[approach])
    
    X = []
    ss = []
    clusts = []
    
    for x in range(-5000,-100,100):
        af, n_clusters_, labels, centers = ml(lengths_1+x,Traj_1)
        try:
            silhouette_score = m.silhouette_score(Traj_1,labels)
            ss.append(silhouette_score)
            clusts.append( n_clusters_)
            X.append(x)
        except:
            continue
    
    af, n_clusters_, labels, centers = ml(lengths_1+X[np.argmax(ss)],Traj_1)
    
    print('Estimated number of clusters: %d' % n_clusters_)
    
    plotTrajectories(n_clusters_, labels, Full_traj[approach], image_save_loc, approach)



