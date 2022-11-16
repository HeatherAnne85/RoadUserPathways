# -*- coding: utf-8 -*-

"""
file: clustering_main.py
description: import trajectories in Traffic Intelligence format, augment for clustering and cluster
author: Heather Kaths
date: 11-10-2022
"""

from utils import clustering_utils as cu

#Parameters
num_points=20               #number of x-y coordinates in reduced trajectory
traj_min_length = 100       #cut off length for too short trajectories in timesteps
traj_min_number = 15        #minimum number of trajectories to attept to cluster
num_SQL = 5                 #maximum number of trajectory databases (.sqlite) to include in clustering analysis
trim = True
delete = True
road_user_types = [1]       #road user types as defined by traffic intelligence (see below)
define_use = 'use'
cluster_omit = 2            #minimum size of cluster to be included

'''
RoadUserTypes = {"unknown": 0, 
                "undefined": 0,
                "car": 1,
                "pedestrian": 2,
                "motorcycle": 3,
                "bicycle": 4,
                "truck_bus": 5}
'''

#File directory
Homes={'C:/Users/heath/Desktop/trajectory_data/inD-dataset-v1.0/IntersectionA/': ['N','E','S'],
       'C:/Users/heath/Desktop/trajectory_data/inD-dataset-v1.0/IntersectionB/': ['N','E','S','W'],
       'C:/Users/heath/Desktop/trajectory_data/inD-dataset-v1.0/IntersectionC/': ['N','E','S','W'],
       'C:/Users/heath/Desktop/trajectory_data/inD-dataset-v1.0/IntersectionD/': ['N','E','S']}
    

for Home, approaches in Homes.items():
    #Load geometric information
    intersection = cu.Intersection()
    if define_use == 'use':
        intersection.load_geometry(Home+'Geometry')
    else:
        intersection.define_geometry(Home+'Geometry', approaches)
    
    #extract, cluster and plot trajectories
    for road_user_type in road_user_types:
        observations = cu.Clusters(Home, intersection, traj_min_length, num_points, trim, delete, num_SQL, road_user_type, cluster_omit, obs_list=[])
        for approach in ['all'] + approaches:
            observations.cluster_trajectories(approach, plot = True, table = True)
              

    

