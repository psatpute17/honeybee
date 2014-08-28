# By Mostapha Sadeghipour Roudsari
# Sadeghipour@gmail.com
# Honeybee started by Mostapha Sadeghipour Roudsari is licensed
# under a Creative Commons Attribution-ShareAlike 3.0 Unported License.

"""
Read Annual Daylight Results I [Standard Daysim Results]

-
Provided by Honeybee 0.0.54

    Args:
        _illFilesAddress: List of .ill files
        _testPoints: List of 3d Points
        occupancyFiles_: Address to a Daysim occupancy file. You can find some example in \Daysim\occ. Use Honeybee Occupancy Generator to generate a custom occupancy file.
        lightingControlGroups_: Daysim lighting control groups. Daysim can model up to 10 lighting control groups together. Default is > cntrlType = 3, lightingPower = 250, lightingSetpoint = 300, ballastLossFactor = 20, standbyPower = 3, delayTime = 5
        _DLAIllumThresholds_: Illuminance threshold for Daylight Autonomy calculation in lux. Default is set to 300 lux.
        SHDGroupI_Sensors_: Senors for dhading group I. Use shadingGroupSensors component to prepare the inputs
        SHDGroupII_Sensors_: Senors for dhading group II. Use shadingGroupSensors component to prepare the inputs
        _runIt: set to True to run the analysis
    Returns:
        DLA: Daylight Autonomy > Percentage of the time during the active occupancy hours that the test point receives more daylight than the illuminance threshold.
        UDLI_Less_100: Useful Daylight illuminance > Percentage of time during the active occupancy hours that the test point receives less than 100 lux.
        UDLI_100_2000: Useful Daylight illuminance > Percentage of time during the active occupancy hours that the test point receives between 100 and 2000 lux.
        UDLI_More_2000: Useful Daylight illuminance > Percentage of time during the active occupancy hours that the test point receives more than 2000 lux.
        CDA: Continuous Daylight Autonomy > Similar to Daylight Autonomy except that the point receives illuminaceLevel/illuminace threshold for hours that illuminance level is less than the threshold.
        sDA: Spatial Daylight Autonomy > sDA is the percent of analysis points across the analysis area that meet or exceed _DLAIllumThresholds value (set to 300 lux for LEED) for at least 50% of the analysis period.
        annualProfiles: A .csv file generated by Daysim that can be used as an schedule for annual daylight simulation
"""
ghenv.Component.Name = "Honeybee_Read Annual Result I"
ghenv.Component.NickName = 'readAnnualResultsI'
ghenv.Component.Message = 'VER 0.0.54\nAUG_25_2014'
ghenv.Component.Category = "Honeybee"
ghenv.Component.SubCategory = "04 | Daylight | Daylight"
#compatibleHBVersion = VER 0.0.55\nAUG_25_2014
#compatibleLBVersion = VER 0.0.58\nAUG_20_2014
try: ghenv.Component.AdditionalHelpFromDocStrings = "2"
except: pass



from System import Object
import Grasshopper.Kernel as gh
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import Rhino as rc
import scriptcontext as sc
import os
import subprocess
import time
import shutil

"""
    def testPtsStr(self, testPoint, ptsNormal):
        return  '%.4f'%testPoint.X + '\t' + \
                '%.4f'%testPoint.Y + '\t' + \
                '%.4f'%testPoint.Z + '\t' + \
                '%.4f'%ptsNormal.X + '\t' + \
                '%.4f'%ptsNormal.Y + '\t' + \
                '%.4f'%ptsNormal.Z + '\n'
"""

def getFilelength(fileName):
    with open(fileName) as inf:
        for i, l in enumerate(inf):
            pass
    return i + 1

def isTheStudyOver(fileNames):
    while True:
        cmd = 'WMIC PROCESS get Commandline' #,Processid'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        cmdCount = 0
        for line in proc.stdout:
            if line.strip().startswith("cmd") and line.strip().endswith(".bat"):
                fileName = line.strip().split(" ")[-1].split("\\")[-1]
                # I should check the file names and make sure they are the right files
                if fileName in fileNames:
                    cmdCount += 1
        time.sleep(0.2)
        if cmdCount == 0:
            return
            
            
def main(illFilesAddress, testPts, testVecs, occFiles, lightingControlGroups, SHDGroupI_Sensors, SHDGroupII_Sensors, DLAIllumThresholds):
    
    if sc.sticky.has_key('honeybee_release'):

        try:
            if not sc.sticky['honeybee_release'].isCompatible(ghenv.Component): return -1
        except:
            warning = "You need a newer version of Honeybee to use this compoent." + \
            " Use updateHoneybee component to update userObjects.\n" + \
            "If you have already updated userObjects drag Honeybee_Honeybee component " + \
            "into canvas and try again."
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, warning)
            return -1
            
        hb_folders = sc.sticky["honeybee_folders"]
        hb_RADPath = hb_folders["RADPath"]
        hb_RADLibPath = hb_folders["RADLibPath"]
        hb_DSPath = hb_folders["DSPath"]
        hb_DSCore = hb_folders["DSCorePath"]
        hb_DSLibPath = hb_folders["DSLibPath"]
    
    else:
        msg = "You should first let Honeybee to fly first..."
        
        return msg, None
    
    daysimHeaderKeywords = ["project_name", "project_directory", "bin_directory", "tmp_directory", "Template_File",
        "place", "latitude", "longitude", "time_zone", "site_elevation", "time_step",
        "wea_data_short_file", "wea_data_short_file_units", "lower_direct_threshold", "lower_diffuse_threshold",
        "output_units", "sensor_file_unit", "material_file", "geometry_file", 
        "radiance_source_files", "sensor_file", "viewpoint_file", "AdaptiveZoneApplies", "dgp_image_x_size", "dgp_image_y_size",
        "ab", "ad", "as", "ar", "aa", "lr", "st", "sj", "lw", "dj", "ds", "dr", "dp", 
        "occupancy", "minimum_illuminance_level", "daylight_savings_time", "shading", "electric_lighting_system",
        "sensor_file_info", "daylight_autonomy_active_RGB", "electric_lighting", "direct_sunlight_file", "thermal_simulation",
        "user_profile", "PNGScheduleExists" ]
    
    # I will remove this function later and just use WriteDS class
    
    
    class genDefaultLightingControl(object):
        
        def __init__(self, sensorPts = [], cntrlType = 3, lightingPower = 250, lightingSetpoint = 300, ballastLossFactor = 20, standbyPower = 3, delayTime = 5):
            
            self.sensorPts = sensorPts
            self.lightingControlStr = self.getLightingControlStr(cntrlType, lightingPower, lightingSetpoint, ballastLossFactor, standbyPower, delayTime)
        
        def getLightingControlStr(self, cntrlType, lightingPower = 250, lightingSetpoint = 300, ballastLossFactor = 20, standbyPower = 3, delayTime = 5):
            
            cntrlType += 1
            
            # manual control
            lightingControlDict = {
            1 : 'manualControl',
            2 : 'onlyOffSensor',
            3 : 'onWhenOccupied',
            4 : 'dimming',
            5 : 'onlyOffSensorAndDimming',
            6 : 'onWithDimming'}
            
            lightingStr = `cntrlType` + " " + lightingControlDict[cntrlType] + " " + `lightingPower` + " 1 "
            
            if cntrlType != 1:
                lightingStr += `standbyPower` + " "
            
            if cntrlType > 3:
                lightingStr += `ballastLossFactor` + " " + `lightingSetpoint` + " "
            
            if cntrlType != 1 and cntrlType!=4:
                lightingStr += `delayTime`
            
            lightingStr += "\n"
            
            return lightingStr
    
    
    
    def isSensor(testPt, sensors):
        for pt in sensors:
            if pt==None: return False
            if pt.DistanceTo(testPt) < sc.doc.ModelAbsoluteTolerance:
                # this is a senor point
                return True
        # not a sensor
        return False
    
    
    
    msg = str.Empty
    
    # PREPARATION/CHECKING THE INPUTS #
    
    # number of spaces
    # this component considers each branch as a separate space and will generate
    # a separate heading file for each space and generate a separate set of results
    numOfSpaces = testPts.BranchCount
    
    # number of total points
    numOfPts = testPts.DataCount
    
    # set up illuminance levels for the spaces if they are not already set
    if len(DLAIllumThresholds)==0: DLAIllumThresholds = [300] * numOfSpaces
    
    # check for occupancy file
    if len(occFiles)!=0:
        for fileName in occFiles:
            try:
                if not os.path.isfile(fileName):
                    msg = "Can't find the occupancy file: " + fileName
                    return msg, None
            except:
                msg = "Occupancy file address is not valid."
                return msg, None
    else:
        daysimOccFile = os.path.join(sc.sticky["Honeybee_DefaultFolder"], "DaysimCSVOCC\\userDefinedOcc_9to17.csv")
        occFiles = [daysimOccFile] * numOfSpaces
        if not os.path.isfile(daysimOccFile):
            msg = "Can't find the default occupancy file at: " + daysimOccFile + \
                  "\nYou can generate an occupancy file and connect the file address to occupancyFiles_ input."
            return msg, None
        
    # separate daylighting controls for each space
    
    class SHDGroupSensors(object):
        def __init__(self, sensorsList):
            self.intSensors = sensorsList[0]
            self.extSensors = sensorsList[1]
    
    lightingControls = []
    SHDGroupISensors = []
    SHDGroupIISensors = []
    originalIllFiles = []
    testPoints = []
    testVectors = []
    numOfPtsInEachSpace = []
    # collect the data for spaces
    for branchNum in range(numOfSpaces):
        
        ptList = list(testPts.Branch(branchNum))
        
        testPoints.append(ptList)
        
        numOfPtsInEachSpace.append(len(ptList))
        
        try: testVectors.append(list(testVecs.Branch(branchNum)))
        except: testVectors.append([rc.Geometry.Vector3d.ZAxis] * testPts.Branch(branchNum).Count)
        
        try: lightingControls.append(list(lightingControlGroups.Branch(branchNum)))
        except: lightingControls.append([genDefaultLightingControl()])
        try: SHDGroupISensors.append(SHDGroupSensors(SHDGroupI_Sensors.Branch(branchNum)))
        except: SHDGroupISensors.append(None)
        try: SHDGroupIISensors.append(SHDGroupSensors((SHDGroupII_Sensors.Branch(branchNum))))
        except: SHDGroupIISensors.append(None)
    
    for branchNum in range(illFilesAddress.BranchCount):
        try: originalIllFiles.append(list(illFilesAddress.Branch(branchNum)))
        except: pass
    
    # sort the ill files based on their names
    # this only matter in case of multiple ill files produced by Honeybee
    originalIllFilesSorted = []
    for illFiles in originalIllFiles:
        try:
            illFiles = sorted(illFiles, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-1]))
            originalIllFilesSorted.append(illFiles)
        except:
            originalIllFilesSorted = originalIllFiles
    
    
    # number of points should be the same in all the illfile lists
    # that's why I just try the first list of the ill files
    numOfPtsInEachFile = []
    for illFile in originalIllFilesSorted[0]:
        with open(illFile, "r") as illInf:
            for lineCount, line in enumerate(illInf):
                if not line.startswith("#"):
                    numOfPtsInEachFile.append(len(line.strip().split(" ")) - 4)
                    break
    
    # find the current project directory that could be differnt from the old one
    projectDirectory = os.path.dirname(originalIllFilesSorted[0][0]) + "\\"
    #print numOfPtsInEachFile
    #print numOfPtsInEachSpace
    
    # make sure the number of points inside the ill file matches the number of points
    # inside the point list
    if sum(numOfPtsInEachFile) != numOfPts:
        msg = "Number of points in ill files: " + `sum(numOfPtsInEachFile)` + \
              " doesn't match the number of points in point files: " + `numOfPts`
        return msg, None
   
    # find the heading files and creat multiple ill files for the study
    heaFiles = []
    filePath =  os.path.dirname(originalIllFiles[0][0])
    try:
        files = os.listdir(filePath)
    except:
        msg = "Can't find the heading files (*.hea) at " + filePath
        return msg, None
    
    for fileName in files:
        if fileName.EndsWith(".hea"): heaFiles.append(fileName)

    # sort heading files and pt files
    try: heaFiles = sorted(heaFiles, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-1]))
    except: pass
    
    # copy one of the heading files to be modified
    heaFile = heaFiles[0]
    with open(os.path.join(filePath, heaFile), "r") as heainf:
        baseHea = heainf.readlines()
    
    modifiedHeaBase = str.Empty
    keywordsToBeRemoved = ["daylight_autonomy_active_RGB", "electric_lighting", "direct_sunlight_file", "thermal_simulation", "occupancy_profile",
                           "continuous_daylight_autonomy_active_RGB", "UDI_100_active_RGB", "UDI_100_2000_active_RGB", "UDI_2000_active_RGB",
                           "DDS_sensor_file", "DDS_file", "sensor_file_info"]
    
    linesToBePassed = []
    
    for lineCount, line in enumerate(baseHea):
        line = line.strip()
        if not lineCount in linesToBePassed:
            if line.split(" ")[0] == ("sensor_file"):
                modifiedHeaBase += "sensor_file [sensor_file]\n"
            elif line.startswith("occupancy-file"):
                modifiedHeaBase += "occupancy-file [occupancy]\n"
            elif line.startswith("occupancy"):
                modifiedHeaBase += "occupancy 5 [occupancy]\n"
            elif line.startswith("project_name"):
                projectName = line.split("project_name")[-1].strip()
                modifiedHeaBase += "project_name       [project_name]\n"
            elif line.startswith("project_directory"):
                # projectDirectory = line.split("project_directory")[-1].strip()
                modifiedHeaBase += "project_directory   " + projectDirectory + "\n"
            elif line.startswith("tmp_directory"):
                # create a place holder for the new temp file
                modifiedHeaBase += "tmp_directory      " + os.path.join(projectDirectory, "tmp[spaceCount]") + "\\\n"
                
            elif line.startswith("daylight_savings_time"):
                modifiedHeaBase += "daylight_savings_time 1\n"
            elif line.startswith("minimum_illuminance_level"):
                modifiedHeaBase += "minimum_illuminance_level [minimum_illuminance_level]\n"
            elif line.split(" ")[0] == "shading":
                
                # add the place holder for new dc and ill file names
                if line.find(".ill") >= 0: line = line.replace(".ill", "[spaceCount].ill")
                if line.find(".dc") >= 0: line = line.replace(".dc", "[spaceCount].dc")
                
                shadingStr = line + "\n"
                for lineC in range(lineCount + 1, len(baseHea)):
                    line = baseHea[lineC].strip()
                    if lineCount > len(baseHea) or line == str.Empty or line.startswith("=") or line.split(" ")[0] in daysimHeaderKeywords:
                        # good example here that I should have used the while loop instead!
                        break
                    else:
                        linesToBePassed.append(lineC)
                        # add the place holder for new dc and ill file names
                        if line.find(".ill") >= 0:
                            line = line.replace(".ill", "[spaceCount].ill")
                        
                        # I'm not sure if I really need to modify the .dc files
                        # based on the graph on daysim page it should only look
                        # for the ill files and not the dc files
                        if line.find(".dc") >= 0:
                            line = line.replace(".dc", "[spaceCount].dc")
                        
                        linesToBePassed.append(lineC)
                        shadingStr += line + "\n"
                
                modifiedHeaBase += shadingStr
                
                
                #modifiedHeaBase.append("minimum_illuminance_level [minimum_illuminance_level]\n")
            elif line.split(" ")[0] == "electric_lighting_system" or line.split(" ")[0] == "user_profile":
                # remove the lines related to electric lighting system as the new ones should be assigned
                for lineC in range(lineCount + 1, len(baseHea)):
                    line = baseHea[lineC].strip()
                    if lineCount > len(baseHea) or line == str.Empty or line.startswith("=") or line.split(" ")[0] in daysimHeaderKeywords:
                        # good example here that I should have used the while loop instead!
                        break
                    else:
                        linesToBePassed.append(lineC)
                
                
            elif line.split(" ")[0] in keywordsToBeRemoved:
                pass
            else:
                modifiedHeaBase += line + "\n"
    
    # clean the parts that are related to lighting control and schedule
    
    ##replace
    
    # re-write the ill files based on the number of points in each space
    # if the study is only for a single space then all the ill files should be merged
    # considering the structure of .ill files and the fact that the files can be really 
    # huge this part can take long. It is good to consider a new name for these files so
    # in case the user has already ran the study for this folder the script just use the
    # available files
    
    #
    # check if the files are already generated once
    firstRun = False
    newIllFileNamesDict = {}
    for shdGroupCounter, illFileList in enumerate(originalIllFilesSorted):
        newIllFileNamesDict[shdGroupCounter] = []
        for spaceCount in range(numOfSpaces):
            newIllFileName  = illFileList[0].split(".ill")[0] + "_space_" + str(spaceCount) + ".ill"
            newDcFileName  = illFileList[0].split(".ill")[0] + "_space_" + str(spaceCount) + ".dc"
            newIllFileNamesDict[shdGroupCounter].append(newIllFileName) #collect ill files to calculate sDA
            if not (os.path.isfile(newIllFileName) and os.path.isfile(newDcFileName)):
                firstRun = True
                break
    
    # open all the available ill files and put them in the dictionary
    if firstRun:
        for shdGroupCounter, illFileList in enumerate(originalIllFilesSorted):
            illFilesDict = {}
            newIllFilesDict = {}
            newIllFileNamesDict[shdGroupCounter] = []
            #illFileDict[shaidngGroupCounter]
            for counter, illFile in enumerate(illFileList):
                illfile = open(illFile, "r")
                illFilesDict[counter] = illfile
            
            # open new ill files for each space and put them in the same directory
            for spaceCount in range(numOfSpaces):
                newIllFileName  = illFileList[0].split(".ill")[0] + "_space_" + str(spaceCount) + ".ill"
                newIllFileNamesDict[shdGroupCounter].append(newIllFileName) #collect ill files to calculate sDA
                newIllFile = open(newIllFileName, "w")
                newIllFilesDict[spaceCount] = newIllFile
            
            # all the files will have the same length of 8760 lines for the hours of the year
            for line in range(8760):
                # merge the line from all the source file
                mergedLine = []
                for illFileKey in illFilesDict.keys():
                    line = illFilesDict[illFileKey].readline()
                    
                    if illFileKey==0:
                        dateInfo = line.strip().split(" ")[:4]
                    mergedLine.extend(line.strip().split(" ")[4:])
            
            
                # write the values to the target files
                for illFileKey in newIllFilesDict.keys():
                    line = " ".join(dateInfo + mergedLine[sum(numOfPtsInEachSpace[:illFileKey]):sum(numOfPtsInEachSpace[:illFileKey+1])])
                    newIllFilesDict[illFileKey].write(line + "\n")
            
            # close all the opened files
            for illFileKey in illFilesDict.keys(): illFilesDict[illFileKey].close()
            for illFileKey in newIllFilesDict.keys(): newIllFilesDict[illFileKey].close()
        
        # print numOfPtsInEachSpace
        # write the new .dc files for 
        for shdGroupCounter, illFileList in enumerate(originalIllFilesSorted):
            
            dcFilesDict = {}
            newDcFilesDict = {}
            
            #illFileDict[shaidngGroupCounter]
            lenOfDCFiles = []
            for counter, illFile in enumerate(illFileList):
                if illFile.endswith("_up.ill"):
                    dcFile = illFile.replace("_up.ill", ".dc")
                    
                elif illFile.endswith("_down.ill"):
                    dcFile = illFile.replace("_down.ill", ".dc")
                    
                else:
                    dcFile = illFile.replace(".ill", ".dc")
                    
                lenOfDCFile = getFilelength(dcFile) - 6 #Daysim files has 6 lines as header
                lenOfDCFiles.append(lenOfDCFile)
                dcfile = open(dcFile, "r")
                dcFilesDict[counter] = dcfile
            
            # open new ill files for each space and put them in the same directory
            for spaceCount in range(numOfSpaces):
                newDcFileName  = illFileList[0].split(".ill")[0] + "_space_" + str(spaceCount) + ".dc"
                newDcFile = open(newDcFileName, "w")
                newDcFilesDict[spaceCount] = newDcFile
            
            heading = str.Empty
            for line in dcFilesDict[0]:
                if line.startswith("#"):
                    #make one instance of heading
                    heading += line
                else:
                    newDcFilesDict[0].write(heading)
                    newDcFilesDict[0].write(line)
                    break
            
            pointCount = 1
            spaceCount = 0
            for dcFileKey in dcFilesDict.keys():
                for line in dcFilesDict[dcFileKey]:
                    if not line.startswith("#"):
                        # write the line
                        newDcFilesDict[spaceCount].write(line)
                        pointCount+=1
                        if pointCount == sum(numOfPtsInEachSpace[:spaceCount + 1]):
                            # end of the file, start a new file
                            spaceCount += 1
                            try: newDcFilesDict[spaceCount].write(heading)
                            except: pass
            
            # close all the opened files
            for dcFileKey in dcFilesDict.keys(): dcFilesDict[dcFileKey].close()
            for dcFileKey in newDcFilesDict.keys(): newDcFilesDict[dcFileKey].close()
        
    
    
    
    heaFileNames = []
    # write point files and heading files
    for spaceCount in range(numOfSpaces):
        tmpFolder = os.path.join(projectDirectory, "tmp_space_" + str(spaceCount))
        if not os.path.isdir(tmpFolder): os.mkdir(tmpFolder)
        subProjectName = projectName + "_space_" + str(spaceCount)
        ptsFileName = subProjectName + ".pts"
        modifiedHea = modifiedHeaBase
        
        with open(os.path.join(filePath, ptsFileName), "w") as ptsf:
            for ptCount, testPoint in enumerate(testPoints[spaceCount]):
                ptNormal = testVectors[spaceCount][ptCount]
                ptStr = '%.4f'%testPoint.X + '\t' + \
                        '%.4f'%testPoint.Y + '\t' + \
                        '%.4f'%testPoint.Z + '\t' + \
                        '%.4f'%ptNormal.X + '\t' + \
                        '%.4f'%ptNormal.Y + '\t' + \
                        '%.4f'%ptNormal.Z + '\n'
                
                ptsf.write(ptStr)
        
        # replace some of the values
        
        # replace sensor file with the new file
        if modifiedHea.find("[sensor_file]") >= 0:
            modifiedHea = modifiedHea.replace("[sensor_file]", ptsFileName)
        else:
            modifiedHea += "sensor_file " + ptsFileName + "\n"
        
        # occupancy file
        try:
            occFileFullPath = occFiles[spaceCount]
        except:
            occFileFullPath = occFiles[0]
        
        
        #copy occupancy file to the folder
        occFileName = os.path.basename(occFileFullPath)
        targetFile = os.path.join(projectDirectory, occFileName)
        
        if not os.path.isdir(targetFile):
            shutil.copy2(occFileFullPath, targetFile)
        
        if modifiedHea.find("[occupancy]") >= 0:
            modifiedHea = modifiedHea.replace("[occupancy]", occFileName)
        else:
            # pass
            modifiedHea += "occupancy-file " + occFileName + "\n"
            modifiedHea += "occupancy 5 " + occFileName + "\n"
        
        modifiedHea = modifiedHea.replace("[project_name]", subProjectName)
        
        # daylight saving
        if modifiedHea.find("daylight_savings_time") >= 0:
            pass
        else:
            modifiedHea += "daylight_savings_time 1\n"
        
        # illuminance level threshold
        try: illumT = DLAIllumThresholds[spaceCount]
        except: illumT = DLAIllumThresholds[0]
        
        if modifiedHea.find("[minimum_illuminance_level]") >= 0:
            modifiedHea = modifiedHea.replace("[minimum_illuminance_level]", str(illumT))
        else:
            modifiedHea += "minimum_illuminance_level " + str(illumT)+ "\n"
        
        
        # replace the file names for advanced shadings
        modifiedHea = modifiedHea.replace("[spaceCount]", "_space_" + str(spaceCount))
        
        # add user information
        modifiedHea += "user_profile 1\n" + \
        "active 100 1 1\n"
        
        try:
            lghtCtrls = lightingControls[spaceCount]
            lightingGroupSensors = []
        except:
            lghtCtrls = []
        
        if len(lghtCtrls)!=0:
            modifiedHea += "\n\nelectric_lighting_system " + str(len(lghtCtrls)) + "\n"
        
        for lightingControl in lghtCtrls:
            lightingGroupSensors.append(lightingControl.sensorPts)
            lightingControlDefinition = lightingControl.lightingControlStr
            modifiedHea += lightingControlDefinition
        
        # write sensor info
        modifiedHea += "\nsensor_file_info "
        
        for pt in testPoints[spaceCount]:
            sensorInfo = []
            
            # test shading group
            for groupCount, shdGroupSensor in enumerate([SHDGroupISensors[spaceCount], SHDGroupIISensors[spaceCount]]):
                if shdGroupSensor!=None:
                    if isSensor(pt, shdGroupSensor.intSensors):
                        sensorInfo.append('BG' + str(groupCount+1))
                    if isSensor(pt, shdGroupSensor.extSensors):
                        sensorInfo.append('BG' + str(groupCount+1) + '_Ext')
            
            # test lighting group
            for groupCount, lightingGroupSensor in enumerate(lightingGroupSensors):
                if lightingGroupSensor!=[] and isSensor(pt, lightingGroupSensor):
                    sensorInfo.append('LG' + str(groupCount+1))
            if len(sensorInfo)==0:
                modifiedHea += "0 "
            elif len(sensorInfo)==1:
                modifiedHea += sensorInfo[0] + " "
            else:
                modifiedHea += ",".join(sensorInfo) + " "
            
        # output files
        modifiedHea += "\n\n############################\n" + \
                       "# Daylighting Result Files #\n" + \
                       "############################\n"
        modifiedHea += "daylight_autonomy_active_RGB " + subProjectName +"_autonomy.DA\n"
        modifiedHea += "continuous_daylight_autonomy_active_RGB " + subProjectName +".CDA\n"
        modifiedHea += "UDI_100_active_RGB " + subProjectName +"_less_than_100.UDI\n"
        modifiedHea += "UDI_100_2000_active_RGB " + subProjectName +"_100_2000.UDI\n"
        modifiedHea += "UDI_2000_active_RGB " + subProjectName + "_more_than_2000.UDI\n"
        modifiedHea += "occupancy_profile " + subProjectName + "_occ_profile.csv\n"
        modifiedHea += "electric_lighting "  + subProjectName + "_electriclighting.htm\n"
        modifiedHea += "direct_sunlight_file "  + subProjectName + ".dir\n"
        modifiedHea += "thermal_simulation " + subProjectName + "_intgain.csv\n"
        #modifiedHea += "DDS_sensor_file "  + subProjectName +".CDA\n".dds\n"
        #modifiedHea += "DDS_file "  + subProjectName +".sen\n"
                           
                           
        heaFileName = subProjectName + ".hea"
        heaFileNames.append(heaFileName)
        with open(os.path.join(filePath, heaFileName), "w") as heaf:
            heaf.write(modifiedHea)
            
    # write batch files
    batchFileNames = []
    pathStr = "SET RAYPATH=.;" + hb_RADLibPath + ";" + hb_DSPath + ";" + hb_DSLibPath + ";\nPATH=" + hb_RADPath + ";" + hb_DSPath + ";" + hb_DSLibPath + ";$PATH\n"
    for heaFileName in heaFileNames:
        batchFileName = heaFileName.replace(".hea", ".bat")
        batchFileNames.append(batchFileName)
        with open(os.path.join(filePath, batchFileName), "w") as batchInf:
            batchFileStr = ":: Daysim Result Calculation - Generated by Honeybee\n\n"
            batchFileStr += pathStr
            # gen glare profile in case there is any dynamic shading systems!
            if len(originalIllFiles)>1:
                batchFileStr += ':: Glare Profile in The Case of Dynamic Shading Calculation\n' + \
                                'gen_directsunlight ' + os.path.join(filePath, heaFileName) + '\n'
            batchFileStr += ':: Generate the result files\n' + \
                            'ds_el_lighting.exe  ' + os.path.join(filePath, heaFileName) + '\n'
            
            batchInf.write(batchFileStr)
            
    # write a batch file and run the study
    ncpus = int(os.environ["NUMBER_OF_PROCESSORS"])
    if ncpus == 0: ncpus = 1
    
    #execute the batch files in parallel if there is enough CPUs!
    fileNames = []

    if ncpus >= numOfSpaces:
        for fileName in batchFileNames:
            batchFileName = os.path.join(filePath, fileName)
            fileNames.append(batchFileName)
            p = subprocess.Popen(r'start cmd /c ' + batchFileName , shell=True)
        
        isTheStudyOver(batchFileNames)
    else:
        for fileName in batchFileNames:
            batchFileName = os.path.join(filePath, fileName)
            os.system(batchFileName)
    
    # calculate sDA    
    
    #sDADict = {}
    
    #if len(newIllFileNamesDict.keys())!=1:
    #    warning = "This version of Honeybee doesn't consider dynamic blinds in sDA calculation!\n"
    #    w = gh.GH_RuntimeMessageLevel.Warning
    #    ghenv.Component.AddRuntimeMessage(w, warning)
    #    
    #for spaceCount, spaceIllFiles in enumerate(newIllFileNamesDict[0]):
    #    totalOccupancyHours = 0
    #    sDADict[spaceCount] = 0
        
    #    try: DLAIllumThreshold = DLAIllumThresholds[spaceCount]
    #    except: DLAIllumThreshold = DLAIllumThresholds[0]
    #    
    #    
    #    # open the file to read the values
    #    with open(spaceIllFiles, "r") as illInf:
    #        
    #        # import occupancy profile
    #        try: occFile = occFiles[spaceCount]
    #        except: occFile = occFiles[0]
    #        with open(occFile, "r") as occInFile:
    #            occupancyLines = occInFile.readlines()
    #            
    #        # each line represnt an hour
    #        for lineCount, line in enumerate(illInf):
    #            higherThanThreshold = 0
    #            # check the occupancy profile
    #            if int(occupancyLines[lineCount + 3].split(",")[-1]) != 0:
    #                totalOccupancyHours += 1
    #                illValues = line.split("  ")[1].strip().split(" ")
    #                
    #                # check number of points that satisfy the minimum illuminance
    #                for sensorCount, illuminance in enumerate(illValues):
    #                    # print float(illuminance), DLAIllumThreshold, float(illuminance) >= DLAIllumThreshold
    #                    if float(illuminance) >= DLAIllumThreshold:
    #                        higherThanThreshold += 1
    #                
    #                if higherThanThreshold/len(illValues) > .5:
    #                    sDADict[spaceCount] += 1
    #        
    #        sDADict[spaceCount] = "%.2f"%((sDADict[spaceCount]/totalOccupancyHours) * 100)
          
    
    # read all the results
    DLALists = []
    underUDLILists = []
    inRangeUDLILists = []
    overUDLILists = []
    CDALists = []
    EPLSchLists = []
    htmLists = []
    
    resultFiles = os.listdir(projectDirectory)
    for fileName in resultFiles:
        if fileName.endswith(".DA"): DLALists.append(os.path.join(filePath,fileName))
        elif fileName.endswith(".CDA"): CDALists.append(os.path.join(filePath,fileName))
        elif fileName.endswith(".htm"): htmLists.append(os.path.join(filePath,fileName))
        elif fileName.endswith("_intgain.csv"): EPLSchLists.append(os.path.join(filePath,fileName))
        elif fileName.endswith("less_than_100.UDI"): underUDLILists.append(os.path.join(filePath,fileName))
        elif fileName.endswith("100_2000.UDI"): inRangeUDLILists.append(os.path.join(filePath,fileName))
        elif fileName.endswith("more_than_2000.UDI"): overUDLILists.append(os.path.join(filePath,fileName))
        
    # sort the lists
    try: CDALists = sorted(CDALists, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-1]))
    except: pass
    try: DLALists = sorted(DLALists, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-2]))
    except: pass
    try: htmLists = sorted(htmLists, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-2]))
    except: pass
    try: EPLSchLists = sorted(EPLSchLists, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-2]))
    except: pass    
    try: underUDLILists = sorted(underUDLILists, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-4]))
    except: pass
    try: inRangeUDLILists = sorted(inRangeUDLILists, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-3]))
    except: pass
    try: overUDLILists = sorted(overUDLILists, key=lambda fileName: int(fileName.split(".")[-2].split("_")[-4]))
    except: pass
    
    return None, [DLALists, underUDLILists, inRangeUDLILists, overUDLILists, CDALists, EPLSchLists, htmLists]

def isAllNone(dataList):
    for item in dataList.AllData():
        if item!=None: return False
    return True


if _runIt and not isAllNone(_illFilesAddress) and not isAllNone(_testPoints):
    
    _testPoints.SimplifyPaths()
    lightingControlGroups_.SimplifyPaths()
    _illFilesAddress.SimplifyPaths()
    
    res = main(_illFilesAddress, _testPoints, ptsVectors_, occupancyFiles_, lightingControlGroups_, SHDGroupI_Sensors_, SHDGroupII_Sensors_, _DLAIllumThresholds_)
    
    if res!= -1:
        msg, results = res
        
        if msg!=None:
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, msg)
            
        else:
            DLALists, underUDLILists, inRangeUDLILists, overUDLILists, CDALists, EPLSchLists, htmLists = results
            DLA = DataTree[Object]()
            UDLI_Less_100 = DataTree[Object]()    
            UDLI_100_2000 = DataTree[Object]()
            UDLI_More_2000 = DataTree[Object]()
            CDA = DataTree[Object]()
            annualProfiles = DataTree[Object]()
            sDA = DataTree[Object]()
            htmReport = DataTree[Object]()
            
            def readDSStandardResults(filePath):
                results = []
                with open(filePath, "r") as inf:
                    for line in inf:
                        if not line.startswith("#"):
                            results.append(float(line.split("\t")[-1]))
                return results
            
            def getsDA(DLARes, threshold = 50):
                moreThan = 0
                for res in DLARes:
                    if res >= threshold:
                        moreThan += 1
                return "%.2f"%((moreThan/len(DLARes)) * 100)
            
            
            for branchNum in range(_testPoints.BranchCount):
                p = GH_Path(branchNum)
                DLARes = readDSStandardResults(DLALists[branchNum])
                DLA.AddRange(DLARes, p)
                UDLI_Less_100.AddRange(readDSStandardResults(underUDLILists[branchNum]), p)
                UDLI_100_2000.AddRange(readDSStandardResults(inRangeUDLILists[branchNum]), p)
                UDLI_More_2000.AddRange(readDSStandardResults(overUDLILists[branchNum]), p)
                CDA.AddRange(readDSStandardResults(CDALists[branchNum]), p)
                annualProfiles.Add(EPLSchLists[branchNum], p)
                sDA.Add(getsDA(DLARes), p)
                htmReport.Add(htmLists[branchNum], p)
                    
    
