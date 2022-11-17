# -*- coding: utf-8 -*-

"""
file: run_trajectory_clustering.py
author: Heather Kaths
"""

import argparse

import RoadUserPathways as rup

#Parameters
def create_args():
    parser = argparse.ArgumentParser(prog = 'road user pathways',
                                     description = 'trajectory clustering to find common pathway types')

    parser.add_argument('--dataset_dir', default="C:/Users/heath/Desktop/trajectory_data/TUM/Karl",
                        help="Path to directory that contains the trajectory SQLite files.", type=str)
    parser.add_argument('--approaches', default=['N','E','S','W'],
                        help="List with labels for the arms of the intersection (eg. ['N','E','S','W']", type=list)  
    parser.add_argument('--num_points', default=20,
                        help="The number of points in each feature vector.", type=int)
    parser.add_argument('--traj_min_length', default=100,
                        help="The minimum length for trajectories to be included in clustering in timesteps.", type=int)    
    parser.add_argument('--traj_min_number', default=15,
                        help="The minimum number of trajectories required to attempt clustering.", type=int)  
    parser.add_argument('--num_SQL', default=5,
                        help="The maximum number of trajectory SQLite files to include in clustering analysis.", type=int)     
    parser.add_argument('--trim', default=False,
                        help="Use polygon to trim trajectories (recommended if starting and ending position points vary in space).", type=bool)    
    parser.add_argument('--delete', default=False,
                        help="Use polygon to delete trajectories starting or ending in polygon.", type=bool)  
    parser.add_argument('--road_user_types', default=[4],
                        help="List with road user types to analyse (eg [1,4]), from types = {car: 1, pedestrian: 2, motorcycle: 3, bicycle: 4, truck_bus: 5", type=list)  
    parser.add_argument('--define_use', default='use',
                        help="Set to 'use' if geometry already defined, otherwise set to 'define'", type=str)      
    parser.add_argument('--cluster_omit', default=2,
                        help="Minimum number of trajectories in a cluster to include in output", type=int)     
      

    return vars(parser.parse_args())


def main():
    config = create_args()
    
    dataset_dir = config["dataset_dir"] + "/"
    approaches = config["approaches"]
    num_points = config["num_points"]
    traj_min_length = config["traj_min_length"]
    traj_min_number = config["traj_min_number"]
    num_SQL = config["num_SQL"]
    trim = config["trim"]
    delete = config["delete"]
    road_user_types = config["road_user_types"]
    define_use = config["define_use"]
    cluster_omit = config["cluster_omit"]
    
    #Geometry
    intersection = rup.Intersection()
    if define_use == 'use':
        intersection.load_geometry(dataset_dir+'Geometry')
    else:
        intersection.define_geometry(dataset_dir+'Geometry', approaches)
    
    #extract, cluster and plot trajectories
    for road_user_type in road_user_types:
        observations = rup.Clusters(dataset_dir, intersection, traj_min_length, num_points, trim, delete, num_SQL, road_user_type, cluster_omit, obs_list=[])
        for approach in ['all'] + approaches:
            observations.cluster_trajectories(approach, plot = True, table = True)
              
if __name__ == '__main__':
    main()
    

