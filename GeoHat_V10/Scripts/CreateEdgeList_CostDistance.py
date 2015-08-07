# -------------------------------------------------------------------------
# CreateEdgeList_CostDistance.py
#
# Description:
#  Loops through each patch in a raster dataset and creates a cost surface
#  to determine the minimum distance to each other patch in the raster and
#  writes these minimum distances out to an edge file, in CSV format. 
#
#  If a cost threshold is supplied, costs will not be calcualted beyond that
#  point. This may save a little time in processing, but rasters are still
#  created for the entire extent.(In future versions, I will revert to a
#  method that creates patch subnetworks and loops through these to speed
#  analysis.
#
#  The user also has an option to save the cost rasters. This requires a lot
#  of disk space, but the rasters can be use for subsequent calculations, e.g.,
#  calculating distance to protected areas and corridor analyses.
#
#  Finally, the user can select to create least cost paths. This adds significant
#  processing time and is not recommended. 
#
# Inputs: <patch raster>, <cost surface raster>, <maxDist>
# Outputs: <edge list CSV file> 
# 
# June 2012, John.Fay@duke.edu
# -------------------------------------------------------------------------
# To do:
#  - Add an option to save all the cost distance and back link rasters
#  - Add an option to calculate least cost paths 

# Import modules
import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = 1

# User variables
patchRaster = sys.argv[1]           # Input patch raster
costRaster = sys.argv[2]            # Cost raster
maxDist = sys.argv[3]               # Maximum cost distance; can reduce processing
saveRasters = sys.argv[4]           # Boolean whether to save cost distance/back link rasters
saveRasterLocation = sys.argv[5]    # Folder where cost distance rasters are saved
computeLCPs = sys.argv[6]           # Boolean whether to create least cost path features
lcpFC = sys.argv[7]                 # Feature class to hold least cost paths
edgeList = sys.argv[8]              # Output edge list

# Script variables
arcpy.env.extent = patchRaster      # Set the extent to minimize processing
if maxDist == "0": maxDist = "#"    # Set maxDist to # if zero is specified
if (computeLCPs == 'true'):         # Create a backlink file, if creating LCPs
    backLink = arcpy.env.scratchWorkspace + "\\backlink"
else:
    backLink = ""

##--FUNCTIONS--
def msg(txt):  print msg; arcpy.AddMessage(txt); return

##--PROCESSES--
# If asked to save LCPs, create the LCP output feature class
if computeLCPs == 'true':
    msg("Creating LCP feature class")
    SR = arcpy.Describe(patchRaster).SpatialReference
    arcpy.CreateFeatureclass_management(os.path.dirname(lcpFC),os.path.basename(lcpFC),"POLYLINE","#","ENABLED","#",SR)
    arcpy.AddField_management(lcpFC,"FromID","LONG",10)
    arcpy.AddField_management(lcpFC,"ToID","LONG",10)
    arcpy.AddField_management(lcpFC,"Cost","DOUBLE",10,2)
    arcpy.DeleteField_management(lcpFC,"ID")
            
# Get a list of patch IDs
msg("Creating a list of patch IDs")
patchIDs = []
rows = arcpy.SearchCursor(patchRaster)
row = rows.next()
while row:
    patchIDs.append(row.Value)
    row = rows.next()
del row, rows

# Initiate the output edge list
msg("Initializing the output edge file")
outFile = open(edgeList,'w')
outFile.write("FromID,ToID,Cost\n")

# Initiate status variables
total = float(len(patchIDs))
interval = total/20 #<-- 20.0 reports status at 5% completion intervals
interval2 = interval
iter = 0
msg("Initiating edge list creation...")

# Loop through each patchID in the PatchIDList
for patchID in patchIDs:
    iter = iter + 1
    if iter > interval:
        msg(" %d%% complete." %(float(iter/total)*100.0))
        interval = interval + interval2
    # - Isolate the TO patch
    selectedPatch = sa.SetNull(patchRaster, patchRaster, "Value <> %s" %patchID)
    # - If saving outputs, set the back link raster name
    if saveRasters == 'true':
        backLink = os.path.join(saveRasterLocation,"BL_%s.img" %patchID)
    # - Calculate a cost distance and cost back link raster to the selected patch
    costDist = sa.CostDistance(selectedPatch, costRaster, maxDist, backLink)
    # - If saving outputs, save the cost distance as an integer raster
    if saveRasters == 'true':
        cdInt = sa.Int(costDist) #Convert to integer raster to save space
        cdInt.save(os.path.join(saveRasterLocation,"CD_%s.img" %patchID))
    # - Tabulate zonal stats for the other patches on the cost distance
    zStatTable = sa.ZonalStatisticsAsTable(patchRaster,"Value",costDist,"in_memory\zstattbl","DATA","MINIMUM")
    # - Write out edges to an edge list; setting to VALUE > patchID writes only the lower half of the matrix
    recs = arcpy.SearchCursor(zStatTable,"VALUE > %d" %patchID)
    rec = recs.next()
    while rec:
        outFile.write("%d,%d,%s\n" %(patchID, rec.VALUE, rec.MIN))
        # - If asked to write LCPs, here we go
        if computeLCPs == 'true':
            ToPatchID = rec.VALUE
            if rec.MIN > 0:
                # Isolate the to-patch
                ToPatch = sa.SetNull(patchRaster,patchRaster,"VALUE <> %d" %ToPatchID)
                # Calculate the least cost path to the to_patch
                lcpRaster = sa.CostPath(ToPatch,costDist,backLink,"BEST_SINGLE")
                # Convert the raster to a feature
                lcpFeature = "in_memory/LCPfeature"
                result = arcpy.RasterToPolyline_conversion(lcpRaster,lcpFeature)
                # Dissolve the feature
                lcpDissolve = "in_memory/LCPdissolve"
                result = arcpy.Dissolve_management(lcpFeature,lcpDissolve)
                # Copy the features over to the LCP feature class
                cur = arcpy.InsertCursor(lcpFC)
                feat = cur.newRow()
                feat.shape = arcpy.SearchCursor(lcpDissolve).next().shape
                feat.FromID = patchID
                feat.ToID = ToPatchID
                feat.Cost = rec.MIN
                cur.insertRow(feat)
                del feat, cur
        rec = recs.next()
    del rec, recs
                
# Close the edge list file object
outFile.close()

# Clean up and exit
arcpy.AddMessage("Edges successfully written to %s" %edgeList)
