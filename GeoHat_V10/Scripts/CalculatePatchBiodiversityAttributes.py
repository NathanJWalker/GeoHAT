#CalculatePatchBiodiversityAttributes.py
#
# Description: Calculates patch biodiversity metrics. These metrics include:
#  - Observed importance: The count of EOs occurring in a given patch and the
#    density of EOs (count over patch area).
#  - Potential importance: The count of zipcodes occurreing in a given patch
#    and the density of zip codes (count over patch area).
#  - Predicted importance: The mean importance rank of all the zip codes found
#    in a given patch. (The rank is derived from counting the EOs found within
#    a zip code divided by the zip code area, with a 5 being the highest).
#
# Inputs: <patch raster> <zipcode raster> <Element occurrence features>
# Outputs: Patch biodiversity importance CSV
#
# July 2012, john.fay@duke.edu

import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

## --I/O--
# Input variables
patchRaster = sys.argv[1]
zipcodeRaster = sys.argv[2]
EOs = sys.argv[3]
# Output variable
outputCSV = sys.argv[4]

## --FUNCTIONS--
def msg(txt): print txt; arcpy.AddMessage(txt); return      

## --PROCESSES--
#Compute variety of zip codes per patch and area weighted zip code frequency
##--THIS SHOULD BE UPDATED TO DO EVENNESS-- (by combining patches and zipcodes)
msg("Computing zip code richness")
#...Compute zonal variety of zipcodes on patches
masterTable = sa.ZonalStatisticsAsTable(patchRaster,"VALUE",zipcodeRaster,"in_memory/zipTable",'',"VARIETY")

#Compute mean zip importance
if not arcpy.ListFields(zipcodeRaster,"EO_Rank"):
    arcpy.AddWarning("No rank attribute in zipcode raster; cannot add zip importantce")
else:
    msg("Calculating mean zipcode importance for each patch")
    zipRank = sa.Lookup(zipcodeRaster,"EO_Rank")
    tmpTable = sa.ZonalStatisticsAsTable(patchRaster,"VALUE",zipcodeRaster,"in_memory/tmpTable",'',"MEAN")
    arcpy.JoinField_management(masterTable,"VALUE",tmpTable,"VALUE",["MEAN"])
    arcpy.Delete_management(tmpTable)

#Compute number of element occurrences per patch and area weighted frequency
msg("Ranking patches by element occurrences")
#...Extract the EO points falling within the extent **THIS COULD BE FILTERED FOR RARE SPECIES HERE TOO!**
msg("...extracting element occurrences with locational uncertainty < 1km")
EOFilter = "\"UNCRT_DIST\" <= 1000"
selEOs = arcpy.Select_analysis(EOs,"in_memory/SelectedEOs",EOFilter)
#...Sample the EO points for zip code values
tmpPoints = sa.Sample(patchRaster,selEOs,"in_memory/SampleResults")
#...Calculate the number of points in each zipcode
rasterNameFld = arcpy.ListFields(tmpPoints)[-1].name
tmpTable = arcpy.Statistics_analysis(tmpPoints,"in_memory\\tmpTable",[["OBJECTID","COUNT"]],rasterNameFld)
# ...Join the patch table to the tmpTable to get count (area)
arcpy.JoinField_management(masterTable,"VALUE",tmpTable,rasterNameFld,["FREQUENCY"])
arcpy.Delete_management(tmpTable)

#Output results to csv file
    #VALUE = patch ID
    #"FREQUENCY" = count of EOs in patch
    #"Count" = patch area (in cells)
    #"VARIETY" = number of different zip codes in patch
    #"MEAN" = mean zip rank (0 = no EOs found in zip; 5 = many)
msg("Writing data to %s" %outputCSV)
csvFile = open(outputCSV,'w')
csvFile.write("PatchID, EOCount, EODensity, ZipVariety, ZipDensity, MeanZipRank\n")
recs = arcpy.SearchCursor(masterTable)
rec = recs.next()
while rec:
    # Get values from record
    ID = rec.VALUE
    AreaHA = (rec.count ** 2) / 10000.0
    EOcount = rec.FREQUENCY
    if not rec.FREQUENCY: EOcount = 0
    EOdensity = EOcount/AreaHA
    ZipCount = rec.VARIETY
    if not rec.VARIETY: ZipCount = 0
    ZipDensity = ZipCount/AreaHA
    ZipRank = rec.MEAN
    # Write them
    csvFile.write("%d,%d,%2.2f,%d,%2.2f,%2.2f\n" %(ID,EOcount,EOdensity,ZipCount,ZipDensity,ZipRank))
    rec = recs.next()
del rec, recs
                  
csvFile.close()