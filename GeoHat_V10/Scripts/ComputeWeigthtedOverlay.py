#MultiCriteriaDecisionAnalysis.py
#
# Description: Multi-criteria decision analysis of patch attributes using
#  supplied attribute tables. Each table represents a single objective attribute
#  class (e.g. geometry, context, or threat). The user selects on attribute
#  from each class, the scaling method for the varible (how its range of values
#  is rescaled to values between 0 and 10), and its weight in determining the overall
#  patch score. 
#
# Inputs: <Patch stack> 
# Outputs: <Patch attribute table>
#
# June 2012, John.Fay@duke.edu
#

import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Input variables
patchStack = sys.argv[1]
wtDict = {}
wtDict['PATCHAREA_HA'] = float(sys.argv[2])   
wtDict['COREAREA_HA'] = float(sys.argv[3])    
wtDict['COREAREARATIO'] = float(sys.argv[4])     
wtDict['SHAPEINDEX'] = float(sys.argv[5])   
wtDict['DEGREE'] = float(sys.argv[6])       
wtDict['BETWEENNESS'] = float(sys.argv[7])   
wtDict['CLOSENESS'] = float(sys.argv[8])   
wtDict['CONNECTEDAREA'] = float(sys.argv[9])
wtDict['IDWAREA'] = float(sys.argv[10])

#Output variables
wtdSumRaster = sys.argv[11] 

##-PROCESSING-
# Get a list of rasters in the stack
origWS = arcpy.env.workspace
arcpy.env.workspace = arcpy.Describe(patchStack).CatalogPath
bandList = arcpy.ListRasters()
#arcpy.env.workspace = origWS

# Loop through the bands
first = True
for band in wtDict.keys():
    weight = wtDict[band]
    if weight == 0: continue
    arcpy.AddMessage("Band %s will comprise %s percent" %(band, weight))
    #Conver the band to a weighted input
    wtRaster = sa.Slice(band,100,"EQUAL_INTERVAL") * (weight / 100.0)
    if first: #If it's the first, then copy it
        wtdSum = sa.Con(wtRaster, wtRaster)
        first = False
    else:
        wtdSum = sa.Plus(wtdSum, wtRaster)

wtdSum.save(wtdSumRaster)
