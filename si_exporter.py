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

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from Qgis3Test_dialog import QgisMapExporter
from qgis.core import *
#QgsPoint , QgsGeometry ,QgsFeature
import os.path
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]



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
        filename = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.txt')
        self.dlg.lineEdit.setText(filename)


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
            # Do something useful here - delete the line containing pass and
            # substitute with your code.


            filename = self.dlg.lineEdit.text()
            #input_file = open(filename, 'w')
            fp = open(filename, "w")

            fillareparse = False
            polygonareparse = False

            numfilldata = 0
            coordinatePairs = []

            selectedLayerIndex = self.dlg.comboBox.currentIndex()
            selectedLayer = layers[selectedLayerIndex]

            #self.transform4326 = QgsCoordinateTransform(selectedLayer, self.epsg4326)
            layerCRS = selectedLayer.crs()
            self.transform4326 = QgsCoordinateTransform(layerCRS, self.epsg4326)


            #defaultPOI = unicode(defaultPOI).replace(u'"', u'""')
            even = 1

            for f in selectedLayer.getFeatures(  ):
                point = self.transform4326.transform(f.geometry().asPoint())
                #point = f.geometry().asPoint()
                deg=abs(float(point.y()))
                d = int(deg)
                md = abs(deg - d) * 60
                m = int(md)
                s = int(100*(md - m) * 60)
                line1 = u'{:0>2}{:0>2}{:0>4}N'.format(d,m,s)
                #print(dd2dms(dd))
                deg=abs(float(point.x()))
                d = int(deg)
                md = abs(deg - d) * 60
                m = int(md)
                s = int(100*(md - m) * 60)
                line2 = u'{:0>3}{:0>2}{:0>4}E'.format(d,m,s)
                line3 = u'{},{}'.format(point.x(), point.y())
                fp.write(line1)
                fp.write(line2)
                #fp.write(' ')
                #fp.write(line3)
                if even%2 ==0:
                        fp.write('\n')
                else:
                        fp.write(' ')
                even = even + 1
            fp.close()

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
