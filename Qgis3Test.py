# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisMapExporter
                                 A QGIS plugin
 tdp map exporter
                              -------------------
        begin                : 2017-09-17
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Olof Astrand
        email                : olof.astrand@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

from qgis.core import QgsMapLayerProxyModel, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject
from qgis.gui import QgsMessageBar
from qgis.core import QgsPoint , QgsGeometry ,QgsFeature

from qgis.core import  QgsCoordinateTransform , QgsCoordinateReferenceSystem 
# from qgis.core import QGis, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsWKBTypes 
#import os.path
import re
#import xml.etree.ElementTree as et
import math
#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Qgis3Test_dialog import QgisMapExporterDialog
import os.path
import os

def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]

class QgisMapExporter:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QgisMapExporter_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        
        # Create the dialog (after translation) and keep reference
        self.epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        self.dlg = QgisMapExporterDialog()
        #self.dlg.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer | QgsMapLayerProxyModel.NoGeometry)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&QgisMapExporter')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'QgisMapExporter')
        self.toolbar.setObjectName(u'QgisMapExporter')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QgisMapExporter', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QgisMapExporter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Vecor'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&QgisMapExporter'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def export_map(self):
        print ("Exporting map")
        filename = self.dlg.lineEdit.text()
        fp = open(filename, "w")
        print(filename)
        even = 1
        numPts = 0
        layer = self.iface.activeLayer()
        self.epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        layerCRS = layer.crs()
        #self.transform4326 = QgsCoordinateTransform(layerCRS, self.epsg4326)
        self.transform4326 = QgsCoordinateTransform(layerCRS,
                                QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())

        iter = layer.getFeatures()
        fp.write("***MAP ")
        fp.write(filename);
        fp.write("\n")
        for feature in iter:
            # retrieve every feature with its geometry and attributes
            # fetch geometry
            geom = feature.geometry()
            #print ("Feature ID %d: " % feature.id())

            # show some information about the feature
            print (geom.type())
            
            if geom.type() == 2:
                #print(geom.wkbType())
                #print(geom.asWkt()) 
                # is WKBMultiPolygon
                #print(y)
                #first_poly = geom.asPolygon()
                #print (first_poly)                
                fp.write("linewidth 0\n")                    
                fp.write("linetype 0\n")                    
                fp.write("linecolourix 3\n")                    

                if geom.wkbType() == 6:
                    y = geom.asMultiPolygon()                
                    for ring in y:
                        #numPts += len(ring)
                        print("X")
                        #print (ring)
                        #fp.write("<fillarea color=\"3\" linetype=\"0\" filltype=\"0\" linesize=\"1\">\n")
                        #fp.write("<coords type=\"decimal\">\n")
                        for poly in ring:
                            numPts += len(poly)
                            even = 1
                            le=0
                            for fe in poly:
                                le += 1
                            fp.write("polyline ");  
                            fp.write(str(le))
                            fp.write("\n")
                            for pt in poly:                            
                                point=self.transform4326.transform(pt)
                                #print("trans")
                                #print(trans)                            
                                deg=abs(float(point.y()))
                                d = int(deg)
                                md = abs(deg - d) * 60
                                m = int(md)
                                s = int(1*(md - m) * 60)
                                #For airport maps 
                                #  s = int(100*(md - m) * 60)
                                #line1 = u'{:0>2}{:0>2}{:0>4}N'.format(d,m,s)
                                line1 = u'{:0>2}{:0>2}{:0>2}N'.format(d,m,s)
                                #print(dd2dms(dd))
                                deg=abs(float(point.x()))
                                d = int(deg)
                                md = abs(deg - d) * 60
                                m = int(md)
                                s = int(1*(md - m) * 60)
                                # For airport maps
                                # s = int(100*(md - m) * 60)
                                # line2 = u'{:0>3}{:0>2}{:0>4}E'.format(d,m,s)
                                line2 = u'{:0>3}{:0>2}{:0>2}E'.format(d,m,s)
                                line3 = u'{},{}'.format(point.x(), point.y())
                                fp.write(line1)
                                fp.write(line2)
                                print(line1,line2)
                                #fp.write(' ')
                                #fp.write(line3)
                                if even%2 ==0:
                                        print('\n')
                                        fp.write('\n')
                                else:
                                        print(' ')
                                        fp.write(' ')
                                even = even + 1                            
                            print(numPts)
                            numPts=0
                            fp.write("\n")
                else:
                    print ("Unknown wkbType")
                    print(geom.wkbType())
            elif geom.type() == 1:
                if geom.wkbType() == 5:
                    x = geom.asMultiPolyline()
                else:
                    x = geom.asPolyline()
                for poly in x:
                    #print(poly)
                    numPts += len(poly)
                    even = 1
                    le = numPts
                    #for fe in poly:
                    #    le += 1                        
                    fp.write("linewidth 0\n")                    
                    fp.write("linetype 0\n")                    
                    fp.write("linecolourix 3\n")                    
                    fp.write("polyline ");  
                    fp.write(str(le))
                    fp.write("\n")
                    for pt in poly:                            
                        point=self.transform4326.transform(pt)
                        #print("trans")
                        #print(trans)                            
                        deg=abs(float(point.y()))
                        d = int(deg)
                        md = abs(deg - d) * 60
                        m = int(md)
                        s = int(1*(md - m) * 60)
                        #For airport maps 
                        #  s = int(100*(md - m) * 60)
                        #line1 = u'{:0>2}{:0>2}{:0>4}N'.format(d,m,s)
                        line1 = u'{:0>2}{:0>2}{:0>2}N'.format(d,m,s)
                        #print(dd2dms(dd))
                        deg=abs(float(point.x()))
                        d = int(deg)
                        md = abs(deg - d) * 60
                        m = int(md)
                        s = int(1*(md - m) * 60)
                        # For airport maps
                        # s = int(100*(md - m) * 60)
                        # line2 = u'{:0>3}{:0>2}{:0>4}E'.format(d,m,s)
                        line2 = u'{:0>3}{:0>2}{:0>2}E'.format(d,m,s)
                        line3 = u'{},{}'.format(point.x(), point.y())
                        fp.write(line1)
                        fp.write(line2)
                        #print(line1,line2)
                        #fp.write(' ')
                        #fp.write(line3)
                        if even%2 ==0:
                                #print('\n')
                                fp.write('\n')
                        else:
                                #print(' ')
                                fp.write(' ')
                        even = even + 1                            
                    print(numPts)
                    numPts=0
                    fp.write("\n")
                    #trans=self.transform4326.transform(pt)
                    #s=trans.toString()
                    #print("pt", pt,s)
            else:
                print ("Unknown Geometry")
            fp.write("\n")
        fp.close()

    def export_multipolyline_xml(self,polyline,fp):
        print ("Line: %d points" % len(polyline))
        fp.write("<polyline color=\"3\" linetype=\"0\" linesize=\"0\">\n")
        #fp.write("<fillarea color=\"15\" linetype=\"0\" filltype=\"0\" linesize=\"1\">\n")
        fp.write("<coords type=\"decimal\">\n")

        for x in polyline:
            print ("Line: %d points" % len(x))
            i = 0
            for pt in x:
                    trans=self.transform4326.transform(pt)
                    s=trans.toString()
                    #print "pt", pt,s
                    #point=s[s.find("(")+1:s.find(")")]
                    #point=s.trim()
                    i += 1
                    #Last point == first point, we dont want that
                    if i<len(x)+1:
                        point = re.sub(r"\s+", "", s, flags=re.UNICODE)
                        fp.write(point)
                        fp.write("\n")
            fp.write("</coords>\n")
            fp.write("</polyline>\n")
            #fp.write("</fillarea>\n")


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        #layers = self.iface.legendInterface().layers()
        #layer_list = []
        #for layer in layers:
        #    layer_list.append(layer.name())
        #    self.dlg.comboBox.addItems(layer_list)
        cwd = os.getcwd()
        print(cwd)

        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            #selectedLayerIndex = self.dlg.mMapLayerComboBox.currentIndex()
            #selectedLayer = layers[selectedLayerIndex]
            print("running")

            if self.dlg.export_map.isChecked():
                self.export_map()
            else:
                filename = self.dlg.lineEdit.text()
                #input_file = open(filename, 'w')
                print("file" , filename)
                #fp = open(filename, "w")
                layer = self.iface.activeLayer()

                filename = self.dlg.lineEdit.text() + ".xml"
                fp = open(filename, "w")
                fp.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
                fp.write("<map>\n")
                fp.write("<elements count=\"")

                count=layer.getFeatures( )
                le=0
                for fe in count:
                        le += 1
                fp.write(str(le))
                fp.write("\">\n")

                self.epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
                layerCRS = layer.crs()
                #self.transform4326 = QgsCoordinateTransform(layerCRS, self.epsg4326)
                self.transform4326 = QgsCoordinateTransform(layerCRS,
                                    QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())

                iter = layer.getFeatures()
                for feature in iter:
                    # retrieve every feature with its geometry and attributes
                    # fetch geometry
                    geom = feature.geometry()
                    #print ("Feature ID %d: " % feature.id())

                    # show some information about the feature
                    #print (geom.type())
                    
                    if geom.type() == 1:
                        #print(geom.wkbType())
                        if geom.wkbType() == 5:
                            #print(geom)
                            x = geom.asMultiPolyline()
                            self.export_multipolyline_xml(x,fp)
                        else:
                            x = geom.asPolyline()
                            print ("Poly Line: %d points" % len(x))
                            fp.write("<polyline color=\"3\" linetype=\"0\" linesize=\"0\">\n")
                            #fp.write("<fillarea color=\"15\" linetype=\"0\" filltype=\"0\" linesize=\"1\">\n")
                            fp.write("<coords type=\"decimal\">\n")

                            x = geom.asPolyline()
                            print ("Line: %d points" % len(x))
                            i = 0
                            for pt in x:
                                    trans=self.transform4326.transform(pt)
                                    s=trans.toString()
                                    #print "pt", pt,s
                                    #point=s[s.find("(")+1:s.find(")")]
                                    #point=s.trim()
                                    i += 1
                                    #Last point == first point, we dont want that
                                    if i<len(x)+1:
                                        point = re.sub(r"\s+", "", s, flags=re.UNICODE)
                                        fp.write(point)
                                        fp.write("\n")
                            fp.write("</coords>\n")
                            fp.write("</polyline>\n")
                            #fp.write("</fillarea>\n")                
                    elif geom.type() == 2:
                    # QGis.Polygon:
                        x = geom.asPolygon()
                        first_poly = geom.asPolygon()
                        print (first_poly)
                        numPts = 0
                        for ring in x:
                            numPts += len(ring)
                            print (ring)
                            fp.write("<fillarea color=\"3\" linetype=\"0\" filltype=\"0\" linesize=\"1\">\n")
                            fp.write("<coords type=\"decimal\">\n")                    
                            for pt in ring:
                                trans=self.transform4326.transform(pt)
                                s=trans.toString()
                                point = re.sub(r"\s+", "", s, flags=re.UNICODE)
                                fp.write(point)
                                fp.write("\n")
                            fp.write("</coords>\n")
                            fp.write("</fillarea>\n")
                    else:
                        print ("Unknown")


                fp.write("</elements>\n")
                fp.write("</map>\n")
                fp.close()


                #if geom.type() == QgsPoint:
                #    x = geom.asPoint()
                #    print ("Point: " + str(x))
                #elif geom.type() == QGis.Line:
                #    x = geom.asPolyline()
                #    print ("Line: %d points" % len(x))
                #elif geom.type() == QGis.Polygon:
                #    x = geom.asPolygon()
                #    numPts = 0
                #    for ring in x:
                #        numPts += len(ring)
                #    print ("Polygon: %d rings with %d points" % (len(x), numPts))
                #else:
                #    print ("Unknown")

                # fetch attributes
                #attrs = feature.attributes()

                # attrs is a list. It contains all the attribute values of this feature
                #print (attrs)
            
