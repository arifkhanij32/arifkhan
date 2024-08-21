import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QDesktopWidget, QFrame, QSizePolicy, QProgressBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt,QSize


# Placeholder for global variables
TOOL_FIXED_WIDTH = 40
SIDE_TOOL_FIXED_WIDTH = 40
TITLE_LABLE_WIDGET_BACKGROUND_COLOR = "gray"
TOOLS_BUTTON_COLOR = "#B8860B"
TOOLTIP_STYLE = "QToolTip {color: white; background-color: black; border: 1px solid white;}"
CLOSE_BUTTON_COLOR =  "#B8860B"
MINIMIZE_BUTTON_COLOR = "#B8860B"
BUTTON_STYLE = "QPushButton {background-color: gray;}"
SIDEBAR_WIDGET_BACKGROUND_COLOR = "gray"
PROGRESSBAR_STYLE = "QProgressBar {border: 2px solid grey; border-radius: 5px; text-align: center;}"
PV_FONT_SIZE_FACTOR = 1
IV_FONT_AND_COLOR = "font-weight: bold; color: black;"
IV_TITLE_FIXED_WIDTH = 250


class dicomViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("DICOM Viewer")
        self.setGeometry(100, 100, 1200, 800)
        self.imageCentralWidget = self.initImageViewerUI()
        self.setCentralWidget(self.imageCentralWidget)

    def initImageViewerUI(self):
        self.rows = 1
        self.cols = 1
        self.imageTitleBarMainLayout = QHBoxLayout()
        self.imageTitleBarMainLayout.setContentsMargins(0, 0, 0, 0)
        self.screenWidth = QDesktopWidget().screenGeometry().width()
        self.screenHeight = QDesktopWidget().screenGeometry().height()

        # MAIN TITLE
        self.titleLabelImageViewer = QLabel("Image Viewer")
        font_size_factor = PV_FONT_SIZE_FACTOR
        font_size = int(self.titleLabelImageViewer.font().pointSize() * font_size_factor)
        font_style = IV_FONT_AND_COLOR
        self.titleLabelImageViewer.setStyleSheet(font_style)
        self.titleLabelImageViewer.setFixedWidth(IV_TITLE_FIXED_WIDTH)
        font_size = min(self.screenWidth, self.screenHeight) // 136

        font = self.titleLabelImageViewer.font()
        font.setPointSize(font_size)
        self.titleLabelImageViewer.setFont(font)

        self.titleLableLayout = QHBoxLayout()
        self.titleLableLayout.addWidget(self.titleLabelImageViewer)
        self.titleLableLayout.setContentsMargins(0, 0, 0, 0)

        self.titleLabelWidget = QWidget()
        self.titleLabelWidget.setStyleSheet(f"background-color: {TITLE_LABLE_WIDGET_BACKGROUND_COLOR};")
        self.titleLabelWidget.setLayout(self.titleLableLayout)
        self.titleLabelWidget.setContentsMargins(0, 0, 0, 0)

        self.lineButton = self.createToolButton("line.png", "Line", self.lineButtonF)
        self.angleButton = self.createToolButton("angle1.png", "Angle", self.angleButtonF)
        self.cobbAngleButton = self.createToolButton("cobb.png", "Cobb Angle", self.cobbAngleButtonF)
        # self.measurementToggleButton = self.createToolButton("measure2.png", "Measurement", self.measurementToggleButtonF, checkable=True)
        self.textButton = self.createToolButton("text.png", "Text", self.textButtonF)
        # self.closeButton = self.createToolButton("close1.png", "Close", self.mainClose, color=CLOSE_BUTTON_COLOR)
        # self.minimizeButton = self.createToolButton("minimize.png", "Minimize", self.mainMinimize, color=MINIMIZE_BUTTON_COLOR)
       

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Plain)
        vline.setLineWidth(0)
        vline.setMidLineWidth(0)
        vline.setStyleSheet("color:black")

        self.toolGridLayout = QGridLayout()
        self.toolGridLayout.setContentsMargins(3, 3, 0, 3)

        # self.toolGridLayout.addWidget(self.measurementToggleButton, 0, 0)
        self.toolGridLayout.addWidget(vline, 0, 1, 2, 1)
        self.toolGridLayout.addWidget(self.lineButton, 0, 2)
        self.toolGridLayout.addWidget(self.angleButton, 0, 3)
        self.toolGridLayout.addWidget(self.textButton, 0, 4)
        self.toolGridLayout.addWidget(self.cobbAngleButton, 0, 5)
        # self.toolGridLayout.addWidget(self.minimizeButton, 0, 6)
        # self.toolGridLayout.addWidget(self.closeButton, 0, 7)

        self.imageTitleBarMainLayout.addWidget(self.titleLabelWidget)
        self.imageTitleBarMainLayout.addLayout(self.toolGridLayout)

        self.imageViewerTitleBarWidget = QWidget()
        self.imageViewerTitleBarWidget.setStyleSheet(f"background-color: {SIDEBAR_WIDGET_BACKGROUND_COLOR};")
        self.imageViewerTitleBarWidget.setLayout(self.imageTitleBarMainLayout)

        self.mainLayout = QHBoxLayout()
        self.sidebarWidget = self.createSidebarWidget()
        titlebarAndImageLayout = QGridLayout()
        titlebarAndImageLayout.addWidget(self.imageViewerTitleBarWidget, 0, 0)

        self.mainLayout.addWidget(self.sidebarWidget)
        self.mainLayout.addLayout(titlebarAndImageLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        imageCentralWidget = QWidget()
        imageCentralWidget.setLayout(self.mainLayout)
        return imageCentralWidget

    def createSidebarWidget(self):
        sidebarLayout = QVBoxLayout()
        self.sidebarWidth = int(0.1 * QDesktopWidget().screenGeometry().width())
        sidebarLayout.addSpacing(55)

        self.fullscreenButton = self.createToolButton("full_screen.png", "Full Screen", self.fullscreenButtonF)
        self.zoomInButton = self.createToolButton("zoom_in.png", "Zoom In", self.zoomInButtonF)
        self.zoomOutButton = self.createToolButton("zoom_out.png", "Zoom Out", self.zoomOutButtonF)
        self.inversionButton = self.createToolButton("inversiondrop.png", "Inversion", self.isInversionButtonClicked)
        self.clockRotateButton90 = self.createToolButton("clockwise1.png", "Clockwise Rotate", self.isClockwiseButtonClicked)
        self.antiClockRotateButton90 = self.createToolButton("anticlock.png", "Anti-Clockwise Rotate", self.isAnticlockwiseButtonClicked)
        self.horizontalFlipButton = self.createToolButton("horizontal_flip.png", "Horizontal Flip", self.isHorizontalFlipButtonClicked)
        self.verticalFlipButton = self.createToolButton("vertical_flip.png", "Vertical Flip", self.isVerticalFlipButtonClicked)

        manipulationGridLayout = QGridLayout()
        manipulationGridLayout.setHorizontalSpacing(15)
        manipulationGridLayout.setContentsMargins(0, 0, 10, 10)

        manipulationGridLayout.addWidget(self.fullscreenButton, 0, 0)
        manipulationGridLayout.addWidget(self.zoomInButton, 0, 1)
        manipulationGridLayout.addWidget(self.zoomOutButton, 1, 0)
        manipulationGridLayout.addWidget(self.inversionButton, 1, 1)
        manipulationGridLayout.addWidget(self.clockRotateButton90, 2, 0)
        manipulationGridLayout.addWidget(self.antiClockRotateButton90, 2, 1)
        manipulationGridLayout.addWidget(self.horizontalFlipButton, 3, 0)
        manipulationGridLayout.addWidget(self.verticalFlipButton, 3, 1)

        sidebarLayout.addLayout(manipulationGridLayout)
        sidebarLayout.addStretch(1)

        self.progressBarIv = QProgressBar(self)
        self.progressBarIv.setValue(0)
        style_sheet = PROGRESSBAR_STYLE
        self.progressBarIv.setStyleSheet(style_sheet)
        self.progressBarIv.setTextVisible(True)
        self.progressBarIv.setAlignment(Qt.AlignCenter)
        sidebarLayout.addWidget(self.progressBarIv, alignment=Qt.AlignCenter)

        sidebarWidget = QWidget()
        sidebarWidget.setLayout(sidebarLayout)
        sidebarWidget.setStyleSheet(f"background-color: {SIDEBAR_WIDGET_BACKGROUND_COLOR};")
        sidebarWidget.setFixedWidth(int(0.06 * QDesktopWidget().screenGeometry().width()))

        return sidebarWidget

    def createToolButton(self, icon_name, tooltip, slot_function, checkable=False, color=TOOLS_BUTTON_COLOR):
        button = QPushButton()
        button.setStyleSheet(f"background-color: {color};")
        button.setFixedWidth(TOOL_FIXED_WIDTH)
        button.setFixedHeight(TOOL_FIXED_WIDTH)
        button.clicked.connect(slot_function)
        icon = QIcon(os.path.join( "icons", icon_name))
        button.setIcon(icon)
        button.setIconSize(QSize(20, 20))
        button.setToolTip(tooltip)
        button.setCheckable(checkable)
        return button

    def lineButtonF(self):
        pass

    def angleButtonF(self):
        pass

    def cobbAngleButtonF(self):
        pass

    def measurementToggleButtonF(self):
        pass

    def textButtonF(self):
        pass

    def mainClose(self):
        self.close()

    def mainMinimize(self):
        self.showMinimized()

    def smartPointerButtonF(self):
        pass

    def fullscreenButtonF(self):
        pass

    def zoomInButtonF(self):
        pass

    def zoomOutButtonF(self):
        pass

    def isInversionButtonClicked(self):
        pass

    def isClockwiseButtonClicked(self):
        pass

    def isAnticlockwiseButtonClicked(self):
        pass

    def isHorizontalFlipButtonClicked(self):
        pass

    def isVerticalFlipButtonClicked(self):
        pass

# Main method
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join( "icons", "logo.ico")))
    mainWindow = dicomViewer()
    mainWindow.show()
    exit_code = app.exec_()
    sys.exit(exit_code)
