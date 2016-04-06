# -*- coding: utf-8 -*-
"""
/***************************************************************************
 __init__
                                 A QGIS plugin
 A loader tool for inserting new features to target vector layer
                             -------------------
        copyright            : (C) 2016 by Mehmet Selim BILGIN
        email                : mselimbilgin@yahoo.com
        web                  : http://cbsuygulama.wordpress.com
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
    """Load featureLoader class from file featureLoader.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .featureLoader import featureLoader
    return featureLoader(iface)
