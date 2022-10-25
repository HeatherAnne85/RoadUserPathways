# -*- coding: utf-8 -*-

"""
file: clustering_main.py
description: import trajectories in Traffic Intelligence format, augment for clustering and cluster
author: Heather Kaths
date: 11-10-2022
"""

from utils import clustering_utils as cu

#Parameters
num_points=20                        #number of x-y coordinates in reduced trajectory
traj_min_length = 100       #cut off length for too short trajectories in timesteps
traj_min_number = 10
num_SQL = 20


#File directory
Home='C:/Users/heath/Desktop/trajectory_data/TUM/Karl/'


#Load geometric information
intersection = cu.Intersection()
intersection.load_geometry(Home+'Geometry')

#extract, cluster and plot trajectories
observations = cu.Observations_set(Home, intersection, traj_min_length, num_points, num_SQL)
for approach in ['all', 'N', 'E', 'S', 'W']:
    observations.cluster_trajectories(approach, plot = True)
              

    

