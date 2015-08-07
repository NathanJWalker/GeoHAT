# -------------------------------------------------------------------------------
# pyJENKs.py (ArcGIS 9.2)
#
# Description: This tool uses attempts to classify a continuous
#              raster dataset into natural groupings based on element
#              occurrence locations. The assumption is that clusters
#              of plants and animals will prefer specific ranges within
#              the continuum of values of the variable supplied. For example,
#              if the sampled raster is a solar exposure, one might find a
#              set of species preferring high solar exposure and another set
#              preferring low, and yet another somethere in between. This script
#              uses the spread of observations in each and applies the Jenks
#              algorigthm to maximize goodness of fit within classes to
#              determine where class breaks might occur. It then applies these
#              breaks to produce a new raster dataset.
#
# Usage: jenks_arc.py <input table> <value field> <number of breaks>
#                     <input raster> <output raster>
#
# Created August 18, 2008
# John Fay
# -------------------------------------------------------------------------------

import random, copy, sys, os, arcgisscripting
gp = arcgisscripting.create()
'''
inputTable = sys.argv[1]      # Table containing sampled raster values at observation locations
valueField = sys.argv[2]      # Value field in the input table conataining values
numBreaks = int(sys.argv[3])  # Number of breaks for the output raster dataset
inputRaster = sys.argv[4]     # Input environmental raster to classify into binned values
outputRaster = sys.argv[5]    # Output binned raster
'''

def getValues(inputTable,valueField):
    '''Extracts values in an attribute field into a sorted list of values'''
    #import random, copy, sys, os, arcgisscripting
    #gp = arcgisscripting.create()
    theValueList = []
    recs = gp.SearchCursor(inputTable)
    rec = recs.next()
    while rec:
        theValueList.append(rec.getValue(valueField))
        rec = recs.next()
    theValueList.sort()
    msg("%d samples added to create breaks" %(len(theValueList)))
    return theValueList
           
def getQuantiles(theValues, numClasses):
    '''Breaks the values into separates lists of values for each quantile'''
    theValues.sort()
    theClasses = []
    if len(theValues)/2 < numClasses:
        print "number of classes must not exceed the number of values"
        return 0
    qInterval = len(theValues)/numClasses
    i = 0
    while i < len(theValues):
        theVals = theValues[i:i + qInterval]
        theClasses.append(theVals)
        i += qInterval
    msg("Initial class breaks set using quantiles...")
    return theClasses

def getEqualInterval(theValues, numClasses):
    '''Breaks the values into separates lists of values at equal intervals'''
    theValues.sort()
    min = theValues[0]
    max = theValues[-1]

    # eq interval - to start
    theIncrement = float((max - min)) / float(numClasses)
    theClasses = []
    for c in range(numClasses):
        valList = []
        for v in theValues:
            if (v >= (min + (c * theIncrement))) and (v < min + ((c + 1) * theIncrement)):
                valList.append(v)
        theClasses.append(valList)
    # add the highest class to the last class
    theClasses[-1].append(theValues[-1])
    msg("Initial class breaks set using equal intervals...")
    return theClasses

def getMeansList(theClasses):
    '''This script finds the means for a list of lists. It should be passed a list of Lists'''
    theMeansList = []
    for Clas in theClasses:
        if len(Clas) == 0:
            mean = (mean + theClasses[-1][-1])/ 2.0
        else:
            mean = sum(Clas) / float(len(Clas))
        theMeansList.append(mean)
    return theMeansList

def getTSSD(theClasses):
    '''This script calculates the total sum of squares deviation (TSSD) for items in a list'''
    theCentralValues = getMeansList(theClasses)
    i = 0
    TSSD = 0
    for Clas in theClasses:
        for Val in Clas:
            TSSD +=  (Val - theCentralValues[i])**2
        i = i + 1
    return TSSD


def SwapItems(theClassesList,theIndex,direction='down'):
    '''This script receives a list of lists and an index number and swaps the last value from the index class to the next
    For example a set of classes starting as [1,2,3,7],[8,9,10] switches to [1,2,3],[7,8,9,10]'''
    if ((theIndex + 1) >= (len(theClassesList)) or ((len(theClassesList[theIndex])) == 0 )):
        #print"All classes processed at this cycle OR Empty class"
        return theClassesList
    else:
        if direction == 'down':
            theClassesList[theIndex + 1].insert(0,theClassesList[theIndex].pop())
        else:
            theClassesList[theIndex].append(theClassesList[theIndex + 1].pop(0))
        #sort the new values before they are returned
        theClassesList[theIndex + 1].sort()
        theClassesList[theIndex].sort()
    return theClassesList
    

def getJenks(theClasses):
    optimal = 0
    while (optimal < 10): #Forcing 3 iterations to make sure classification is optimal. This may be highly redundant
        i = 0
        while i < len(theClasses) - 1:
            theError = getTSSD(theClasses)

            #First, swap down values and test the error change  
            theTestClasses = copy.deepcopy(theClasses)
            theTestClasses = SwapItems(theTestClasses, i, "down")
            theNewError = getTSSD(theTestClasses)
            
            #Check for improvements
            if (theNewError < theError):
                theClasses = copy.deepcopy(theTestClasses)
            else:
                # If no improvments, try swapping up
                theTestClasses = copy.deepcopy(theClasses)
                theTestClasses = SwapItems(theTestClasses, i,"up")
                theNewError = getTSSD(theTestClasses)
                if theNewError < theError:
                    theClasses = copy.deepcopy(theTestClasses)
            # Compare the next pair of adjancent classes
            i = i + 1
        # try another time
        optimal = optimal + 1
    return theClasses

def getBreaks(theClasses):
    breakList = [min(theClasses[0])]
    for i in theClasses:
        breakList.append("%2.6F" %max(i))
    return breakList

def ReclassRaster(inputRaster,outputRaster,jenksClasses):
    reclassString = ""
    i = 0
    minX = 0
    for Clas in jenksClasses:
        i += 1
        maxX = max(Clas)
        reclassString += '%2.6f %2.6f %d;' %(minX, maxX, i)
        minX = maxX + 0.000001
    gp.checkoutextension("Spatial")
    msg("reclassifying output raster")
    msg(reclassString)
    try:
        gp.reclassify_sa(inputRaster,"Value", reclassString, outputRaster, "NODATA")
        gp.CalculateStatistics_management(outputRaster)
        gp.BuildRasterAttributeTable_management(outputRaster)
    except:
        msg("Error in calculating breaks!")
        msg(gp.getmessages())
    return reclassString

'''
msg("Values extracted from %s using the %s field" %(inputTable, valueField))
msg(" to be binned into %d categories" %numBreaks)
msg(" %s to be reclassified into %s" %(inputRaster, outputRaster))
    
v = getValues(inputTable, valueField)
q = getQuantiles(v, numBreaks)
j = getJenks(q)
ReclassRaster(inputRaster, outputRaster, j)
'''