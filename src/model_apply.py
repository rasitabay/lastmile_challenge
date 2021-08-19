###################################################

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 21:49:08 2021

@author: okanarslan
"""

import numpy as np 
import pandas as pd 
import os
import sys, json, collections, csv, math, time
from os import path

t0= time.time()

print("Last Mile Routing Research Challenge")
print("Team Futurifai")

# Preparation
###########################################################################################
# Get Directory
BASE_DIR = path.dirname(path.dirname(path.abspath(__file__)))

# Create a temporary directory
temp_path = path.join(BASE_DIR, 'data/model_apply_outputs/temp')
try:
    os.mkdir(temp_path)
except OSError as error:
    print(error)

# The path to c++ implementation of TSP heuristic
GA_path = path.join(BASE_DIR, 'src/code')

# Parameter settings
###########################################################################################
bigM = 99999999                 # a very large number
# following paramaters help discourage the driver to visit other nodes
a1 = 1/10
a2 = 5/10
a4 = 50/10
a5 = 150/10
b = 1/10  
distMultiplier = 10
returnArcLengthMultiplier = 0

# Read data files 
###########################################################################################
# Only the route and travel times are read. Our method does not require package data.
prediction_routes_path = path.join(BASE_DIR, 'data/model_apply_inputs/new_route_data.json')
with open(prediction_routes_path, newline='') as in_file:
    dataRoute = json.load(in_file)

prediction_travel_path = path.join(BASE_DIR, 'data/model_apply_inputs/new_travel_times.json')
with open(prediction_travel_path, newline='') as in_file2:
    dataTravel = json.load(in_file2)
###########################################################################################
    
# This module transforms the distance matrix and 
# creates input files for a heuristic in 'temp' folder 
# (as symetric TSP instances in the TSPLIB format)

# Given a "node", this procedure returns its closest neighbor on the given instance.
def closestNode(route, node):
    x_node = dataRoute[route].get('stops').get(node).get('lat')
    y_node = dataRoute[route].get('stops').get(node).get('lng')
    min_node = bigM
    which_node = ''   # the error is handled in calling arguments
    for n in dataRoute[route].get('stops'):
        if n == node or not isinstance(dataRoute[route].get('stops').get(n).get('zone_id'), str):
            continue
        x1 = dataRoute[route].get('stops').get(n).get('lat')
        y1 = dataRoute[route].get('stops').get(n).get('lng')
        dist_node = math.sqrt((x1-x_node)*(x1-x_node)+(y1-y_node)*(y1-y_node))
        if dist_node < min_node and dist_node>math.exp(-15):
            min_node = dist_node
            which_node = n
    return which_node

# Given two nodes, this function returns a "discouragement penalty multiplier".
# It also handles the exceptional cases when a node does not have a zone (nan) or 
# when the node is depot.
def penalty(zone1, zone2,node,i,depot,route):
    try:
        if (isinstance(zone1, str) and isinstance(zone2, str)):
            
            if "." not in zone1 or "-" not in zone1:
                tempNode = closestNode(route,node)
                node = tempNode
                zone1 = dataRoute[route].get('stops').get(node).get('zone_id')
            if "." not in zone2 or "-" not in zone2:
                tempNode = closestNode(route,i)
                i = tempNode
                zone2 = dataRoute[route].get('stops').get(i).get('zone_id')


            split1 = zone1.split("-")
            P1 = split1[0]
            split2 = split1[1].split(".")
            rkm11 = split2[0]
            res = []
            res[:]=split2[1]
            rkm12 = res[0]
            hrf1 = res[1]

            split1 = zone2.split("-")
            P2 = split1[0]
            split2 = split1[1].split(".")
            rkm21 = split2[0]
            res = []
            res[:]=split2[1]
            rkm22 = res[0]
            hrf2 = res[1]

            toplamAyni = 0
            if rkm11==rkm21:
                toplamAyni += 1
            if rkm12==rkm22:
                toplamAyni += 1
            if hrf1==hrf2:
                toplamAyni += 1

            if P1==P2:
                if toplamAyni == 3:
                    return a1
                if toplamAyni == 2:
                    return a2
            else:
                return a4
            
            return a5
        else:

            newCeza = b
            if node==depot or i==depot:
                return b
            else:
                # Neither is depot. Either of the nodes could be "nan"

                zoneNew1 = zone1
                zoneNew2 = zone2
                which_node1 = node
                which_node2 = i

                if not isinstance(zone1, str):
                    which_node1 = closestNode(route, node)
                    zoneNew1 = dataRoute[route].get('stops').get(which_node1).get('zone_id')
                
                if not isinstance(zone2, str):               
                    which_node2 = closestNode(route, i)
                    zoneNew2 = dataRoute[route].get('stops').get(which_node2).get('zone_id')

                newCeza = penalty(zoneNew1, zoneNew2, which_node1, which_node2, depot, route)

            return newCeza
            
    except:
        print("Error reading zones -", zone1, " ", zone2, " ",node, " ",i, " ",depot, " ",route)
        return a5


# This procedure transforms the distance matrix,
#  generates the ".tsp" files as symmetric TSP instances and
# saves them under "temp folder".

counter = 0
print("Creating routes...")

for route in dataRoute:

    lines = []
    counter += 1

    nNodes = len(dataRoute[route].get('stops').keys())

    # START CREATING INPUT FILE
    lines.append("NAME : " + route)
    lines.append("TYPE : ATSP")
    lines.append("DIMENSION : " + str(2*nNodes))
    lines.append("EDGE_WEIGHT_TYPE : EXPLICIT")
    lines.append("EDGE_WEIGHT_FORMAT : FULL_MATRIX ")
    lines.append("EDGE_WEIGHT_SECTION")

    routeDist = 0

    depot = ''
    say = 0

    # Detect the depot
    for node in dataRoute[route].get('stops'):    
        if dataRoute[route].get('stops').get(node).get('type') == 'Station':
            depot = node


    # Generate the distance matrix (We modify the arc lengths by applying penalties according to multiple factors.)
    # We then transform this matrix (for asymmetric TSP) into a symmetric TSP matrix, which we use for solving the 
    # instance.

    # round1
    mat=np.zeros((nNodes,nNodes))
    ii = 0
    for node in dataRoute[route].get('stops'):    
        metin = ""
        for j in dataTravel[route].get(node).keys():
            metin+=str(bigM)
            metin+=str('\t')            
        jj = 0        
        for i in dataTravel[route].get(node).keys():
            dist = dataTravel[route].get(node).get(i)
            ceza = 1
            if node != i:
                zone1 = dataRoute[route].get('stops').get(node).get('zone_id')
                zone2 = dataRoute[route].get('stops').get(i).get('zone_id')                
                ceza = penalty(zone1,zone2,node,i,depot,route)
            if i==depot:
                dist = returnArcLengthMultiplier * dist

            if node == i:
                mat[ii, jj] = -bigM
                metin+=str(-bigM)
            else:
                val = int(distMultiplier * dist * ceza) 
                mat[ii, jj] = val
                metin+=str(val)
            
            metin+=str('\t')
            jj += 1
        lines.append(metin)
        ii += 1


    # round2
    ii = 0
    for node in dataRoute[route].get('stops'):    
        metin = ""
        jj = 0        
        for i in dataTravel[route].get(node).keys():
            if node == i:
                metin+=str(-bigM)
            else:
                metin+=str(int(mat[jj, ii]))
            metin+=str('\t')
            jj += 1

        for j in dataTravel[route].get(node).keys():
            metin+=str(bigM)
            metin+=str('\t')            
        lines.append(metin)
        ii += 1
                 
    lines.append('EOF\n')

    with open(temp_path + "/Route-" + str(counter) + ".tsp", 'w') as f:
        for line in lines:
            f.write(line)
            f.write('\n')

# FINISHED CREATING THE FILE
t1 = time.time() - t0
print("Created the tsp files. Time elapsed: ", t1)

# In case the heuristic does not generate a feasible tour, we have a greedy
# algorithm as a backup plan.
def runGreedy(filename,route, depot, nodeNames):
    
    # Read distance matrix from the file
    nNodes = len(dataRoute[route].get('stops').keys())
    distanceMatrix = np.zeros((nNodes,nNodes)) 

    sum = 0;
    nodeNumbers = {}
    for node in dataRoute[route].get('stops'):
        nodeNumbers[node] = sum
        sum+=1
                 
    for u in range(0, nNodes):
        distanceMatrix[u,u] = bigM

    ii = -6
    for line in open(filename).readlines():
        jj = 0
        for val in line.split("\t"):
            if ii < nNodes and jj > nNodes + ii and jj < 2*nNodes:
                distanceMatrix[ii,jj-nNodes] = val
            elif ii>=nNodes and jj < ii - nNodes  and ii < 2*nNodes:
                distanceMatrix[ii-nNodes,jj] = val
            jj += 1
        ii += 1

    # Start building the tour
    isVisited = {}
    say = 0
    nNodes = len(dataRoute[route].get('stops'))
    for node in dataRoute[route].get('stops'):
        isVisited[node] = 0

    order = { depot : 0}
    node = depot
    isVisited[depot] = 1
    sum = 1
    while sum < len(isVisited):
        minVal = bigM
        minKey =''
        for i in dataTravel[route].get(node).keys():
            if distanceMatrix[nodeNumbers[node],nodeNumbers[i]] < minVal and i!=node and isVisited[i] == 0:
                minVal = distanceMatrix[nodeNumbers[node],nodeNumbers[i]]
                minKey = i
        node = minKey
        order[minKey] = sum
        isVisited[node] = 1
        sum += 1

    return order

# read a tour generated by the heuristic    
def read_tour(filename, route):
    tour = []
    try:
        for line in open(filename).readlines():
            for i in line.split(" "):
                if i != '' and int(i) <= len(dataRoute[route].get('stops').keys()):
                    tour.append(int(i))
    except:
        tour = []
    return tour

counter = 0
routeYaz = {}
os.chdir(GA_path)

# We now start running the heuristic
for route in dataRoute:
    counter += 1
    lines = []
    success = os.system("./a.out " + temp_path + "/Route-" + str(counter) + ".tsp")

    # detect the depot and the names of the nodes in order
    depot = ''
    nNodes = len(dataRoute[route].get('stops'))
    nodeNames = [""]* (nNodes+1)
    sum = 1;
    for node in dataRoute[route].get('stops'):
        nodeNames[sum] = node
        if dataRoute[route].get('stops').get(node).get('type') == 'Station':
            depot = node
        sum += 1

    isTourFeasible = True
    if success != 0:
        isTourFeasible = False
    else:
        # start creating the JSON file
        order = { depot : 0}
        node = depot

         # read the tour from the file and reorder to find the correct order starting from the depot
        tour = read_tour("./bestSolution.txt", route)
        os.remove("./bestSolution.txt")
        sum = 1
        backtrack = 0
        for t in tour:
            node = nodeNames[t]
            if node == depot:
                backtrack = sum
            sum += 1

        sum = 1
        isNodeVisited = [0] * (nNodes)
        lastNode = 0
        for t in tour:
            node = nodeNames[t]
            ordr = (sum + nNodes - backtrack) % nNodes
            if node == depot and ordr!=0:
                isTourFeasible = False
                break
            isNodeVisited[ordr] = 1
            order[nodeNames[t]] = ordr
            if ordr == nNodes-1:
                lastNode = nodeNames[t]
            sum += 1

        if backtrack == 0 and isTourFeasible == True:
            isTourFeasible = False
        for i in range(0, nNodes):
            if isNodeVisited[i] == 0 and isTourFeasible == True:
                isTourFeasible = False
                break

    # Check for feasibility and run Greedy heuristic if infeasible for any reason that we cannot foresee
    if isTourFeasible == False:
        order = runGreedy(temp_path + "/Route-" + str(counter) + ".tsp", route,depot,nodeNames)
    
    od = {}
    for i in sorted (order.keys()) : 
         od[i] = order[i]

    proposed = {'proposed' : od }
    routeYaz[route] = proposed

os.chdir("../")

# Write output data
output_path=path.join(BASE_DIR, 'data/model_apply_outputs/proposed_sequences.json')
with open(output_path, 'w') as outfile:
    json.dump(routeYaz, outfile)

print("Success: The '{}' file has been saved".format(output_path))

t1 = time.time() - t0
print("Done. Time elapsed: ", t1)

os.system("rm -rf " + temp_path)
    
###################################################