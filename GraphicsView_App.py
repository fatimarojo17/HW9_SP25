# region imports
from GraphicsView_GUI import Ui_Form
import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import math
import sys
import numpy as np
import scipy as sp
from scipy import optimize


# endregion

# region class definitions
class RigidLink(qtw.QGraphicsItem):

    def __init__(self, stX, stY, enX, enY, radius=10, parent=None, pen=None, brush=None, name='RigidLink'):
        """
        This is a custom class for drawing a rigid link.  The paint function executes everytime the scene
        which holds the link is updated.  The steps to making the link are:

        1. Specify the pen, brush, start and end x,y coordinates of the link and radius by unpacking arguments
        2. Compute the length and angle of the link (also sets self.DX, self.DY)
        3. Compute the rectangle that will contain the link (i.e., its bounding box)
        4. Setup the transformation that will rotate and then translate the link

        *Note:  The paint function is called each time the scene changes.  I draw a link aligned with the x-axis first
        with the start point at 0,0 and end point at length, 0. Then, the path painter draws the centerline and the
        start and end pivot points, then the start semicircle, a line to the end semicircle, the end semicircle,
        and a line back to the start semicircle.  Finally, the link is rotated about 0,0 and then translated to startX,
        startY.  In this way, the bounding rectangle gets transformed and this helps with detecting the item in the
        graphics view when the mouse hovers.

        :param stX:
        :param stY:
        :param enX:
        :param enY:
        :param radius:
        :param parent:
        :param pen:
        :param brush:
        """
        super().__init__(parent)

        # Step 1
        self.pen = pen
        self.brush = brush
        self.name = name
        self.startX = stX
        self.startY = stY
        self.endX = enX
        self.endY = enY
        self.radius = radius

        # Step 2
        self.angle = self.linkAngle()

        # Step 3
        self.rect = qtc.QRectF(-self.radius, -self.radius, self.length + self.radius, self.radius)

        # Step 4
        self.transform = qtg.QTransform()
        self.transform.reset()

    def boundingRect(self):
        return self.transform.mapRect(self.rect)

    def deltaY(self):
        self.DY = self.endY - self.startY
        return self.DY

    def deltaX(self):
        self.DX = self.endX - self.startX
        return self.DX

    def linkLength(self):
        self.length = math.sqrt(math.pow(self.deltaX(), 2) + math.pow(self.deltaY(), 2))
        return self.length

    def linkAngle(self):
        self.linkLength()
        if self.length == 0.0:
            self.angle = 0
        else:
            self.angle = math.acos(self.DX / self.length)
            self.angle *= -1 if (self.DY > 0) else 1
        return self.angle

    def paint(self, painter, option, widget=None):
        """
        This function creates a path painter the paints a semicircle around the start point (ccw), a straight line
        offset from the main axis of the link, a semicircle around the end point (ccw), and a straight line offset from
        the main axis.  It then assigns a pen and brush.  Finally, it draws a circle at the start and end points to
        indicate the pivot points.
        :param painter:
        :param option:
        :param widget:
        :return:
        """
        # Instantiate painter path
        path = qtg.QPainterPath()

        # Compute length and angle
        len = self.linkLength()
        angLink = self.linkAngle() * 180 / math.pi

        # Define rectangles for semicircular ends
        rectSt = qtc.QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
        rectEn = qtc.QRectF(self.length - self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

        # Draw dashed centerline
        centerLinePen = qtg.QPen()
        centerLinePen.setStyle(qtc.Qt.DashDotLine)
        r, g, b, a = self.pen.color().getRgb()
        centerLinePen.setColor(qtg.QColor(r, g, b, 128))
        centerLinePen.setWidth(1)
        p1 = qtc.QPointF(0, 0)
        p2 = qtc.QPointF(len, 0)
        painter.setPen(centerLinePen)
        painter.drawLine(p1, p2)

        # Draw link shape: start semicircle, line, end semicircle, line back
        path.arcMoveTo(rectSt, 90)
        path.arcTo(rectSt, 90, 180)
        path.lineTo(self.length, self.radius)
        path.arcMoveTo(rectEn, 270)
        path.arcTo(rectEn, 270, 180)
        path.lineTo(0, -self.radius)

        # Apply pen and brush
        if self.pen is not None:
            painter.setPen(self.pen)
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawPath(path)

        # Draw pivot point circles
        pivotStart = qtc.QRectF(-self.radius / 6, -self.radius / 6, self.radius / 3, self.radius / 3)
        pivotEnd = qtc.QRectF(self.length - self.radius / 6, -self.radius / 6, self.radius / 3, self.radius / 3)
        painter.drawEllipse(pivotStart)
        painter.drawEllipse(pivotEnd)

        # Update bounding rectangle
        self.rect = qtc.QRectF(-self.radius, -self.radius, self.length + 2 * self.radius, 2 * self.radius)

        # Apply transformations: rotate then translate
        self.transform.reset()
        self.transform.translate(self.startX, self.startY)
        self.transform.rotate(-angLink)
        self.setTransform(self.transform)
        self.transform.reset()

        # Set tooltip with link details
        stTT = (self.name + "\nstart: ({:0.3f}, {:0.3f})\nend: ({:0.3f}, {:0.3f})\n"
                            "length: {:0.3f}\nangle: {:0.3f}".format(
            self.startX, self.startY, self.endX, self.endY, self.length, self.angle * 180 / math.pi))
        self.setToolTip(stTT)


class RigidPivotPoint(qtw.QGraphicsItem):

    def __init__(self, ptX, ptY, pivotHeight, pivotWidth, parent=None, pen=None, brush=None, rotation=0,
                 name='RigidPivotPoint'):

        super().__init__(parent)

        # Step 1
        self.x = ptX
        self.y = ptY
        self.pen = pen
        self.brush = brush
        self.height = pivotHeight
        self.width = pivotWidth
        self.radius = min(self.height, self.width) / 4
        self.rotationAngle = rotation
        self.name = name

        # Step 2
        self.rect = qtc.QRectF(self.x - self.width / 2, self.y - self.radius, self.width, self.height + self.radius)

        # Step 3
        self.transformation = qtg.QTransform()

        # Step 4
        stTT = self.name + "\nx={:0.3f}, y={:0.3f}".format(self.x, self.y)
        self.setToolTip(stTT)

    def boundingRect(self):
        """
        Return the transformed bounding rectangle for mouse interaction.

        :return: QRectF, the bounding rectangle after transformation
        """
        return self.transformation.mapRect(self.rect)

    def rotate(self, angle):
        """
        Set the rotation angle of the pivot.

        :param angle: Rotation angle in degrees
        """
        self.rotationAngle = angle

    def paint(self, painter, option, widget=None):

        # Instantiate painter path
        path = qtg.QPainterPath()
        radius = min(self.height, self.width) / 2

        # Compute trapezoid geometry
        H = math.sqrt(math.pow(self.width / 2, 2) + math.pow(self.height, 2))
        phi = math.asin(radius / H)
        theta = math.asin(self.height / H)
        ang = math.pi - phi - theta
        l = H * math.cos(phi)

        # Define trapezoid points
        x1 = self.width / 2
        y1 = self.height
        path.moveTo(x1, y1)
        x2 = l * math.cos(ang)
        y2 = l * math.sin(ang)
        path.lineTo(x1 + x2, y1 - y2)

        # Draw pivot arc
        pivotRect = qtc.QRectF(-radius, -radius, 2 * radius, 2 * radius)
        stAng = math.pi / 2 - phi - theta
        spanAng = math.pi - 2 * stAng
        path.arcTo(pivotRect, stAng * 180 / math.pi, spanAng * 180 / math.pi)

        # Complete trapezoid
        x4 = -self.width / 2
        y4 = self.height
        path.lineTo(x4, y4)

        # Apply pen and brush
        if self.pen is not None:
            painter.setPen(self.pen)
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawPath(path)

        # Draw pivot point circle
        pivotPtRect = qtc.QRectF(-radius / 4, -radius / 4, radius / 2, radius / 2)
        painter.drawEllipse(pivotPtRect)

        # Draw base line
        x5 = -self.width
        x6 = self.width
        painter.drawLine(x5, y4, x6, y4)

        # Draw hatched support rectangle
        penOutline = qtg.QPen(qtc.Qt.NoPen)
        hatchbrush = qtg.QBrush(qtc.Qt.BDiagPattern)
        painter.setPen(penOutline)
        painter.setBrush(hatchbrush)
        support = qtc.QRectF(x5, y4, self.width * 2, self.height)
        painter.drawRect(support)

        # Update bounding rectangle
        self.rect = qtc.QRectF(-self.width, -self.radius, self.width * 2, self.height * 2 + self.radius)

        # Apply transformations
        self.transformation.reset()
        self.transformation.translate(self.x, self.y)
        self.transformation.rotate(self.rotationAngle)
        self.setTransform(self.transformation)
        self.transformation.reset()


class MainWindow(Ui_Form, qtw.QWidget):

    def __init__(self):
        """
         This program illustrates the use of the graphics view framework.  The QGraphicsView widget is created in
        designer.  The QGraphicsView displays a QGraphicsScene.  A QGraphicsScene contains QGraphicsItem objects
        """
        super().__init__()

        # Step 1
        self.setupUi(self)

        # Step 2
        self.setupGraphics()

        # Step 3
        self.gv_Main.setMouseTracking(True)
        self.pushButton.setMouseTracking(True)
        self.setMouseTracking(True)

        # Step 4
        self.buildScene()
        self.prevAlpha = self.link1.angle
        self.prevBeta = self.link3.angle
        self.angle1 = math.pi
        self.angle2 = math.pi

        # Step 5
        self.spnd_Zoom.valueChanged.connect(self.setZoom)
        self.pushButton.clicked.connect(self.pickAColor)
        self.scene.installEventFilter(self)
        self.mouseDown = False
        self.show()

    def setupGraphics(self):
        """
        Set up the QGraphicsScene and assign it to the QGraphicsView.

        """
        # Step 1
        self.scene = qtw.QGraphicsScene()
        self.scene.setObjectName("MyScene")
        self.scene.setSceneRect(-200, -200, 400, 400)  # xLeft, yTop, Width, Height

        # Step 2
        self.gv_Main.setScene(self.scene)

        # Step 3
        self.setupPensAndBrushes()

    def setupPensAndBrushes(self):
        """
        Define pens and brushes for drawing.

        """
        # Step 1
        self.penThick = qtg.QPen(qtc.Qt.darkGreen)
        self.penThick.setWidth(5)  # Thick green pen
        self.penMed = qtg.QPen(qtc.Qt.darkBlue)
        self.penMed.setStyle(qtc.Qt.SolidLine)
        self.penMed.setWidth(2)  # Medium blue pen
        self.penLink = qtg.QPen(qtg.QColor("orange"))
        self.penLink.setWidth(1)  # Thin orange pen for links
        self.penGridLines = qtg.QPen()
        self.penGridLines.setWidth(1)
        self.penGridLines.setColor(qtg.QColor.fromHsv(197, 144, 228, 128))  # Grid line pen

        # Step 2
        self.brushFill = qtg.QBrush(qtc.Qt.darkRed)  # Solid red fill
        self.brushHatch = qtg.QBrush()
        self.brushHatch.setStyle(qtc.Qt.DiagCrossPattern)  # Hatch pattern
        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, 128))  # Grid background
        self.brushLink = qtg.QBrush(qtg.QColor.fromHsv(35, 255, 255, 64))  # Link fill
        self.brushPivot = qtg.QBrush(qtg.QColor.fromHsv(0, 0, 128, 255))  # Pivot fill

    def mouseMoveEvent(self, a0: qtg.QMouseEvent):
        """
        Update window title with mouse coordinates and widget name.

        """
        w = app.widgetAt(a0.globalPos())
        name = 'none' if w is None else w.objectName()
        self.setWindowTitle(str(a0.x()) + ',' + str(a0.y()) + name)

    def eventFilter(self, obj, event):
        """
        Handle mouse and wheel events in the graphics scene.

        """
        if obj == self.scene:
            if event.type() == qtc.QEvent.GraphicsSceneMouseMove:
                # Update window title with screen and scene coordinates
                screenPos = event.screenPos()
                scenePos = event.scenePos()
                strScreen = "screen x = {}, screen y = {}".format(screenPos.x(), screenPos.y())
                strScene = ":  scene x = {}, scene y = {}".format(scenePos.x(), scenePos.y())
                self.setWindowTitle(strScreen + strScene)

                if self.mouseDown:
                    # Compute link lengths
                    l1 = self.link1.linkLength()
                    l2 = self.link2.linkLength()
                    l3 = self.link3.linkLength()

                    # Get mouse position
                    x = scenePos.x()
                    y = scenePos.y()

                    # Calculate angle for link1
                    if x == self.link1.startX:
                        self.angle1 = math.pi / 2 if y <= self.link1.startY else math.pi * 3.0 / 2.0
                    else:
                        self.angle1 = math.atan(-(y - self.link1.startY) / (x - self.link1.startX))
                        self.angle1 += math.pi if x < self.link1.startX else 0

                    # Calculate angle for link3
                    if self.link3.endX == self.link3.startX:
                        self.angle2 = math.pi / 2 if self.link3.endY <= self.link3.startY else math.pi * 3.0 / 2.0
                    else:
                        self.angle2 = math.atan(
                            -(self.link3.endY - self.link2.startY) / (self.link3.endX - self.link3.startX))
                        self.angle2 += math.pi if self.link3.endX < self.link3.startX else 0

                    # Update link1 position
                    self.link1.endX = self.link1.startX + math.cos(self.angle1) * l1
                    self.link1.endY = self.link1.startY - math.sin(self.angle1) * l1
                    x1 = self.link1.endX
                    y1 = self.link1.endY

                    # Solve for link3 angle to maintain link2 length
                    def fn1(angle2):
                        x2 = self.link3.startX + l3 * math.cos(angle2)
                        y2 = self.link3.startY - l3 * math.sin(angle2)
                        self.lTest = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2))
                        return l2 - self.lTest

                    result = optimize.fsolve(fn1, [self.angle2])

                    # Check if solution is valid
                    if abs(self.lTest - l2) > 0.001:
                        self.angle2 = self.prevBeta
                        self.angle1 = self.prevAlpha
                        self.link1.endX = self.link1.startX + math.cos(self.angle1) * l1
                        self.link1.endY = self.link1.startY - math.sin(self.angle1) * l1
                    else:
                        self.angle2 = result[0]
                        self.prevAlpha = self.angle1
                        self.prevBeta = self.angle2

                    # Update link3 and link2 positions
                    self.link3.endX = self.link3.startX + l3 * math.cos(self.angle2)
                    self.link3.endY = self.link3.startY - l3 * math.sin(self.angle2)
                    self.link2.startX = self.link1.endX
                    self.link2.startY = self.link1.endY
                    self.link2.endX = self.link3.endX
                    self.link2.endY = self.link3.endY
                    self.scene.update()

            elif event.type() == qtc.QEvent.GraphicsSceneWheel:
                # Adjust zoom with wheel
                if event.delta() > 0:
                    self.spnd_Zoom.stepUp()
                else:
                    self.spnd_Zoom.stepDown()

            elif event.type() == qtc.QEvent.GraphicsSceneMousePress:
                if event.button() == qtc.Qt.LeftButton:
                    self.mouseDown = True

            elif event.type() == qtc.QEvent.GraphicsSceneMouseRelease:
                self.mouseDown = False

        return super(MainWindow, self).eventFilter(obj, event)

    def buildScene(self):
        """
        Construct the graphics scene with grid, pivots, and links.

        """
        # Step 1
        self.scene.clear()

        # Step 2
        self.drawAGrid(DeltaX=10, DeltaY=10, Height=400, Width=400, Pen=self.penGridLines, Brush=self.brushGrid)

        # Step 3
        self.pivot0 = self.drawPivot(-100, 0, 10, 20)
        self.pivot0.setTransformOriginPoint(qtc.QPointF(self.pivot0.x, self.pivot0.y))
        self.pivot0.rotate(90)
        self.pivot1 = self.drawPivot(60, -30, 10, 20)
        self.pivot1.setTransformOriginPoint(qtc.QPointF(self.pivot1.x, self.pivot1.y))
        self.pivot1.rotate(-90)

        # Step 4
        self.link0 = self.drawLinkage(self.pivot0.x, self.pivot0.y, self.pivot1.x, self.pivot1.y, radius=5,
                                      pen=self.penGridLines, brush=self.brushGrid)
        self.link1 = self.drawLinkage(-100, 0, -100, -60, 5)
        self.link2 = self.drawLinkage(-100, -60, 100, -150, 5)
        self.link3 = self.drawLinkage(60, -30, 100, -150, 5)

    def drawAGrid(self, DeltaX=10, DeltaY=10, Height=200, Width=200, CenterX=0, CenterY=0, Pen=None, Brush=None,
                  SubGrid=None):
        """
        Draw a reference grid in the scene.

        """
        # Set grid dimensions
        height = self.scene.sceneRect().height() if Height is None else Height
        width = self.scene.sceneRect().width() if Width is None else Width
        left = self.scene.sceneRect().left() if CenterX is None else (CenterX - width / 2.0)
        right = self.scene.sceneRect().right() if CenterX is None else (CenterX + width / 2.0)
        top = self.scene.sceneRect().top() if CenterY is None else (CenterY - height / 2.0)
        bottom = self.scene.sceneRect().bottom() if CenterY is None else (CenterY + height / 2.0)
        Dx = DeltaX
        Dy = DeltaY
        pen = qtg.QPen() if Pen is None else Pen

        # Draw background rectangle
        if Brush is not None:
            rect = self.drawARectangle(left, top, width, height)
            rect.setBrush(Brush)
            rect.setPen(pen)

        # Draw vertical lines
        x = left
        while x <= right:
            lVert = self.drawALine(x, top, x, bottom)
            lVert.setPen(pen)
            x += Dx

        # Draw horizontal lines
        y = top
        while y <= bottom:
            lHor = self.drawALine(left, y, right, y)
            lHor.setPen(pen)
            y += Dy

    def drawARectangle(self, leftX, topY, widthX, heightY, pen=None, brush=None):
        """
        Draw a rectangle in the scene.

        """
        rect = qtw.QGraphicsRectItem(leftX, topY, widthX, heightY)
        if brush is not None:
            rect.setBrush(brush)
        if pen is not None:
            rect.setPen(pen)
        self.scene.addItem(rect)
        return rect

    def drawALine(self, stX, stY, enX, enY, pen=None):
        """
        Draw a line in the scene.

        """
        if pen is None:
            pen = self.penMed
        line = qtw.QGraphicsLineItem(stX, stY, enX, enY)
        line.setPen(pen)
        self.scene.addItem(line)
        return line

    def polarToRect(self, centerX, centerY, radius, angleDeg=0):
        """
        Convert polar coordinates to rectangular coordinates.

        """
        angleRad = angleDeg * 2.0 * math.pi / 360.0
        return centerX + radius * math.cos(angleRad), centerY + radius * math.sin(angleRad)

    def drawACircle(self, centerX, centerY, Radius, angle=0, brush=None, pen=None):
        """
        Draw a circle in the scene.

        """
        ellipse = qtw.QGraphicsEllipseItem(centerX - Radius, centerY - Radius, 2 * Radius, 2 * Radius)
        if pen is not None:
            ellipse.setPen(pen)
        if brush is not None:
            ellipse.setBrush(brush)
        self.scene.addItem(ellipse)
        return ellipse

    def drawASquare(self, centerX, centerY, Size, brush=None, pen=None):
        """
        Draw a square in the scene.

        """
        sqr = qtw.QGraphicsRectItem(centerX - Size / 2.0, centerY - Size / 2.0, Size, Size)
        if pen is not None:
            sqr.setPen(pen)
        if brush is not None:
            sqr.setBrush(brush)
        self.scene.addItem(sqr)
        return sqr

    def drawATriangle(self, centerX, centerY, Radius, angleDeg=0, brush=None, pen=None):
        """
        Draw a triangle in the scene.

        """
        pts = []
        x, y = self.polarToRect(centerX, centerY, Radius, 0 + angleDeg)
        pts.append(qtc.QPointF(x, y))
        x, y = self.polarToRect(centerX, centerY, Radius, 120 + angleDeg)
        pts.append(qtc.QPointF(x, y))
        x, y = self.polarToRect(centerX, centerY, Radius, 240 + angleDeg)
        pts.append(qtc.QPointF(x, y))
        x, y = self.polarToRect(centerX, centerY, Radius, 0 + angleDeg)
        pts.append(qtc.QPointF(x, y))

        pg = qtg.QPolygonF(pts)
        PG = qtw.QGraphicsPolygonItem(pg)
        if pen is not None:
            PG.setPen(pen)
        if brush is not None:
            PG.setBrush(brush)
        self.scene.addItem(PG)
        return PG

    def drawAnArrow(self, startX, startY, endX, endY, pen=None, brush=None):
        """
        Draw an arrow (line with triangular head) in the scene.

        """
        line = qtw.QGraphicsLineItem(startX, startY, endX, endY)
        p = qtg.QPen() if pen is None else pen
        line.setPen(p)
        angleDeg = 180.0 / math.pi * math.atan((endY - startY) / (endX - startX))
        self.scene.addItem(line)
        self.drawATriangle(endX, endY, 5, angleDeg=angleDeg, pen=pen, brush=brush)

    def drawRigidSurface(self, centerX, centerY, Width=10, Height=3, pen=None, brush=None):
        """
        Draw a surface with a solid top line and hatched fill.

        """
        top = centerY
        left = centerX - Width / 2
        self.drawALine(left, top, left + Width, top, pen=pen)
        penOutline = qtg.QPen(qtc.Qt.NoPen)
        self.drawARectangle(left, top, Width, Height, pen=penOutline, brush=brush)

    def drawLinkage(self, stX, stY, enX, enY, radius=10, pen=None, brush=None):
        """
        Create and add a rigid link to the scene.

        """
        if pen is None:
            pen = self.penLink
        if brush is None:
            brush = self.brushLink
        lin1 = RigidLink(stX, stY, enX, enY, radius, pen=pen, brush=brush)
        self.scene.addItem(lin1)
        return lin1

    def drawPivot(self, x, y, ht, wd):
        """
        Create and add a pivot point to the scene.

        """
        pivot = RigidPivotPoint(x, y, ht, wd, brush=self.brushPivot)
        self.scene.addItem(pivot)
        return pivot

    def pickAColor(self):
        """
        Open a color dialog to change the grid line color and rebuild scene.
        """
        cdb = qtw.QColorDialog(self)
        c = cdb.getColor()
        hsv = c.getHsv()
        self.pushButton.setText(str(hsv))
        self.penGridLines.setColor(qtg.QColor.fromHsv(hsv[0], hsv[1], hsv[2], hsv[3]))
        self.buildScene()

    def setZoom(self):
        """
        Update the graphics view zoom level based on spinbox value.
        """
        self.gv_Main.resetTransform()
        self.gv_Main.scale(self.spnd_Zoom.value(), self.spnd_Zoom.value())


# endregion

# region function calls
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    mw.setWindowTitle('GraphicsView')
    sys.exit(app.exec())
# endregion