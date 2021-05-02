# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
from osgeo import osr, gdal
import tempfile
from gdalconst import *
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsWkbTypes,
                       QgsFields,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingUtils,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFile,
                       QgsCoordinateTransformContext,
                       QgsMessageLog,
                       QgsProject,
                       QgsMapLayer,
                       QgsRasterLayer, 
                       QgsProcessingParameterVectorDestination
                       )
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
import processing


class AccessibleNavigationProcessingAlgorithm(QgsProcessingAlgorithm):
  

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    PATH_SLOPES = 'PATH_SLOPES'
    ENDPOINTS = 'ENDPOINTS'
    OUTPUT_ALL = 'OUTPUT_ALL'
    OUTPUT_ACCESS = 'OUTPUT_ACCESS'
    STYLE = 'STYLE'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return AccessibleNavigationProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'linevecextraction'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Line Vector Extraction')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Wheelchair Accessibility of Paths')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'accessibility'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Converts path raster (e.g., output from Path Slope Analysis function) to line vectors. \
		Two output files: line vector of overall paths and line vector of wheelchair accessible paths  \
		(i.e., excludes paths which have slope greater than 8.33%)")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.PATH_SLOPES,
                self.tr('Raster of Path Slopes')
            )
        )
        
        
       # self.addParameter(
       #     QgsProcessingParameterFeatureSource(
       #         self.ENDPOINTS,
       #         self.tr('Endpoints (e.g., building entrances)'),
       #         [QgsProcessing.TypeVectorPoint]
       #         )
       # )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).

        self.addParameter(
        QgsProcessingParameterFeatureSink (
            self.OUTPUT_ALL,
            self.tr('Output layer 1 (all paths)')
        )
        )
    
        self.addParameter(
        QgsProcessingParameterFeatureSink (
            self.OUTPUT_ACCESS,
            self.tr('Output layer 2 (accessible paths)')
        )
        )
   
  
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
                
        path_slopes = self.parameterAsRasterLayer(
            parameters,
            self.PATH_SLOPES,
            context
        )
        (sink, output_dest1) = self.parameterAsSink(
            parameters, 
            self.OUTPUT_ALL, 
            context,
            QgsFields(),
            QgsWkbTypes.LineString,
            path_slopes.crs()
        )
        
        (sink, output_dest2) = self.parameterAsSink(
            parameters, 
            self.OUTPUT_ACCESS, 
            context,
            QgsFields(),
            QgsWkbTypes.LineString,
            path_slopes.crs()
        )
        
        
        crs = path_slopes.crs()
        
        # endpoints = parameters[self.ENDPOINTS]
        
        QgsMessageLog.logMessage("parameters self path slopes " + parameters[self.PATH_SLOPES], "Processing", level=1)
        QgsMessageLog.logMessage("Starting raster calculator", "Processing", level=1)
        accessible_path_slopes = processing.run("gdal:rastercalculator", { 
        'BAND_A' : 1, 
        'EXTRA' : '', 
        'FORMULA' : 'logical_or(A > 8.33, A <0)*9999 + logical_and(A <= 8.33, A >= 0)*A', 
        'INPUT_A' : path_slopes,
        'NO_DATA' : None, 
        'OPTIONS' : '', 
        'OUTPUT' : 'TEMPORARY_OUTPUT', 
        'RTYPE' : 5 })['OUTPUT']
        
        QgsMessageLog.logMessage("Starting reclassify", "Processing", level=1)
        # reclassify no data values as 9999
        accessible_path_slopes = processing.run("saga:reclassifyvaluessingle", { 
        'INPUT' : accessible_path_slopes, 
        'NEW' : 1, 
        'NODATA' : 9999, 
        'NODATAOPT' : True, 
        'OLD' : 0, 
        'OTHEROPT' : False, 
        'OTHERS' : 0, 
        'RESULT' : 'TEMPORARY_OUTPUT', 
        'SOPERATOR' : 2 }, feedback=feedback, context=context)['RESULT']
        
        QgsMessageLog.logMessage("Saga output" + accessible_path_slopes, "Processing", level=1)
        QgsMessageLog.logMessage("Starting translate", "Processing", level=1)
        # set no data value to be 9999 and translate to int32 data type
        accessible_path_slopes = processing.run("gdal:translate", {
        'COPY_SUBDATASETS' : False, 
        'DATA_TYPE' : 5, 
        'EXTRA' : '', 
        'INPUT' : accessible_path_slopes, 
        'NODATA' : 9999, 
        'OPTIONS' : '', 
        'OUTPUT' : 'TEMPORARY_OUTPUT', 
        'TARGET_CRS' : None}, feedback=feedback, context=context)['OUTPUT']
        
        QgsMessageLog.logMessage("Starting translate #2", "Processing", level=1)
        # translate overall path slopes to int 32
        all_path_slopes = processing.run("gdal:translate", {
        'COPY_SUBDATASETS' : False, 
        'DATA_TYPE' : 5, 
        'EXTRA' : '', 
        'INPUT' : path_slopes, 
        'NODATA' : None, 
        'OPTIONS' : '', 
        'OUTPUT' : 'TEMPORARY_OUTPUT', 
        'TARGET_CRS' : None}, feedback=feedback, context=context)['OUTPUT']
        
        
        QgsMessageLog.logMessage("Starting thin", "Processing", level=1)
        # thin the accessible and overall path slopes
        accessible_thin = processing.run("grass7:r.thin", { 
        'GRASS_RASTER_FORMAT_META' : '', 
        'GRASS_RASTER_FORMAT_OPT' : '', 
        'GRASS_REGION_CELLSIZE_PARAMETER' : 0, 
        'GRASS_REGION_PARAMETER' : None, 
        'input' : accessible_path_slopes, 
        'iterations' : 200, 
        'output' : 'TEMPORARY_OUTPUT' }, feedback=feedback, context=context)['output']
        
        QgsMessageLog.logMessage("Starting thin #2", "Processing", level=1)
        all_thin = processing.run("grass7:r.thin", { 
        'GRASS_RASTER_FORMAT_META' : '', 
        'GRASS_RASTER_FORMAT_OPT' : '', 
        'GRASS_REGION_CELLSIZE_PARAMETER' : 0, 
        'GRASS_REGION_PARAMETER' : None, 
        'input' : all_path_slopes, 
        'iterations' : 200, 
        'output' : 'TEMPORARY_OUTPUT' }, feedback=feedback, context=context)['output']
        
        QgsMessageLog.logMessage("Starting vectorization", "Processing", level=1)
        # convert thinned paths to vector line
        accessible_line_vec = processing.run("grass7:r.to.vect", { 
        '-b' : False, '-s' : False, '-t' : False, '-v' : False, '-z' : False, 
        'GRASS_OUTPUT_TYPE_PARAMETER' : 0, 
        'GRASS_REGION_CELLSIZE_PARAMETER' : 0, 
        'GRASS_REGION_PARAMETER' : None, 
        'GRASS_VECTOR_DSCO' : '', 
        'GRASS_VECTOR_EXPORT_NOCAT' : False, 
        'GRASS_VECTOR_LCO' : '', 
        'column' : 'value', 
        'input' : accessible_thin, 
        'output' : output_dest2, 'type' : 0 }, feedback=feedback, context=context)['output']
       
        QgsMessageLog.logMessage("Starting vectorization #2", "Processing", level=1)
        all_line_vec = processing.run("grass7:r.to.vect", { 
        '-b' : False, '-s' : False, '-t' : False, '-v' : False, '-z' : False, 
        'GRASS_OUTPUT_TYPE_PARAMETER' : 0, 
        'GRASS_REGION_CELLSIZE_PARAMETER' : 0, 
        'GRASS_REGION_PARAMETER' : None, 
        'GRASS_VECTOR_DSCO' : '', 
        'GRASS_VECTOR_EXPORT_NOCAT' : False, 
        'GRASS_VECTOR_LCO' : '', 
        'column' : 'value', 
        'input' : all_thin, 
        'output' : output_dest1, 'type' : 0 }, feedback=feedback, context=context)['output']
            
        return {self.OUTPUT_ALL: output_dest1, self.OUTPUT_ACCESS: output_dest2}
