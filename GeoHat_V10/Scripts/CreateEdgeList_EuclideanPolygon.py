#---------------------------------------------------------------------------------
# CreateEdgeList_EuclideanPolygon.py
#
# Description: Creates an edge list using Euclidean distances from patch
#  centroids. This is much faster, but possibly less accurate than the
#  cost distance approach.
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
subPatchRaster = r'C:\WorkSpace\GHAT\GeoHAT_016_Squirrel\Data\SubPatches'#sys.argv[1]
searchRadius = ''

# Output variables
edgeListFN = r'C:\WorkSpace\GHAT\GeoHAT_016_Squirrel\Scratch\PolyEdges.csv'

##---FUNCTIONS---
def msg(txt):
    print txt
    arcpy.AddMessage(txt)
    return

##---PROCESSES---
# Convert raster to polygon
msg("Converting %s to polygons" %subPatchRaster)
tmpPoly = "in_memory/tmpPoly"
arcpy.RasterToPolygon_conversion(subPatchRaster,tmpPoly,"NO_SIMPLIFY")
dslvPoly =  "in_memory/dslvPoly"
arcpy.Dissolve_management(tmpPoly,dslvPoly,"grid_code")

# Generate near table
nearTable = "in_memory/NearTable"
arcpy.GenerateNearTable_analysis(dslvPoly,dslvPoly,nearTable,searchRadius,"LOCATION","NO_ANGLE","ALL")

# Join IDs back to near table
arcpy.JoinField_management(nearTable,"IN_FID",dslvPoly,"OBJECTID","grid_code")
arcpy.JoinField_management(nearTable,"NEAR_FID",dslvPoly,"OBJECTID","grid_code")
arcpy.CopyRows_management(nearTable,r'C:\WorkSpace\GHAT\GeoHAT_016_Squirrel\Scratch\scratch.gdb\nearTable')

# Create the output file
edgeFile = open(edgeListFN, 'w')
edgeFile.write("FromID, ToID, Distance, FromX, FromY, ToX, ToY\n")

# Update the fields in the PtDist Table
msg("Writing edge list to %s" %edgeListFN)
rows = arcpy.SearchCursor(nearTable,"grid_code < grid_code_1")
row = rows.next()
while row:
    fromID = row.grid_code
    toID = row.grid_code_1
    fromRec = arcpy.SearchCursor(nearTable,"grid_code = %s AND grid_code_1 = %s" %(toID, fromID)).next()
    if fromRec:
        fromX = fromRec.NEAR_X
        fromY = fromRec.NEAR_Y
    else:
        fromX = 0
        fromY = 0
    del fromRec
    toX = row.NEAR_X
    toY = row.NEAR_Y
    distance = round(row.NEAR_DIST)
    edgeFile.write("%d, %d, %d, %s, %s, %s, %s\n" %(fromID,toID,distance,fromX,fromY,toX,toY))
    row = rows.next()
edgeFile.close()

   
msg("Finished")