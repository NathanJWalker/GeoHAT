#CreateZipCodes.py
#
# Description: Creates a raster of biodiversity zip codes. Currently,
#  zip codes are created from Elevation, Topographic Convergence, and
#  solar exposure, but future versions will allow for zipcodes to be
#  created from site specific components such as soil pH, soil texture,
#  topographic position.
#   The range of each component is parsed into 5 classes. If EO data are
#  provided, (and EO BREAKS is selected as the parse method) natural breaks 
#  are found among the values found at plant EOlocations and used to create
#  the 5 classes. Alternatively, breaks can be established by equal interval
#  or by equal area (quantile).
#   ZipCodes are calculated by combining the classes of each component. To
#  preserve information, the first component is multiplied by 100, the second
#  by 10, and the third remains as is.
#   Furthermore, to emphasize extremes in the TCI and solar exposure components
#  the middle three classes are collapsed into a single class, so a class value
#  of 1 is the lowest 1/5th, a value of 2 includes the middle 3/5ths, and a value
#  of 3 includes the highest 5th.
#
#   An option to calculate ranking is provided. If selected, ZipCodes are given
#  a rank, from 1 to 5, based on the number of EOs observed anywhere within the
#  zipcode divided by the total area of that zipcode. Also included are total
#  EO count in each zipcode as well as the area weighted EO count (count /
#  zip code area). **SOME ADDITIONAL CODE COULD ALLOW FOR SELECTION OF RARE OR
#  THREATENED ELEMENT OCCURRENCES IN FUTURE VERSIONS**
#
# Inputs: <Elevation> <Flow Accumulation> <Element Occurrence Data>
#
# Outputs: <Zipcodes>
#
# June 28, 2012; John.Fay@duke.edu

import sys, os, math, copy, random, arcpy
import arcpy.sa as sa

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

# Inputs
elevRaster = sys.argv[1]    
zValue = sys.argv[2]        #Since NHD+ DEM is in cm, use 0.01
flacRaster = sys.argv[3]    #TO DO: Make optional, and derive from Elevation if not supplied 
EOs = sys.argv[4]           #Optional, since not always available
parseMethod = sys.argv[5]   #("EQUAL_INTERVAL","EQUAL_AREA", or "EO BREAKS" - if EO's supplied)
calcRankings = sys.argv[6]  # 
# Outputs
zipCodeRaster = sys.argv[7] 

## --ENVIRONMENT VARIABLES--
arcpy.env.extent = elevRaster

## --FUNCTIONS--
def msg(txt): print txt; arcpy.AddMessage(txt); return      
def getJenksBreaks( dataList, numClass ):
    '''From http://danieljlewis.org/2010/06/07/jenks-natural-breaks-algorithm-in-python/'''
    dataList.sort()
    
    mat1 = []
    for i in range(0,len(dataList)+1):
        temp = []
        for j in range(0,numClass+1):
            temp.append(0)
            mat1.append(temp)
            
    mat2 = []
    for i in range(0,len(dataList)+1):
        temp = []
        for j in range(0,numClass+1):
            temp.append(0)
            mat2.append(temp)
    for i in range(1,numClass+1):
        mat1[1][i] = 1
        mat2[1][i] = 0
        for j in range(2,len(dataList)+1):
            mat2[j][i] = float('inf')
    v = 0.0
    for l in range(2,len(dataList)+1):
        s1 = 0.0
        s2 = 0.0
        w = 0.0
        for m in range(1,l+1):
            i3 = l - m + 1
            
            val = float(dataList[i3-1])
            
            s2 += val * val
            s1 += val
            w += 1
            v = s2 - (s1 * s1) / w
            i4 = i3 - 1
            
            if i4 != 0:
                for j in range(2,numClass+1):
                    if mat2[l][j] >= (v + mat2[i4][j - 1]):
                        mat1[l][j] = i3
                        mat2[l][j] = v + mat2[i4][j - 1]
        mat1[l][1] = 1
        mat2[l][1] = v
        
    k = len(dataList)
    kclass = []
    for i in range(0,numClass+1):
        kclass.append(0)
        
    kclass[numClass] = float(dataList[len(dataList) - 1])
    
    countNum = numClass
    while countNum >= 2:
        print "rank = " + str(mat1[k][countNum])
        id = int((mat1[k][countNum]) - 2)
        print "val = " + str(dataList[id])
        
        kclass[countNum - 1] = dataList[id]
        k = int((mat1[k][countNum] - 1))
        countNum -= 1

    return kclass

def getRemap(jenksBreaks,outValues=None):
    '''Creates an arcpy remapRange object used for reclassifying a raster'''
    remap = sa.RemapRange([])
    remapTbl = remap.remapTable
    if outValues == None: outValues = range(1,len(jenksBreaks))
    for i in range(1, len(jenksBreaks)):
        remapTbl.append([jenksBreaks[i-1],jenksBreaks[i],outValues[i-1]])
    #Lop off the last comma and close the string
    return remap

## --PROCESSES--
# Solar Radiation
msg("Calculating insolation")
#solRaster = sa.Hillshade(elevRaster, 225, 35, "SHADOWS", zValue)
solRaster = (sa.Cos((sa.Aspect(elevRaster) - 45) * math.pi / 180.0) * -100) + 100
                   
# Topographic convergence index
msg("Calculating topographic convergence")
slopeRad = sa.Slope(elevRaster,"DEGREE",zValue) * math.pi / 180.0
tciRaster1 = sa.Ln(sa.Plus(flacRaster,30.0) / sa.Tan(slopeRad))
# Where slope is zero, set TCI to its max value
tciRaster = sa.Con(slopeRad, tciRaster1.maximum, tciRaster1, "Value = 0")

# Create class breaks according to the method selected
if parseMethod in ("EQUAL_INTERVAL","EQUAL_AREA"):
    msg("Using equal interval breaks")
    #Slice values
    msg("...decomposing values into equal quantiles")
    elevSlice = sa.Slice(elevRaster,5,parseMethod,1) * 100
    solSlice = sa.Slice(solRaster,5,parseMethod,1)
    tciSlice = sa.Slice(tciRaster,5,parseMethod,1)
    # Remap the extremes of the solar and tci rasters
    msg("...recoding group values")
    remap = sa.RemapValue([[1,1],[2,2],[3,2],[4,2],[5,3]])
    solRemap = sa.Reclassify(solSlice,"VALUE",remap) * 10
    tciRemap = sa.Reclassify(tciSlice,"VALUE",remap)
    # Combine into zip codes
    msg("...combining values into zip codes")
    msg("Computing zipcodes")
    zipCodes = elevSlice + solRemap + tciRemap
    zipCodes.save(zipCodeRaster)
    msg("Output saved to %s" %zipCodeRaster)
elif parseMethod == ("EO BREAKS"):
    msg("Using natural breaks informed by element occurrences")    
    # Create a feature class of Plant EOs with good precision
    whereClause = "\"UNCRT_DIST\" <= 1000 AND \"NAME_CATGY\" IN ( 'Vascular Plant', 'Nonvascular Plant', 'Natural Community')"
    plantEOs = arcpy.MakeFeatureLayer_management(EOs,"plantEOs",whereClause)

    # Find class breaks using EO locations
    msg("Extracting data at element occurrence locations")
    sampleTbl = "in_memory/SampleTbl"
    sa.Sample([elevRaster,solRaster,tciRaster],plantEOs,sampleTbl,"Nearest")

    # Get field names
    flds = arcpy.ListFields(sampleTbl)
    elevFld = flds[-3].name
    solFld = flds[-2].name
    tciFld = flds[-1].name

    # Create lists of values
    msg("Creating a list of values at EO locations")
    elevList = [];solList = [];tciList = []
    recs = arcpy.SearchCursor(sampleTbl)
    rec = recs.next()
    while rec:
        for fld, lst in [[elevFld,elevList],[solFld,solList],[tciFld,tciList]]:
            val = rec.getValue(fld)
            if type(val) == int or type(val) == float:
                lst.append(val)
        rec = recs.next()
    elevList.sort()
    solList.sort()
    tciList.sort()
    msg("%d samples used to create breaks" %(len(elevList)))

    # Elevation
    msg("Finding elevation class breaks")
    j = getJenksBreaks(elevList, 5)
    if j[-1] < elevList[-1]: j[-1] = elevList[-1]
    msg("Elevation breaks are: %s" %j)
    remap = getRemap(j,[100,200,300,400,500])
    elevReclass = sa.Reclassify(elevRaster,"VALUE",remap,"NODATA")

    # Solar radiation
    msg("Finding insolation class breaks")
    j = getJenksBreaks(solList, 5)
    if j[-1] < solRaster.maximum: j[-1] = solRaster.maximum
    msg("Insolation breaks are: %s" %j)
    remap = getRemap(j,[10,20,20,20,30])
    solarReclass = sa.Reclassify(solRaster,"VALUE",remap,"NODATA")

    # Topgraphic convergence
    msg("Finding TCI class breaks")
    j = getJenksBreaks(tciList, 5)
    if j[-1] < tciList[-1]: j[-1] = tciList[-1]
    msg("TCI breaks are: %s" %j)
    remap = getRemap(j,[1,2,2,2,3])
    tciReclass = sa.Reclassify(tciRaster,"VALUE",remap,"NODATA")

    # Combine into zip codes
    msg("Computing zipcodes")
    zipCodes = elevReclass + solarReclass + tciReclass
    zipCodes.save(zipCodeRaster)
    msg("Output saved to %s" %zipCodeRaster)
else:
    # Whoops! Somehow a bad selection was made...
    arcpy.AddError("%s is an incorrect break method" %parseMethod)
    calcRankings = 'false'

if calcRankings == 'true' and 'EOs' <> "#":
    # Calculate zip code rankings
    msg("Ranking element occurrences for zipcodes")
    #...Extract the EO points falling within the extent **THIS COULD BE FILTERED FOR RARE SPECIES HERE TOO!**
    msg("...extracting element occurrences with locational uncertainty < 1km")
    EOFilter = "\"UNCRT_DIST\" <= 1000"
    selEOs = arcpy.Select_analysis(EOs,"in_memory/SelectedEOs",EOFilter)
    #...Sample the EO points for zip code values
    tmpPoints = sa.Sample(zipCodes,selEOs,"in_memory/SampleResults")
    #...Calculate the number of points in each zipcode
    tmpTable = arcpy.Statistics_analysis(tmpPoints,"in_memory\\tmpTable",[["OBJECTID","COUNT"]],"zipcodes")
    # ...Join the results to the zip codes attribute table
    msg("Joining the EO rankings to the zip code attribute table")
    arcpy.JoinField_management(zipCodes,"VALUE",tmpTable,"zipcodes",["FREQUENCY"])
    #...Add fields
    arcpy.AddField_management(zipCodes,"EO_Count","LONG",5)
    arcpy.AddField_management(zipCodes,"wtd_Count","DOUBLE",10,3)
    arcpy.AddField_management(zipCodes,"EO_Rank","LONG",5)
    #...Calculate weighted frequency (count per 1000 km2)
    cellSizeIn1000KM = (zipCodes.meanCellHeight ** 2) / 1000000
    arcpy.CalculateField_management(zipCodes,"wtd_Count","[FREQUENCY] / ([COUNT] * %s / 1000.0)" %cellSizeIn1000KM)

    # Scale the rankings into equal intervals
    recs = arcpy.UpdateCursor(zipCodes,"","","","wtd_Count D")
    rec = recs.next()
    # Get the max value (first record since the update cursor is sorted)
    maxValue = rec.wtd_Count
    msg("...max richness is %d occurrences per 1000 km2" %round(maxValue))
    interval = maxValue / 5
    curInterval = 0
    curRank = 5
    while rec:
        curValue = rec.wtd_Count
        #Set the value of the EOCount field
        rec.EO_Count = rec.FREQUENCY
        #Check the current rank; decrease it if necessary
        if curValue < (maxValue - curInterval):
            curRank -= 1
            curInterval += interval
        #Assign the rank
        rec.EO_Rank = curRank
        # Update the record and move to the next
        recs.updateRow(rec)
        rec = recs.next()
    del rec, recs

    # Delete frequency field
    arcpy.DeleteField_management(zipCodes,"FREQUENCY")

    