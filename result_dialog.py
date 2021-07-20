# -*- coding: utf-8 -*-
"""
/***************************************************************************
 featureLoaderDialog
                                 A QGIS plugin
 A loader tool for inserting new features to target vector layer
                             -------------------
        begin                : 2016-02-19
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Mehmet Selim BILGIN
        email                : mselimbilgin@yahoo.com
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

import os

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'result.ui'))


class resultDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(resultDialog, self).__init__(parent)
        self.setupUi(self)
