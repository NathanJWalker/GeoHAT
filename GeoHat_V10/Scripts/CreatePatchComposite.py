#CreatePatchComposite.py
#
# Description: Creates a raster stack from each patch attribute. The output
#  composite raster will have a band for each weight field in the input patch
#  raster with values rescaled from 0 to 255. The output is useful for
#  visualizing multiple patch attributes at once via a color composite.
#  The input patch raster should be the output of the Merge summary ranks
#  tool or at least have attribute fields with "wt_" prepended to the field names. 
#
# Inputs: <Patch attribute raster> 
# Outputs: <Patch composite>
#
# June 2012, John.Fay@duke.edu
#

import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Input variables
patchRaster =  sys.argv[1]

#Output variables
patchStack =  sys.argv[2]

##-FUNCTIONS-
def msg(txt): print txt; arcpy.AddMessage(txt)

##-PROCESSING-
# Loop through the fields and create individual raters
msg("...creating bands")
attribFlds = arcpy.ListFields(patchRaster, "*_Wt")
tmpBands = []
keepNames = []
for fld in attribFlds:
    msg("   ...adding band %s" %fld.name)
    keepNames.append(fld.name)
    lookup = sa.Lookup(patchRaster,fld.name)
    stretch = sa.Slice(lookup,256,"EQUAL_INTERVAL",0)
    tmpBands.append(stretch)

# Merge rasters into the composite
msg("...merging bands")
arcpy.CompositeBands_management(tmpBands,patchStack)

# Rename layers
msg("...renaming bands")
origWS = arcpy.env.workspace
arcpy.env.workspace = patchStack
lyrs = arcpy.ListRasters()
for lyr in lyrs:
    band = keepNames[lyrs.index(lyr)]
    arcpy.Rename_management(lyr, band)
arcpy.env.workspace = origWS
