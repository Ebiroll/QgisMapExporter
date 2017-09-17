# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisMapExporter
                                 A QGIS plugin
 tdp map exporter
                             -------------------
        begin                : 2017-09-17
        copyright            : (C) 2017 by Olof Astrand
        email                : olof.astrand@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QgisMapExporter class from file QgisMapExporter.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .Qgis3Test import QgisMapExporter
    return QgisMapExporter(iface)
