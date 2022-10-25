# -*- coding: utf-8 -*-


import cv2
from trafficintelligence import moving, cvutils, storage
from sklearn.cluster import AffinityPropagation
import sklearn.metrics as m
import shapely.geometry as SG
import pickle
import os
import numpy as np
from itertools import groupby


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
        P = self.trajectory[0]
        for app, poly in self.intersection.approach_polys.items():
            if poly.contains(SG.Point(P.x,P.y)):
                self.approach = app
    
    
    def get_in_polygon(self):
        #return true if a trajectory starts or ends within a shapely polygon
        P0 = self.trajectory[0]
        PL = self.trajectory[-1]
        if self.intersection.inner_poly.contains(SG.Point(P0.x,P0.y)) == False and self.intersection.inner_poly.contains(SG.Point(PL.x,PL.y)) == False:
            self.in_poly = False
        else:
            self.in_poly = True
            
    def get_length(self):
        self.length = self.trajectory.getTotalDistance()

    
    def get_f_star(self):
        self.trajectory.computeCumulativeDistances()
        Length=np.floor(self.trajectory.getCumulativeDistance(len(self.trajectory)-1))
        reduced=[]
        for X in range(self.num_points):
            minimum=1000
            goal=X*Length/self.num_points
            for pos in range(len(self.trajectory)-1):
                dist=self.trajectory.getCumulativeDistance(pos)
                app=np.abs(goal-dist)
                if app<minimum:
                    minimum=app
                else:
                    reduced.extend([self.trajectory[pos-1].x, self.trajectory[pos-1].y])
                    break
        self.f_star = reduced
    


class Clusters(object):
    '''
    Class to store observations
    '''
    def __init__(self, filedirectory, intersection, traj_min_length, num_points, num_SQL = 1000, obs_list = [], A_star = None, af = None):
        self.filedirectory = filedirectory
        self.intersection = intersection
        self.traj_min_length = traj_min_length
        self.num_points = num_points
        self.num_SQL = num_SQL
        self.obs_list =  obs_list
        self.A_star = A_star 
        self.load_observations()
        self.af = af
        
    
    def load_observations(self):   
        
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
                    
                    if obj.userType == 4 and len(obj.positions) > self.traj_min_length:
                        
                        traj_red = obj.positions.getTrajectoryInPolygon(self.intersection.outer_poly)[0]  
                        
                        if len(traj_red) > self.traj_min_length:
                            obs = Observation(len(self.obs_list), obj.num, traj_red, self.intersection, trajectory_plot = traj_red.__mul__(1/self.intersection.mpp), num_points = self.num_points)
                        
                            if obs.in_poly == False:
                                self.obs_list.append(obs)    
            c+=1
                            
                            
   

    def cluster_trajectories(self, approach = 'all', plot = False, table = False):
        '''
        
        '''
        Traj, lengths, Traj_plot = [], [], []
        
        for obs in self.obs_list:
            if approach != 'all' and obs.approach != approach:
                continue                    
            Traj.append(obs.f_star)
            lengths.append(obs.length)
            Traj_plot.append(obs.trajectory_plot)
            
        Traj_1=np.asarray(Traj)   
        lengths_1 = np.array(lengths)
        
        X, ss, clusts = [], [], []
        
        for x in range(-5000,-100,100):
            
            af = AffinityPropagation(preference=lengths_1+x, random_state=1).fit(Traj_1)

            try:
                silhouette_score = m.silhouette_score(Traj_1, af.labels_)
                ss.append(silhouette_score)
                clusts.append(len(af.cluster_centers_indices_))
                X.append(x)
            except:
                continue
            
        if len(X) == 0:
            print('clustering failed - possibly not enough trajectories')
            return 
        
        self.af = AffinityPropagation(preference=lengths_1+X[np.argmax(ss)], random_state=1).fit(Traj_1)
       
        silhouette_score = m.silhouette_score(Traj_1, af.labels_)
        
        if plot == True:
            self.plot_trajectories(Traj_plot, approach)
            
        if table == True:
            x = x
      
                            
 
    def plot_trajectories(self, Full_traj, approach):
        import matplotlib.colors as colors
        import matplotlib.pyplot as plt
        import matplotlib.cm as cmx
        
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
            indicies = [i for i, D in enumerate(self.af.labels_) if D == cluster]
            for i in indicies:
                t = Full_traj[i]
                cvutils.cvPlot(image_all,t,colors[cluster%len(colors)],t.length())  
                if i in self.af.cluster_centers_indices_:
                    cvutils.cvPlot(image_dl,t,colors[cluster%len(colors)],t.length(), thickness=2)   
                    cv2.arrowedLine(image_dl, t[t.length()-2].asint().astuple(), t[t.length()-1].asint().astuple(), colors[cluster%len(colors)], thickness=2, tipLength=5)
                    cv2.putText(image_dl,str(frequencies[cluster])+'/'+str(proportions[cluster])+'%',t[t.length()-1].asint().astuple(),cv2.FONT_HERSHEY_PLAIN,1.3,colors[cluster%len(colors)],thickness=2)
                    
        cv2.imwrite(self.filedirectory+'clustering/desire_lines_TEST{}.jpg'.format(approach), image_dl)
        cv2.imwrite(self.filedirectory+'clustering/all_traj__TEST{}.jpg'.format(approach), image_all)                


    

class Intersection(object):
    '''
    Class to define the geometry of the infrastructure
    '''
    def __init__(self, inner_poly = None, outer_poly = None, center = None, arm_centers = None, mpp = None, approach_polys = None):
        self.inner_poly = inner_poly
        self.outer_poly = outer_poly
        self.center = center
        self.arm_centers = arm_centers
        self.mpp = mpp                              #mpp is a meters per pixel value for the world image
        self.approach_polys = approach_polys
        return
        
    def load_geometry(self, filedirectory):
        '''load existing geometrical information from given directory'''
        self.inner_poly = SG.Polygon(np.load(filedirectory+'/innerBoundary.npy'))
        self.outer_poly = SG.Polygon(np.load(filedirectory+'/outerBoundary.npy'))
        self.center = np.load(filedirectory+'/intersectionCenter.npy')
        self.arm_centers = np.load(filedirectory+'/armCenters.npy')
        self.mpp = np.loadtxt(filedirectory+'/mpp.txt')    
        with open(filedirectory+'/approach_polys.pickle', 'rb') as handle:
            self.approach_polys = pickle.load(handle)  
        return
    
    
    def define_geometry(self, approach_polys = None):
        '''write function to create polys needed for trimming and deleting'''
        #self.approach_polys = self.poly(self.center, self.arm_centers, save = filedirectory+'/approach_polys.pickle')
        return

    
    def save_geometry(self):
        '''write function to save created geometric information about the intersection'''
        return
    

    def P_ave(p1,p2):
        #return the midpoint of a line / average of two points
        return SG.Point((p1[0]+p2[0])/2,(p1[1]+p2[1])/2)


    def plotPoly(self, image, out_file):
        #plot polygons on world image and save image
        for app, poly in self.approach_polys.items():
            point_list = [moving.Point(point[0]/self.mpp,point[1]/self.mpp) for point in poly.exterior.coords]
            t = moving.Trajectory.fromPointList(point_list)
            cvutils.cvPlot(image,t,(255, 0, 0),thickness=2)   
            cv2.imwrite(out_file, image)


    def polys(self, directions = ['N','E','S','W'], save = False):
        #create polygons from points in the middle of the approach arms and the center of the intersection.
        #directions is input if it is not a four-approach intersection
        #save is a file pathways
        l = len(self.arm_centers)
        points = {}
        approaches = {}
        for c,row in enumerate(self.arm_centers):
            points[directions[c]]=SG.Point(row)
            points[directions[c]+directions[(c+1)%l]] = self.P_ave(row,self.arm_centers[(c+1)%l])
        for c,row in enumerate(self.arm_centers):
            vals = [value for key, value in points.items() if directions[c] in key]
            vals.append(SG.Point(self.center[0][0],self.center[0][1]))
            approaches[directions[c]]=SG.MultiPoint(vals).convex_hull
        if save !=False:
            with open(save, 'wb') as handle:
                pickle.dump(approaches, handle, protocol=pickle.HIGHEST_PROTOCOL)
        self.approach_polys

 
        


    


