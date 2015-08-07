# MergePatchAttributes.py
#
# Description: Merges patch attributes into a single table that can
#  be analyzed for correlations and other statistcal patterns.
#
# Inputs: <Patch raster> <Patch CSV files> 
# Outputs: <Patch attribute raster>
#
# July 2012, John.Fay@duke.edu

import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Inputs
patchRaster = sys.argv[1]
csvList = sys.argv[2].split(";")
#Output
patchAttributeRaster = sys.argv[3]

##--FUNCTIONS--
def msg(txt): print txt; arcpy.AddMessage(txt); return

##--PROCESSES--
# Copy patch attribute raster
arcpy.CopyRaster_management(patchRaster, patchAttributeRaster)

for csv in csvList:
    msg("Extracting records from %s" %csv)
    # Make table from the CSV files
    joinTbl = "in_memory/joinTable"
    arcpy.CopyRows_management(csv,joinTbl)
    # Get field names (all but first one)
    fldNames = []
    for f in arcpy.ListFields(joinTbl):
        fldNames.append(str(f.name))
    # Get the Join field name (the second field)
    joinFld = fldNames[1]
    #Join to the master table
    arcpy.JoinField_management(patchAttributeRaster, "VALUE", joinTbl, joinFld, fldNames[2:])
    msg("%s joined to table\n" %fldNames[2:])

msg("Saving results to %s" %patchAttributeRaster)




