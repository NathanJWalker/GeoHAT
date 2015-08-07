#---------------------------------------------------------------------------------
#CalculateDistancesToProteced.py
#
# Description: 
#  This script uses the cost distance and cost back link rasters generated when
#  the Create Edge List script is run. It loops through each patch and calculates
#  zonal statistics to find the least cost distances between the patch and all
#  the protected area clusters in the supplied protected areas raster. The result
#  is an edge list of each patch, the protected areas, and the distances between
#  them.
#
# Inputs: <Patch raster> <Protected area raster> <Cost distance raster folder>
# Outputs: <Patch to protected area edge list>
#
# July 2012, John.Fay@duke.edu
#---------------------------------------------------------------------------------

import sys, os, math, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Input variables
patchRaster = sys.argv[1]
protectedRaster = sys.argv[2]
CDs = sys.argv[3]
#Output variable
distanceCSV_Filename = sys.argv[4]

##--FUNCTIONS--
def msg(txt): print txt; arcpy.AddMessage(txt); return

##--PROCESSES--
# Get a list of patch IDs
msg("Creating a list of patch IDs")
patchIDs = []
rows = arcpy.SearchCursor(patchRaster)
row = rows.next()
while row:
    patchIDs.append(row.Value)
    row = rows.next()
del row, rows

#Create the output
outFile = open(distanceCSV_Filename,'w')
outFile.write("PatchID,ProtAreaID,Cost\n")

# Loop through CD rasters and calculate zonal min to each protected area
for ID in patchIDs:
    msg("Working on patch %d" %ID)
    CD_Raster = CDs + "\\CD_%s.img" %ID
    zStatTable = sa.ZonalStatisticsAsTable(protectedRaster,"VALUE",CD_Raster,"in_memory/ZStat",'',"MINIMUM")
    recs = arcpy.SearchCursor(zStatTable)
    rec = recs.next()
    while rec:
        outFile.write("%s,%d,%s\n" %(ID, rec.VALUE, rec.MIN))
        rec = recs.next()
    del rec, recs

outFile.close()