#---------------------------------------------------------------------------------
# CalculatePatchEfficiency.py
#
# Description: Efficiency here is defined as a patch's potential contribution
#  to connecting existing protected areas. This is calculated three ways:
#  First, the number of protected areas within a cost threshold is tabulated
#  for each patch. Second, the amount of protected area within a threshold
#  distance is tabulated for each patch. And finally a distance weighted value
#  of protected area near each patch is tabulated. 
#
# Inputs: <Patch raster> <edge list> <maxDistance>
# Output: <Patch connected attribute table (CSV format)>
#  
# June 14, 2012
# John.Fay@duke.edu
#---------------------------------------------------------------------------------

# Import system modules
import sys, string, os, arcpy
import arcpy.sa as sa

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

# Input variables
protareaRaster = sys.argv[1]   
edgeListFN = sys.argv[2]    
maxDistance = int(sys.argv[3])   
k = math.log(0.1) / maxDistance ##Decay coefficient

# Output variables
outputFN = sys.argv[4]   

##---FUNCTIONS---
def msg(txt): print txt; arcpy.AddMessage(txt); return

##---PROCESSES---
msg("Computing protected area and distance weighted protected area from each patch")
#Create a table from the edge list
#edgeTbl = arcpy.CopyRows_management(edgeListFN,"in_memory/EdgeTbl")
edgeTbl = arcpy.TableSelect_analysis(edgeListFN,"in_memory/EdgtTbl",'"Cost" < %s' %maxDistance)
#Join protected area VAT to table
arcpy.JoinField_management(edgeTbl,"ProtAreaID",protareaRaster,"VALUE",["COUNT"])
#Calculate area and IDW area for each patch
arcpy.AddField_management(edgeTbl,"protArea","DOUBLE",10,2)
arcpy.AddField_management(edgeTbl,"idwArea","DOUBLE",10,2)
cellSize2HA = (arcpy.Raster(protareaRaster).meanCellWidth ** 2) / 10000
arcpy.CalculateField_management(edgeTbl,"protArea","[COUNT] * %s" %cellSize2HA)
#round(math.exp(k * distance) * patchAreas[toID])
arcpy.CalculateField_management(edgeTbl,"idwArea","[protArea] * Exp(%s * [Cost])" %k)

#Calculate summary stats on patch field
msg("Digesting results")
sumTbl = arcpy.Statistics_analysis(edgeTbl,"in_memory/sumTbl",[["protArea","SUM"],["idwArea","SUM"]],"PatchID")

# Create the output CSV file
msg("Writing outputs to %s" %outputFN)
connAreaFileObj = open(outputFN, 'w')
connAreaFileObj.write("patchID, PAreaCount, connectedPArea, idwPArea\n")

# Loop through patch IDs
recs = arcpy.SearchCursor(sumTbl)
rec = recs.next()
while rec:
    #Get row values
    patchID = rec.PatchID
    paCount = rec.FREQUENCY
    paArea = rec.SUM_protArea
    idwArea = rec.SUM_idwArea
    # Write values to the file
    connAreaFileObj.write("%d, %d, %2.4f, %2.4f\n" %(patchID, paCount, paArea, idwArea))
    # Move to next record
    rec = recs.next()

# Close the text file
connAreaFileObj.close()
msg("Finished")


    


