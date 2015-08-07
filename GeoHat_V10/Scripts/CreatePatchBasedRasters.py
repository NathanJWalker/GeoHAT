#----------------------------------------------------------------------------------------------------------
#CreatePatchBasedRasters.py
#
# Description: Derives a set of rasters used to prioritize areas for conservation. These
#   include a cost-based sub-network raster, distance to habitat, distance to protected area
#   and a distance to patch edge. 
#
# Inputs: <Patch Raster> <Cost surface> <Subnet cost threshold> <Protected Areas Raster or Feature Class>
# Outputs: <Dist. to Edge> <Dist. to Habitat> <Dist. to Protected Area> <Subnetwork Raster>
#
# June 2012; John.Fay@duke.edu
#----------------------------------------------------------------------------------------------------------
## This script does too much. I'm considering breaking this into separate sub-models:
##  - Create patch cores
##  - Calculate patch geometry (area, core areas, edge-area ratio, shape-index)
##  - Calculate patch biodiversity support potential
##  - Calculate patch threat
##  - Calculate patch connected area


import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Input variables
patchRaster = sys.argv[1]       #r'C:\WorkSpace\GBAT2012\GHAT_V011\Data\Patches'
edgeWidth = sys.argv[2]         #60
costRaster = sys.argv[3]        #r'C:\WorkSpace\GBAT2012\GHAT_V011\Scratch\CostRaster'
costThreshold = sys.argv[4]     #10000
protAreaInput = sys.argv[5]     #r'C:\WorkSpace\GBAT2012\GHAT_V011\Data\LMCOS.shp'

#Output variables
dist2edgeRaster = sys.argv[6]   #r'C:\WorkSpace\GBAT2012\GHAT_V011\scratch\dist2edge'
corePatches = sys.argv[7]       #r'C:\WorkSpace\GBAT2012\GHAT_V011\scratch\corePatches'
dist2habRaster = sys.argv[8]    #r'C:\WorkSpace\GBAT2012\GHAT_V011\scratch\dist2hab'
subnetRaster = sys.argv[9]      #r'C:\WorkSpace\GBAT2012\GHAT_V011\scratch\subnet'
dist2protRaster = sys.argv[10]  #r'C:\WorkSpace\GBAT2012\GHAT_V011\scratch\dist2prot'

##--Process 1: Calculate distance to patch edge--
arcpy.AddMessage("Calculating distance to patch edge")
arcpy.AddMessage("...inverting habitat raster")
nonHabitatBinary = sa.Con(sa.IsNull(patchRaster), 1)
arcpy.AddMessage("...calculating distances from edge into patch")
eucDist = sa.EucDistance(nonHabitatBinary)
eucDist.save(dist2edgeRaster)

##--Process 2: Extract core areas (using distance to edge)
arcpy.AddMessage("Extracting core areas")
core = sa.SetNull(eucDist,patchRaster,"VALUE <= %s" %edgeWidth)
core.save(corePatches)

##--Process 3: Calculate cost distance away from patch
arcpy.AddMessage("Calculating cost distance from patches")
costDist2H = sa.CostDistance(patchRaster, costRaster)
costDist2H.save(dist2habRaster)

##-Process 4: Extract patch subnetwork areas (from distance to habitat)
arcpy.AddMessage("Extracting subnetworks")
subnetAreas = sa.SetNull(costDist2H,1,"VALUE > %s" %costThreshold)
subnetRegions = sa.RegionGroup(subnetAreas,"FOUR","WITHIN","NO_LINK")
subnetRegions.save(subnetRaster)

##--Process 5: Calculate cost distance away from protected areas
if dist2protRaster <> "#":
    arcpy.AddMessage("Calculating cost distance from protected areas")
    costDist2P = sa.CostDistance(protAreaInput, costRaster)
    costDist2P.save(dist2protRaster)