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
import os, shutil, tempfile
from osgeo import osr, gdal
import tempfile
from gdalconst import *
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsFields,
                       QgsWkbTypes,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingUtils,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFolderDestination,
                       QgsCoordinateTransformContext,
                       QgsMessageLog,
                       QgsProject,
                       QgsMapLayer,
                       QgsRasterLayer, 
                       QgsVectorLayer,
                       QgsProcessingParameterVectorDestination,
                       QgsCoordinateReferenceSystem
                       )
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
import processing
import shutil


class AccessibleNavigationProcessingAlgorithm(QgsProcessingAlgorithm):
   

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    PATH_VEC = 'PATH_VEC'
    ACCESS_PATH_VEC = 'ACCESS_PATH_VEC'
    ALL_PATH_VEC = 'ALL_PATH_VEC'
    ENDPOINTS = 'ENDPOINTS'
    OUTPUT = 'OUTPUT'
    STYLE = 'STYLE'
    OUTPUT_DIR = 'OUTPUT_DIR'

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
        return 'accessiblenavigation'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Accessible Navigation')

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
        return self.tr("Creates vectors of shortest overall path and \
        shortest wheelchair accessible path between each pair of buildings \
        based on the 2010 ADA standards for ramp slopes.")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ENDPOINTS,
                self.tr('Endpoints (e.g., building entrances)'),
                [QgsProcessing.TypeVectorPoint]
                )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ACCESS_PATH_VEC,
                self.tr('Line Vector of Accessible Paths'),
                [QgsProcessing.TypeVectorLine]
                )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ALL_PATH_VEC,
                self.tr('Line Vector of All Paths'),
                [QgsProcessing.TypeVectorLine]
                )
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_DIR,
                self.tr('Directory to store Output Files'),
                [QgsProcessing.TypeVectorLine]
                )
        )
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        #self.addParameter(
        #QgsProcessingParameterFeatureSink (
        #    self.OUTPUT,
        #    self.tr('Output layer')
        #)
        #)
    
    # helper function gets the shortest path between two points
    def get_shortest_path(self, coordsA, coordsB, inputfile, tmpfile, feedback, context):
        try:
            shortest_path = processing.run("native:shortestpathpointtopoint", { 
            'DEFAULT_DIRECTION' : 2, 
            'DEFAULT_SPEED' : 50, 
            'DIRECTION_FIELD' : '', 
            'END_POINT' : coordsB , 
            'INPUT' : inputfile, 
            'OUTPUT' : tmpfile.name, 
            'SPEED_FIELD' : '', 
            'START_POINT' : coordsA, 
            'STRATEGY' : 0, 
            'TOLERANCE' : 6, 
            'VALUE_BACKWARD' : '', 
            'VALUE_BOTH' : '', 
            'VALUE_FORWARD' : '' }, feedback = feedback, context = context)['OUTPUT']
            # QgsMessageLog.logMessage("shortest path " + shortest_path, "Processing", level = 1)
            
            result_layer = QgsVectorLayer(shortest_path)
            result_layer.setShortName("shortest-path")
            return result_layer
            
        except Exception as e:
           return None
    
    # helper function updates the shortest path from building A to building B
    # if result layer's path is shorter than the current shortest path
    def update_shortest_path(self, buildingA, buildingB, result_layer, cost_dict, tmpfile):
        result_features = result_layer.getFeatures()
        for feature in result_features:
            key = buildingA + buildingB
            cost = feature.attribute("cost")
            if (not key in cost_dict or cost < cost_dict[key][0]):
                    #QgsMessageLog.logMessage("Moving " + tmpfile.name + " to " + outputfile, "Processing", level = 1)
                    #QgsMessageLog.logMessage("Because old: " + str(cost_dict[key]) + " and new: " + str(cost), "Processing", level = 1)
                    #shutil.move(tmpfile.name + ".gpkg",outputfile)
                    cost_dict[key] = [cost, tmpfile.name]
                    # QgsMessageLog.logMessage("And now the cost dictionary is" + str(cost_dict),"Processing",level=1)
                    break #Will only be one feature anyway
        result_layer = None
        return cost_dict
  
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        access_cost_dict =  dict() # keep track of shortest path between buildings
        all_cost_dict =  dict() # keep track of shortest path between buildings
                
        access_path_vec = self.parameterAsVectorLayer(
            parameters,
            self.ACCESS_PATH_VEC,
            context
        )
        
        all_path_vec = self.parameterAsVectorLayer(
            parameters,
            self.ALL_PATH_VEC,
            context
        )
        
        out_dir = self.parameterAsFile(
            parameters,
            self.OUTPUT_DIR,
            context)
        
                
        endpoints = self.parameterAsVectorLayer(
        parameters, 
        self.ENDPOINTS, 
        context)
        crs = access_path_vec.crs().authid()
        QgsMessageLog.logMessage("CRS:  " + crs, "Processing", level = 1)
        endpoint_feat1 = endpoints.getFeatures()
        
        # loop through pairs of endpoints
        for pointA in endpoint_feat1: 
            endpoint_feat2 = endpoints.getFeatures()
            for pointB in endpoint_feat2: 
                QgsMessageLog.logMessage("feature field A: " + pointA.attribute("building"), "Processing", level = 1)
                QgsMessageLog.logMessage("feature field B: " + pointB.attribute("building"), "Processing", level = 1)
                
                # endpoint building names
                buildingA = pointA.attribute("building")
                buildingB = pointB.attribute("building")
                
                # don't run if already found shortest path in other direction
                opposite_key = buildingB + buildingA
                if opposite_key in all_cost_dict: continue
                if opposite_key in access_cost_dict: continue
                
                # endpoint coordinates
                coordsA = str(pointA.geometry().vertexAt(0).x()) + "," +  str(pointA.geometry().vertexAt(0).y()) + " [" + crs + "]"
                coordsB = str(pointB.geometry().vertexAt(0).x()) + "," +  str(pointB.geometry().vertexAt(0).y()) + " [" + crs + "]"
                QgsMessageLog.logMessage("CoordsA:  " + coordsA, "Processing", level = 1)
                QgsMessageLog.logMessage("CoordsB:  " + coordsB, "Processing", level = 1)
                
                
                
                # check endpoints are in different buildings
                if not buildingA == buildingB:
                    # overall shortest path between point A and point B
                    
                    tmp = tempfile.NamedTemporaryFile(dir=out_dir)
                    #QgsMessageLog.logMessage("all out file:" + str(outputfile), "Processing", level = 1)
                    shortest_path = self.get_shortest_path(coordsA, coordsB, all_path_vec, tmp, feedback, context)
                    if not shortest_path is None:
                        all_cost_dict = self.update_shortest_path(buildingA, buildingB, shortest_path, all_cost_dict, tmp)
                        # QgsMessageLog.logMessage("overall best paths " + str(all_cost_dict), "Processing", level = 1)
                    # for accessible navigation, check that neither endpoint has an inaccessible entrance type
                    tmp.close()
                    if not pointA.attribute("entrance") == "inaccessible" and not pointB.attribute("entrance") == "inaccessible":
                        outputfile = out_dir + "\\" + buildingA + buildingB + "-accessible.gpkg"
                        tmp = tempfile.NamedTemporaryFile(dir=out_dir)
                        #QgsMessageLog.logMessage("accessible out file:" + str(outputfile), "Processing", level = 1)
                        shortest_path = self.get_shortest_path(coordsA, coordsB, access_path_vec, tmp, feedback, context)
                        if not shortest_path is None:
                            access_cost_dict = self.update_shortest_path(buildingA, buildingB, shortest_path, access_cost_dict, tmp)
                            # QgsMessageLog.logMessage("accessible best paths " + str(access_cost_dict), "Processing", level = 1)
                        tmp.close()

        QgsMessageLog.logMessage("accessible best paths " + str(access_cost_dict), "Processing", level = 1)
        QgsMessageLog.logMessage("overall best paths " + str(all_cost_dict), "Processing", level = 1)
        # QgsProject.instance().removeAllMapLayers()
        for key in access_cost_dict:
            outputfile = out_dir + "\\" + key + "-access.kml"
            input = access_cost_dict[key][1] + ".gpkg"
            result = processing.run('native:reprojectlayer',
            {'INPUT' : input, 
              'OPERATION' : '+proj=noop', 
              'OUTPUT': outputfile,
              'TARGET_CRS' : QgsCoordinateReferenceSystem('ESRI:102729') 
            })
        for key in all_cost_dict:
            outputfile = out_dir + "\\" + key + "-all.kml"
            input = all_cost_dict[key][1] + ".gpkg"
            result = processing.run('native:reprojectlayer',
            {'INPUT' : input, 
              'OPERATION' : '+proj=noop', 
              'OUTPUT': outputfile,
              'TARGET_CRS' : QgsCoordinateReferenceSystem('ESRI:102729') 
            })
    
          
        return {self.OUTPUT: all_cost_dict }
