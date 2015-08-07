#SummarizePatchAttributes.py
#
# Description: Applies multi-criteria decision framework to summarize
#  patch threat attributes. Normalizes values for each attributes,
#  applies the weight and adds the weighted, normalized values together
#
# Inputs: <Patch Threat CSV> <User weightings for each variable>
# Outputs: Patch Threat rank
#
# July 2012, john.fay@duke.edu

# Import system modules
import sys, string, os, arcpy
import arcpy.sa as sa

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

##--VARIABLES--
#Input variables
inputCSV = sys.argv[1]
weights = sys.argv[2:-2]
method = "EQUAL_INTERVAL" # Can be switched to QUANTILE
#Output variable
patchTable = sys.argv[-2] # The last input is a boolean in the tool that allows for resetting values

##--FUNCTIONS--
def msg(txt): print txt; arcpy.AddMessage(txt); return

##--PROCESSES--
#Create a table from the CSV file
msg("Creating attribute table")
attributeTbl = arcpy.CopyRows_management(inputCSV, "in_memory/attributeTbl")

#Get field names for everything but the patch id field (i.e. the first field)
fldNames = []
for f in arcpy.ListFields(attributeTbl)[2:]:
    fldNames.append(str(f.name))

#Calculate summary stats for each field
msg("Analysing values to compute normalizations")
statFlds = []
for f in fldNames:
    msg("...%s" %f)
    statFlds.append([f,"MIN"])
    statFlds.append([f,"MAX"])
    statFlds.append([f,"RANGE"])
sumTbl = arcpy.Statistics_analysis(attributeTbl,"in_memory/sumTbl",statFlds)

#Create a dictionary of summary stats
statDict = {}
rec = arcpy.SearchCursor(sumTbl).next()
for f in fldNames:
    minVal = rec.getValue("MIN_" + f)
    maxVal = rec.getValue("RANGE_" + f)
    wt = weights[fldNames.index(f)]
    statDict[f] = (minVal, maxVal, wt)
del rec

#Add normalized scores, wtd scores, and rank to attributeTbl
arcpy.AddField_management(attributeTbl,"WtdScore","DOUBLE",10,2)
arcpy.AddField_management(attributeTbl,"Rank","LONG",10)

#Update values for each patch in the attributeTbl
msg("Normalizing values")
maxScore = 0
recs = arcpy.UpdateCursor(attributeTbl)
rec = recs.next()
while rec:
    wtdScore = 0
    for f in fldNames:
        val = rec.getValue(f)                   #Get attribute value for current field
        minVal, range, wt  = statDict[f]        #Get the min value, value range, and weight
        normVal = ((val - minVal) / range)*100  #Calculate normalized value
        wtdVal = normVal * (float(wt) / 100)                 #Apply weight to normalized value
        wtdScore += wtdVal                      #Tally weighted score for attribute
    rec.setValue("WtdScore",wtdScore)
    if wtdScore > maxScore: maxScore = wtdScore #Keep track of the highest score
    recs.updateRow(rec)
    rec = recs.next()

#Assign ranks to values EQUAL INTERVAL (across observed values, not absolute values)
if method == "EQUAL_INTERVAL":
    msg("Ranking values using equal intervals")
    msg("Max value is %2.4f" %maxScore)
    recs = arcpy.UpdateCursor(attributeTbl,'','','',"WtdScore A")
    rec = recs.next()
    while rec:
        score = rec.WtdScore        # The current record's score
        rank = int(round(score / maxScore * 10.0))
        if rank == 0: rank = 1
        rec.setValue("Rank",rank)   # Set the rank value
        recs.updateRow(rec)         # Apply the value
        rec = recs.next()
    del rec, recs
    
#Assign ranks to values QUANTILE
if method == "QUANTILE":
    msg("Ranking values")
    numRecs = int(arcpy.GetCount_management(attributeTbl).getOutput(0))
    breakPt = numRecs / 10
    rank = 1
    iterator = 0
    recs = arcpy.UpdateCursor(attributeTbl,'','','',"WtdScore A")
    rec = recs.next()
    while rec:
        iterator += 1               # Increase the iterator
        if iterator >= breakPt:     # If the iterator has hit a break point...
            iterator = 0            # ...Reset the iterator
            rank += 1               # ...Increase the rank value
        rec.setValue("Rank",rank)   # Set the value
        recs.updateRow(rec)         # Apply the value
        rec = recs.next()
    del rec, recs

#Delete fields
for f in fldNames:
    arcpy.DeleteField_management(attributeTbl,f)
arcpy.CopyRows_management(attributeTbl, patchTable)

##VALIDATION SCRIPT -- Copy and paste this into the script validation section
'''
class ToolValidator:
  """Class for validating a tool's parameter values and controlling
  the behavior of the tool's dialog."""

  def __init__(self):
    """Setup arcpy and the list of tool parameters."""
    import arcpy
    self.params = arcpy.GetParameterInfo()
    return

  def initializeParameters(self):
    """Refine the properties of a tool's parameters.  This method is
    called when the tool is opened."""
    numParams = len(self.params)
    # Lock the last weight parameter as its value is auto calculated
    self.params[-3].enabled = False
    for i in range(1,numParams - 3):
      # Set initial values to equal (100 / number of weight attributes)
      self.params[i].value = 100.0 / float(numParams - 3)
      # Filter the parameters to values between 0 and 100
      self.params[i].filter.type = "Range"
      self.params[i].filter.list = [0.0,100.0]
    return

  def updateParameters(self):
    """Modify the values and properties of parameters before internal
    validation is performed.  This method is called whenever a parmater
    has been changed."""
    numParams = len(self.params)
    # Sum of the weight values
    wtTotal = 0 
    for i in range(1,numParams - 3):
      wtTotal += float(self.params[i].value)
    # Set the locked weight parameter to 100 minus the wt total
    self.params[-3].value = 100 - wtTotal
    #Reset values to defaults if clicked
    if self.params[-1].value == True:
      for i in range(1,numParams - 2):
        self.params[i].value = 100.0/float(numParams - 3)
        self.params[i].filter.type = "Range"
        self.params[i].filter.list = [0.0, 100.0]
      self.params[-1].value = False
    return

  def updateMessages(self):
    """Modify the messages created by internal validation for each tool
    parameter.  This method is called after internal validation."""
    return
'''