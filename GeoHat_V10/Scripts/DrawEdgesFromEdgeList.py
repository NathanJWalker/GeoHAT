#---------------------------------------------------------------------------------
# DrawEdgesFromEdgeList.py
#
# Description: Creates a feature class of edge lines drawn between patch centroids.
#  Each edge is labeled with the cost distance associated in traveling between
#  patch pairs.
#
# Inputs: <Patch raster> <edge list> <maxDistance>
# Output: <Patch connected area raster> {patch connected area table}
#  
# June 14, 2012
# John.Fay@duke.edu
#---------------------------------------------------------------------------------

# Import system modules
import sys, string, os, arcpy, math
import arcpy.sa as sa

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

# Input variables
patchRaster = r'O:\GeoHAT_16July\Data\CatchPatch.img'#sys.argv[1]
edgeListFN = r'O:\GeoHAT_16July\Data\EdgeList.csv'#sys.argv[2]
costThreshold = 0#sys.argv[3]
if costThreshold == '#': costThreshold = 0

# Output variables 
edgeFC = r'O:\GeoHAT_16July\Data\Edges.shp'#sys.argv[4]

##---FUNCTIONS---
def msg(txt): print txt; arcpy.AddMessage(txt); return

##---PROCESSES---
#Create centroids from patch raster
msg("Creating centroids from patch raster")
centroidRaster = sa.ZonalGeometry(patchRaster,"VALUE","CENTROID")

#Create centroid FC from patch raster
msg("Converting centroids to features")
centroidFC = arcpy.RasterToPoint_conversion(centroidRaster,"in_memory\\Centroids","VALUE")

#Create the feature class
msg("Creating Edge feature class")
SR = arcpy.Describe(centroidFC).SpatialReference
arcpy.CreateFeatureclass_management(os.path.dirname(edgeFC),os.path.basename(edgeFC),"POLYLINE","#","ENABLED","#",SR)
arcpy.AddField_management(edgeFC,"FromID","LONG",10)
arcpy.AddField_management(edgeFC,"ToID","LONG",10)
arcpy.AddField_management(edgeFC,"Cost","DOUBLE",10,2)
arcpy.DeleteField_management(edgeFC,"ID")
# Create a dictionary of points from the centroid FC
msg("Extracting coordinates from centroids")
pointDict = {}
recs = arcpy.SearchCursor(centroidFC)
rec = recs.next()
while rec:
    pnt = rec.shape
    id = int(rec.grid_code)
    pointDict[id] = pnt.firstPoint
    rec = recs.next()
del rec, recs
# Initiaize an insert cursor and line array for the Edge FC
msg("Creating edge features. Please be patient...")
cur = arcpy.InsertCursor(edgeFC)
lineArray = arcpy.Array()
# Loop through the edge list and draw lines
edgeFile = open(edgeListFN,'r')
header = edgeFile.readline()
lineText = edgeFile.readline()
while lineText:
    # Get the data
    lineData = lineText[:-1].split(",")
    fromID = int(lineData[0])
    toID = int(lineData[1])
    cost = float(lineData[2])
    if cost < float(costThreshold) or costThreshold == 0:
        # Create a new feature object
        feat = cur.newRow()
        lineArray.add(pointDict[fromID])
        lineArray.add(pointDict[toID])
        polyline = arcpy.Polyline(lineArray)
        lineArray.removeAll()
        feat.shape = polyline
        feat.FromID = fromID
        feat.ToID = toID
        feat.Cost = cost
        # Add the feature to the cursor
        cur.insertRow(feat)
    # Go to the next line
    lineText = edgeFile.readline()
edgeFile.close()
del feat, cur
    
    
msg("Finished")