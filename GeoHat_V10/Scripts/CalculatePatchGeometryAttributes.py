#-----------------------------------------------------------------------------------
#CalculatePatchGeometryAttributes.py
#
# Description: Calculates attributes for each patch or sub-patch based on patch 
#  geometry. These include patch area, core area, core:area ratio, shape index,
#  and mean distance to patch edge. 
#
# Inputs: <Patch raster> 
# Outputs: <Patch attribute table (CSV format)>
#
# June 2012, John.Fay@duke.edu
#-----------------------------------------------------------------------------------

import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Input variables
patchRaster = sys.argv[1]        
edgeWidth = sys.argv[2]

#Output variables
outputTableFN = sys.argv[3]      
outputCoreRaster = sys.argv[4]

##--FUNCTIONS--
def msg(txt): print txt; arcpy.AddMessage(txt); return

def RenameField(inputFC,inFldName,outFldName,outFldAlias=''):
    '''Renames a field in the supplied table'''
    # Set outFldAlias to outFldName if blank
    if outFldAlias == '':
        outFldAlias = outFldName
    # Delete output field if it already exists
    if len(arcpy.ListFields(inputFC,outFldName)) > 0:
        arcpy.DeleteField_management(inputFC,outFldName)
    # Get the field properties
    curFld = arcpy.ListFields(inputFC,inFldName)[0]
    # Create the new field with the same properties
    arcpy.AddField_management(inputFC,outFldName,curFld.type,curFld.precision,curFld.scale,curFld.length,outFldAlias)
    # Copy the values
    arcpy.CalculateField_management(inputFC, outFldName, "!%s!" %inFldName,"PYTHON")
    # Delete the old field
    arcpy.DeleteField_management(inputFC,inFldName)
    return 

##--PROCESSING--
#Calculate area, perimeter, shape index
msg("Calculating patch shape index")
areaRaster = sa.ZonalGeometry(patchRaster,"VALUE","AREA")
perimRaster = sa.ZonalGeometry(patchRaster,"VALUE","PERIMETER")
idxRaster = 4.0 * sa.SquareRoot(areaRaster) / perimRaster #Shp index is the patch shape relative to a square)
shpIdxTbl = "in_memory\shpIndexTbl" 
result = sa.ZonalStatisticsAsTable(patchRaster,"VALUE",idxRaster,shpIdxTbl,"DATA","MAXIMUM")

#Convert area from sq m to HA
arcpy.CalculateField_management(shpIdxTbl,"AREA","!AREA! / 10000.0","PYTHON")

#Rename some fields
RenameField(shpIdxTbl,"VALUE","PatchID")
RenameField(shpIdxTbl,"AREA","PatchArea","Patch Area (HA)")
RenameField(shpIdxTbl,"MAX","ShapeIdx","Shape Index")
arcpy.DeleteField_management(shpIdxTbl,"COUNT")

#Create the core raster
nonHabitatBinary = sa.Con(sa.IsNull(patchRaster), 1)
arcpy.AddMessage("...calculating distances from edge into patch")
eucDist = sa.EucDistance(nonHabitatBinary)
arcpy.AddMessage("Extracting core areas")
coreRaster = sa.SetNull(eucDist,patchRaster,"VALUE <= %s" %edgeWidth)

#Save the core raster, if asked
if not outputCoreRaster == '#':
    msg("Saving core areas to %s" %outputCoreRaster)
    coreRaster.save(outputCoreRaster)

#Calculate mean distance to patch edge for each patch
msg("Calculating mean distance to edge")
dstToEdgeTbl = "in_memory/Dist2EdgeTbl"
result = sa.ZonalStatisticsAsTable(patchRaster,"VALUE",eucDist,dstToEdgeTbl,"DATA","MEAN")
RenameField(dstToEdgeTbl,"MEAN","DistToEdge","Mean distance to edge")
arcpy.JoinField_management(shpIdxTbl,"PatchID",dstToEdgeTbl,"VALUE",["DistToEdge"])

#Calculate core:area ratio
msg("Calculating patch core:area ratio")
coreAreaRaster = sa.Float(sa.Lookup(coreRaster,"COUNT")) / sa.Float(sa.Lookup(patchRaster,"COUNT"))
coreAreaTbl = "in_memory\CoreAreaTbl"
coreAreaTable = sa.ZonalStatisticsAsTable(patchRaster,"VALUE",coreAreaRaster,coreAreaTbl,"DATA","MAXIMUM")
arcpy.CalculateField_management(coreAreaTable,"AREA","!AREA! / 10000.0","PYTHON")
RenameField(coreAreaTbl,"AREA","CoreArea","Core Area (HA)")
RenameField(coreAreaTbl,"MAX","CAratio","Core Area ratio")
arcpy.JoinField_management(shpIdxTbl,"PatchID",coreAreaTable,"VALUE",["CoreArea","CAratio"])

# If output is a DBF file, save as dbf file
if outputTableFN[-3:] == "dbf":
    msg("Writing patch geometry attributes to %s" %outputTableFN)
    arcpy.CopyRows_management(shpIdxTbl,outputTableName)
else:
    # Otherwise, write to the output CSV Table
    msg("Writing patch geometry attributes to %s" %outputTableFN)
    outTable = open(outputTableFN, 'w')
    outTable.write("PatchID,PatchArea_HA,CoreArea_HA,AvgDistToEdge,CoreAreaRatio,ShapeIndex\n")
    recs = arcpy.SearchCursor(shpIdxTbl)
    rec = recs.next()
    while rec:
        patchID = rec.PatchID
        patchArea = rec.PatchArea
        coreArea = rec.CoreArea
        caRatio = rec.CAratio
        shpIndex = rec.ShapeIdx
        dist2Edge = rec.DistToEdge
        if str(coreArea).isalpha():
            coreArea = 0.0
            caRatio = 0.0
        outTable.write("%d,%2.2f,%2.2f,%2.1f,%2.4f,%2.5f\n" %(patchID,patchArea,coreArea,dist2Edge,caRatio,shpIndex))
        rec = recs.next()
    del rec, recs
    outTable.close()

