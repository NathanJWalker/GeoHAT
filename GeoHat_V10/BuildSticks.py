#---------------------------------------------------------------------------------
# BuildSticks.py
#
# Description: Create sticks (lines between connected patches, with appropriate weights),
# from edge list csv file
#
# Requires: NetworkX to be stored in script folder (or installed)
# Create Edge List tool must be run first
#
# Inputs: <edge list> <Patch raster> <scratch directory>
# Output: <Patch connected attribute table (CSV format)>
#  
# August 4, 2016
# Nathan Walker
# Building on code from John Fay
#
#---------------------------------------------------------------------------------

# Import modules
import sys, os, arcpy
import arcpy.sa as sa

##---FUNCTIONS---
# Message management
def msg(txt):  print msg; arcpy.AddMessage(txt); return

# Input variables
edgeList = arcpy.GetParameterAsText(0)
patchRaster = arcpy.GetParameterAsText(1)
sticks = arcpy.GetParameterAsText(3)

# Output variables
outdir = arcpy.GetParameterAsText(2)  

# set overwrite to true
arcpy.env.overwriteOutput = True

##---PROCESSES---

msg("Converting table to dbf")

# Convert csv to format that is editable and includes OID
edgeListDBF = arcpy.CopyRows_management(in_rows=edgeList, out_table=outdir + "/edgeList.dbf", config_keyword="")

# Add edge ID field
arcpy.AddField_management(in_table=edgeListDBF, field_name="EdgeID", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
arcpy.CalculateField_management(edgeListDBF, "EdgeID", "!OID!", "PYTHON_9.3", "")

msg("Converting patch raster to polygon")

# Convert Raster to Polygon
patch_RtoP = arcpy.RasterToPolygon_conversion(patchRaster, "in_memory/Patch_RtoP", "NO_SIMPLIFY", "Value")

# Add X and Y fields to polygons, representing patch centroid locations
arcpy.AddField_management(patch_RtoP, "X", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(patch_RtoP, "Y", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(patch_RtoP, "X", "!Shape.Centroid.X!", "PYTHON_9.3", "")
arcpy.CalculateField_management(patch_RtoP, "Y", "!Shape.Centroid.Y!", "PYTHON_9.3", "")

msg("Joining patch centroids to edge list")

# Join FromID to patch
arcpy.JoinField_management(edgeListDBF, "FromID", patch_RtoP, "GRIDCODE", "")

# Join ToID to patch
arcpy.JoinField_management(edgeListDBF, "ToID", patch_RtoP, "GRIDCODE", "")

msg("Convert X/Y start/end points to line")

# Create line from coordinates of From and To patches
arcpy.XYToLine_management(in_table=edgeListDBF, out_featureclass=sticks, startx_field="X", starty_field="Y", endx_field="X_1", endy_field="Y_1", line_type="GEODESIC", id_field="EdgeID", spatial_reference="PROJCS['WGS_1984_UTM_Zone_18S',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',10000000.0],PARAMETER['Central_Meridian',-75.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]];-5120900 1900 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision")

msg("Adding cost information to line")

# Join back cost information from edge list
arcpy.JoinField_management(sticks, "EdgeID", edgeListDBF, "EdgeID", "")

msg("Cleaning up")

# Delete extra fields
arcpy.DeleteField_management(in_table=sticks, drop_field="X;Y;X_1;Y_1;EdgeID_1;ID;GRIDCODE;X_12;Y_12;ID_1;GRIDCODE_1;X_12_13;Y_12_13")

# Delete temporary file
arcpy.Delete_management(in_data=outdir + "/edgeList.dbf", data_type="DbaseTable")
