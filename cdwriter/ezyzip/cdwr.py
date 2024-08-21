import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

class MedicalMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle("Medical Application")
        self.setGeometry(100, 100, 800, 600)

        # Set background color for the main window
        self.setStyleSheet("background-color: gray;")

        # Create the central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create the main vertical layout
        main_layout = QVBoxLayout()

        # Create the top horizontal layout with custom background color
        top_layout = QHBoxLayout()
        top_container = QWidget()
        top_container.setLayout(top_layout)
        top_container.setStyleSheet("background-color:white ;")  # Light gray background for the layout

        
        button_style = """
        QPushButton {
           background-color: yellow; font-size: 16px; min-height: 30px; max-height: 30px; min-width: 30px; max-width: 30px;
        }
        QPushButton:hover {
            background-color: #45a049;   # Darker green on hover
        }
        """

        button1 = QPushButton("/")
        button2 = QPushButton("ABC")
        button3 = QPushButton("/")
        button4 = QPushButton("&")

        button1.setStyleSheet(button_style)
        button2.setStyleSheet("background-color: yellow; font-size: 16px; min-height: 30px; max-height: 30px; min-width: 30px; max-width: 30px;")
        button3.setStyleSheet("background-color: yellow; font-size: 16px; min-height: 30px; max-height: 30px; min-width: 30px; max-width: 30px;")
        button4.setStyleSheet("background-color: yellow; font-size: 16px; min-height: 30px; max-height: 30px; min-width: 30px; max-width: 30px;")
        
        top_layout.addWidget(button1)
        top_layout.addWidget(button2)
        top_layout.addWidget(button3)
        top_layout.addWidget(button4)

        main_layout.addWidget(top_container)
        main_layout.addStretch()  

        # Set the layout for the central widget
        central_widget.setLayout(main_layout)

        # Prepare the window for display
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MedicalMainWindow()
    sys.exit(app.exec_())
