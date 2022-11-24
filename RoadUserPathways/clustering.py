# -*- coding: utf-8 -*-


import cv2
from trafficintelligence import moving, cvutils, storage
from sklearn.cluster import AffinityPropagation
import sklearn.metrics as m
import shapely.geometry as SG
from shapely import affinity
import pickle
import os
import numpy as np
from itertools import groupby
import matplotlib.pyplot as plt
import matplotlib.cm as cmx


class Observation(object):
    '''
    Class to define a trajectory observation
    '''
    def __init__(self, num, traffic_intelligence_id, trajectory, intersection, trajectory_plot = None, f_star = None, approach = None, in_poly = None, length = None, num_points = 20):
        self.num = num
        self.ID = traffic_intelligence_id
        self.trajectory = trajectory
        self.intersection = intersection
        self.trajectory_plot = trajectory_plot
        self.f_star = f_star
        self.num_points = num_points
        self.approach = approach
        self.in_poly = in_poly
        self.length = length
        
        self.get_approach()
        self.get_f_star()
        self.get_in_polygon()
        self.get_length()
                
    
    def get_approach(self):
        '''Function to find the directional approach based on the approach polygons'''
        P = self.trajectory[0]
        for app, poly in self.intersection.approach_polys.items():
            if poly.contains(SG.Point(P.x,P.y)):
                self.approach = app
                continue
 
    
    def get_in_polygon(self):
        '''return true if a trajectory starts or ends within a Shapely polygon'''
        P0 = self.trajectory[0]
        PL = self.trajectory[-1]
        if self.intersection.inner_poly.contains(SG.Point(P0.x,P0.y)) == False and self.intersection.inner_poly.contains(SG.Point(PL.x,PL.y)) == False:
            self.in_poly = False
        else:
            self.in_poly = True
            
    def get_length(self):
        '''get total distance travelled by the road user'''
        self.length = self.trajectory.getTotalDistance()

    
    def get_f_star(self):
        '''locate position coordinates at given distance cut-off points'''
        self.trajectory.computeCumulativeDistances()
        Length=np.floor(self.trajectory.getCumulativeDistance(len(self.trajectory)-1))
        goal = np.array([X*Length/self.num_points for X in range(self.num_points)])
        distances = np.array([self.trajectory.getCumulativeDistance(pos) for pos in range(len(self.trajectory)-1)])
        indexes = abs(goal[:, None] - distances).argmin(axis=1)
        out = list(enumerate(indexes))
        reduced = []
        for pair in out:
            reduced.extend([self.trajectory[int(pair[1])].x, self.trajectory[int(pair[1])].y])
        self.f_star = reduced
    


class Clusters(object):
    '''
    Class to store and cluster observations and output the results
    '''
    
    def __init__(self, filedirectory, intersection, traj_min_length, num_points, trim = False, delete = False, num_SQL = 1000, road_user_type = 4, cluster_omit = 0, obs_list = [], af = None):
        self.filedirectory = filedirectory
        self.intersection = intersection
        self.traj_min_length = traj_min_length
        self.num_points = num_points
        self.trim = trim
        self.delete = delete
        self.num_SQL = num_SQL
        self.road_user_type = road_user_type
        self.cluster_omit = cluster_omit
        self.obs_list =  obs_list
        self.af = af
        
        self.load_observations()
        
    
    def load_observations(self):   
        '''function to load observations from an SQLite database and append to a list of observations'''
        c = 0 
        for traj_sql in os.listdir(self.filedirectory+'SQLite/'):
            if c < self.num_SQL:
                SQL = self.filedirectory+'SQLite/{}'.format(traj_sql)
                print('loading SQLite: {}'.format(SQL))
                try:
                    objects = storage.loadTrajectoriesFromSqlite(SQL, 'object')
                except:
                    print('fail')
                    continue
                for obj in objects:
                    if obj.userType == self.road_user_type and len(obj.positions) > self.traj_min_length:
                        if self.trim == True:
                            traj_red = obj.positions.getTrajectoryInPolygon(self.intersection.outer_poly)[0]  
                        else:
                            traj_red = obj.positions
                        if traj_red.length() > self.traj_min_length:
                            obs = Observation(len(self.obs_list), obj.num, traj_red, self.intersection, trajectory_plot = traj_red.__mul__(1/self.intersection.mpp), num_points = self.num_points)
                            if self.delete == False or obs.in_poly == False:
                                self.obs_list.append(obs)    
            c+=1
                            
                            
    def find_optimal_preference(self, ss, clusters):
        '''function to find the preference value with the highest silhouette score and lowest number of clusters'''
        ss = np.asarray(ss)
        highest_ss = np.flatnonzero(ss == np.max(ss))                       #indices of highest silhouette scores
        _cluster = np.take(clusters, highest_ss)                            #number of clusters for highest silhouette score
        lowest_clusters = np.flatnonzero(clusters == np.min(_cluster))      #indices of lowest clusters 
        overlaps = [i for i in highest_ss if i in lowest_clusters]
        return overlaps[0]
    

    def cluster_trajectories(self, approach = 'all', plot = False, table = False):
        '''function to create A_star matrix and cluster using sklearn (Affinity Propagation)'''
        A_star_list, Traj_plot = [], []
        
        for obs in self.obs_list:
            if (approach != 'all' and obs.approach != approach) or obs.f_star == []:
                continue                    
            A_star_list.append(obs.f_star)
            Traj_plot.append(obs.trajectory_plot)
            
        if len(A_star_list) < 10:
            return
        
        A_star = np.asarray(A_star_list)
        
        X, ss, clusts = [], [], []
        for x in range(-5000,-100,100):
            af = AffinityPropagation(preference=x, random_state=1).fit(A_star)
            try:
                ss.append(m.silhouette_score(A_star, af.labels_))
                clusts.append(len(af.cluster_centers_indices_))
                X.append(x)
            except:
                continue
            
        if len(X) == 0:
            print('clustering failed - possibly not enough trajectories')
            return 
        
        opt = self.find_optimal_preference(ss, clusts)
        print(np.argmax(ss), opt, X[opt])
        
        self.af = AffinityPropagation(preference=X[opt], random_state=1).fit(A_star)
       
        silhouette_score = m.silhouette_score(A_star, af.labels_)
        
        if plot == True:
            self.plot_trajectories(Traj_plot, approach)
            
        if table == True:
            self.output_table(approach, silhouette_score)
      
     
    def output_table(self, approach, silhouette_score):
        '''creates a text file with information about the clustered pathways'''
        Table = []
        for entry in set(self.af.labels_):
            if np.count_nonzero(self.af.labels_ == entry) < self.cluster_omit:
                continue
            Table.append([entry, np.count_nonzero(self.af.labels_ == entry), round(np.count_nonzero(self.af.labels_ == entry)*100/len(self.af.labels_),1)])
        with open(self.filedirectory+f'output/{self.road_user_type}_{approach}.txt', 'w') as fp:
            fp.write(f'Observed road users ({self.road_user_type}): {len(self.af.labels_)}\n')
            fp.write(f'Number of total clusters: {len(set(self.af.labels_))}\n')
            fp.write(f'Number of clusters greater than {self.cluster_omit}: {len(Table)-1}\n')
            fp.write(f'Silhouette score: {silhouette_score}\n')
            fp.write('Pathway ID, # of trajectories,  % of trajectories\n')
            for item in Table:
                for pos in item:
                    fp.write(f"{pos},")  
                fp.write("\n")  
                            
    
 
    def plot_trajectories(self, Full_traj, approach):
        '''function to plot all trajectories by cluster and plot the cluster exemplars with additional information'''
        import matplotlib.colors as colors
        
        image_all = cv2.imread(self.filedirectory+'Geometry/plan.png')
        image_dl = cv2.imread(self.filedirectory+'Geometry/plan.png')
        
        jet = plt.get_cmap('jet') 
        cNorm  = colors.Normalize(vmin=0, vmax=len(self.af.cluster_centers_indices_))
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)
        
        colors = []
        for idx in range(len(self.af.cluster_centers_indices_)):
            colorVal = scalarMap.to_rgba(idx)
            colorVal = [C*250 for C in colorVal] 
            colors.append(colorVal)
        
        frequencies = [len(list(group)) for key, group in groupby(sorted(self.af.labels_))]
        proportions = [round(clust*100/np.sum(frequencies),1) for clust in frequencies]
        
        for cluster in set(self.af.labels_):
            if np.count_nonzero(self.af.labels_ == cluster) < self.cluster_omit:
                continue
            indicies = [i for i, D in enumerate(self.af.labels_) if D == cluster]
            for i in indicies:
                t = Full_traj[i]
                cvutils.cvPlot(image_all,t,colors[cluster%len(colors)],t.length())  
                if i in self.af.cluster_centers_indices_:
                    cvutils.cvPlot(image_dl,t,colors[cluster%len(colors)],t.length(), thickness=2)   
                    cv2.arrowedLine(image_dl, t[t.length()-2].asint().astuple(), t[t.length()-1].asint().astuple(), colors[cluster%len(colors)], thickness=2, tipLength=5)
                    cv2.putText(image_dl,f'ID {cluster}/{frequencies[cluster]} obs/{proportions[cluster]}%',t[t.length()-np.random.randint(1,20)].asint().astuple(),cv2.FONT_HERSHEY_PLAIN,1,colors[cluster%len(colors)],thickness=2)
                    
        cv2.imwrite(self.filedirectory+f'output/{self.road_user_type}_{approach}_desire_lines.jpg', image_dl)
        cv2.imwrite(self.filedirectory+f'output/{self.road_user_type}_{approach}_all.jpg', image_all)                


    

class Intersection(object):
    '''
    Class to define the geometry of the infrastructure
    '''
    def __init__(self, filedirectory = None, inner_poly = None, outer_poly = None, center = None, arm_centers = None, mpp = None, approaches = None, approach_polys = None):
        self.filedirectory = filedirectory
        self.inner_poly = inner_poly
        self.outer_poly = outer_poly
        self.center = center
        self.arm_centers = arm_centers
        self.mpp = mpp                              #mpp is a meters per pixel value for the world image
        self.approaches = approaches
        self.approach_polys = approach_polys
        return
        
    def load_geometry(self, filedirectory):
        '''load existing geometrical information from given directory'''
        self.filedirectory = filedirectory
        self.inner_poly = SG.Polygon(np.load(filedirectory+'/innerBoundary.npy'))
        self.outer_poly = SG.Polygon(np.load(filedirectory+'/outerBoundary.npy'))
        self.center = np.load(filedirectory+'/intersectionCenter.npy')
        self.arm_centers = np.load(filedirectory+'/armCenters.npy')
        self.mpp = np.loadtxt(filedirectory+'/mpp.txt') 
        try:
            with open(filedirectory+'/approach_polys.pickle', 'rb') as handle:
                self.approach_polys = pickle.load(handle)
                self.plotPoly()           
        except:
            self.approach_polys = self.polys(directions = self.approaches, save = filedirectory+'/approach_polys.pickle') 
            self.plotPoly()
        return
    
    
    def point_input(self, image, info):
        '''function to get coordinate points from user clicking on image'''
        print(info[0])
        plt.figure(figsize=(5,5))
        plt.imshow(image)
        point = np.array(plt.ginput(info[1], timeout=3000))  
        plt.close('all')
        return point
        
    
    def define_geometry(self, filedirectory, approaches):
        '''write function to create polys needed for trimming and deleting'''
        self.filedirectory = filedirectory
        self.mpp = np.loadtxt(filedirectory+'/mpp.txt') 
        self.approaches = approaches
        image = plt.imread(filedirectory + '/plan.png')
        geometry = {'center': ['Click on the center of the intersection', 1, '/intersectionCenter.npy'],
                           'arm_centers': [f'Select a midpoint on approach arms {approaches} (starting with {approaches[0]})', len(approaches), '/armCenters.npy'],
                           'inner_poly':['Select four points of a polygon for deleting trajectories (inner_poly)', 4, '/innerBoundary.npy'],
                           'outer_poly':['Select four points of a polygon for trimming trajectories (outer_poly)', 4, '/outerBoundary.npy']}
        for key, info in geometry.items():
            points = self.point_input(image, info)*self.mpp
            np.save(filedirectory + info[2], points) 
        self.load_geometry(self.filedirectory)
        return


    def P_ave(self,p1,p2):
        '''return the midpoint of a line / average of two points'''
        return SG.Point((p1[0]+p2[0])/2,(p1[1]+p2[1])/2)


    def plotPoly(self):
        '''plot polygons on world image and save image'''
        image = cv2.imread(self.filedirectory+'/plan.png')
        out_file = self.filedirectory+'/approach_polys.jpg'
        for app, poly in self.approach_polys.items():
            point_list = [moving.Point(point[0]/self.mpp,point[1]/self.mpp) for point in poly.exterior.coords]
            t = moving.Trajectory.fromPointList(point_list)
            cvutils.cvPlot(image,t,(255, 0, 0),thickness=2)   
            cv2.imwrite(out_file, image)


    def polys(self, directions = ['N','E','S','W'], save = False):
        '''create polygons from points in the middle of the approach arms and the center of the intersection.
        directions is input if it is not a four-approach intersection
        save is a file pathways'''
        C = self.center[0]
        arm_centers_extend = []
        for row in self.arm_centers:
            arm_centers_extend.append(row)   
        approaches = {}
        for c,arm in enumerate(arm_centers_extend):
            L1 = SG.LineString([C,arm])
            L2 = affinity.rotate(L1,45,origin=SG.Point(C))
            L3 = affinity.rotate(L1,-45,origin=SG.Point(C))
            approach_poly = SG.MultiPoint(list(L2.coords) + list(L3.coords)+ list(L1.coords))
            approaches[directions[c]] = approach_poly.convex_hull
        if save !=False:
            with open(save, 'wb') as handle:
                pickle.dump(approaches, handle)     
        return approaches

        


    


