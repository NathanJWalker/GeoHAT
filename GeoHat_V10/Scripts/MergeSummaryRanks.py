#MergeRankSummaries.py
#
# Description: Merges rank summaries and attaches values as
#  an attribute table to the patch raster
#
# Inputs: <Patch raster> <Geometry CSV> <Connectivity CSV>
# Outputs: <Patch composite>
#
# June 2012, John.Fay@duke.edu
#

import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Input variables
patchRaster = sys.argv[1]

geometryTbl = sys.argv[2]
geometryWt = float(sys.argv[3])
connectivityTbl = sys.argv[4]
connectivityWt = float(sys.argv[5])
efficiencyTbl = sys.argv[6]
efficiencyWt = float(sys.argv[7])
threatTbl = sys.argv[8]
threatWt = float(sys.argv[9])
biodiversityTbl = sys.argv[10]
biodiversityWt = float(sys.argv[11])

prefixes = ("geom", "conn","effic", "vuln", "bio")
inputTbls = (geometryTbl, connectivityTbl,efficiencyTbl, threatTbl, biodiversityTbl)
inputWts = (geometryWt, connectivityWt,efficiencyWt, threatWt, biodiversityWt)

#Output variables
outputRaster = sys.argv[12]

##-FUNCTIONS-
def msg(txt):print txt; arcpy.AddMessage(txt); return

##-PROCESSING-
#Create the output raster
msg("Creating output raster: %s" %outputRaster)
outRaster = arcpy.CopyRaster_management(patchRaster,outputRaster)
#Initiate the calcString - used for calculating final ranks
calcString = ''
#Loop through each attribute group
for prefix in prefixes:
    msg("Working on %s" %prefix)
    wt = float(inputWts[prefixes.index(prefix)] / 100.0)
    tbl = inputTbls[prefixes.index(prefix)]
    # Add a field to the ouput raster
    arcpy.AddField_management(outRaster,prefix+"_Wt","DOUBLE",10,2)  #Weight value
    arcpy.AddField_management(outRaster,prefix+"_Rank","DOUBLE",10,2)       #Rank
    # Join the table to the outRaster
    arcpy.JoinField_management(outRaster,"VALUE",tbl,"PatchID",["WtdScore","Rank"])
    arcpy.CalculateField_management(outRaster,prefix+"_Wt","[WtdScore]")
    arcpy.CalculateField_management(outRaster,prefix+"_Rank","[Rank]")
    arcpy.DeleteField_management(outRaster,"WtdScore")
    arcpy.DeleteField_management(outRaster,"Rank")
    # Update the calcString
    calcString += "([%s_Wt] * %s) + " %(prefix,wt)

# Add final ranking
arcpy.AddField_management(outRaster,"FinalWt","DOUBLE",10,2)
arcpy.AddField_management(outRaster,"FinalRank","DOUBLE",10,2)
arcpy.CalculateField_management(outRaster,"FinalWt",calcString[:-3])
arcpy.CalculateField_management(outRaster,"FinalRank",calcString.replace("Wt","Rank")[:-3])
    


