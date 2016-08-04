#----------------------------------------------------------------------------
# CreateHabitatPatches.py
#
# Description: Converts a raster of habitat/NoData into a patch raster.
#  Patches of a minimum size can be excluded and patches boundaries can
#  be "cleaned" to remove jagged edges.  
#  
# Inputs: <Habitat raster> <Clean boundary boolean> {Minimum size} 
# Outputs: <Patch raster>
#
# June 15 2012
# John.Fay@duke.edu
#
# Edits: Nathan Walker
# August 4, 2016
# Give user choice of Queen/Rook's rule (4 or 8 cell adjacency), when defining patches:
# That is, is a cell connected to a patch if it's adjacent to that patch diagonally,
# or just if it's directly above/below/left/right of a patch cell?
#----------------------------------------------------------------------------

import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

# Input variables
HabRaster = sys.argv[1]     
CleanBoundary = sys.argv[2] 
MinPatchSize = sys.argv[3]
Neighbors = sys.argv[5] 

# Output variables
PatchRaster = sys.argv[4]

# Boundary clean the patches, if asked
if CleanBoundary == 'true':
    arcpy.AddMessage("Cleaning patch boundaries")
    HabRaster2 = sa.BoundaryClean(HabRaster,"NO_SORT","TWO_WAY")
else:
    HabRaster2 = HabRaster

# RegionGroup the HabSource into Patches
arcpy.AddMessage("Finding habitat clusters")
AllPatches = sa.RegionGroup(HabRaster2,Neighbors,"WITHIN","NO_LINK")

# Convert minimum patch size HA to cells (based on cell size of HabRaster)
arcpy.AddMessage("Converting minimum size to cells") 
cellSizeResult = arcpy.GetRasterProperties_management(HabRaster,"CELLSIZEX")
cellSize = float(cellSizeResult.getOutput(0))
minCellSize = round(10000.0 * float(MinPatchSize) / (cellSize ** 2))

# Remove patches below the cell size
arcpy.AddMessage("Removing patches smaller than %s HA (%d cells)" %(MinPatchSize, minCellSize))
keepPatches = sa.SetNull(AllPatches,1,'"COUNT" < %2.2f' %minCellSize)

# RegionGroup the kept patches
finalPatches = sa.RegionGroup(keepPatches,Neighbors,"WITHIN","NO_LINK")
arcpy.AddMessage("Saving result to %s" %PatchRaster)
#finalPatches.save(PatchRaster)

# this created weird artifacts with my data; I'm not sure why; I copied to different pixel depth to fix, then removed 0 values
arcpy.CopyRaster_management(in_raster=finalPatches, out_rasterdataset="in_memory/patch_copy", config_keyword="", background_value="", nodata_value="-2147483647", onebit_to_eightbit="NONE", colormap_to_RGB="NONE", pixel_type="16_BIT_UNSIGNED", scale_pixel_value="NONE", RGB_to_Colormap="NONE")
arcpy.gp.ExtractByAttributes_sa("in_memory/patch_copy", """"Value">0""", PatchRaster)
