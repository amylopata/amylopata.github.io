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
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingUtils,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFile,
                       QgsCoordinateTransformContext,
                       QgsMessageLog,
                       QgsProject,
                       QgsMapLayer,
                       QgsRasterLayer
                       )
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
import processing


class PathSlopeProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    PATHS = 'PATHS'
    DTM = 'DTM'
    MISSING_UNDER = 'MISSING_UNDER'
    MISSING_OTHER = 'MISSING_OTHER'
    OUTLINE = 'OUTLINE'
    BUILDINGS = 'BUILDINGS'
    OUTPUT = 'OUTPUT'
    STYLE = 'STYLE'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PathSlopeProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'pathslopeanalysis'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Path Slope Analysis')

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
        return self.tr("Creates raster displaying wheelchair accessibility of paths.\
        \n Note: Missing pathways under buildings should be manually assessed as wheelchair accessible. \
        These pathways will be assigned slope = 0. ")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.PATHS,
                self.tr('Path Raster')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DTM,
                self.tr('Digital Terrain Model')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.MISSING_UNDER,
                self.tr('Missing Paths (under buildings)'),
                [QgsProcessing.TypeVectorPolygon], 
                optional = True
            )
        )
         
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.MISSING_OTHER,
                self.tr('Missing Paths (not under buildings)'),
                [QgsProcessing.TypeVectorPolygon], 
                optional = True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OUTLINE,
                self.tr('Area to Clip'),
                [QgsProcessing.TypeVectorPolygon], 
                optional = True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BUILDINGS,
                self.tr('Building Outlines'),
                [QgsProcessing.TypeVectorPolygon], 
                optional = True
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                self.STYLE,
                self.tr('Output Style'),
                extension = 'qml',
                optional = True
            )
        )
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).

        self.addParameter(QgsProcessingParameterRasterDestination(
            self.OUTPUT,
            self.tr('Output layer')))
   
  
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
                
        paths = self.parameterAsRasterLayer(
            parameters,
            self.PATHS,
            context
        )
        
        output_dest= self.parameterAsOutputLayer(parameters,
                self.OUTPUT, 
                context)
        
        crs = paths.crs()
        QgsMessageLog.logMessage("Got: " + paths.crs().description(), "Processing", level=1)
        dtm = parameters[self.DTM]
        
        missing_under = parameters[self.MISSING_UNDER]
        
        missing_other = parameters[self.MISSING_OTHER]
        
        area_clip = parameters[self.OUTLINE]

        buildings = parameters[self.BUILDINGS]
        
        # fill 'no data' gaps in path raster
        filled_paths = processing.run("gdal:fillnodata",{ 
        'BAND' : 1, 
        'DISTANCE' : 2, 
        'EXTRA' : '', 
        'INPUT' : paths, 
        'ITERATIONS' : 0, 
        'MASK_LAYER' : None, 
        'NO_MASK' : False, 
        'OPTIONS' : '', 
        'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        
        # clip path raster by main campus
        if not area_clip is None:
            filled_paths = processing.run("gdal:cliprasterbymasklayer", { 
            'ALPHA_BAND' : False, 
            'CROP_TO_CUTLINE' : True, 
            'DATA_TYPE' : 0, 
            'EXTRA' : '--config GDALWARP_IGNORE_BAD_CUTLINE YES', 
            'INPUT' : filled_paths, 
            'KEEP_RESOLUTION' : False, 
            'MASK' : area_clip, 
            'MULTITHREADING' : False, 
            'NODATA' : None, 
            'OPTIONS' : '', 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
            'SET_RESOLUTION' : False, 
            'SOURCE_CRS' : None, 
            'TARGET_CRS' : None, 
            'X_RESOLUTION' : None, 
            'Y_RESOLUTION' : None }, context = context)['OUTPUT'] 
        
        # clip out buildings from path raster
        if not buildings is None:
            path_extent = processing.run("native:polygonfromlayerextent", { 
            'INPUT' : filled_paths, 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
            'ROUND_TO' : 0 })['OUTPUT']
            
            extent_minus_buildings = processing.run("native:difference", { 
            'INPUT' : path_extent, 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
            'OVERLAY' : buildings})['OUTPUT']
            
            filled_paths = processing.run("gdal:cliprasterbymasklayer", { 
            'ALPHA_BAND' : False, 
            'CROP_TO_CUTLINE' : True, 
            'DATA_TYPE' : 0, 
            'EXTRA' : '--config GDALWARP_IGNORE_BAD_CUTLINE YES', 
            'INPUT' : filled_paths, 
            'KEEP_RESOLUTION' : False, 
            'MASK' : extent_minus_buildings, 
            'MULTITHREADING' : False, 
            'NODATA' : None, 
            'OPTIONS' : '', 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
            'SET_RESOLUTION' : False, 
            'SOURCE_CRS' : None, 
            'TARGET_CRS' : None, 
            'X_RESOLUTION' : None, 
            'Y_RESOLUTION' : None }, context = context)['OUTPUT']
        
        
        
        
        # calculate slopes from digital terrain model
        slopes = processing.run("gdal:slope", {
        'AS_PERCENT' : False, 
        'BAND' : 1, 
        'COMPUTE_EDGES' : False, 
        'EXTRA' : '', 
        'INPUT' : dtm, 
        'OPTIONS' : '', 
        'OUTPUT' : 'TEMPORARY_OUTPUT', 
        'SCALE' : 1, 
        'ZEVENBERGEN' : False 
        })['OUTPUT']
        
        if not missing_under is None:
            #add missing paths under buildings as slope 0 
            # these areas were manually determined to be wheelchair accessible
            slopes = processing.run("gdal:rasterize_over_fixed_value", {
            'ADD' : False, 
            'BURN' : 0, 
            'EXTRA' : '', 
            'INPUT' : missing_under,
            'INPUT_RASTER' : slopes        
            })['OUTPUT']
        #Set the coordinate reference systems for each of the temporary files so they are known when loaded
        srs = osr.SpatialReference()
        srs.ImportFromWkt(crs.toWkt())
        dataset = gdal.Open(slopes, GA_Update)
        band = dataset.GetRasterBand(1)
        dataset.SetProjection( srs.ExportToWkt() )
        dataset = None
        dataset = gdal.Open(filled_paths, GA_Update)
        band = dataset.GetRasterBand(1)
        dataset.SetProjection( srs.ExportToWkt() )
        dataset = None
        
        #Load the temporary files as layers that can be processed by a Qgis algorithm"
        slopes_layer = QgsRasterLayer(slopes, 'Slope')
        paths_layer = QgsRasterLayer(filled_paths, 'Paths')
    
        #Create a temporary files to store the results
        output = tempfile.NamedTemporaryFile(mode='w+b')
        
        #Configure and run the raster calculator
        entries = []
        slope_band = QgsRasterCalculatorEntry()
        slope_band.ref = 'slope@1'
        slope_band.raster = slopes_layer
        slope_bandNumber = 1
        paths_band = QgsRasterCalculatorEntry()
        paths_band.ref = 'paths@1'
        paths_band.raster = paths_layer
        paths_bandNumber = 1
        entries.append(slope_band)
        entries.append(paths_band)
        calc = QgsRasterCalculator("(paths@1 >=0) * slope@1", 
                                        output_dest, 
                                        'GTiff', 
                                        slopes_layer.extent(), 
                                        slopes_layer.width(), 
                                        slopes_layer.height(), 
                                        entries,
                                        QgsCoordinateTransformContext ())
        calc.processCalculation()
        QgsMessageLog.logMessage("Calculator results are in " + output.name, "Messages", level=1)
        all_path_slopes = output_dest
        
        
        QgsMessageLog.logMessage("starting rasterize", "Processing", level=1)
        if not missing_under is None:
            
            
            QgsMessageLog.logMessage("starting clip", "Processing", level=1)
            # clip slope raster by missing slopes under buildings
            slopes_missing_under = processing.run("gdal:cliprasterbymasklayer", { 
            'ALPHA_BAND' : False, 
            'CROP_TO_CUTLINE' : True, 
            'DATA_TYPE' : 0, 
            'EXTRA' : '--config GDALWARP_IGNORE_BAD_CUTLINE YES', 
            'INPUT' : slopes, 
            'KEEP_RESOLUTION' : False, 
            'MASK' : missing_under, 
            'MULTITHREADING' : False, 
            'NODATA' : None, 
            'OPTIONS' : '', 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
            'SET_RESOLUTION' : False, 
            'SOURCE_CRS' : None, 
            'TARGET_CRS' : None, 
            'X_RESOLUTION' : None, 
            'Y_RESOLUTION' : None }, context = context)['OUTPUT']
            
            QgsMessageLog.logMessage("starting merge", "Processing", level=1)
            
            QgsMessageLog.logMessage("missing under: " + str(slopes_missing_under), "Processing", level=1)
            QgsMessageLog.logMessage("all_path_slopes: " + str(all_path_slopes), "Processing", level=1)

            # merge detected and manually added slopes
            all_path_slopes = processing.run("gdal:merge", { 
            'DATA_TYPE' : 5, 
            'EXTRA' : '', 
            'INPUT' : [all_path_slopes, slopes_missing_under], 
            'NODATA_INPUT' : None, 
            'NODATA_OUTPUT' : None, 
            'OPTIONS' : '', 
            'OUTPUT' : output_dest, 
            'PCT' : False, 
            'SEPARATE' : False })['OUTPUT']
            
            QgsMessageLog.logMessage("successfully merged", "Messages", level=1)
            
            
        if not missing_other is None:
            # clip slope raster by missing paths not under buildings
            slopes_missing_other = processing.run("gdal:cliprasterbymasklayer", { 
            'ALPHA_BAND' : False, 
            'CROP_TO_CUTLINE' : True, 
            'DATA_TYPE' : 0, 
            'EXTRA' : '--config GDALWARP_IGNORE_BAD_CUTLINE YES', 
            'INPUT' : slopes, 
            'KEEP_RESOLUTION' : False, 
            'MASK' : missing_other, 
            'MULTITHREADING' : False, 
            'NODATA' : None, 
            'OPTIONS' : '', 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
            'SET_RESOLUTION' : False, 
            'SOURCE_CRS' : None, 
            'TARGET_CRS' : None, 
            'X_RESOLUTION' : None, 
            'Y_RESOLUTION' : None }, context = context)['OUTPUT']
            
            # merge detected and manually added slopes
            QgsMessageLog.logMessage("Output Layer is " + output_dest, "Messages", level=1)
            all_path_slopes = processing.run("gdal:merge", { 
            'DATA_TYPE' : 5, 
            'EXTRA' : '', 
            'INPUT' : [all_path_slopes, slopes_missing_other], 
            'NODATA_INPUT' : None, 
            'NODATA_OUTPUT' : None, 
            'OPTIONS' : '', 
            'OUTPUT' : output_dest, 
            'PCT' : False, 
            'SEPARATE' : False })['OUTPUT']
            
        result_layer = QgsProcessingUtils.mapLayerFromString(output_dest, context)
        result_layer.loadNamedStyle(parameters[self.STYLE])

        return {self.OUTPUT: output_dest }
