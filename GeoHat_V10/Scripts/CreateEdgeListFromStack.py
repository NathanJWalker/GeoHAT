#---------------------------------------------------------------------------------
# CreateEdgeListFromStack.py
#
# Description: 
#  Creates an edge list of all patches from cost distance rasters saved in
#  the supplied workspace. 
#
# June 14, 2012
# John.Fay@duke.edu
#---------------------------------------------------------------------------------

# Import system modules
import sys, string, os, arcpy
import arcpy.sa as sa

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

# Input variables
patchRaster = sys.argv[1]   #r'C:\WorkSpace\GHAT\GHAT_014\Data\Patches'
CostDistWS = sys.argv[2]    #r'C:\WorkSpace\GHAT\GHAT_014\Scratch\CostRasters'

# Output variables
edgeListFN = sys.argv[3]    #r'C:\WorkSpace\GHAT\GHAT_014\Scratch\EdgeListStack.csv'

##---FUNCTIONS---
def msg(txt):
    print txt
    arcpy.AddMessage(txt)
    return

##---PROCESSES---
# Create a list of patch IDs
msg("Creating list of patch IDs...")
patchIDs = []
rows = arcpy.SearchCursor(patchRaster)
row = rows.next()
while row:
    patchIDs.append(row.VALUE)
    row = rows.next()
del row, rows

# Create a list of rasters and patch IDs
msg("Extracting cost distance rasters...")
origWS = arcpy.env.workspace
arcpy.env.workspace = CostDistWS
cdRasters = arcpy.ListRasters("*CostDist.img")

# Create the edge list
msg("Creating edge list...")
edgeList = open(edgeListFN, 'w')
edgeList.write("FromID,ToID,Cost\n")

# Loop through cdRaster and calculate zonal stats for the patches
zStatTbl = "in_memory/zStatTbl"
for cdRaster in cdRasters:
    # Get the from patch from the file name
    fromID = int(cdRaster.split("_")[0][1:])
    msg("Adding edges to patch %s" %fromID)
    # Calculate zonal min (shortest distance) for each patch
    result = sa.ZonalStatisticsAsTable(patchRaster,"VALUE",cdRaster,zStatTbl,"#","MINIMUM")
    # Write the table to the edge list (only records not added before)
    rows = arcpy.SearchCursor(zStatTbl,"VALUE > %s" %fromID)
    row = rows.next()
    while row:
        toID = row.VALUE
        cost = row.MIN
        edgeList.write("%s, %s, %s\n" %(fromID,toID,cost))
        row = rows.next()
        
#Restore original workspace
arcpy.env.workspace = origWS

#Close the edgelist
edgeList.close()

msg("Finished")