#-------------------------------------------------------------
#ExtractDataFromSDE.py
#
# Description: Extracts data subsets from the NC SDE server.
#  Outputs are masked and set to the extent of the supplied
#  mask polygon feature. 
#
# Inputs: Mask Poly
# Outputs: Several see below
#
# July 10, 2012; john.fay@duke.edu
#-------------------------------------------------------------

import sys, os, arcpy
from arcpy import sa

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

## Input variables
SDEfile = sys.argv[1]   # NC.sde file 
maskPoly = sys.argv[2]  # Mask polygon used to set extent and mask outputs

## Output variables
maskRaster = sys.argv[3] #r'C:\WorkSpace\FaySVN\GeoHAT\Data\SFCatawba\mask.img'
nlcdOutput = sys.argv[4] #r'C:\WorkSpace\FaySVN\GeoHAT\Data\SFCatawba\nlcd.img'
elevOutput = sys.argv[5] #r'C:\WorkSpace\FaySVN\GeoHAT\Data\SFCatawba\elevation.img'
fdirOutput = sys.argv[6] #r'C:\WorkSpace\FaySVN\GeoHAT\Data\SFCatawba\flowdir.img'
faccOutput = sys.argv[7] #r'C:\WorkSpace\FaySVN\GeoHAT\Data\SFCatawba\flowacc.img'
flowLinesOutput = sys.argv[8] #r'C:\WorkSpace\FaySVN\GeoHAT\Data\SFCatawba\flowlines.shp'
hydgrpOutput = sys.argv[9] #r'C:\WorkSpace\FaySVN\GeoHAT\Data\SFCatawba\hydrogroup.img'
catchmentOutput = sys.argv[10] #r'C:\WorkSpace\FaySVN\GeoHAT\Data\SFCatawba\Catchments.img'
protAreasOutput = sys.argv[11] #r'C:\WorkSpace\FaySVN\GeoHAT\Data\SFCatawba\protareas.img'


## --FUNCTIONS--
def msg(txt): print txt; arcpy.AddMessage(txt); return

## --PROCESSES--
#Get source rasters (located in SDE file) **NEED TO HANDLE ERRORS WHEN THESE AREN'T FOUND**
nlcdInput = SDEfile + "\\NC.DBO.NLCD2006"
elevInput = SDEfile + "\\NC.DBO.ELEVATION"
fdirInput = SDEfile + "\\NC.DBO.FDR"
faccInput = SDEfile + "\\NC.DBO.FAC"
fLineInput = SDEfile + "\\nc.DBO.NHD_FD\\nc.DBO.NHDFlowlines"
hgrpInput = SDEfile + "\\NC.DBO.HYDROGROUP"
nhdCatInput = SDEfile + "\\NC.DBO.CATCHMENT"
protAreas = SDEfile + "\\NC.NC_ONEMAP.lmcos"

#Set environment settings
cellSize = arcpy.Raster(elevInput).meanCellHeight
msg("Setting cell size to %s" %cellSize)
arcpy.env.snapRaster = elevInput
msg("Setting snap raster size to %s" %elevInput)
arcpy.env.extent = arcpy.Describe(maskPoly).extent
msg("Setting extent to %s" %elevInput)
arcpy.env.outputCoordinateSystem = arcpy.Describe(elevInput).SpatialReference
msg("Setting spatial reference to %s" %elevInput)

#Create a maskRaster from the maskPoly
msg("Creating mask raster")
fld = arcpy.ListFields(maskPoly)[0].name
arcpy.FeatureToRaster_conversion(maskPoly,fld,maskRaster,cellSize)

#Set the mask to the mask raster
arcpy.env.mask = maskRaster

#Extract datasets by mask
if nlcdOutput <> "#":
    msg("Extracting NLCD to %s" %nlcdOutput)
    rasterLyr = arcpy.MakeRasterLayer_management(nlcdInput)
    outputRaster = sa.ExtractByMask(rasterLyr,maskRaster)
    outputRaster.save(nlcdOutput)
if elevOutput <> "#":
    msg("Extracting elevation to %s" %elevOutput)
    rasterLyr = arcpy.MakeRasterLayer_management(elevInput)
    outputRaster = sa.ExtractByMask(rasterLyr,maskRaster)
    outputRaster.save(elevOutput)
if fdirOutput <> "#":
    msg("Extracting flow direction to %s" %fdirOutput)
    rasterLyr = arcpy.MakeRasterLayer_management(fdirInput)
    outputRaster = sa.ExtractByMask(rasterLyr,maskRaster)
    outputRaster.save(fdirOutput)
if faccOutput <> "#":
    msg("Extracting flow accumulation to %s" %faccOutput)
    rasterLyr = arcpy.MakeRasterLayer_management(faccInput)
    outputRaster = sa.ExtractByMask(rasterLyr,maskRaster)
    outputRaster.save(faccOutput)
if flowLinesOutput <> "#":
    msg("Extracting stream flow lines to %s" %flowLinesOutput)
    #Create a feature layer from flow lines
    featLyr = arcpy.MakeFeatureLayer_management(fLineInput,"flowLines")
    #Select lines within the mask poly
    arcpy.SelectLayerByLocation_management(featLyr,"INTERSECT",maskPoly)
    #Write them to the output file
    arcpy.CopyFeatures_management(featLyr, flowLinesOutput)
    #Delete the layer
    arcpy.Delete_management(featLyr)
if hydgrpOutput <> "#":
    msg("Extracting soil hydrologic group to %s" %hydgrpOutput)
    rasterLyr = arcpy.MakeRasterLayer_management(hgrpInput)
    outputRaster = sa.ExtractByMask(rasterLyr,maskRaster)
    outputRaster.save(hydgrpOutput)
if catchmentOutput <> "#":
    msg("Extracting NHD+ catchments to %s" %catchmentOutput)
    rasterLyr = arcpy.MakeRasterLayer_management(nhdCatInput)
    outputRaster = sa.ExtractByMask(rasterLyr,maskRaster)
    outputRaster.save(catchmentOutput)
if protAreasOutput <> "#":
    msg("Extracting protected areas to %s" %protAreasOutput)
    arcpy.FeatureToRaster_conversion(protAreas, "LMCOS_ID", protAreasOutput, cellSize)