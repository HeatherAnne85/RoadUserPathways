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
| `--approaches`                 | `exid` | Name of the dataset (ind, round, exid, unid). Needed to apply dataset specific visualization adjustments. |
| `--num_points`               | `26`            | Name of the recording given by a number with a leading zero. | 
| `--traj_min_length`          | `4`               | During playback, only consider every nth frame. | 
| `--traj_min_number`   | `False`           | Do not show the track window when clicking on a track. Only surrounding vehicle colors are displayed. | 
| `--num_SQ`       | `False`           | Plot the rotated bounding boxes of all vehicles.  Please note, that for vulnerable road users, no bounding box is given. |  
| `--trim`        | `False`           | Indicate the orientation of all vehicles by triangles. | 
| `--delete`         | `False`           | Show the trajectory up to the current frame for every track. | 
| `--road_user_types`  | `False`           | Show the remaining trajectory for every track. | 
| `--define_use`       | `False`           | Annotate every track by its id. | 
| `--cluster_omit`          | `False`           | Annotate every track by its class label. | 
