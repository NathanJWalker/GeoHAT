# CreateLCPsFromStack.py
#
# Description: 
#  Creates a feature class of least cost paths between all patch pairs.
#  Each path among patch pairs is a separate feature and is attributed
#  with the cost of traveling that path.
#
# June 14, 2012
# John.Fay@duke.edu

# Import system modules
import sys, string, os, arcpy
import arcpy.sa as sa

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

# Input variables
patchRaster = sys.argv[1]
CostDistWS = sys.argv[2]
edgeListFN = sys.argv[3]

# Output variables
lcpFCSave = sys.argv[4]

##---FUNCTIONS---
def msg(txt):
    print txt
    arcpy.AddMessage(txt)
    return

##---PROCESSES---
# Create a dictionary of edge costs from edge list file
msg("Creating list of edge costs")
edgeDict = {}
edgeList = open(edgeListFN,'r')
headerLine = edgeList.readline()
dataLine = edgeList.readline()
while dataLine:
    lineData = dataLine.split(",")
    fromID = int(lineData[0])
    toID = int(lineData[1])
    cost = float(lineData[2][:-1])
    edgeDict[(fromID,toID)] = cost
    dataLine = edgeList.readline()
edgeList.close()

# Create a list of patch IDs
msg("Creating list of patch IDs...")
patchIDs = []
rows = arcpy.SearchCursor(patchRaster)
row = rows.next()
while row:
    patchIDs.append(row.VALUE)
    row = rows.next()
del row, rows

# Loop through patches and and calculate least cost paths
streamFC = "in_memory/LCPlines"
dslvFC = "in_memory/LCPline"
lcpFC = "in_memory/LCPlineOut"

first = True
for to_patch in patchIDs:
    # Idenfity the cost and back link rasters
    cdRaster = os.path.join(CostDistWS,"CD_%s.img" %to_patch)
    blRaster = os.path.join(CostDistWS,"BL_%s.img" %to_patch)
    # Loop through each from patch (skipping ones already processed...)
    for from_patch in patchIDs:
        if from_patch <= to_patch: continue
        msg("Creating least cost path from %s to %s" %(to_patch, from_patch))
        # Extract the cost
        cost = edgeDict[(to_patch,from_patch)]
        # Isolate the to patch
        fromPatch = sa.SetNull(patchRaster,patchRaster,"VALUE <> %s" %from_patch)
        # Calculate least cost paths from all patches to the current patch
        lcpRaster = sa.CostPath(fromPatch,cdRaster,blRaster,"BEST_SINGLE")
        # Convert the backlink to a flow direction raster
        #fdRaster = sa.Int(sa.Exp2(blRaster) / 2)
        # Convert the LCP raster to a vector
        arcpy.RasterToPolyline_conversion(lcpRaster,streamFC,'ZERO',0,"NO_SIMPLIFY")
        #sa.StreamToFeature(lcpRaster,fdRaster,streamFC,"NO_SIMPLIFY")
        if first:   # If the first patch, dissolve to the output FC file
            arcpy.Dissolve_management(streamFC,lcpFC)
            arcpy.AddField_management(lcpFC,"FromID","LONG",10)
            arcpy.AddField_management(lcpFC,"ToID","LONG",10)
            arcpy.AddField_management(lcpFC,"Cost","DOUBLE",10,2)
            arcpy.CalculateField_management(lcpFC,"FromID",from_patch)
            arcpy.CalculateField_management(lcpFC,"ToID",to_patch)
            arcpy.CalculateField_management(lcpFC,"Cost",cost)
            first = False
        else:       # Otherwise, dissolve it and append it to the original
            arcpy.Dissolve_management(streamFC,dslvFC)
            arcpy.AddField_management(dslvFC,"FromID","LONG",10)
            arcpy.AddField_management(dslvFC,"ToID","LONG",10)
            arcpy.AddField_management(dslvFC,"Cost","DOUBLE",10,2)
            arcpy.CalculateField_management(dslvFC,"FromID",from_patch)
            arcpy.CalculateField_management(dslvFC,"ToID",to_patch)
            arcpy.CalculateField_management(dslvFC,"Cost",cost)
            arcpy.Append_management(dslvFC,lcpFC)

arcpy.CopyFeatures_management(lcpFC,lcpFCSave)
msg("Finished")