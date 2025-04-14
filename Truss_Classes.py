#region imports
import math
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from GraphicsView_App import RigidLink, RigidPivotPoint
#endregion

#region class definitions
class Position():
    """
    I made this position for holding a position in 3D space (i.e., a point).  I've given it some ability to do
    vector arithmitic and vector algebra (i.e., a dot product).  I could have used a numpy array, but I wanted
    to create my own.  This class uses operator overloading as explained in the class.
    """
    def __init__(self, pos=None, x=None, y=None, z=None):
        """
        x, y, and z have the expected meanings
        :param pos: a tuple (x,y,z)
        :param x: float
        :param y: float
        :param z: float
        """
        # set default values
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        # unpack position from a tuple if given
        if pos is not None:
            self.x, self.y, self.z = pos
        # override the x,y,z defaults if they are given as arguments
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.z = z if z is not None else self.z

    #region operator overloads
    def __eq__(self, other):
        if self.x != other.x or self.y != other.y or self.z != other.z:
            return False
        return True

    # this is overloading the addition operator.  Allows me to add Position objects with simple math: c=a+b, where
    # a, b, and c are all position objects.
    def __add__(self, other):
        return Position((self.x + other.x, self.y + other.y, self.z + other.z))

    # this overloads the iterative add operator
    def __iadd__(self, other):
        if isinstance(other, (float, int)):
            self.x += other
            self.y += other
            self.z += other
            return self
        if isinstance(other, Position):
            self.x += other.x
            self.y += other.y
            self.z += other.z
            return self

    # this is overloading the subtraction operator.  Allows me to subtract Positions. (i.e., c=b-a)
    def __sub__(self, other):
        return Position((self.x - other.x, self.y - other.y, self.z - other.z))

    # this overloads the iterative subtraction operator
    def __isub__(self, other):
        if isinstance(other, (float, int)):
            self.x -= other
            self.y -= other
            self.z -= other
            return self
        if isinstance(other, Position):
            self.x -= other.x
            self.y -= other.y
            self.z -= other.z
            return self

    # this is overloading the multiply operator.  Allows me to multiply a scalar or do a dot product (i.e., b=s*a or c=b*a)
    def __mul__(self, other):
        if isinstance(other, (float, int)):
            return Position((self.x * other, self.y * other, self.z * other))
        if isinstance(other, Position):
            return Position((self.x * other.x, self.y * other.y, self.z * other.z))

    # this is overloading the __rmul__ operator so that s*Pt works.
    def __rmul__(self, other):
        return self * other

    # this is overloading the *= operator.  Same as a = Position((a.x*other, a.y*other, a.z*other))
    def __imul__(self, other):
        if isinstance(other, (float, int)):
            self.x *= other
            self.y *= other
            self.z *= other
            return self

    # this is overloading the division operator.  Allows me to divide by a scalar (i.e., b=a/s)
    def __truediv__(self, other):
        if isinstance(other, (float, int)):
            return Position((self.x / other, self.y / other, self.z / other))

    # this is overloading the /= operator.  Same as a = Position((a.x/other, a.y/other, a.z/other))
    def __idiv__(self, other):
        if isinstance(other, (float, int)):
            self.x /= other
            self.y /= other
            self.z /= other
            return self
    # endregion

    def set(self, strXYZ=None, tupXYZ=None):
        # set position by string or tuple
        if strXYZ is not None:
            cells = strXYZ.replace('(', '').replace(')', '').strip().split(',')
            x, y, z = float(cells[0]), float(cells[1]), float(cells[2])
            self.x, self.y, self.z = float(x), float(y), float(z)
        elif tupXYZ is not None:
            x, y, z = tupXYZ #[0], strXYZ[1],strXYZ[2]
            self.x, self.y, self.z = float(x), float(y), float(z)

    def getTup(self): #return (x,y,z) as a tuple
        return (self.x, self.y, self.z)

    def getStr(self, nPlaces=3):
        return '{}, {}, {}'.format(round(self.x, nPlaces), round(self.y, nPlaces), round(self.z, nPlaces))

    def mag(self): # normal way to calculate magnitude of a vector
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def normalize(self): # typical way to normalize to a unit vector
        l = self.mag()
        if l <= 0.0:
            return
        self.__idiv__(l)

    def getAngleRad(self):
        """
        Gets angle of position relative to an origin (0,0) in the x-y plane
        :return: angle in x-y plane in radians
        """
        l = self.mag()
        if l <= 0.0:
            return 0
        if self.y >= 0.0:
            return math.acos(self.x / l)
        return 2.0 * math.pi - math.acos(self.x / l)

    def getAngleDeg(self):
        """
        Gets angle of position relative to an origin (0,0) in the x-y plane
        :return: angle in x-y plane in degrees
        """
        return 180.0 / math.pi * self.getAngleRad()

class Rectangle():
    def __init__(self, top=None, left=None, bottom=None, right=None):
        self.top = 0 if top is None else top
        self.left = 0 if left is None else left
        self.bottom = 0 if bottom is None else bottom
        self.right = 0 if right is None else right

    def height(self):
        return self.top - self.bottom

    def width(self):
        return self.right - self.left

    def centerY(self):
        return self.bottom + self.height() / 2.0

    def centerX(self):
        return self.left + self.width() / 2.0

class Material():
    def __init__(self, uts=None, ys=None, modulus=None, staticFactor=None):
        self.uts = uts
        self.ys = ys
        self.E = modulus
        self.staticFactor = staticFactor

class Node():
    def __init__(self, name=None, position=None):
        self.name = name
        self.position = position if position is not None else Position()
        self.graphic = RigidPivotPoint(position.x, position.y, 10, 30)
        self.support_type = "pin" if name.lower() == "left" else "roller"  # Left is grounded (pin), Right is roller
        self.load = 0.0  # To store vertical load due to truss weight

    def __eq__(self, other):
        """
        This overloads the == operator such that I can compare two nodes to see if they are the same node.  This is
        useful when reading in nodes to make sure I don't get duplicate nodes
        """
        if self.name != other.name or self.position != other.position:
            return False
        return True

class Link():
    def __init__(self, name="", node1="1", node2="2", length=None, angleRad=None, width=None, thickness=None, material=None):
        """
        Basic definition of a link contains a name and names of node1 and node2
        """
        self.name = name
        self.node1_Name = node1
        self.node2_Name = node2
        self.length = length
        self.angleRad = angleRad
        self.width = width
        self.thickness = thickness
        self.material = material  # "Steel" or "Aluminum"
        self.weight = None  # To be calculated
        self.graphic = RigidLink(0, 0, 1, 1)
        self.graphic.name = name

    def __eq__(self, other):
        """
        This overloads the == operator for comparing equivalence of two links.
        """
        if self.node1_Name != other.node1_Name or self.node2_Name != other.node2_Name:
            return False
        if self.length != other.length or self.angleRad != other.angleRad:
            return False
        return True

    def set(self, node1=None, node2=None, length=None, angleRad=None):
        self.node1_Name = node1
        self.node2_Name = node2
        self.length = length
        self.angleRad = angleRad

    def calculate_weight(self):
        if self.length is None or self.width is None or self.thickness is None or self.material is None:
            return
        # Densities in lb/in^3
        density = 0.283 if self.material.lower() == "steel" else 0.098  # Steel: 0.283 lb/in^3, Aluminum: 0.098 lb/in^3
        # Weight = length * width * thickness * density
        self.weight = self.length * self.width * self.thickness * density

class TrussModel():
    def __init__(self):
        self.title = None
        self.links = []
        self.nodes = []
        self.material = Material()
        self.rct = Rectangle()
        self.total_weight = 0.0  # To store total truss weight

    def getNode(self, name):
        for n in self.nodes:
            if n.name == name:
                return n

    def getCenterPt(self):
        """
        sets the rectangle that encloses the truss nodes
        :return:
        """
        rct = Rectangle()
        rct.left = self.nodes[0].position.x
        rct.right = self.nodes[0].position.x
        rct.top = self.nodes[0].position.y
        rct.bottom = self.nodes[0].position.y
        for n in self.nodes:
            if rct.left > n.position.x:
                rct.left = n.position.x
            if rct.right < n.position.x:
                rct.right = n.position.x
            if rct.top < n.position.y:
                rct.top = n.position.y
            if rct.bottom > n.position.y:
                rct.bottom = n.position.y
        self.rct = rct

class TrussView():
    def __init__(self):
        # setup widgets for display.  redefine these when you have a gui to work with using setDisplayWidgets
        self.scene = qtw.QGraphicsScene()
        self.le_LongLinkName = qtw.QLineEdit()
        self.le_LongLinkNode1 = qtw.QLineEdit()
        self.le_LongLinkNode2 = qtw.QLineEdit()
        self.le_LongLinkLength = qtw.QLineEdit()
        self.te_Report = qtw.QTextEdit()
        self.gv = qtw.QGraphicsView()

        # region setup pens and brushes and scene
        # make the pens first
        # a thick darkGray pen
        # self.penLink = qtg.QPen(qtc.Qt.orange)
        # self.penLink.setWidth(1)
        self.penLink = qtg.QPen(qtg.QColor("orange"))
        self.penLink.setWidth(1)
        # a medium darkBlue pen
        self.penNode = qtg.QPen(qtc.Qt.darkBlue)
        self.penNode.setStyle(qtc.Qt.SolidLine)
        self.penNode.setWidth(1)
        # a medium purple pen
        self.penLabel = qtg.QPen(qtc.Qt.darkMagenta)
        self.penLabel.setStyle(qtc.Qt.SolidLine)
        self.penLabel.setWidth(1)
        # a pen for the grid lines
        self.penGridLines = qtg.QPen()
        self.penGridLines.setWidth(1)
        # I wanted to make the grid lines more subtle, so set alpha=25
        self.penGridLines.setColor(qtg.QColor.fromHsv(197, 144, 228, alpha=50))
        # now make some brushes
        self.brushLink = qtg.QBrush(qtg.QColor.fromHsv(35, 255, 255, 64))
        self.brushPivot = qtg.QBrush(qtg.QColor.fromRgb(215, 215, 215, alpha=128))
        # build a brush for filling with solid red
        self.brushFill = qtg.QBrush(qtc.Qt.darkRed)
        # a brush that makes a hatch pattern
        self.brushNode = qtg.QBrush(qtg.QColor.fromCmyk(0, 0, 255, 0, alpha=100))
        # a brush for the background of my grid
        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, alpha=128))
        #end region

    def setDisplayWidgets(self, args):
        self.te_Report, self.le_LongLinkName, self.le_LongLinkNode1, self.le_LongLinkNode2, self.le_LongLinkLength, self.gv = args
        self.gv.setScene(self.scene)

    def displayReport(self, truss=None):
        st = '\tTruss Design Report\n'
        st += 'Title:  {}\n'.format(truss.title)
        st += 'Static Factor of Safety:  {:0.2f}\n'.format(truss.material.staticFactor)
        st += 'Ultimate Strength:  {:0.2f}\n'.format(truss.material.uts)
        st += 'Yield Strength:  {:0.2f}\n'.format(truss.material.ys)
        st += 'Modulus of Elasticity:  {:0.2f}\n'.format(truss.material.E)
        st += '_____________Link Summary________________\n'
        st += 'Link\t(1)\t(2)\tLength\tAngle\tWidth\tWeight\n'
        longest = None
        for l in truss.links:
            if longest is None or l.length > longest.length:
                longest = l
            st += '{}\t{}\t{}\t{:0.2f}\t{:0.2f}\t{:0.2f}\t{:0.2f}\n'.format(
                l.name, l.node1_Name, l.node2_Name, l.length, l.angleRad, l.width, l.weight
            )
        self.te_Report.setText(st)
        self.le_LongLinkName.setText(longest.name)
        self.le_LongLinkLength.setText("{:0.2f}".format(longest.length))
        self.le_LongLinkNode1.setText(longest.node1_Name)
        self.le_LongLinkNode2.setText(longest.node2_Name)

    def buildScene(self, truss=None):
        """
        Builds the scene by centering a grid within the scene and then drawing the truss links and then nodes.
        Builds center the grid on the scene such that the 0,0 point in scene coordinates is at the middle of the grid.
        Places the truss in the scene such that the middle of all the nodes is at 0,0.
        This will mean that the left lower node will be offset from 0,0
        :param truss:
        :return:
        """
        # Creates a QRect() object to help with drawing the background grid.
        truss.getCenterPt() # this creates a rectangle.encloses the nodes
        rct = truss.rct
        rct.left -= 50
        rct.right += 50
        rct.top += 50
        rct.bottom -= 50

        # clear out the old scene first
        self.scene.clear()

        # draw a grid
        self.drawAGrid(DeltaX=10, DeltaY=10, Height=abs(rct.height()), Width=abs(rct.width()), CenterX=0, CenterY=0)
        # draw the truss
        self.drawLinks(truss=truss)
        self.drawNodes(truss=truss)

    def drawAGrid(self, DeltaX=10, DeltaY=10, Height=320, Width=180, CenterX=120, CenterY=60):
        """
        This makes a grid for reference.  No snapping to grid enabled.
        :param DeltaX: grid spacing in x direction
        :param DeltaY: grid spacing in y direction
        :param Height: height of grid (y)
        :param Width: width of grid (x)
        :param CenterX: center of grid (x, in scene coords)
        :param CenterY: center of grid (y, in scene coords)
        :param Pen: pen for grid lines
        :param Brush: brush for background
        :return: nothing
        """
        Pen = self.penGridLines
        Brush = self.brushGrid
        height = self.scene.sceneRect().length() if Height is None else Height
        width = self.scene.sceneRect().width() if Width is None else Width
        left = self.scene.sceneRect().left() if CenterX is None else (CenterX - width / 2.0)
        right = self.scene.sceneRect().right() if CenterX is None else (CenterX + width / 2.0)
        top = -1.0 * self.scene.sceneRect().top() if CenterY is None else (CenterY - height / 2.0)
        bottom = -1.0 * self.scene.sceneRect().bottom() if CenterY is None else (CenterY + height / 2.0)
        Dx = DeltaX
        Dy = DeltaY
        pen = qtg.QPen() if Pen is None else Pen

        # make the background rectangle first
        if Brush is not None:
            rect = qtw.QGraphicsRectItem(left, top, width, height)
            rect.setBrush(Brush)
            rect.setPen(pen)
            self.scene.addItem(rect)
        # draw the vertical grid lines
        x = left
        while x <= right:
            lVert = qtw.QGraphicsLineItem(x, top, x, bottom)
            lVert.setPen(pen)
            self.scene.addItem(lVert)
            x += Dx
        # draw the horizontal grid lines
        y = bottom
        while y >= top:
            lHor = qtw.QGraphicsLineItem(left, y, right, y)
            lHor.setPen(pen)
            self.scene.addItem(lHor)
            y -= Dy

    def drawLinks(self, truss=None):
        """
        I copied most of this code from drawPipes in PipeNetwork_classes
        :param truss:
        :return:
        """
        scene = self.scene
        truss.getCenterPt()
        rct = truss.rct
        offset = Position(x=rct.centerX(), y=rct.centerY())

        for l in truss.links:
            n1 = truss.getNode(l.node1_Name)
            n2 = truss.getNode(l.node2_Name)
            l.graphic = RigidLink(
                n1.position.x - offset.x, -(n1.position.y - offset.y),
                n2.position.x - offset.x, -(n2.position.y - offset.y),
                radius=3, pen=self.penLink, brush=self.brushLink, name="link name = " + l.name
            )
            # build a tool tip string
            st = f'link: {l.name}\nMaterial: {l.material}\nWeight: {l.weight:.2f} lb'
            # assign tool tip string
            l.graphic.setToolTip(st)
            scene.addItem(l.graphic)

    def drawNodes(self, truss=None):
        truss.getCenterPt()
        rct = truss.rct
        offset = Position(x=rct.centerX(), y=rct.centerY())
        for n in truss.nodes:
            x = n.position.x - offset.x
            y = (n.position.y - offset.y)
            support_label = "Grounded" if n.name.lower() == "left" else n.support_type.capitalize()
            toolTip = f"Node: {n.name}\nSupport: {support_label}\nVertical Load: {n.load:.2f} lb"
            if n.name.lower() in ['left', 'right']:
                if n.name.lower() == "left":
                    n.graphic = RigidPivotPoint(x, -y, 10, 18, brush=self.brushPivot, name=n.name)
                    n.graphic.setToolTip(toolTip)
                    self.scene.addItem(n.graphic)
                elif n.support_type == "roller":
                    radius = 5
                    circle = qtw.QGraphicsEllipseItem(x - radius, -y - radius, 2 * radius, 2 * radius)
                    circle.setBrush(self.brushPivot)
                    circle.setPen(self.penNode)
                    circle.setToolTip(toolTip)
                    self.scene.addItem(circle)
                    n.graphic = circle
            # self.drawACircle(centerX=x,centerY=y,Radius=8,pen=self.penNode,brush=self.brushNode, name=toolTip, tooltip=toolTip)
            self.drawALabel(x=x - 5, y=y + 15, str=n.name, pen=self.penLabel)

    def drawALabel(self, x, y, str='', pen=None, brush=None, tip=None):
        scene = self.scene
        lbl = qtw.QGraphicsTextItem(str)
        w = lbl.boundingRect().width()
        h = lbl.boundingRect().height()
        lbl.setX(x - w / 2.0)
        lbl.setY(-y - h / 2.0)
        if tip is not None:
            lbl.setToolTip(tip)
        if pen is not None:
            lbl.setDefaultTextColor(pen.color())
        if brush is not None:
            # this makes a nice background
            bkg = qtw.QGraphicsRectItem(lbl.x(), lbl.y(), w, h)
            bkg.setBrush(brush)
            outlinePen = qtg.QPen(brush.color())
            bkg.setPen(outlinePen)
            scene.addItem(bkg)
        scene.addItem(lbl)

class TrussController():
    def __init__(self):
        self.truss = TrussModel()
        self.view = TrussView()

    def ImportFromFile(self, data):
        """
        Data is the list of strings read from the data file.
        We need to parse this file and build the lists of nodes and links that make up the truss.
        Also, we need to parse the lines that give the truss title, material (and strength values).

        Reading Nodes:
        I create a new node object and then set its name and position.x and position.y values.  Next, I check to see
        if the list of nodes in the truss model has this node with self.hasNode(n.name).  If the trussModel does not
        contain the node, I append it to the list of nodes

        Reading Links:
        The links should come after the nodes.  Each link has a name and two node names.  See method addLink
        """
        self.truss = TrussModel() # create a new truss object
        for L in data: #scan through all the lines
            L = L.strip()
            if L.find('#') == 0:
                continue
            Cells = L.split(',')
            if len(Cells) <= 1:
                continue
            elif Cells[0].lower().find('material') >= 0:
                sut = float(Cells[1].strip())
                sy = float(Cells[2].strip())
                E = float(Cells[3].strip())
                self.truss.material = Material(uts=sut, ys=sy, modulus=E)
            elif Cells[0].lower().find('static') >= 0:
                sf = float(Cells[1].strip())
                self.truss.material.staticFactor = sf
            elif Cells[0].lower().find('node') >= 0:
                name = Cells[1].strip()
                x = float(Cells[2].strip())
                y = float(Cells[3].strip())
                self.truss.nodes.append(Node(name=name, position=Position(x=x, y=y)))
            elif Cells[0].lower().find('link') >= 0:
                name = Cells[1].strip()
                n1 = Cells[2].strip()
                n2 = Cells[3].strip()
                width = float(Cells[4].strip())
                thickness = float(Cells[5].strip())
                material = Cells[6].strip()
                self.truss.links.append(Link(name=name, node1=n1, node2=n2, width=width, thickness=thickness, material=material))
        self.calcLinkVals()
        self.calculateLoads()
        self.displayReport()
        self.drawTruss()

    def hasNode(self, name):
        for n in self.truss.nodes:
            if n.name == name:
                return True
        return False

    def addNode(self, node):
        self.truss.nodes.append(node)

    def getNode(self, name):
        for n in self.truss.nodes:
            if n.name == name:
                return n

    def addLink(self, link):
        self.truss.links.append(link)

    def calcLinkVals(self):
        for l in self.truss.links:
            n1 = self.getNode(l.node1_Name)
            n2 = self.getNode(l.node2_Name)
            if n1 is not None and n2 is not None:
                r = n2.position - n1.position
                l.length = r.mag()
                l.angleRad = r.getAngleRad()
                l.calculate_weight()

    def calculateLoads(self):
        self.truss.total_weight = sum(l.weight for l in self.truss.links if l.weight is not None)
        vertical_load = self.truss.total_weight / 2
        for n in self.truss.nodes:
            if n.name.lower() in ['left', 'right']:
                n.load = vertical_load

    def setDisplayWidgets(self, args):
        self.view.setDisplayWidgets(args)

    def displayReport(self):
        self.view.displayReport(truss=self.truss)

    def drawTruss(self):
        self.view.buildScene(truss=self.truss)

    def handleMouseMove(self, scenePos):
        strScene = f"Mouse Position:  x = {round(scenePos.x(), 2)}, y = {round(-scenePos.y(), 2)}"
        s = self.view.scene.itemAt(scenePos, qtg.QTransform())
        if s is not None and s.data(0) is not None:
            strScene += f' ({s.data(0)})'
        items = self.view.scene.items(scenePos)
        item_names = [item.name if hasattr(item, 'name') else None for item in items]
        for i in item_names:
            strScene += ', ' + (i if i is not None else 'none')
        return strScene
#endregion