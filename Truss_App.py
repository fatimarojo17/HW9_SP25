# region imports
from Truss_GUI import Ui_TrussStructuralDesign
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from Truss_Classes import TrussController
import sys


# endregion

# region class definitions
class MainWindow(Ui_TrussStructuralDesign, qtw.QWidget):

    def __init__(self):
        """
        Initialize the main window and set up the truss design UI.

        """
        super().__init__()

        # Step 1: Set up UI
        self.setupUi(self)

        # Step 2: Connect signals
        self.btn_Open.clicked.connect(self.OpenFile)
        self.spnd_Zoom.valueChanged.connect(self.setZoom)

        # Step 3: Initialize controller
        self.controller = TrussController()
        self.controller.setDisplayWidgets((
            self.te_DesignReport,  # Text edit for design report
            self.le_LinkName,  # Line edit for link name
            self.le_Node1Name,  # Line edit for node 1 name
            self.le_Node2Name,  # Line edit for node 2 name
            self.le_LinkLength,  # Line edit for link length
            self.gv_Main  # Graphics view for truss visualization
        ))

        # Step 4: Configure event handling
        self.controller.view.scene.installEventFilter(self)
        self.gv_Main.setMouseTracking(True)

        # Step 5: Display window
        self.show()

    def setZoom(self):
        """
        Update the graphics view zoom level based on spinbox value.

        """
        # Step 1: Reset transform
        self.gv_Main.resetTransform()

        # Step 2: Apply zoom
        self.gv_Main.scale(self.spnd_Zoom.value(), self.spnd_Zoom.value())

    def eventFilter(self, obj, event):
        """
        Handle events in the graphics scene, such as mouse movement and wheel scrolling.

        """
        if obj == self.controller.view.scene:
            # Step 2: Handle mouse move
            if event.type() == qtc.QEvent.GraphicsSceneMouseMove:
                scenePos = event.scenePos()
                strScene = self.controller.handleMouseMove(scenePos)  # Get position string from controller
                self.lbl_MousePos.setText(strScene)

            # Step 3: Handle wheel
            elif event.type() == qtc.QEvent.GraphicsSceneWheel:
                if event.delta() > 0:
                    self.spnd_Zoom.stepUp()  # Zoom in
                else:
                    self.spnd_Zoom.stepDown()  # Zoom out

            # Step 4: Handle tooltip (no action)
            elif event.type() == qtc.QEvent.ToolTip:
                pass

        # Step 5: Pass to parent
        return super(MainWindow, self).eventFilter(obj, event)

    def OpenFile(self):
        """
        Open a file dialog to load truss data and pass it to the controller.

        """
        # Step 1: Open file dialog
        filename = qtw.QFileDialog.getOpenFileName()[0]

        # Step 2: Check for valid selection
        if len(filename) == 0:
            return

        # Step 3: Update UI with file path
        self.te_Path.setText(filename)

        # Step 4: Read file
        with open(filename, 'r') as file:
            data = file.readlines()

        # Step 5: Pass to controller
        self.controller.ImportFromFile(data)


# endregion

# region function definitions
def Main():
    """
    Create and run the QApplication for the truss design tool.
    """
    # Step 1: Create app
    app = qtw.QApplication(sys.argv)

    # Step 2: Create window
    mw = MainWindow()

    # Step 3: Run app
    sys.exit(app.exec())

# function calls are from the controller
# endregion

# region function calls
if __name__ == "__main__":
    Main()
# endregion