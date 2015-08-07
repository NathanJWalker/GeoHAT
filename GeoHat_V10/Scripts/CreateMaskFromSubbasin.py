#----------------------------------------------------------------------
# CreateMaskFromSubbasin.py
#
# Description: Creates a mask raster and polygon from a selected
#  subbasin name generated from a hydrologic unit map located on
#  the SDE server.
#    The script selects the HUC 14s with the specified subbasin name
#  and then selects all the NHD+ catchments with their center in this
#  subbasin. Selecing the NHD+ catchments vs. the HUCs ensures proper
#  drainage as the hydrologic datasets use the NHD+ layers.
#
# **Requires the NC.sde file in the Data folder**
#
# Input: <Subbasin name>
# Output: <Raster mask> <Polygon mask>
#
# July 2012; john.fay@duke.edu
#----------------------------------------------------------------------

import sys, os, arcpy
from arcpy import sa

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

# Input variables
SDEfile = sys.argv[1]           # Path to the NC.SDE file
subbasinName = sys.argv[2]      # Selected sub basin

# Output variable
maskPoly = sys.argv[3]          # Mask polygon feature class created by the script

# Script variables
HUCs = os.path.join(SDEfile,"nc.DBO.hu")
Catchments = os.path.join(SDEfile,"nc.DBO.NHD_FD\\nc.DBO.catchments")

##--FUNCTIONS--
# Message function
def msg(txt): print txt; arcpy.AddMessage(txt); return

##--PROCESSES--
# Make a feature layer of the selected HUC
msg("Selecting the %s subbasin" %subbasinName)
HUClyr = arcpy.MakeFeatureLayer_management(HUCs,"HUClyr","SUBBASIN = '%s'" %subbasinName)

# Make a feature layer of the NHD catchments
msg("Finding NHD+ catchments falling within the %s subbasin" %subbasinName)
CATlyr = arcpy.MakeFeatureLayer_management(Catchments)
arcpy.SelectLayerByLocation_management(CATlyr,"HAVE_THEIR_CENTER_IN",HUClyr)

# Dissolve catchment features, saving to the output mask polygon
msg("Dissolving catchment features")
arcpy.Dissolve_management(CATlyr,maskPoly)

# Update user
msg("Mask polygon saved to: %s" %maskPoly)


