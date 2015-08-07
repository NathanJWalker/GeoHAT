#CreateRankComposite.py
#
# Description: Creates a raster stack from each patch ranking 
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
CSVs = sys.argv[2]
sliceMethod = "EQUAL_INTERVAL"

#Output variables
patchStack = sys.argv[3]

##-FUNCTIONS-
def msg(txt):
    print txt
    arcpy.AddMessage(txt)

##-PROCESSING-
# Create the output workspace, if needed
scratchWS = arcpy.env.scratchWorkspace
if not os.path.exists(os.path.join(scratchWS,'tmpBands')):
    msg("Creating tmp workspce to hold band rasters")
    arcpy.CreateFolder_management(scratchWS,'tmpBands')
arcpy.env.scratchWorkspace = scratchWS + "\\tmpBands"

# Create a copy of the patch raster
msg("Creating base raster")
patchGrid = sa.Con(patchRaster,patchRaster)

# Join the attributes to the patchGrid
msg("...joining attributes")
for tbl in CSVs.split(";"):
    result = arcpy.JoinField_management(patchGrid,"VALUE",tbl,"PatchID",["Rank"])

# Loop through the fields and create individual rasters
msg("...creating bands")
attribFlds = arcpy.ListFields(patchGrid)
keepBands = []
keepNames = []
for fld in attribFlds:
    if not fld.name in ['Rowid','VALUE','GRID_CODE','grid_code','PATCHID','COUNT']:
        msg("   ...adding band %s" %fld.name)
        keepNames.append(fld.name)
        lookup = sa.Lookup(patchGrid,fld.name)
        keepBands.append(lookup)

# Merge rasters into the composite
msg("...merging bands")
arcpy.CompositeBands_management(keepBands,patchStack)

# Rename layers
msg("...renaming bands")
origWS = arcpy.env.workspace
arcpy.env.workspace = patchStack
lyrs = arcpy.ListRasters()
for lyr in lyrs:
    #band = os.path.basename(str(keepBands[lyrs.index(lyr)]))
    band = keepNames[lyrs.index(lyr)]
    arcpy.Rename_management(lyr, band)
arcpy.env.workspace = origWS
