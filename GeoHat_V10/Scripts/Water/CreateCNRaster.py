#CreateCNRaster.py
#
# Description: Combines SSURGO Hydrologic Group and NLCD to produce a Curve Number
#  raster based on values listed in http://www.cbrfc.noaa.gov/present/rdhm/sac_ssurgo.pdf.
#
# NOTE: The SSURGO soil hydologic group data have no values for Urban or Water areas. These
#       are assigned a hydrologic group code of 'D' based on the assumption that most water
#       is passed along as runoff and not infiltrated.       
#
# Inputs: <Hydrogroup raster> <NLCD raster> {Mask}
# Output: <Curve number raster>
#
# June 27, 2012; John.Fay@duke.edu

import sys, os, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = 1

#inputs
nlcdRaster = sys.argv[1] 
hgrpRaster = sys.argv[2] 

#output
outRaster = sys.argv[3] 

#Message function
def msg(txt): print txt; arcpy.AddMessage(txt); return

def createCNDict():
# make a dictionary of CN values; the key is the NLCD class and the
# values are a list of CN values for A|A/D, B|B/D, C|C/D, D hydro groups
    cnDict = {}
    cnDict[11] = ['100', '100', '100', '100'] #Water 
    cnDict[12] = ['95', '95', '95', '95'] #Ice/Snow 
    cnDict[21] = ['29', '48', '61', '69'] #Open Space 
    cnDict[22] = ['40', '56', '67', '74'] #Low Intensity 
    cnDict[23] = ['58', '70', '79', '83'] #Medium Intensity 
    cnDict[24] = ['70', '79', '84', '87'] #High Intensity 
    cnDict[31] = ['95', '95', '95', '95'] #Bare Rock/Sand/Clay 
    cnDict[32] = ['58', '72', '81', '87'] #Unconsolidated Shore 
    cnDict[41] = ['19', '39', '53', '61'] #Deciduous Forest 
    cnDict[42] = ['19', '39', '53', '61'] #Evergreen Forest 
    cnDict[43] = ['19', '39', '53', '61'] #Mixed Forest 
    cnDict[51] = ['34', '51', '64', '77'] #Dwarf Scrub Alaska 
    cnDict[52] = ['34', '52', '64', '72'] #Shrub/Scrub Areas dominated by shrubs 
    cnDict[61] = ['24', '44', '57', '66'] #Orchards/Vineyards/Other 
    cnDict[71] = ['29', '48', '61', '69'] #Grasslands/Herbaceous 
    cnDict[72] = ['28', '46', '58', '67'] #Sedge/Herbaceous Alaska only 
    cnDict[73] = ['47', '61', '72', '77'] #Lichens Alaska only 
    cnDict[74] = ['47', '61', '72', '77'] #Moss- Alaska only 
    cnDict[81] = ['29', '48', '61', '69'] #Pasture/Hay 
    cnDict[82] = ['45', '57', '66', '70'] #Cultivated Crops 
    cnDict[90] = ['100', '100', '100', '100'] #Woody Wetlands 
    cnDict[91] = ['100', '100', '100', '100'] #Palustrine Forested Wetland 
    cnDict[92] = ['100', '100', '100', '100'] #Palustrine Scrub/Shrub Wetland 
    cnDict[93] = ['100', '100', '100', '100'] #Estuarine Forested Wetland 
    cnDict[94] = ['100', '100', '100', '100'] #Estuarine Scrub/Shrub Wetland 
    cnDict[95] = ['100', '100', '100', '100'] #Emergent Herbaceous Wetlands 
    cnDict[96] = ['100', '100', '100', '100'] #Palustrine Emergent Wetland 
    cnDict[97] = ['100', '100', '100', '100'] #Estuarine Emergent Wetland 
    cnDict[98] = ['100', '100', '100', '100'] #Palustrine Aquatic Bed 
    cnDict[99] = ['100', '100', '100', '10'] #Estuarine Aquatic Bed
    return cnDict


def createHgrpLookup():
    # Creates a dictionary to convert hydrogroup values to index
    dict = {}
    dict[1] = 3 #D
    dict[2] = 2 #C
    dict[3] = 1 #V
    dict[4] = 2 #C/D 
    dict[5] = 0 #A
    dict[6] = 1 #B/D
    dict[7] = 0 #A/D
    return dict
    

cnDict = createCNDict()
hgrpDict = createHgrpLookup()

# Plug NoData values in hgrpRasters with a class of D
hgrpFix = sa.Con(sa.IsNull(hgrpRaster),1, hgrpRaster)

# combine the rasters
msg("Combining NLCD and Hydrologic group rasters")
comboRaster = sa.Combine([nlcdRaster,hgrpFix])
nlcdFld = arcpy.ListFields(comboRaster)[-2].name
hgrpFld = arcpy.ListFields(comboRaster)[-1].name

# add a new field to the comboRaster
msg("Adding curve number field to output raster")
arcpy.AddField_management(comboRaster,"CN","LONG",4)

# update values based on the dictionary
msg("Adding curve number values to output raster")
rows = arcpy.UpdateCursor(comboRaster)
row = rows.next()
while row:
    nlcdVal = row.getValue(nlcdFld) # NLCD value
    hgrpVal = row.getValue(hgrpFld) # Hydrologic group value
    hgrpIdx = hgrpDict[hgrpVal]     # Index to look up HGROUP recode column
    cnRow = cnDict[nlcdVal]         # List of values for the selected NLCD value
    cnVal = cnRow[hgrpIdx]          # Item in the list of values corresponding to hgrpIndex
    row.setValue("CN",cnVal)
    rows.updateRow(row)
    row = rows.next()
del row, rows

# Convert Curve number to time
#cnRaster = sa.Int(sa.Minus(100.0, sa.Lookup(comboRaster,"CN")) / 10)
cnRaster = sa.Lookup(comboRaster,"CN")
cnRaster.save(outRaster)
