#---------------------------------------------------------------------------------
# CreateSubpatchEdgeList.py
#
# Description: Creates a list of subpatchIDs connected via habitat patches.
#  This edge list can be used to identify other conservation zones that
#  would benefit if a given zone is selected. 
#
# Inputs: <Subpatch raster> 
# Output: <EdgelistFN>
#  
# June 22, 2012
# John.Fay@duke.edu
#---------------------------------------------------------------------------------

# Import system modules
import sys, string, os, arcpy, math
import arcpy.sa as sa

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

# Input variables
subPatchRaster = sys.argv[1] #r'C:\WorkSpace\GHAT\GeoHAT_016_Squirrel\Data\SubPatches'#sys.argv[1]

# Output variables
edgeListFN = sys.argv[2] #r'C:\WorkSpace\GHAT\GeoHAT_016_Squirrel\Scratch\SubpatchEdges.csv'

# Script variables
scratchWS = arcpy.env.scratchWorkspace #"c:\\workspace\\GHAT\\geohat_016_squirrel\\Scratch"
subpatchCov= os.path.join(scratchWS,"SubpatchPoly")


##---FUNCTIONS---
def msg(txt):
    print txt
    arcpy.AddMessage(txt)
    return

##---PROCESSES---
# Convert raster to polygon
msg("Converting %s to polygons" %subPatchRaster)
tmpPoly = "in_memory/tmpPoly"
arcpy.RasterToPolygon_conversion(subPatchRaster,tmpPoly,"NO_SIMPLIFY")
dslvPoly =  "in_memory/dslvPoly"
arcpy.Dissolve_management(tmpPoly,dslvPoly,"grid_code")

# Convert the subpatch polygons to a coverage
msg("Converting subpatch zones to an Arc/Info coverage")
arcpy.FeatureclassToCoverage_conversion("%s POLYGON" %dslvPoly,subpatchCov)
subpatchCovPoly = arcpy.SelectData_management(subpatchCov,"polygon").getOutput(0)
subpatchCovArc = arcpy.SelectData_management(subpatchCov,"arc").getOutput(0)

# Select records into tmpTable
msg("Creating connectitivty table")
subPatchEdgeTbl = "in_memory/subPatchEdgeTbl"
selString = r'"$LEFTPOLYGON" > 1 AND "$RIGHTPOLYGON" > 1'
arcpy.TableSelect_analysis(subpatchCovArc,subPatchEdgeTbl,selString)

# Join ID codes to the subPatchedgeTable
msg("Joining IDs to connecitivty table")
arcpy.JoinField_management(subPatchEdgeTbl, "LEFTPOLYGON", subpatchCovPoly, "SUBPATCHPOLY#", "GRID_CODE")
arcpy.JoinField_management(subPatchEdgeTbl, "RIGHTPOLYGON", subpatchCovPoly, "SUBPATCHPOLY#", "GRID_CODE")

# Initialize output edge list
edgeList = open(edgeListFN, 'w')
edgeList.write("FromID, ToID\n")

# Write values to an edge list
msg("Writing edge list to %s" %edgeListFN)
rows = arcpy.SearchCursor(subPatchEdgeTbl,'"GRID_CODE" > 0 AND "GRID_CODE_1" > 0')
row = rows.next()
while row:
    fromID = row.GRID_CODE
    toID = row.GRID_CODE_1
    edgeList.write("%d, %d\n" %(fromID,toID))
    row = rows.next()


msg("Cleaning up")
del row, rows
edgeList.close()
arcpy.Delete_management(subpatchCov)

msg("Finished")