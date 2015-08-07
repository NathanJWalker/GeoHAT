# CreateLCPsFromStackQUICK.py
#
# Description: 
#  Creates a feature class of least cost paths between all patch pairs.
#  The paths created are not attributed in any useful manner, but processing
#  them is *relatively* quick. The output is useful for display purposes.
#
#  This tool requires the cost distance and cost back link rasters created
#  when the CreateEdgeList script is run. It loops through each patch, extracts
#  the cost distance and cost back link raster associated with that patch and
#  uses them to draw raster LCPs back to that patch. At each iteration, the
#  LCP is combined with previously calculated LCPs to create a raster identifying
#  all cells involved in any least cost path. After all patches have been processed
#  this raster is converted to a polyline feature class.
#
#  A commented out procedure (which adds processing time) converts the LCP to a set
#  of stream features at each patch iteration. The stream features are combined into
#  a master feature class containing the stream features from each iteration. The
#  result more accurately reflects the directions of each LCP, but at a cost of
#  processing time.
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

# Output variables
lcpFC = sys.argv[3]

##---FUNCTIONS---
def msg(txt): print txt; arcpy.AddMessage(txt); return

##---PROCESSES---
# Regiongroup the patch ID to ensure they are contiguous
msg("Preprocessing the patch raster")
patchFix = sa.RegionGroup(patchRaster,"EIGHT","WITHIN","ADD_LINK")
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
first = True
for patchID in patchIDs:
    msg("Working on patch %s of %s" %(patchID,len(patchIDs)))
    # Idenfity the cost and back link rasters
    cdRaster = os.path.join(CostDistWS,"CD_%s.img" %patchID)
    blRaster = os.path.join(CostDistWS,"BL_%s.img" %patchID)
    # Calculate least cost paths from all patches to the current patch
    lcpRaster = sa.CostPath(patchFix,cdRaster,blRaster,"EACH_ZONE")
    if first:
        lcpOutput = sa.Con(sa.IsNull(lcpRaster),0,1)
        first = False
    else:
        lcpTemp = sa.Con(sa.IsNull(lcpRaster),0,1) + lcpOutput
        lcpOutput = sa.Con(lcpTemp,1,0,"VALUE > 0")
    '''
    # Convert the backlink to a flow direction raster
    #fdRaster = sa.Int(sa.Exp2(blRaster) / 2)
    # Convert the LCP raster to a vector
    if first:   # If the first patch, save the streamsFC to the output FC file
        sa.StreamToFeature(lcpRaster,fdRaster,lcpFC,"NO_SIMPLIFY")
        first = False
    else:       # Otherwise, create it and append it to the original
        sa.StreamToFeature(lcpRaster,fdRaster,streamFC,"NO_SIMPLIFY")
        arcpy.Append_management(streamFC,lcpFC)
    '''
msg("preprocessing raster")
lcpR = sa.SetNull(lcpOutput,1, "VALUE = 0")
msg("Converting raster to polyline")
arcpy.RasterToPolyline_conversion(lcpR,lcpFC,'NODATA','','SIMPLIFY')

msg("Finished")