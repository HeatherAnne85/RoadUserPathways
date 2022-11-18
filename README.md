# RoadUserPathways
Python code for clustering trajectory data extracted from video data. The clustered trajectories can be used to examine the tactical behaviour of road users crossing intersections. For example, the *desire lines* of pedestrians and cyclists, or the turning rates for all types of road users can be analysed. 

## Dependencies
- OpenCV
- trafficintelligence (from https://bitbucket.org/Nicolas/trafficintelligence/)
- sklearn
- shapely
- numpy
- matplotlib
- os
- pickle

## Data
RoadUserPathways takes trajectory data and geometric information about road infrastructure to cluster trajectories into commonly used pathways. The necessary input data is:
- **Trajectory data** stored in an SQLite database and defined in the *Traffic Intelligence* project. Trajectories must describe the complete crossing maneouvre of the road user and cannot be disjointed in the middle of the video frame. Trajectories are described in a local coordinate system in which the coordinate point (0,0) is the upper left-hand corner of the video frame. Position coordinates are given in UTM meters and the velocity in m/frame. The road user types defined by *Traffic Intelligence* are used:
```
RoadUserTypes = {"unknown": 0, 
                "undefined": 0,
                "car": 1,
                "pedestrian": 2,
                "motorcycle": 3,
                "bicycle": 4,
                "truck_bus": 5}
```
- A **scale factor** relating the image pixels to UTM meters (meters/pixel).
- An **orthoimage** of the intersection.

## Parameters
| Command-line Options      | Default value   | Description |
| ---                       | ---             | --- |
| `--dataset_dir`             | `"../data/"`      | Path to directory that contains the trajectory SQLite files and geometric information. |
| `--approaches`                 | `['N','E','S','W']` | List with labels for the arms of the intersection (eg. ['N','E','S','W']). |
| `--num_points`               | `20`            | The number of coordinate points taken from each trajectoriy to form the feature vector. | 
| `--traj_min_length`          | `100`               | The minimum length for trajectories to be included in clustering (in timesteps). | 
| `--num_SQ`       | `5`           | The maximum number of trajectory SQLite files from the dataset directory to include in clustering analysis. |  
| `--trim`        | `False`           | Use polygon to trim trajectories (recommended if starting and ending position points vary in space). | 
| `--delete`         | `False`           | Use polygon to delete trajectories starting or ending in polygon. | 
| `--road_user_types`  | `False`           | List with road user types to cluster (eg [1,4]) as defined by *Traffic Intelligence*  | 
| `--define_use`       | `False`           | Set to 'use' if geometry already defined, otherwise set to 'define'. | 
| `--cluster_omit`          | `2`           | Minimum number of trajectories in a cluster to include in output | 
