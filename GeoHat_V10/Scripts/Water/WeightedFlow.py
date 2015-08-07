#WeightedFlow.py
#
# Description: Calculates Curve Number weighted flow distance from streams. Each
#  cell in the output raster is assigne a value reflecting the decay-distance along
#  the flow path to the stream. As the flow path intersects cells with high curve
#  numbers, water is assumed to move faster along the cell 

# Import system modules
import sys, string, os, math, arcpy
import arcpy.sa as sa

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = 1

# inputs
cnRaster = sys.argv[1]          # SCS Curve number 
flowdirRaster = sys.argv[2]     # NHD+ Flow direction 
streamsRaster = sys.argv[3]     # Streams (from NDH+)
coverRaster = sys.argv[4]       # Areas to weigth
effectiveDistance = sys.argv[5] # Distance beyond which impacts are negligable
# outputs
flowlengthOutput = sys.argv[6]  # Decayed flow 
wtdOutput = sys.argv[7]         # Decay weighted output


# Message function
def msg(txt): print txt; arcpy.AddMessage(txt); return

##-PROCESSES-
# 1. Convert curve number to a weight: Int((100 - cn) / 10). Higher CN values
#  reflect increased runoff across the cell. This equation inverts the
#  CN value and scales it to values from 0 to 10. The resulting value reflects
#  a proxy for infiltration: higher values suggest more runoff stays in the cell
#  meaning less pollutants will leave the cell to downstream neighbors. 
msg("Calculating flow length weight from %s" %cnRaster)
weightRaster = sa.Int(sa.Divide(sa.Minus(100.0,cnRaster), 10.0) + 1)

# 2. Create a flow direction where streams are NoData. This enables calculation
#  of flow length to the stream vs to the stream outlet.
msg("Creating modified flow direction to calculate distance to streams")
fdRaster = sa.Con(sa.IsNull(streamsRaster),flowdirRaster)

# 3. Calculate cost-weighted flowlength. Cell values represent the infiltrated-
#  weighted distance along the flow path to a stream. Two paths may be the same
#  length, but if one goes through cells with high curve numbers (low weights)
#  it's path will be effectively shorter whereas a path going through cells with
#  low curve numbers (high weights) will be effectively longer - in terms of
#  suspended/dissolved pollutants reaching the stream. 
msg("Calculating weighted flow length")
wtdflRaster1 = sa.FlowLength(fdRaster,"DOWNSTREAM",weightRaster) + 30
#Set stream pixels to 0
wtdflRaster = sa.Con(sa.IsNull(streamsRaster), wtdflRaster1, 0)

# 4. Apply a decay coefficient to weighted flow lengths to create distance decay raster
#    k = math.log(0.01) / d, where d is obtained from the unweighted flow length(?)
msg("Calculating distance decayed rasters")
k = math.log(0.01) / float(effectiveDistance)   #k = decay coeffcient; decays to 1% at specified distance
ddFlowRaster = sa.Exp(sa.Times(wtdflRaster,k))  #Applies decay to distance values, output is now decayed distance
ddFlowRaster.save(flowlengthOutput)

### 4ALT. Apply decay coefficients to weighted flow lengths to create distance decay rasters
#for dist in distList:
#    k = math.log(0.01) / d
#    ddFlowRaster = sa.Exp(sa.Times(wtdflRaster,k))
#    wtdDeveloped = sa.Divide(ddFlowRaster,devRaster)

# 6. Create decay weighted developed and forested rasters
if wtdOutput <> "#":
    msg("Applying decay values to developed")
    wtdDeveloped = sa.Times(ddFlowRaster,coverRaster)
    wtdDeveloped.save(wtdflRaster)
