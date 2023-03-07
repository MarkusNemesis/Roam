from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QCursor, QPixmap, QColor
from qgis.core import (QgsRectangle, QgsTolerance,
                       QgsFeatureRequest, QgsFeature, QgsGeometry,
                       QgsVectorLayer, QgsWkbTypes)
from qgis.gui import QgsMapTool, QgsRubberBand


class InspectionTool(QgsMapTool):
    """
        Inspection tool which copies the feature to a new layer
        and copies selected data from the underlying feature.
    """

    finished = pyqtSignal(QgsVectorLayer, QgsFeature)
    error = pyqtSignal(str)

    def __init__(self, canvas, layerfrom, layerto,
                 mapping, validation_method):
        """
            mapping - A dict of field - field mapping with values to
                            copy to the new layer
        """
        QgsMapTool.__init__(self, canvas)
        self.layerfrom = layerfrom
        self.layerto = layerto
        self.fields = mapping
        self.validation_method = validation_method
        self.band = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.band.setColor(QColor.fromRgb(255, 0, 0, 65))
        self.band.setWidth(5)

        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                       "      c None",
                                       ".     c #FF0000",
                                       "+     c #FFFFFF",
                                       "                ",
                                       "       +.+      ",
                                       "      ++.++     ",
                                       "     +.....+    ",
                                       "    +.     .+   ",
                                       "   +.   .   .+  ",
                                       "  +.    .    .+ ",
                                       " ++.    .    .++",
                                       " ... ...+... ...",
                                       " ++.    .    .++",
                                       "  +.    .    .+ ",
                                       "   +.   .   .+  ",
                                       "   ++.     .+   ",
                                       "    ++.....+    ",
                                       "      ++.++     ",
                                       "       +.+      "]))

    def clearBand(self):
        self.band.reset()

    def canvasReleaseEvent(self, event):
        searchRadius = (QgsTolerance.toleranceInMapUnits(5, self.layerfrom,
                                                         self.canvas().mapRenderer(), QgsTolerance.Pixels))

        point = self.toMapCoordinates(int(event.pos()))

        rect = QgsRectangle()
        rect.setXMinimum(point.x() - searchRadius)
        rect.setXMaximum(point.x() + searchRadius)
        rect.setYMinimum(point.y() - searchRadius)
        rect.setYMaximum(point.y() + searchRadius)

        rq = QgsFeatureRequest().setFilterRect(rect)

        try:
            # Only supports the first feature
            # TODO build picker to select which feature to inspect
            feature = next(self.layerfrom.getFeatures(rq))
            self.band.setToGeometry(feature.geometry(), self.layerfrom)

            fields = self.layerto.fields()
            newfeature = QgsFeature(fields)
            if self.layerto.geometryType() == QgsWkbTypes.PointGeometry:
                newfeature.setGeometry(QgsGeometry.fromPointXY(point))
            else:
                newfeature.setGeometry(QgsGeometry(feature.geometry()))

            # Set the default values
            for indx in range(fields.count()):
                newfeature[indx] = self.layerto.dataProvider().defaultValue(indx)

            # Assign the old values to the new feature
            for fieldfrom, fieldto in self.fields.items():
                newfeature[fieldto] = feature[fieldfrom]

            passed, message = self.validation_method(feature=newfeature,
                                                     layerto=self.layerto)

            if passed:
                self.finished.emit(self.layerto, newfeature)
            else:
                self.band.reset()
                self.error.emit(message)

        except StopIteration:
            pass

    def activate(self):
        """
        Set the tool as the active tool in the canvas. 

        @note: Should be moved out into qmap.py 
               and just expose a cursor to be used
        """
        self.canvas().setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
