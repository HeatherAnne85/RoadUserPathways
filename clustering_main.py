# -*- coding: utf-8 -*-

"""
file: clustering.py
description: import trajectories in Traffic Intelligence format, augment for clustering and cluster
author: Heather Kaths
date: 11-10-2022
"""

from sklearn.cluster import AffinityPropagation
from trafficintelligence import storage
import sklearn.metrics as m
import numpy as np
import os
import shapely.geometry as SG
import pickle

from utils import poly_utils as PU


def ml(pref, Traj):
    af = AffinityPropagation(preference=pref, random_state=1).fit(Traj)
    labels = af.labels_
    centers = af.cluster_centers_indices_
    n_clusters_ = len(af.cluster_centers_indices_) 
    return af, n_clusters_, labels, centers
            
    
n=20    #number of x-y coordinates in reduced trajectory
traj_min_length = 100

Home='C:/Users/heath/Desktop/trajectory_data/TUM/Mars/'
Geometry = Home+'Geometry/'
Clustering = Home+'clustering/'

mpp = np.loadtxt(Geometry+'mpp.txt')
trim = SG.Polygon(np.load(Geometry+'outerBoundary.npy'))
delete = SG.Polygon(np.load(Geometry+'innerBoundary.npy'))


try: 
    with open(Home+'Geometry/approach_polys.pickle', 'rb') as handle:
        app_polys = pickle.load(handle)   
except:
    arm_centers = np.load(Geometry+'armCenters.npy')
    center = np.load(Geometry+'intersectionCenter.npy')
    app_polys = PU.polys(center, arm_centers, save = Geometry+'approach_polys.pickle')
    
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
            
            if approach not in Full_traj:
                Full_traj[approach] = []
                Traj[approach] = []
                lengths[approach] = []
            
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
            Full_traj[approach].append(traj_red.__mul__(1/mpp))
            lengths['all'].append(traj_red.getTotalDistance())        
            Traj['all'].append(reduced)
            Full_traj['all'].append(traj_red.__mul__(1/mpp))
    
    count+=1
    if count == 1:
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
    
    PU.plotTrajectories(Home+'Geometry/plan.png', n_clusters_, labels, Full_traj[approach], image_save_loc, approach, centers)



