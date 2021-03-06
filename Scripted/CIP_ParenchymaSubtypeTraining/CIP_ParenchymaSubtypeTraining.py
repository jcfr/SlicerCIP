import os, sys
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

# Add the CIP common library to the path if it has not been loaded yet
try:
    from CIP.logic.SlicerUtil import SlicerUtil
except Exception as ex:
    currentpath = os.path.dirname(os.path.realpath(__file__))
    # We assume that CIP_Common is in the development structure
    path = os.path.normpath(currentpath + '/../CIP_Common')
    if not os.path.exists(path):
        # We assume that CIP is a subfolder (Slicer behaviour)
        path = os.path.normpath(currentpath + '/CIP')
    sys.path.append(path)
    print("The following path was manually added to the PythonPath in CIP_ParenchymaSubtypeTraining: " + path)
    from CIP.logic.SlicerUtil import SlicerUtil

from CIP.logic import SubtypingParameters, Util
from CIP.logic import geometry_topology_data as GTD

#
# CIP_ParenchymaSubtypeTraining
#
class CIP_ParenchymaSubtypeTraining(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Parenchyma Subtype Training"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Training for a subtype of emphysema done quickly by an expert"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


#
# CIP_ParenchymaSubtypeTrainingWidget
#
class CIP_ParenchymaSubtypeTrainingWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    @property
    def moduleName(self):
        return "CIP_ParenchymaSubtypeTraining"

    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)

        from functools import partial
        def __onNodeAddedObserver__(self, caller, eventId, callData):
            """Node added to the Slicer scene"""
            if callData.GetClassName() == 'vtkMRMLScalarVolumeNode' \
                    and slicer.util.mainWindow().moduleSelector().selectedModule == self.moduleName:
                self.__onNewVolumeLoaded__(callData)

        self.__onNodeAddedObserver__ = partial(__onNodeAddedObserver__, self)
        self.__onNodeAddedObserver__.CallDataType = vtk.VTK_OBJECT




    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_ParenchymaSubtypeTrainingLogic()
        self.currentVolumeLoaded = None
        self.blockNodeEvents = False

        ##########
        # Main area
        self.mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        self.mainAreaCollapsibleButton.text = "Main area"
        self.layout.addWidget(self.mainAreaCollapsibleButton, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.mainLayout = qt.QGridLayout(self.mainAreaCollapsibleButton)

        # Node selector
        volumeLabel = qt.QLabel("Active volume: ")
        volumeLabel.setStyleSheet("margin-left:5px")
        self.mainLayout.addWidget(volumeLabel, 0, 0)
        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.volumeSelector.selectNodeUponCreation = True
        self.volumeSelector.autoFillBackground = True
        self.volumeSelector.addEnabled = False
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene(slicer.mrmlScene)
        self.volumeSelector.setFixedWidth(250)
        self.volumeSelector.setStyleSheet("margin: 15px 0")
        #self.volumeSelector.selectNodeUponCreation = False
        self.mainLayout.addWidget(self.volumeSelector, 0, 1, 1, 3)

        labelsStyle = "font-weight: bold; margin: 0 0 5px 5px;"
        # Types Radio Buttons
        typesLabel = qt.QLabel("Select the type")
        typesLabel.setStyleSheet(labelsStyle)
        typesLabel.setFixedHeight(15)
        self.mainLayout.addWidget(typesLabel, 1, 0)
        self.typesFrame = qt.QFrame()
        self.typesLayout = qt.QVBoxLayout(self.typesFrame)
        self.mainLayout.addWidget(self.typesFrame, 2, 0, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.typesRadioButtonGroup = qt.QButtonGroup()
        for key in self.logic.params.mainTypes.iterkeys():
            rbitem = qt.QRadioButton(self.logic.params.getMainTypeLabel(key))
            self.typesRadioButtonGroup.addButton(rbitem, key)
            self.typesLayout.addWidget(rbitem)
        self.typesRadioButtonGroup.buttons()[0].setChecked(True)

        # Subtypes Radio buttons
        subtypesLabel = qt.QLabel("Select the subtype")
        subtypesLabel.setStyleSheet(labelsStyle)
        subtypesLabel.setFixedHeight(15)
        self.mainLayout.addWidget(subtypesLabel, 1, 1)
        self.subtypesRadioButtonGroup = qt.QButtonGroup()
        self.subtypesFrame = qt.QFrame()
        self.subtypesFrame.setMinimumHeight(275)
        self.subtypesLayout = qt.QVBoxLayout(self.subtypesFrame)
        self.subtypesLayout.setAlignment(SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.subtypesLayout.setStretch(0, 0)
        self.mainLayout.addWidget(self.subtypesFrame, 2, 1, SlicerUtil.ALIGNMENT_VERTICAL_TOP)     # Put the frame in the top
        # The content will be loaded dynamically every time the main type is modified

        # Artifact radio buttons
        self.artifactsLabel = qt.QLabel("Artifact")
        self.artifactsLabel.setStyleSheet(labelsStyle)
        self.artifactsLabel.setFixedHeight(15)
        self.mainLayout.addWidget(self.artifactsLabel, 1, 2)
        #self.mainLayout.addWidget(qt.QLabel("Select the artifact"), 1, 1)
        self.artifactsRadioButtonGroup = qt.QButtonGroup()
        self.artifactsFrame = qt.QFrame()
        self.artifactsLayout = qt.QVBoxLayout(self.artifactsFrame)
        self.mainLayout.addWidget(self.artifactsFrame, 2, 2, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.artifactsRadioButtonGroup = qt.QButtonGroup()
        for artifactId in self.logic.params.artifacts.iterkeys():
            rbitem = qt.QRadioButton(self.logic.params.getArtifactLabel(artifactId))
            self.artifactsRadioButtonGroup.addButton(rbitem, artifactId)
            self.artifactsLayout.addWidget(rbitem)
        self.artifactsRadioButtonGroup.buttons()[0].setChecked(True)

        # Load caselist button
        self.loadButton = ctk.ctkPushButton()
        self.loadButton.text = "Load fiducials file"
        self.loadButton.setIcon(qt.QIcon("{0}/open_file.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.loadButton.setIconSize(qt.QSize(20, 20))
        self.loadButton.setFixedWidth(135)
        self.mainLayout.addWidget(self.loadButton, 3, 0)

        # Remove fiducial button
        self.removeLastFiducialButton = ctk.ctkPushButton()
        self.removeLastFiducialButton.text = "Remove last fiducial"
        self.removeLastFiducialButton.toolTip = "Remove the last fiducial added"
        self.removeLastFiducialButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeLastFiducialButton.setIconSize(qt.QSize(20, 20))
        self.removeLastFiducialButton.setFixedWidth(200)
        self.mainLayout.addWidget(self.removeLastFiducialButton, 3, 1)

        # Save results button
        self.saveResultsButton = ctk.ctkPushButton()
        self.saveResultsButton.setText("Save markups")
        self.saveResultsButton.toolTip = "Save the markups in the specified directory"
        self.saveResultsButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveResultsButton.setIconSize(qt.QSize(20,20))
        self.mainLayout.addWidget(self.saveResultsButton, 4, 0)

        # Save results directory button
        defaultPath = os.path.join(SlicerUtil.getSettingsDataFolder(self.moduleName), "Results")     # Assign a default path for the results
        path = SlicerUtil.settingGetOrSetDefault(self.moduleName, "SaveResultsDirectory", defaultPath)
        self.saveResultsDirectoryButton = ctk.ctkDirectoryButton()
        self.saveResultsDirectoryButton.directory = path
        self.saveResultsDirectoryButton.setMaximumWidth(375)
        self.mainLayout.addWidget(self.saveResultsDirectoryButton, 4, 1, 1, 2)

        #####
        # Case navigator
        if SlicerUtil.isSlicerACILLoaded():
            caseNavigatorAreaCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorAreaCollapsibleButton.text = "Case navigator"
            self.layout.addWidget(caseNavigatorAreaCollapsibleButton, 0x0020)
            # caseNavigatorLayout = qt.QVBoxLayout(caseNavigatorAreaCollapsibleButton)

            # Add a case list navigator
            from ACIL.ui import CaseNavigatorWidget
            self.caseNavigatorWidget = CaseNavigatorWidget(self.moduleName, caseNavigatorAreaCollapsibleButton)
            self.caseNavigatorWidget.setup()
            # Listen for the event of loading volume
            #self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_VOLUME_LOADED, self.onNewVolumeLoaded)

        self.layout.addStretch()

        self.updateState()

        # Connections
        self.typesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onTypesRadioButtonClicked__)
        self.subtypesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onSubtypesRadioButtonClicked__)
        self.artifactsRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onSubtypesRadioButtonClicked__)

        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.__onCurrentNodeChanged__)
        self.loadButton.connect('clicked()', self.openFiducialsFile)
        self.removeLastFiducialButton.connect('clicked()', self.__onRemoveLastFiducialButtonClicked__)
        # self.saveResultsOpenDirectoryDialogButton.connect('clicked()', self.onOpenDirectoryDialogButtonClicked)
        self.saveResultsDirectoryButton.connect("directoryChanged (str)", self.__onSaveResultsDirectoryChanged__)
        self.saveResultsButton.connect('clicked()', self.__onSaveResultsButtonClicked__)

        self.observers = []
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.__onNodeAddedObserver__))
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__))


    def updateState(self):
        """ Refresh the markups state, activate the right fiducials list node (depending on the
        current selected type) and creates it when necessary
        :return:
        """
        # Load the subtypes for this type
        subtypesDict = self.logic.getSubtypes(self.typesRadioButtonGroup.checkedId())
        # Remove all the existing buttons
        for b in self.subtypesRadioButtonGroup.buttons():
            b.hide()
            b.delete()
        # Add all the subtypes with the full description
        for subtype in subtypesDict.iterkeys():
            rbitem = qt.QRadioButton(self.logic.getSubtypeFullDescription(subtype))
            self.subtypesRadioButtonGroup.addButton(rbitem, subtype)
            self.subtypesLayout.addWidget(rbitem, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        # Check first element by default
        self.subtypesRadioButtonGroup.buttons()[0].setChecked(True)

        # Set the correct state for fiducials
        if self.currentVolumeLoaded is not None:
            self.logic.setActiveFiducialsListNode(self.currentVolumeLoaded,
                self.typesRadioButtonGroup.checkedId(), self.subtypesRadioButtonGroup.checkedId(), self.artifactsRadioButtonGroup.checkedId())

    def saveResultsCurrentNode(self):
        d = self.saveResultsDirectoryButton.directory
        if not os.path.isdir(d):
            # Ask the user if he wants to create the folder
            if qt.QMessageBox.question(slicer.util.mainWindow(), "Create directory?",
                "The directory '{0}' does not exist. Do you want to create it?".format(d),
                                       qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
                try:
                    os.makedirs(d)
                    # Make sure that everybody has write permissions (sometimes there are problems because of umask)
                    os.chmod(d, 0777)
                    self.logic.saveCurrentFiducials(d)
                    qt.QMessageBox.information(slicer.util.mainWindow(), 'Results saved',
                        "The results have been saved succesfully")
                except:
                     qt.QMessageBox.warning(slicer.util.mainWindow(), 'Directory incorrect',
                        'The folder "{0}" could not be created. Please select a valid directory'.format(d))
        else:
            self.logic.saveCurrentFiducials(d)
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Results saved',
                "The results have been saved succesfully")

    def openFiducialsFile(self):
        volumeNode = self.volumeSelector.currentNode()
        if volumeNode is None:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Select a volume',
                                       'Please load a volume first')
            return

        f = qt.QFileDialog.getOpenFileName()
        if f:
            self.logic.loadFiducials(volumeNode, f)
            self.saveResultsDirectoryButton.directory = os.path.dirname(f)
            qt.QMessageBox.information(slicer.util.mainWindow(), "File loaded", "File loaded successfully")

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        self.blockNodeEvents = False
        # if len(self.observers) == 0:
        #     self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.__onNodeAddedObserver__))
        #     self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__))
        SlicerUtil.setFiducialsCursorMode(True, True)

        if self.volumeSelector.currentNodeId != "":
            SlicerUtil.setActiveVolumeId(self.volumeSelector.currentNodeId)
            self.currentVolumeLoaded = slicer.util.getNode(self.volumeSelector.currentNodeId)
            self.updateState()

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        try:
            self.blockNodeEvents = True
            SlicerUtil.setFiducialsCursorMode(False)
            # for observer in self.observers:
            #     slicer.mrmlScene.RemoveObserver(observer)
            #     self.observers.remove(observer)
        except:
            pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        try:
            for observer in self.observers:
                slicer.mrmlScene.RemoveObserver(observer)
                self.observers.remove(observer)
        except:
            pass

    def __onNewVolumeLoaded__(self, newVolumeNode):
        """ Added a new node in the scene
        :param newVolumeNode:
        :return:
        """
        self.__checkNewVolume__(newVolumeNode)
        self.blockNodeEvents = True
        self.volumeSelector.setCurrentNode(newVolumeNode)
        self.blockNodeEvents = False

    def __onCurrentNodeChanged__(self, volumeNode):
        self.__checkNewVolume__(volumeNode)
        # if volumeNode:
        #     #self.logic.reset(volumeNode)
        #     SlicerUtil.setActiveVolumeId(volumeNode.GetID())
        #     self.updateState()

    def __checkNewVolume__(self, newVolumeNode):
        if self.blockNodeEvents:
            return
        self.blockNodeEvents = True
        volume = self.currentVolumeLoaded
        if volume is not None and newVolumeNode is not None \
                and newVolumeNode.GetID() != volume.GetID()  \
                and not self.logic.isVolumeSaved(volume.GetID()):
            # Ask the user if he wants to save the previously loaded volume
            if qt.QMessageBox.question(slicer.util.mainWindow(), "Save results?",
                    "The fiducials for the volume '{0}' have not been saved. Do you want to save them?"
                    .format(volume.GetName()),
                    qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
                self.saveResultsCurrentNode()
        # Remove all the previously existing nodes
        if self.currentVolumeLoaded is not None and newVolumeNode != self.currentVolumeLoaded:
            # Remove previously existing node
            self.logic.removeMarkupsAndNode(self.currentVolumeLoaded)
        if newVolumeNode is not None:
            SlicerUtil.setActiveVolumeId(newVolumeNode.GetID())
            SlicerUtil.setFiducialsCursorMode(True, True)

        self.currentVolumeLoaded = newVolumeNode
        self.updateState()
        self.blockNodeEvents = False

    def __onTypesRadioButtonClicked__(self, button):
        """ One of the radio buttons has been pressed
        :param button:
        :return:
        """
        self.updateState()

    def __onSubtypesRadioButtonClicked__(self, button):
        """ One of the subtype radio buttons has been pressed
        :param button:
        :return:
        """
        selectedVolume = self.volumeSelector.currentNode()
        if selectedVolume is not None:
            self.logic.setActiveFiducialsListNode(selectedVolume,
                    self.typesRadioButtonGroup.checkedId(), self.subtypesRadioButtonGroup.checkedId(), self.artifactsRadioButtonGroup.checkedId())

    def __onRemoveLastFiducialButtonClicked__(self):
       self.logic.removeLastMarkup()

    def __onSaveResultsDirectoryChanged__(self, directory):
        # f = qt.QFileDialog.getExistingDirectory()
        # if f:
        #     self.saveResultsDirectoryText.setText(f)
        SlicerUtil.setSetting(self.moduleName, "SaveResultsDirectory", directory)

    def __onSaveResultsButtonClicked__(self):
        self.saveResultsCurrentNode()

    def __onSceneClosed__(self, arg1, arg2):
        self.currentVolumeLoaded = None
#
# CIP_ParenchymaSubtypeTrainingLogic
#
class CIP_ParenchymaSubtypeTrainingLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        self.params = SubtypingParameters.SubtypingParameters()
        self.markupsLogic = slicer.modules.markups.logic()

        self.currentVolumeId = None
        self.currentTypeId = -1
        self.currentSubtypeId = -1
        self.currentArtifactId = 0
        self.savedVolumes = {}

    def getSubtypes(self, typeId):
        """ Get all the subtypes for the specified type
        :param typeId: type id
        :return: List of tuples with (Key, Description) with the subtypes """
        return self.params.getSubtypes(typeId)

    def getSubtypeFullDescription(self, subtypeId):
        """ Get the subtype description including the abbreviation in parenthesis.
        Ex: Subpleural line (SpL)
        :param subtypeId:
        :return:
        """
        return self.params.getSubtypeLabel(subtypeId)

    def getEffectiveType(self, typeId, subtypeId):
        """ Return the subtype id unless it's 0. In this case, return the main type id
        :param typeId:
        :param subtypeId:
        :return:
        """
        return typeId if subtypeId == 0 else subtypeId


    def _createFiducialsListNode_(self, nodeName, typeId, artifactId):
        """ Create a fiducials list node for this volume and this type. Depending on the type, the color will be different
        :param nodeName: Full name of the fiducials list node
        :param typeId: type id that will modify the color of the fiducial
        :param artifactId: type id that will modify the color and tag of the fiducial
        :return: fiducials list node
        """
        fidListID = self.markupsLogic.AddNewFiducialNode(nodeName, slicer.mrmlScene)
        fidNode = slicer.util.getNode(fidListID)
        displayNode = fidNode.GetDisplayNode()
        displayNode.SetSelectedColor(self.params.getColor(typeId, artifactId))
        displayNode.SetTextScale(1.5)
        # print("DEBUG: Type Id = {0}. Color for the fiducial: ".format(typeId), self.params.getColor(typeId))

        # Add an observer when a new markup is added
        fidNode.AddObserver(fidNode.MarkupAddedEvent, self.onMarkupAdded)

        return fidNode

    def setActiveFiducialsListNode(self, volumeNode, typeId, subtypeId, artifactId, createIfNotExists=True):
        """ Get the vtkMRMLMarkupsFiducialNode node associated with this volume and this type.
        :param volumeNode: Scalar volume node
        :param typeId: main type id
        :param subtypeId: subtype id
        :param artifactId: artifact id
        :param createIfNotExists: create the node if it doesn't exist yet
        :return: fiducials volume node
        """
        if volumeNode is not None:
            if artifactId == -1:
                # No artifact
                nodeName = "{0}_fiducials_{1}".format(volumeNode.GetID(), typeId)
            else:
                # Artifact. Add the type of artifact to the node name
                nodeName = "{0}_fiducials_{1}_{2}".format(volumeNode.GetID(), typeId, artifactId)
            fid = slicer.util.getNode(nodeName)
            if fid is None and createIfNotExists:
                # print("DEBUG: creating a new fiducials node: " + nodeName)
                fid = self._createFiducialsListNode_(nodeName, typeId, artifactId)
                # Add the volume to the list of "managed" cases
                self.savedVolumes[volumeNode.GetID()] = False
            self.currentVolumeId = volumeNode.GetID()
            self.currentTypeId = typeId
            self.currentSubtypeId = subtypeId
            self.currentArtifactId = artifactId
            # Mark the node list as the active one
            self.markupsLogic.SetActiveListID(fid)
            return fid


    def getMarkupLabel(self, typeId, subtypeId, artifactId):
        """ Get the text that will be displayed in the fiducial
        :param typeId:
        :param subtypeId:
        :param artifactId:
        :return: test
        """
        if subtypeId == 0:
            # No subtype. Just add the general type description
            label = self.params.getMainTypeAbbreviation(typeId)
        else:
            # Initials of the subtype
            label = self.params.getSubtypeAbbreviation(subtypeId)

        if artifactId != 0:
            # There is artifact
            return "{0}-{1}".format(label, self.params.getArtifactAbbreviation(artifactId))
        # No artifact
        return label


    def onMarkupAdded(self, markupListNode, event):
        """ New markup node added. It will be renamed based on the type-subtype
        :param nodeAdded: Markup LIST Node that was added
        :param event:
        :return:
        """
        label = self.getMarkupLabel(self.currentTypeId, self.currentSubtypeId, self.currentArtifactId)
        # Get the last added markup (there is no index in the event!)
        n = markupListNode.GetNumberOfFiducials()
        # Change the label
        markupListNode.SetNthMarkupLabel(n-1, label)
        # Use the description to store the type of the fiducial that will be saved in
        # the GeometryTopolyData object
        markupListNode.SetNthMarkupDescription(n-1,
            "{0}_{1}".format(self.getEffectiveType(self.currentTypeId, self.currentSubtypeId), self.currentArtifactId))
        # Markup added. Mark the current volume as state modified
        # if self.currentVolumeId in self.savedVolumes:
        #     self.savedVolumes.remove(self.currentVolumeId)
        self.savedVolumes[self.currentVolumeId] = False


    def saveCurrentFiducials(self, directory):
        """ Save all the fiducials for the current volume.
        The name of the file will be VolumeName_parenchymaTraining.xml"
        :param volume: scalar node
        :param directory: destiny directory
        :return:
        """
        volume = slicer.util.getNode(self.currentVolumeId)
        print("DEBUG: saving the fidcuals for volume " + volume.GetName())
        # Iterate over all the fiducials list nodes
        pos = [0,0,0]
        topology = GTD.GeometryTopologyData()
        topology.coordinate_system = topology.LPS
        # Get the transformation matrix LPS-->IJK
        matrix = Util.get_lps_to_ijk_transformation_matrix(volume)
        topology.lps_to_ijk_transformation_matrix = Util.convert_vtk_matrix_to_list(matrix)

        for fidListNode in slicer.util.getNodes("{0}_fiducials_*".format(volume.GetID())).itervalues():
            # Get all the markups
            for i in range(fidListNode.GetNumberOfMarkups()):
                fidListNode.GetNthFiducialPosition(i, pos)
                # Get the type from the description (region will always be 0)
                desc = fidListNode.GetNthMarkupDescription(i)
                typeId = int(desc.split("_")[0])
                artifactId = int(desc.split("_")[1])
                # Switch coordinates from RAS to LPS
                lps_coords = Util.ras_to_lps(list(pos))
                p = GTD.Point(0, typeId, artifactId, lps_coords)
                topology.add_point(p)

        # Get the xml content file
        xml = topology.to_xml()
        # Save the file
        fileName = os.path.join(directory, "{0}_parenchymaTraining.xml".format(volume.GetName()))
        with open(fileName, 'w') as f:
            f.write(xml)

        # Mark the current volume as saved
        #self.savedVolumes.add(volume.GetID())
        self.savedVolumes[volume.GetID()] = True


    def removeLastMarkup(self):
        """ Remove the last markup that was added to the scene. It will remove all the markups if the user wants
        """
        fiducialsList = slicer.util.getNode(self.markupsLogic.GetActiveListID())
        if fiducialsList is not None:
            # Remove the last fiducial
            fiducialsList.RemoveMarkup(fiducialsList.GetNumberOfMarkups()-1)
        # Markup removed. Mark the current volume as state modified
        # if self.currentVolumeId in self.savedVolumes:
        #     self.savedVolumes.remove(self.currentVolumeId)
        self.savedVolumes[self.currentVolumeId] = False

    def isVolumeSaved(self, volumeId):
        """ True if there are no markups unsaved for this volume
        :param volumeId:
        :return:
        """
        if not self.savedVolumes.has_key(volumeId):
            raise Exception("Volume {0} is not in the list of managed volumes".format(volumeId))
        return self.savedVolumes[volumeId]


    def loadFiducials(self, volumeNode, fileName):
        """ Load from disk a list of fiducials for a particular volume node
        :param volumeNode: Volume (scalar node)
        :param fileName: full path of the file to load the fiducials where
        """
        with open(fileName, "r") as f:
            xml = f.read()

        geom = GTD.GeometryTopologyData.from_xml(xml)
        for point in geom.points:
            subtype = point.chest_type
            if subtype in self.params.mainTypes.keys():
                # Main type. The subtype will be "Any"
                mainType = subtype
                subtype = 0
            else:
                mainType = self.params.getMainTypeForSubtype(subtype)
            # Activate the current fiducials list based on the main type
            fidList = self.setActiveFiducialsListNode(volumeNode, mainType, subtype, point.feature_type)
            # Check if the coordinate system is RAS (and make the corresponding transform otherwise)
            if geom.coordinate_system == geom.LPS:
                coord = Util.lps_to_ras(point.coordinate)
            elif geom.coordinate_system == geom.IJK:
                coord = Util.ijk_to_ras(volumeNode, point.coordinate)
            else:
                # Try default mode (RAS)
                coord = point.coordinate
            # Add the fiducial
            fidList.AddFiducial(coord[0], coord[1], coord[2], self.getMarkupLabel(mainType, subtype, point.feature_type))


    def reset(self, volumeToKeep=None):
        """ Remove a volume node and all its associated fiducials """
        if volumeToKeep is None:
            # Just clear the scene
            slicer.mrmlScene.Clear(False)
        else:
            # Remove scalarNodes
            nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLScalarVolumeNode")
            nodes.InitTraversal()
            node = nodes.GetNextItemAsObject()
            while node is not None:
                if node.GetID() != volumeToKeep.GetID():
                    slicer.mrmlScene.RemoveNode(node)
                node = nodes.GetNextItemAsObject()

            # Remove fiducials
            nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLMarkupsFiducialNode")
            nodes.InitTraversal()
            node = nodes.GetNextItemAsObject()
            while node is not None:
                slicer.mrmlScene.RemoveNode(node)
                node = nodes.GetNextItemAsObject()

    def removeMarkupsAndNode(self, volume):
        nodes = slicer.util.getNodes(volume.GetID() + "_*")
        for node in nodes.itervalues():
            slicer.mrmlScene.RemoveNode(node)
        slicer.mrmlScene.RemoveNode(volume)

    def printMessage(self, message):
        print("This is your message: ", message)
        return "I have printed this message: " + message



class CIP_ParenchymaSubtypeTrainingTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_ParenchymaSubtypeTraining_PrintMessage()

    def test_CIP_ParenchymaSubtypeTraining_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_ParenchymaSubtypeTrainingLogic()

        myMessage = "Print this test message in console"
        logging.info("Starting the test with this message: " + myMessage)
        expectedMessage = "I have printed this message: " + myMessage
        logging.info("The expected message would be: " + expectedMessage)
        responseMessage = logic.printMessage(myMessage)
        logging.info("The response message was: " + responseMessage)
        self.assertTrue(responseMessage == expectedMessage)
        self.delayDisplay('Test passed!')
