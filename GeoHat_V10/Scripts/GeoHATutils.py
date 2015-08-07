#GeoHATutils.py
#
# Utilities for Geospatial Habiat Assessment Tools. These include a
#  reporting function (msg) and a function for renaming fields.
#
# June 2012
# John Fay


def msg(txt='',severity="normal"):
    '''Writes messages both to arcpy and to the immediate window'''
    import arcpy
    print txt
    if severity == "normal":
        arcpy.AddMessage(txt)
    elif severity == "warning":
        arcpy.AddWarning(txt)
    elif severity == "error":
        arcpy.AddError(txt)
    return

def RenameField(inputFC,inFldName,outFldName,outFldAlias=''):
    import arcpy
    # Set outFldAlias to outFldName if blank
    if outFldAlias == '':
        outFldAlias = outFldName
    ### REJECT ALIASES ###
    outFldAlias = outFldName
    ### REJECT ALIASES ###
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