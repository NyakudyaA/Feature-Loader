# -*- coding: utf-8 -*-
"""
/***************************************************************************
 featureLoader
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
"""
from __future__ import absolute_import

import os.path
import timeit
from builtins import object
from builtins import str

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMessageBox, QApplication
from qgis.core import QgsVectorDataProvider, QgsProject

# Initialize Qt resources from file resources.py
# Import the code for the dialog
from .featureLoader_dialog import featureLoaderDialog
from .loader import Loader, Committer
from .result_dialog import resultDialog


class featureLoader(object):
    def __init__(self, iface):
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'featureLoader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.wkbText = {0: "GeometryUnknown", 1: "Point", 2: "LineString", 3: "Polygon", 4: "MultiPoint",
                        5: "MultiLineString",
                        6: "MultiPolygon", 7: "NoGeometry", 8: "Point25D", 9: "LineString25D", 10: "Polygon25D",
                        11: "MultiPoint25D", 12: "MultiLineString25D", 13: "MultiPolygon25D", 100: "NoGeometry"}

        # sometime qgis cannot return geometry type truly. this bug is handling in here
        self.geometryText = {0: "Point", 1: "LineString", 2: "Polygon", 3: "GeometryUnknown", 4: "NoGeometry"}

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Feature Loader')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'featureLoader')
        self.toolbar.setObjectName(u'featureLoader')

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
        return QCoreApplication.translate('featureLoader', message)

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

        icon_path = ':/plugins/featureLoader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Feature Loader'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Feature Loader'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def layerControl(self):
        if len(self.allVectorLayers) > 1:
            self.targetLayer = self.allVectorLayers[self.dlg.cmbTargetLayer.currentIndex()]
            sourceLayer = self.allVectorLayers[self.dlg.cmbSourceLayer.currentIndex()]

            openedAttrWindow = False  # This variable is used for detecting opened attribute windows.
            # During loading operation, opened windows make qgis crashed (maybe a bug)
            # so they must be closed
            for dialog in QApplication.instance().allWidgets():
                # I noticed that in my laptop getting all Qt widget's (in QGIS) names give error.
                # But no problem with desktop. Here is try-except ;)
                try:
                    if dialog.objectName() in [u'QgsAttributeTableDialog', u'AttributeTable']:
                        openedAttrWindow = True
                except:
                    pass

            if openedAttrWindow:
                QMessageBox.warning(None, u'Notification', u'Please close all attribute windows to start the process.')

            else:
                # checking target and source layers must not be in editing mode.
                if not self.targetLayer.isEditable() and not sourceLayer.isEditable():
                    # checking for targetLayer editing capability.
                    isEditable = self.targetLayer.dataProvider().capabilities() & QgsVectorDataProvider.AddFeatures
                    if isEditable:
                        # checking targetLayer and sourceLayer are not same
                        if self.targetLayer.extent() != sourceLayer.extent() or self.targetLayer.publicSource() \
                                != sourceLayer.publicSource():
                            # checking layers geometry types
                            if self.targetLayer.geometryType() == sourceLayer.geometryType():
                                self.loader = Loader(targetLayer=self.targetLayer, sourceLayer=sourceLayer)
                                self.loader.setOptions(onlySelected=self.dlg.checkBox.isChecked())

                                self.dlg.btnStart.setEnabled(False)
                                self.dlg.btnStop.setEnabled(True)
                                self.dlg.btnStop.clicked.connect(self.loader.stop)
                                self.iface.mapCanvas().setRenderFlag(False)  # QGIS can not render dramatic changes
                                # in the target layer feature count and crashes down.
                                # So before starting we need to stop rendering.

                                self.loader.progressLenght.connect(self.setProgressLength)
                                self.loader.progress.connect(self.setProgress)
                                self.loader.error.connect(self.error)
                                self.loader.finished.connect(self.done)
                                self.loader.status.connect(self.setStatus)
                                # QObject.connect(self.loader, SIGNAL('insertFeature'), self.insert)
                                self.loader.start()
                                self.start_time = timeit.default_timer()  # for calculating total run time

                            else:
                                QMessageBox.warning(self.dlg, u'Error',
                                                    u'The layers geometry types have to be same to start the process.')
                        else:
                            QMessageBox.warning(self.dlg, u'Error', u'Target Layer and Source Layer must be different.')
                    else:
                        QMessageBox.warning(self.dlg, u'Error', u'Target Layer does not support editing.')
                else:
                    QMessageBox.warning(self.dlg, u'Error',
                                        u'Target Layer and Source Layer must not be in editing mode.')
        else:
            QMessageBox.warning(self.dlg, u'Error', u'There must be at least two vector layers added in QGIS canvas.')

    def setProgress(self, val):
        self.dlg.progressBar.setValue(val)

    def setProgressLength(self, val):
        self.dlg.progressBar.setMaximum(val)
        if val == 0:
            self.dlg.btnStop.setEnabled(False)
            # this control may prevent errors when clicking stop button during saving changes.

    # def insert(self,feat):
    #     self.targetLayer.startEditing()
    #     self.targetLayer.addFeature(feat)

    def done(self):
        # this function is used by loader class's finished() signal.
        if not self.loader.hasError:
            if not self.loader.isCancel:
                # self.dlg.lblStatus
                self.committer = Committer(self.targetLayer)  # this thread saves changes to datasource.

                self.committer.finished.connect(lambda: self.commitFinished(self.targetLayer))
                self.targetLayer.startEditing()

                self.targetLayer.addFeatures(self.loader.featureList, False)

                self.dlg.btnStop.setEnabled(False)
                self.committer.commitStarted.connect(self.commitStarted)
                self.committer.start()
                # self.resultGenerator(targetLayer.commitErrors())
            else:
                self.resultGenerator(['Operation was canceled by user. All changes were rollbacked.'])
                self.onStop()
        else:
            self.onStop()

    def commitStarted(self):
        self.dlg.lblStatus.setText(u'Please wait while saving changes to the datasource...')
        self.dlg.progressBar.setMaximum(0)
        self.dlg.btnStop.setEnabled(False)

    def commitFinished(self, targetLayer):
        self.onStop()
        self.resultGenerator(targetLayer.commitErrors())

    def error(self, exception):
        QMessageBox.critical(self.dlg, 'Error', str(exception) + ' All changes were rollbacked.')

    def onStop(self):
        self.dlg.progressBar.reset()
        self.dlg.progressBar.setMaximum(1)
        self.dlg.lblStatus.clear()
        self.loader.terminate()
        try:
            del self.loader
            del self.committer
        except:
            pass
        self.dlg.btnStart.setEnabled(True)
        self.dlg.btnStop.setEnabled(False)
        self.iface.mapCanvas().setRenderFlag(True)
        self.iface.mapCanvas().refresh()

    def resultGenerator(self, commitErrorList):
        self.resultDlg.textEdit.clear()
        total_run_time = '<p></p><b>Total execution time is %.2f seconds.</b><p></p>' \
                         % (timeit.default_timer() - self.start_time)
        self.resultDlg.textEdit.append(total_run_time)  # First line is total tun time information
        for errorString in commitErrorList:
            self.resultDlg.textEdit.append(errorString)
        self.resultDlg.exec_()

    def setStatus(self, message):
        self.dlg.lblStatus.setText(message)

    def run(self):
        self.dlg = featureLoaderDialog()
        self.resultDlg = resultDialog()
        self.resultDlg.setFixedSize(self.resultDlg.size())
        self.dlg.setFixedSize(self.dlg.size())
        self.allVectorLayers = []
        self.allMapLayers = list(QgsProject.instance().mapLayers().items())

        for (notImportantForNow, layerObj) in self.allMapLayers:
            if layerObj.type() == 0:  # 0 is vectorlayer
                self.allVectorLayers.append(layerObj)
                if layerObj.wkbType() in self.wkbText:
                    # Sometime qgis cannot return geometry type truly. This bug is handling in here
                    cmbLabel = layerObj.name() + ' (%d) (%s)' \
                               % (layerObj.featureCount(), self.wkbText[layerObj.wkbType()])
                else:
                    cmbLabel = layerObj.name() + ' (%d) (%s)' \
                               % (layerObj.featureCount(), self.geometryText[layerObj.geometryType()])
                self.dlg.cmbTargetLayer.addItem(cmbLabel)
                self.dlg.cmbSourceLayer.addItem(cmbLabel)

        self.dlg.btnStart.clicked.connect(self.layerControl)

        # if len(self.allVectorLayers) < 2:
        #     self.dlg.btnStart.setEnabled(False)

        result = self.dlg.exec_()

        # Closing control
        if not result:
            try:
                self.loader.stop()
                self.committer.terminate()
                del self.loader
                del self.committer
            except:
                pass
