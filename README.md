# RoadUserPathways
This project provides python code for clustering trajectory data extracted from videos. The results can be used to examine the unexpected tactics employed by cyclists, pedestrians, e-kick scooter users, scooter drivers and other users of mini and micro vehicles to cross inter-sections. Akin to desire lines, the output from this tool can help urban planners and traffic engi-neers create road infrastructure that serves the needs of users of sustainable modes of transport.

The following images display the clustered trajectories from cyclists crossing an intersection in Munich, Germany. On the left side, all clustered trajectories are shown (each color represents a cluster/type of pathways). On the right side, the centers of each cluster which represent the average shape of the pathway type with the number and percentage of cyclists observed using this type of pathway.

<p align="center">
  <img src="Example_plot_clustered_trajectories.jpg"  width=49% height=49%>
  <img src="Example_plot_pathways.jpg"  width=49% height=49%>
</p>

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
- **Trajectory data** stored in an SQLite database and defined in the *Traffic Intelligence* project. Trajectories must describe the complete crossing maneouvre of the road user and cannot be disjointed in the middle of the video frame. Trajectories are described in a local coordinate system in which the coordinate point (0,0) is the upper left-hand corner of the video frame. Position coordinates are given in UTM meters and the velocity in m/frame. RoadUserPathways was developed using trajectories extracted from video data with 25 position coordinates per second (one per video frame). Trajectories with a lower frequency of observations will work as long as the shape of the crossing manoeuvre is captured.

The road user types defined by *Traffic Intelligence* are used:
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

# Trajectory pre-processing
Trajectory data can be pre-processed to increase the quality of the clustering results. This is particularly necessary if the trajectories are incomplete, meaning that they do not contain the entire crossing maneuver of the road user, and if the start/end position coordinates of the trajectories differ in space. 
These functionalities work as follows: 
1.	Incomplete trajectories can be removed using a polygon outlining the most important part of the intersection (or other part of the road infrastructure). This polygon is shown in blue below. To input this polygon on an areal image, the analyst should set the `--define_use` parameter to `define`. To use this polygon to filter out incomplete trajectories, the analyst should set the `--delete` parameter to `True`. 
2.	Trajectories can be trimmed to ensure comparability using a polygon that defines the area of interest or the starting/end points of the shortest trajectories. An example is shown in green below. To input this polygon on an areal image, the analyst should set the '--define_use' parameter to `define`. To use this polygon to trim trajectories (remove position coordinates at the start/end of the trajectory that fall outside the polygon), the analyst should set the `--trim` parameter to `True`.

<p align="center">
  <img src="Example_polygons_trimming_filtering.jpg"  width=60% height=60%>
</p>

In the figure, the orange dashed trajectory will be filtered from the dataset because it starts within the blue polygon. The dashed sections of the red trajectory will be removed to ensure comparability.

The analyst also has the option to cluster trajectories from road users approaching from each arm of the intersection separately. To do this, the center point of the intersection and a point along each approach arm of the intersection can be selected from an areal image by setting the `--define_use` parameter to `define`. The approaches of interest can be input using the `--approaches` parameter. For example, if a T-intersection with no north approach is to be analyzed, `--approaches` should be set to `[‘E’,’S’,’W’]`. 

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
