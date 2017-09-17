# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SiImporter
                                 A QGIS plugin
 Si maps import/export
                              -------------------
        begin                : 2016-06-21
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Olof Astrand
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QFileDialog
from PyQt4.QtCore import *

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from si_importer_dialog import SiImporterDialog
from qgis.core import *

from qgis.core import QgsPoint , QgsGeometry ,QgsFeature
import os.path
import re
import xml.etree.ElementTree as et
import math
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class SiImporter:
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
            'SiImporter_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = SiImporterDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SiImporter')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SiImporter')
        self.toolbar.setObjectName(u'SiImporter')

        self.dlg.lineEdit.clear()
        self.dlg.pushButton.clicked.connect(self.select_output_file)
        self.epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")


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
        return QCoreApplication.translate('SiImporter', message)


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
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SiImporter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Si map import / export'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SiImporter'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar



    def select_output_file(self):
        filename = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.xml')
        self.dlg.lineEdit.setText(filename)

    def export_xml(self):
        layers = self.iface.legendInterface().layers()
        print ("Exporting")
        filename = self.dlg.lineEdit.text()
        #input_file = open(filename, 'w')
        fp = open(filename, "w")
        selectedLayerIndex = self.dlg.comboBox.currentIndex()
        selectedLayer = layers[selectedLayerIndex]


        layerCRS = selectedLayer.crs()
        self.transform4326 = QgsCoordinateTransform(layerCRS, self.epsg4326)
        fp.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        fp.write("<map>\n")
        fp.write("<elements count=\"")
        count=selectedLayer.getFeatures( )
        le=0
        for fe in count:
                le += 1
        fp.write(str(le))
        fp.write("\">\n")
        for f in selectedLayer.getFeatures(  ):
            #point = self.transform4326.transform(f.geometry().asPoint())
            # fetch geometry
            geom = f.geometry()
            print geom
            print "---"

            if geom.type() == QGis.Point:
                x = geom.asPoint()
                print "Point: " + str(x)
            elif geom.type() == QGis.Line:
                fp.write("<polyline color=\"15\" linetype=\"0\" linesize=\"1\">\n")
                fp.write("<coords type=\"decimal\">\n")

                x = geom.asPolyline()
                print "Line: %d points" % len(x)
                i = 0
                for pt in x:
                        trans=self.transform4326.transform(pt)
                        s=trans.toString()
                        #print "pt", pt,s
                        #point=s[s.find("(")+1:s.find(")")]
                        #point=s.trim()
                        i += 1
                        #Last point == firts point, we dont want that
                        if i<len(x):
                            point = re.sub(r"\s+", "", s, flags=re.UNICODE)
                            fp.write(point)
                            fp.write("\n")
                fp.write("</coords>\n")
                fp.write("</polyline>\n")

            elif geom.type() == QGis.Polygon:

                x = geom.asPolygon()
                first_poly = geom.asPolygon()
                print first_poly
                numPts = 0
                for ring in x:
                    numPts += len(ring)
                    print ring
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

                print "Polygon: %d rings with %d points" % (len(x), numPts)

            else:
                print "Unknown"
        fp.write("</elements>\n")
        fp.write("</map>\n")

         
    def import_xml(self):
        layers = self.iface.legendInterface().layers()
        print ("Importing")
        filename = self.dlg.lineEdit.text()
        input_file = open(filename, 'r')

        #parse xml
        try:
            data = et.ElementTree()
            data.parse(filename)
            root = data.getroot()
            print(root)

        except:
            # raise
            message = unicode(sys.exc_info()[1])
            QMessageBox.information(self,"LandXml error","Problem importing xml\n"+message)
    


        selectedLayerIndex = self.dlg.comboBox.currentIndex()
        selectedLayer = layers[selectedLayerIndex]
        lyr=selectedLayer

        dataProvider = lyr.dataProvider()
        dataProvider.addAttributes([QgsField("name", QVariant.String)])


        name = "none"
        coordinatePairs = []            
        values = root.findall('elements/polyline')
        for elem in values:
            #print elem.find('coords'), elem.find('coords').text
            all=elem.find('coords').text
            coords = all.split()
            for coord in coords:
                p = coord.strip().split(",")
                flon=float(p[0])
                flat=float(p[1])
                if len(p)>2:
                    name=(p[2])
                coordinatePairs.append(QgsPoint(flon, flat))
                oldcoord=coord
            newPolygon = QgsGeometry.fromPolygon([coordinatePairs])
            coordinatePairs = []
            feature = QgsFeature()
            feature.setGeometry(newPolygon)
            #feature.setAttribute('name', name)

            # access the layer"s data provider, add the feature to it
            # ,QgsField("age", QVariant.Int),QgsField("size", QVariant.Double)
            dataProvider = lyr.dataProvider()
            #dataProvider.setAttributes([name])
            dataProvider.addFeatures([feature])
        coordinatePairs = []  
        #coordinatePairsList = []  
        index=0
        
        areas = root.findall('elements/fillarea')
        for elem in areas:
            nlayer_name="poly" + str(index)
            index+=1
            nlayer =  QgsVectorLayer('Polygon?crs=epsg:4326', nlayer_name , "memory")
            pr = nlayer.dataProvider() 
            #print elem.find('coords'), elem.find('coords').text
            all=elem.find('coords').text
            coords = all.split()
            for coord in coords:
                p = coord.strip().split(",")
                flon=float(p[0])
                flat=float(p[1])
                if len(p)>2:
                    name=(p[2])
                coordinatePairs.append(QgsPoint(flon, flat))
                oldcoord=coord
            newPolygon = QgsGeometry.fromPolygon([coordinatePairs])
            coordinatePairs = []
            feature = QgsFeature()
            feature.setGeometry(newPolygon)
            #feature.setAttribute('name', name)

            # access the layer"s data provider, add the feature to it
            # ,QgsField("age", QVariant.Int),QgsField("size", QVariant.Double)
            dataProvider = lyr.dataProvider()
            #dataProvider.setAttributes([name])
            dataProvider.addFeatures([feature])
            pr.addFeatures([feature])
            nlayer.updateExtents()
            QgsMapLayerRegistry.instance().addMapLayers([nlayer])
        



    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        layers = self.iface.legendInterface().layers()
        layer_list = []
        for layer in layers:
            layer_list.append(layer.name())
            self.dlg.comboBox.addItems(layer_list)

        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            if self.dlg.export_xml.isChecked():
                self.export_xml()
            else:
                self.import_xml()




            if False: '''

            row = input_file.readlines()

            fillareparse = False
            polygonareparse = False

            numfilldata = 0
            coordinatePairs = []

            selectedLayerIndex = self.dlg.comboBox.currentIndex()
            selectedLayer = layers[selectedLayerIndex]

            for line in row:
                if (fillareparse or polygonareparse):
                    #print(row)
                    info = line.split()
                    try :
                        #first=info[0]
                        for first in info:
                            #print first
                            lat, lon = first.strip().split('N') # move inside `try` just in case...
                            #lat = float( lat )
                            #lon = float( lon )
                            _,deg,min,sec,hundr,_ = re.split("([0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])",lat)
                            #print ("lat",deg,min,sec)
                            _,ldeg,lmin,lsec,lhundr,_ = re.split("([0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])",lon)
                            #print ("lon",ldeg,lmin,lsec)
                            flat=float(deg) + float(min)/60.0 + float(sec)/3660.0  + float(hundr)/360000.0
                            flon=float(ldeg) + float(lmin)/60.0 +  float(lsec)/3660.0 + float(lhundr)/360000.0
                            coordinatePairs.append(QgsPoint(flon, flat))
                            #print ("ll",flat,flon)
                    except :
                        print ("ex" , info)

                    #print (numfilldata)
                    numfilldata=int(numfilldata)
                    numfilldata=numfilldata-len(info)
                    if (numfilldata<=0):
                        #lyr = self.iface.activeLayer()
                        lyr=selectedLayer
                        if (fillareparse):
                            newPolygon = QgsGeometry.fromPolygon([coordinatePairs])
                            # create a feature, add the polygon to it
                            feature = QgsFeature()
                            feature.setGeometry(newPolygon)
                            #feature.setAttribute('name', 'hello')

                            # access the layer"s data provider, add the feature to it
                            dataProvider = lyr.dataProvider()
                            dataProvider.addFeatures([feature])

                            # refresh map canvas to see the result
                            #self.iface.mapCanvas().refresh()
                            coordinatePairs = []
                        if (polygonareparse):
                            newPolygon = QgsGeometry.fromPolygon([coordinatePairs])
                            # create a feature, add the polygon to it
                            feature = QgsFeature()
                            feature.setGeometry(newPolygon)
                            #feature.setAttribute('name', 'hello')

                            # access the layer"s data provider, add the feature to it
                            dataProvider = lyr.dataProvider()
                            dataProvider.addFeatures([feature])

                            # refresh map canvas to see the result
                            #self.iface.mapCanvas().refresh()
                            coordinatePairs = []

                        fillareparse = False
                        polygonareparse = False


                if line.find("***MAP") > -1:
                    print("Found map")
                    #coordinatePairs.append(QgsPoint(-80.23, -3.28))
                    #coordinatePairs.append(QgsPoint(-65.58, -4.21))
                    #coordinatePairs.append(QgsPoint(-65.87, 9.50))
                    #coordinatePairs.append(QgsPoint(-80.10, 10.44))
                    # create a polygon using the above coordinates


                if line.find("fillarea") > -1:
                    #print("Found fillarea")
                    fillareparse = True
                    info = line.split()
                    numfilldata = info[1]

                if line.find("polyline") > -1:
                    #print("Found polyline")
                    polygonareparse = True
                    info = line.split()
                    numfilldata = info[1]

'''

            self.iface.mapCanvas().refresh()

            #selectedLayerIndex = self.dlg.comboBox.currentIndex()
            #selectedLayer = layers[selectedLayerIndex]
            #fields = selectedLayer.pendingFields()
            #fieldnames = [field.name() for field in fields]

            #for f in selectedLayer.getFeatures():
            #    line = ','.join(unicode(f[x]) for x in fieldnames) + '\n'
            #    unicode_line = line.encode('utf-8')
            #    output_file.write(unicode_line)
            #output_file.close()
