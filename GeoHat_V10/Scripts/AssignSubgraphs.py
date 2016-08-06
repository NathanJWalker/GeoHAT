#---------------------------------------------------------------------------------
# AssignSubgraphs.py
#
# Create edge list with subgraph assignments, for given threshold distance
#
# Requires: NetworkX to be stored in script folder (or installed)
# Create Edge List tool must be run first
#
# Inputs: <edge list> <maxDistance>
# Output: <Patch connected attribute table (CSV format)>
#  
# August 5, 2016
# Nathan Walker
# Building on code from John Fay
#
#---------------------------------------------------------------------------------

# Import system modules
import sys, string, os, arcpy, math
import arcpy.sa as sa
import networkx as nx

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

# Input variables
edgeListFN = sys.argv[1]    
maxDistance = int(sys.argv[2])
k = math.log(0.1) / maxDistance ##Decay coefficient

# Output variables
outputFN = sys.argv[3]   

##---FUNCTIONS---
# Message management
def msg(txt): print txt; arcpy.AddMessage(txt); return

##---PROCESSES---
# Create a graph from the edge list
msg("Creating graph from nodes < %d from each other" %maxDistance)
G = nx.Graph()
subDict = {}
edgeList = open(edgeListFN,'r')
headerLine = edgeList.readline()
dataLine = edgeList.readline()
while dataLine:
    lineData = dataLine.split(",")
    u = int(lineData[0])
    v = int(lineData[1])
    w = float(lineData[2][:-1])
    if w <= maxDistance:
        G.add_edge(u,v,weight = w)
    dataLine = edgeList.readline()
edgeList.close()

# create subgraphs from this graph
subGs = nx.connected_component_subgraphs(G)
msg("The graph contains %d subgraph(s)" %len(subGs))

# Initiate the output edge list
msg("Initializing the output edge file")
outFile = open(outputFN,'w')
outFile.write("FromID,ToID,Cost,Subgraph\n")

# For each subgraph, assign edges in that subgraph with subgraph ID
cnt = 0
for subG in subGs:
    cnt += 1
    # for each edge, add subgraph ID
    for line in nx.generate_edgelist(subG, data=['weight']):
        fromPatch = int(line.split(" ")[0])
        toPatch = int(line.split(" ")[1])
        cost = float(line.split(" ")[2])
        # write to output file
        outFile.write("%d,%d,%s,%d\n" %(fromPatch,toPatch,cost,cnt))

arcpy.CheckInExtension("spatial")
