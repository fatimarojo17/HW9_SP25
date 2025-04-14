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
    """A custom QGraphicsItem to draw a rigid link with semicircular ends and pivot points."""

    def __init__(self, stX, stY, enX, enY, radius=10, parent=None, pen=None, brush=None, name='RigidLink'):
        """
        Initialize a rigid link with start and end points, radius, pen, and brush.

        Steps:
        1. Store pen, brush, coordinates, and radius.
        2. Compute length and angle of the link.
        3. Define the bounding rectangle.
        4. Set up transformation for rotation and translation.

        Note: The link is drawn aligned with the x-axis (start at 0,0, end at length,0),
        then rotated and translated to its final position.

        :param stX: Start x-coordinate
        :param stY: Start y-coordinate
        :param enX: End x-coordinate
        :param enY: End y-coordinate
        :param radius: Radius of semicircular ends
        :param parent: Parent QGraphicsItem, default None
        :param pen: QPen for outline, default None
        :param brush: QBrush for fill, default None
        :param name: Name of the link, default 'RigidLink'
        """
        super().__init__(parent)

        # Step 1: Store properties
        self.pen = pen
        self.brush = brush
        self.name = name
        self.startX = stX
        self.startY = stY
        self.endX = enX
        self.endY = enY
        self.radius = radius

        # Step 2: Compute angle (also sets length, DX, DY)
        self.angle = self.linkAngle()

        # Step 3: Define bounding rectangle
        self.rect = qtc.QRectF(-self.radius, -self.radius, self.length + self.radius, self.radius)

        # Step 4: Initialize transformation
        self.transform = qtg.QTransform()
        self.transform.reset()

    def boundingRect(self):
        """
        Return the transformed bounding rectangle for mouse interaction.

        :return: QRectF, the bounding rectangle after transformation
        """
        return self.transform.mapRect(self.rect)

    def deltaY(self):
        """
        Calculate the difference in y-coordinates (endY - startY).

        :return: float, delta y
        """
        self.DY = self.endY - self.startY
        return self.DY

    def deltaX(self):
        """
        Calculate the difference in x-coordinates (endX - startX).

        :return: float, delta x
        """
        self.DX = self.endX - self.startX
        return self.DX

    def linkLength(self):
        """
        Compute the Euclidean length of the link using deltaX and deltaY.

        :return: float, length of the link
        """
        self.length = math.sqrt(math.pow(self.deltaX(), 2) + math.pow(self.deltaY(), 2))
        return self.length

    def linkAngle(self):
        """
        Calculate the angle of the link relative to the x-axis.

        Steps:
        1. Compute length.
        2. If length is zero, set angle to 0.
        3. Otherwise, compute angle using acos(DX/length) and adjust sign based on DY.

        :return: float, angle in radians
        """
        self.linkLength()
        if self.length == 0.0:
            self.angle = 0
        else:
            self.angle = math.acos(self.DX / self.length)
            self.angle *= -1 if (self.DY > 0) else 1
        return self.angle

    def paint(self, painter, option, widget=None):
        """
        Draw the rigid link with semicircular ends and pivot points.

        Steps:
        1. Create a QPainterPath for the link shape.
        2. Draw a dashed centerline.
        3. Draw semicircles at start and end, connected by lines.
        4. Draw pivot point circles.
        5. Apply pen, brush, and transformations.
        6. Set tooltip with link details.

        :param painter: QPainter object
        :param option: QStyleOptionGraphicsItem
        :param widget: QWidget, default None
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
    """A custom QGraphicsItem to draw a pivot point with a base and circular pivot."""

    def __init__(self, ptX, ptY, pivotHeight, pivotWidth, parent=None, pen=None, brush=None, rotation=0,
                 name='RigidPivotPoint'):
        """
        Initialize a pivot point with position, dimensions, and styling.

        Steps:
        1. Store coordinates, dimensions, pen, brush, rotation, and name.
        2. Define bounding rectangle.
        3. Set up transformation.
        4. Set tooltip with coordinates.

        :param ptX: X-coordinate of pivot center
        :param ptY: Y-coordinate of pivot center
        :param pivotHeight: Height of pivot base
        :param pivotWidth: Width of pivot base
        :param parent: Parent QGraphicsItem, default None
        :param pen: QPen for outline, default None
        :param brush: QBrush for fill, default None
        :param rotation: Initial rotation angle in degrees, default 0
        :param name: Name of the pivot, default 'RigidPivotPoint'
        """
        super().__init__(parent)

        # Step 1: Store properties
        self.x = ptX
        self.y = ptY
        self.pen = pen
        self.brush = brush
        self.height = pivotHeight
        self.width = pivotWidth
        self.radius = min(self.height, self.width) / 4
        self.rotationAngle = rotation
        self.name = name

        # Step 2: Define bounding rectangle
        self.rect = qtc.QRectF(self.x - self.width / 2, self.y - self.radius, self.width, self.height + self.radius)

        # Step 3: Initialize transformation
        self.transformation = qtg.QTransform()

        # Step 4: Set tooltip
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
        """
        Draw the pivot point with a trapezoidal base, circular pivot, and hatched support.

        Steps:
        1. Create a QPainterPath for the pivot shape.
        2. Compute geometric parameters for trapezoid.
        3. Draw trapezoid, pivot circle, and base line.
        4. Draw hatched support rectangle.
        5. Apply pen, brush, and transformations.

        :param painter: QPainter object
        :param option: QStyleOptionGraphicsItem
        :param widget: QWidget, default None
        """
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
    """Main application window for displaying and interacting with a linkage system."""

    def __init__(self):
        """
        Initialize the main window and set up the graphics view, scene, and UI.

        Steps:
        1. Set up UI from designer.
        2. Configure graphics view and scene.
        3. Enable mouse tracking.
        4. Build initial scene with pivots and links.
        5. Connect signals for zoom and color picking.
        """
        super().__init__()

        # Step 1: Set up UI
        self.setupUi(self)

        # Step 2: Configure graphics
        self.setupGraphics()

        # Step 3: Enable mouse tracking
        self.gv_Main.setMouseTracking(True)
        self.pushButton.setMouseTracking(True)
        self.setMouseTracking(True)

        # Step 4: Build initial scene
        self.buildScene()
        self.prevAlpha = self.link1.angle
        self.prevBeta = self.link3.angle
        self.angle1 = math.pi
        self.angle2 = math.pi

        # Step 5: Connect signals
        self.spnd_Zoom.valueChanged.connect(self.setZoom)
        self.pushButton.clicked.connect(self.pickAColor)
        self.scene.installEventFilter(self)
        self.mouseDown = False
        self.show()

    def setupGraphics(self):
        """
        Set up the QGraphicsScene and assign it to the QGraphicsView.

        Steps:
        1. Create a scene with a defined rectangle.
        2. Assign scene to graphics view.
        3. Set up pens and brushes.
        """
        # Step 1: Create scene
        self.scene = qtw.QGraphicsScene()
        self.scene.setObjectName("MyScene")
        self.scene.setSceneRect(-200, -200, 400, 400)  # xLeft, yTop, Width, Height

        # Step 2: Assign to graphics view
        self.gv_Main.setScene(self.scene)

        # Step 3: Set up pens and brushes
        self.setupPensAndBrushes()

    def setupPensAndBrushes(self):
        """
        Define pens and brushes for drawing.

        Steps:
        1. Create pens with different styles and colors.
        2. Create brushes for filling shapes.
        """
        # Step 1: Define pens
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

        # Step 2: Define brushes
        self.brushFill = qtg.QBrush(qtc.Qt.darkRed)  # Solid red fill
        self.brushHatch = qtg.QBrush()
        self.brushHatch.setStyle(qtc.Qt.DiagCrossPattern)  # Hatch pattern
        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, 128))  # Grid background
        self.brushLink = qtg.QBrush(qtg.QColor.fromHsv(35, 255, 255, 64))  # Link fill
        self.brushPivot = qtg.QBrush(qtg.QColor.fromHsv(0, 0, 128, 255))  # Pivot fill

    def mouseMoveEvent(self, a0: qtg.QMouseEvent):
        """
        Update window title with mouse coordinates and widget name.

        :param a0: QMouseEvent object
        """
        w = app.widgetAt(a0.globalPos())
        name = 'none' if w is None else w.objectName()
        self.setWindowTitle(str(a0.x()) + ',' + str(a0.y()) + name)

    def eventFilter(self, obj, event):
        """
        Handle mouse and wheel events in the graphics scene.

        Steps:
        1. Check if event is for the scene.
        2. Handle mouse move: Update link positions during dragging.
        3. Handle mouse press: Start dragging.
        4. Handle mouse release: Stop dragging.
        5. Handle wheel: Adjust zoom.

        :param obj: Object receiving the event
        :param event: QEvent object
        :return: bool, whether event was handled
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

        Steps:
        1. Clear existing scene.
        2. Draw grid.
        3. Add pivot points.
        4. Add rigid links.
        """
        # Step 1: Clear scene
        self.scene.clear()

        # Step 2: Draw grid
        self.drawAGrid(DeltaX=10, DeltaY=10, Height=400, Width=400, Pen=self.penGridLines, Brush=self.brushGrid)

        # Step 3: Add pivots
        self.pivot0 = self.drawPivot(-100, 0, 10, 20)
        self.pivot0.setTransformOriginPoint(qtc.QPointF(self.pivot0.x, self.pivot0.y))
        self.pivot0.rotate(90)
        self.pivot1 = self.drawPivot(60, -30, 10, 20)
        self.pivot1.setTransformOriginPoint(qtc.QPointF(self.pivot1.x, self.pivot1.y))
        self.pivot1.rotate(-90)

        # Step 4: Add links
        self.link0 = self.drawLinkage(self.pivot0.x, self.pivot0.y, self.pivot1.x, self.pivot1.y, radius=5,
                                      pen=self.penGridLines, brush=self.brushGrid)
        self.link1 = self.drawLinkage(-100, 0, -100, -60, 5)
        self.link2 = self.drawLinkage(-100, -60, 100, -150, 5)
        self.link3 = self.drawLinkage(60, -30, 100, -150, 5)

    def drawAGrid(self, DeltaX=10, DeltaY=10, Height=200, Width=200, CenterX=0, CenterY=0, Pen=None, Brush=None,
                  SubGrid=None):
        """
        Draw a reference grid in the scene.

        Steps:
        1. Determine grid dimensions.
        2. Draw background rectangle if brush provided.
        3. Draw vertical and horizontal grid lines.

        :param DeltaX: Grid spacing in x-direction
        :param DeltaY: Grid spacing in y-direction
        :param Height: Grid height
        :param Width: Grid width
        :param CenterX: Grid center x-coordinate
        :param CenterY: Grid center y-coordinate
        :param Pen: QPen for grid lines
        :param Brush: QBrush for background
        :param SubGrid: Not implemented
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

        :param leftX: Left x-coordinate
        :param topY: Top y-coordinate
        :param widthX: Rectangle width
        :param heightY: Rectangle height
        :param pen: QPen for outline
        :param brush: QBrush for fill
        :return: QGraphicsRectItem
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

        :param stX: Start x-coordinate
        :param stY: Start y-coordinate
        :param enX: End x-coordinate
        :param enY: End y-coordinate
        :param pen: QPen for line
        :return: QGraphicsLineItem
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

        :param centerX: Center x-coordinate
        :param centerY: Center y-coordinate
        :param radius: Radius
        :param angleDeg: Angle in degrees
        :return: tuple, (x, y) coordinates
        """
        angleRad = angleDeg * 2.0 * math.pi / 360.0
        return centerX + radius * math.cos(angleRad), centerY + radius * math.sin(angleRad)

    def drawACircle(self, centerX, centerY, Radius, angle=0, brush=None, pen=None):
        """
        Draw a circle in the scene.

        :param centerX: Center x-coordinate
        :param centerY: Center y-coordinate
        :param Radius: Circle radius
        :param angle: Rotation angle (not used)
        :param brush: QBrush for fill
        :param pen: QPen for outline
        :return: QGraphicsEllipseItem
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

        :param centerX: Center x-coordinate
        :param centerY: Center y-coordinate
        :param Size: Side length
        :param brush: QBrush for fill
        :param pen: QPen for outline
        :return: QGraphicsRectItem
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

        :param centerX: Center x-coordinate
        :param centerY: Center y-coordinate
        :param Radius: Radius to vertices
        :param angleDeg: Rotation angle in degrees
        :param brush: QBrush for fill
        :param pen: QPen for outline
        :return: QGraphicsPolygonItem
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

        :param startX: Start x-coordinate
        :param startY: Start y-coordinate
        :param endX: End x-coordinate
        :param endY: End y-coordinate
        :param pen: QPen for outline
        :param brush: QBrush for fill
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

        :param centerX: Center x-coordinate
        :param centerY: Center y-coordinate
        :param Width: Surface width
        :param Height: Surface height
        :param pen: QPen for outline
        :param brush: QBrush for fill
        """
        top = centerY
        left = centerX - Width / 2
        self.drawALine(left, top, left + Width, top, pen=pen)
        penOutline = qtg.QPen(qtc.Qt.NoPen)
        self.drawARectangle(left, top, Width, Height, pen=penOutline, brush=brush)

    def drawLinkage(self, stX, stY, enX, enY, radius=10, pen=None, brush=None):
        """
        Create and add a rigid link to the scene.

        :param stX: Start x-coordinate
        :param stY: Start y-coordinate
        :param enX: End x-coordinate
        :param enY: End y-coordinate
        :param radius: Radius of semicircular ends
        :param pen: QPen for outline
        :param brush: QBrush for fill
        :return: RigidLink object
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

        :param x: X-coordinate
        :param y: Y-coordinate
        :param ht: Height of pivot base
        :param wd: Width of pivot base
        :return: RigidPivotPoint object
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