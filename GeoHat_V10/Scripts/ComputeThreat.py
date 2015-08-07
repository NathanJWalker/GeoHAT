#ComputeThreat.py
#
# Description: For each patch, computes the proximity to threat and the magnitude
#  of the threat to which it is near. In this version, the threat is development
#  (NLCD classes 22,23,24), and this script calculates three measurements of threat.
#  First is the fraction of development within 1200 m of each patch pixel (averaged
#  across all pixels in the patch). The second is the Euclidean distance between patch 
#  and the nearest developed pixel. And the third is a distance decayed value between
#  patch and development: patches with development closer to the patch is weighted greater
#  than development further away. (Development has 1% influence at 1200 m away.)
#
# Inputs: <Patch raster> <NLCD raster>
# Outputs: <Threat CSV table>
#
# July 2012, John.Fay@duke.edu
#

import sys, os, math, arcpy
import GeoHATutils
import arcpy.sa as sa

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Input variables
patchRaster = sys.argv[1] 
nlcdRaster = sys.argv[2] 
distanceThreshold = float(1200)
#Output variable
threatCSV_Filename = sys.argv[3] 

##--FUNCTIONS--
def msg(txt): print txt; arcpy.AddMessage(txt); return

##--PROCESSES--
# Extract development from NLCD
msg("Extracting developed area from NLCD")
devBinary = sa.Con(nlcdRaster,1,0,"VALUE IN (22,23,24)")

# Compute focal mean of development
msg("Calculating focal stats")
nbrHood = sa.NbrCircle(distanceThreshold, "MAP")
focalMean = sa.FocalStatistics(devBinary,nbrHood,"MEAN")

# Compute distance decay
msg("Computing distance decayed development")
devNodata = sa.Con(nlcdRaster,1,'',"VALUE IN (22,23,24)")
eucDist = sa.EucDistance(devNodata)
k = math.log(0.01) / distanceThreshold
devDecay = sa.Exp(eucDist * k)

# FOCAL MEAN: Compute zonal stats
msg("Computing patch threat values")
tmpTable = "in_memory/TmpTable"
sa.ZonalStatisticsAsTable(patchRaster,"VALUE",devBinary,tmpTable,'',"MEAN")
GeoHATutils.RenameField(tmpTable,"MEAN","FocalMean")

tmpTable2 = "in_memory/TmpTable2"
sa.ZonalStatisticsAsTable(patchRaster,"VALUE",devDecay,tmpTable2,'',"MEAN")
GeoHATutils.RenameField(tmpTable2,"MEAN","MeanDecay")
arcpy.JoinField_management(tmpTable,"VALUE",tmpTable2,"VALUE")

tmpTable3 = "in_memory/TmpTable3"
sa.ZonalStatisticsAsTable(patchRaster,"VALUE",devDecay,tmpTable3,'',"MINIMUM")
GeoHATutils.RenameField(tmpTable3,"MIN","Dist2Threat")
arcpy.JoinField_management(tmpTable,"VALUE",tmpTable3,"VALUE")

#Write to CSV file
msg("Writing patch threat values to %s" %threatCSV_Filename)
threatCSV = open(threatCSV_Filename, 'w')
threatCSV.write("PatchID, ThrtDist, ThrtWtdDist, ThrtNbrMean\n")
recs = arcpy.SearchCursor(tmpTable)
rec = recs.next()
while rec:
    patchID = rec.VALUE
    minDist = rec.Dist2Threat
    wtdDist = rec.MeanDecay
    focalMean = rec.FocalMean
    threatCSV.write("%d, %2.2f, %2.2f, %2.2f\n" %(patchID,minDist,wtdDist,focalMean))
    rec = recs.next()
del rec, recs
threatCSV.close()