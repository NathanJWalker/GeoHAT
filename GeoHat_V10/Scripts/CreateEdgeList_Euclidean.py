#---------------------------------------------------------------------------------
# CreateEuclieanEdgeList.py
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
patchRaster = sys.argv[1]
saveCentroids = sys.argv[3]

# Output variables
edgeListFN = sys.argv[2]
centroidFC = sys.argv[4]

##---FUNCTIONS---
def msg(txt):
    print txt
    arcpy.AddMessage(txt)
    return

##---PROCESSES---
# Create a centroid feature class from the patch raster
msg("Extracting patch centroids")
patchCentroids = "in_memory\Centroids"
centroidRaster = sa.ZonalGeometry(patchRaster,"VALUE","CENTROID")
arcpy.RasterToPoint_conversion(centroidRaster,patchCentroids)

# Save the centroids, if requested
if saveCentroids == 'true':
    msg("Centroids will be saved to %s" %centroidFC)
    arcpy.CopyFeatures_management(patchCentroids,centroidFC)
    arcpy.AddField_management(centroidFC,"PatchID","LONG",10)
    arcpy.CalculateField_management(centroidFC,"PatchID","[grid_code]")
    arcpy.DeleteField_management(centroidFC,"pointid")
    arcpy.DeleteField_management(centroidFC,"grid_code")


# Calculate point distance table
msg("Calculating point distance")
ptDistTbl = "in_memory\PtDistance"
result = arcpy.PointDistance_analysis(patchCentroids, patchCentroids,ptDistTbl)

# Add attribute indices to point distance table
msg("Adding fields")
result = arcpy.AddField_management(ptDistTbl,"FromID","Long",10)
result = arcpy.AddField_management(ptDistTbl,"ToID","Long",10)

# Create a dictionary of FIDs:GridCodes
msg("Updating ID fields")
idDict = {}
fidFld = arcpy.Describe(patchCentroids).OIDFieldName
idFld = "grid_code"
rows = arcpy.SearchCursor(patchCentroids)
row = rows.next()
while row:
    idDict[row.getValue(fidFld)] = row.getValue(idFld)
    row = rows.next()
del row, rows

# Create the output file
edgeFile = open(edgeListFN, 'w')
edgeFile.write("FromID, ToID, Distance\n")

# Update the fields in the PtDist Table
msg("Writing edge list to %s" %edgeListFN)
rows = arcpy.SearchCursor(ptDistTbl,"INPUT_FID < NEAR_FID")
row = rows.next()
while row:
    fromID = idDict[row.INPUT_FID]
    toID = idDict[row.NEAR_FID]
    distance = row.DISTANCE
    edgeFile.write("%d, %d, %d\n" %(fromID, toID, round(distance)))
    row = rows.next()
edgeFile.close()

   
msg("Finished")