import os
from PyQt5.QtCore import QSize

SCALE_COLOR = "coral"

ICON_SIZE = QSize(15, 15)
LOGO_ICON_SIZE = QSize(75, 75)  # To change icon size
PV_FONT_SIZE_FACTOR = 20000  # To change "patient viewer" font size
IV_FONT_SIZE_FACTOR = 2  # To change icon "image viewer" font size
CD_FONT_SIZE_FACTOR = 2
PIC_FONT_AND_COLOR = f"font-size: {36}px;color:white;font-family: Arial;"
IV_FONT_AND_COLOR = f"font-size: {36}px;color:white;font-family: Arial;"

# To change icon "CD Writer" font size
FONTSIZEFACTOR = 2  # To change button size
TIME_LINE_FONTSIZE_FACTOR = 0.5  # To change font size of  timeLineDropdown(ComboBox)
SERIES_SELECTION_FONTSIZE_FACTOR = 0.5  # To change font size of  series selection
ID_ACCESSION_ID_SET_FIXED_WIDTH = 70  # To set the width of id&assesment line edit
CLOSE_SET_FIXED_WIDTH = 30  # To set width of close button
# FIXED_WIDTH=20
META_DATA_FONT_SIZE = 10  # OVERLAY AND SUBPLOT(META DATA FONT SIZE)

ANNOTATE_LINE_SPACING = 0.01  # METADATA LINE SPACING
LINE_SPACING = 0.02
PRESET_BUTTON_FIXED_WIDTH = 50
PRESET_LINE_EDIT_FIXED_WIDTH = 60
PRESET_LABEL_FIXED_WIDTH = 60


PV_TITLE_FIXED_WIDTH = 1200
IV_TITLE_FIXED_WIDTH = 800
CD_TITLE_FIXED_WIDTH = 300  # to set the width of all title
NAME_LABEL_FIXED_WIDTH = 40  # to set the width of name label
NAME_LINE_EDIT_FIXED_WIDTH = 70  # to set the width of name line_edit
CALENDAR_LINE_EDIT_FIXED_WIDTH = 70  # to set the width of calendar line_edit
MODALITY_DROPDOWN_FIXED_WIDTH = 70  # to set the width of modality dropdown(ct,mr,us,cr)
SEARCH_FIXED_WIDTH = 60  # to set search button width
TOOL_FIXED_WIDTH = 60
SIDE_TOOL_FIXED_WIDTH = 50  # to set the width of all measurement tool button
# WINDOW_WIDTH=256
# WINDOW_CENTER=128
TABLE_ROW_SELECTION_COLOR = "QTableWidget::item:selected { background-color:#B8860B; }"

# COMBOBOX_SELECTION_COLOR="QComboBox::item:selected { background-color: cyan; }"
BUTTON_STYLE = (  # to se style for all button's
    "QPushButton {"
    "background-color: #B8860B; "
    "padding: 0px; "
    "margin: 0px; "
    "border-radius: 10px; "  # Adjust this based on your button's height
    "}"
)


# BUTTON_STYLE=("""
#             QPushButton {
#                 border: 2px solid #FFA52C; /* Green border */
#                 border-radius: 10px;
#                 background: qradialgradient(cx: 0.5, cy: 0.5, fx: 0.5, fy: 0.5, radius: 1, stop: 0 #FFFFFF, stop: 1 #B0E0E6); /* Cloud-like radial gradient background */
#                 color: #333333; /* Text color */
#                 font-size: 16px;
#                 font-weight: bold;
#             }
#             QPushButton:hover {
#                 background: qradialgradient(cx: 0.5, cy: 0.5, fx: 0.5, fy: 0.5, radius: 1, stop: 0 #E0FFFF, stop: 1 #00CED1); /* Light blue cloud-like radial gradient background on hover */
#             }
#         """)
PROGRESSBAR_STYLE = (
    "QProgressBar {border: 1px solid grey; border-radius: 10px; background: #B8860B;}"
    "QProgressBar::chunk {background: white;}"
)


PATCH_SET_LINE_WIDTH = 4 # "SELECT ALL"(figure_canvas)thickness color
CLOSE_BUTTON_COLOR = os.getenv(
    "CLOSE_BUTTON_COLOR", "#B8860B"
)  # set close button color
MINIMIZE_BUTTON_COLOR = os.getenv(
    "CLOSE_BUTTON_COLOR", "#B8860B"
)  # set close button color
PATCH_SET_EDGE_COLOR1 = os.getenv(
    "PATCH_SET_EDGE_COLOR1", "black"
)  # "select all" 2nd page  edge color change  without image and when click image

PATCH_SET_EDGE_COLOR2 = os.getenv(
    "PATCH_SET_EDGE_COLOR2", "#B8860B"
)  # "select all" edge color change when click image

PREVIEW_SET_FACE_COLOR = os.getenv(
    "PREVIEW_SET_FACE_COLOR", "#626665"
)  # PREVIEW 1st page
PATCH_SET_FACE_COLOR = os.getenv("PATCH_SET_FACE_COLOR", "black")  # 2nd page
# M_COLOR1=os.getenv("M_COLOR1", "GREEN")                                                  #title label
META_DATA_COLOR = os.getenv("META_DATA_COLOR", "white")  # meta data color
POSITION_COLOR = os.getenv("POSITION_COLOR", "lime")  # position color
# PRESET_WIDGET_BACKGROUND_COLOR=os.getenv("PRESET_WIDGET_BACKGROUND_COLOR", "#1d334a")                           #to set bg color for preset widget
DOCK_WIDGET_BACKGROUND_COLOR = os.getenv(
    "DOCK_WIDGET_BACKGROUND_COLOR", "#626665"
)  # to set bg color for docker widget
TITLE_LABLE_WIDGET_BACKGROUND_COLOR = os.getenv(
    "TITLE_LABLE_WIDGET_BACKGROUND_COLOR", "#626665"
)
SIDEBAR_WIDGET_BACKGROUND_COLOR = os.getenv(
    "SIDEBAR_WIDGET_BACKGROUND_COLOR", "#626665"
)  # "#1d334a"       #to set bg color for sidebar widget
IMAGE_NAMELIST_WIDGET_BACKGROUND_COLOR = os.getenv(
    "IMAGE_NAMELIST_WIDGET_BACKGROUND_COLOR", "#626665"
)  # to set bg color for image namelist widget
# TITLE_BAR_WIDGET_BACKGROUND_COLOR=os.getenv("TITLE_BAR_WIDGET_BACKGROUND_COLOR", "#1d334a")            #to set bg color for title bar widget
# M_BACKGROUND_COLOR2=os.getenv("M_BACKGROUND_COLOR2", "#FFA52C")
FILTER_GROUP_BOX_BG_COLOR = os.getenv(
    "FILTER_GROUP_BOX_BG_COLOR", "#B8860B"
)  # FILTER GROUP BOX BG COLOR
TOOLS_BUTTON_COLOR = os.getenv("TOOLS_BUTTON_COLOR", "#B8860B")  # TOOL BUTTONS  COLOR
TOOL_BOX_BG_COLOR = os.getenv("TOOL_BOX_BG_COLOR", "#B8860B")  # TOOL BOX bg color
# M_BACKGROUND_COLOR3=os.getenv("M_BACKGROUND_COLOR3", "dark#1d334a")
# M_BACKGROUND_COLOR4=os.getenv("M_BACKGROUND_COLOR4", "light#1d334a")
TABLE_WIDGET_BG_COLOR = os.getenv(
    "TABLE_WIDGET_BG_COLOR", "lightgrey"
)  #  to set bg color for tablewidget
# M_BACKGROUND_COLOR5=os.getenv("M_BACKGROUND_COLOR5", "white")                               #tablewidget bg color
# M_BACKGROUND_COLOR6=os.getenv("M_BACKGROUND_COLOR6", "black")
FULLSCREEN_WIDGET_BG_COLOR = os.getenv(
    "M_BACKGROUND_COLOR6", "black"
)  # fullscreen bg color



ANNOTATE_DATA_FONT_SIZE = 80

# P_I_C_BUTTON_STYLE="padding: 0px; margin: 0px; border: none;  "
P_I_C_BUTTON_STYLE = "padding: 0px; margin: 3px; border: 0px; font-size: 16px; background-color: #B8860B; min-height: 300px;"

LINE_EDIT_STYLE = "color: #F5F5F5;"
                
LINE_EDIT_BG_COLOR = "background-color: #F5F5F5;"
MODALITY_BG_COLOR = "background-color: #F5F5F5"
LINE_EDIT_BG_COLOR = "background-color: #F5F5F5"
MODALITY_BG_COLOR = "background-color: #F5F5F5"
LABEL_STYLE = "color: black;"
IMAGE_NAMELIST_TEXT_COLOR = os.getenv("IMAGE_NAMELIST_TEXT_COLOR", "WHITE")
TIME_LINE_DEOPDOWN_STYLE = "background-color: #F5F5F5; color: black;"
MODALITY_DROPDOWN_STYLE = "color: #F5F5F5;"
SERIES_SELECTION_STYLE = "background-color: #F5F5F5; color: black;"
BUTTON_HIDE = "border-style: none;"
TOOLTIP_STYLE = "QToolTip { color: black; background-color: black; }"

MODALITY_DROPDOWN_BORDER_COLOR = "QComboBox { border: 1px solid #F5F5F5; }"

# app.setStyleSheet(
# #             """
# #     # QWidget {
# #     #     font-weight: bold;

# #     # }
# #     # """
#         )

# CLOSE_BUTTON_FIXED_SIZE=(20, 20)

# COLUMN_WIDTHS= [150, 100, 50, 50, 100, 80, 80, 60, 80, 150]

# FILTER_GRID_SETCONTENTMARGINS=(10,10,10,10)
# SETCONTENTMARGINS=(0,0,0,0)
# CLOSE_SET_GEOMETRY=(1, 1, 1, 1)

# image_bgr = cv2.cvtColor(image, cv2.COLOR_#1d334a2BGR)

# self.figure.tight_layout(pad=0.09)
# self.imageAreaLayout.setSpacing(0)
ANNOTATION_BOX_STYLE = "round,pad=0.5"
ANNOTATION_TEXT_COLOR = "orange"
ANNOTATION_FONT_SIZE = 12
TEXT_ANNOTATION_FONT_SIZE = 12
ANNOTATION_BOX_FACE_COLOR = "brown"
HOVER_ANNOTATION_BACKGROUND_COLOR = "maroon"
LINE_WIDTH = 1
LINE_COLOR = "lime"
MARKER_SIZE = 5.5
ARROW_MARKER_COLOR = "yellow"
ANNOTATION_BOX_EDGE_COLOR = "black"
DRAW_LINE_PRESS = "lime"
POLY_HOVER_MARKER_COLOR = "hotpink"
POLY_DESELECT_MARKER_COLOR = "cornsilk"
POLY_HOVER_LINE_COLOR = "red"

POLY_GLOW_LINE_COLOR1 = "yellow"
POLY_GLOW_LINE_COLOR2 = "lime"


HOVER_ANNOTATION_BOX_EDGE_COLOR = "red"
SELECTED_ANNOTATION_FACE_COLOR = "red"
HOVER_ANNOTATION_BOX_FACE_COLOR = "maroon"
FILL_COLOR = "lime"
HOVER_MARKER_COLOR = "yellow"
MARKER_COLOR = "red"
SQUARE_SELECTED_COLOR = "red"
SQUARE_EDGE_COLOR = "red"
RESET_SQUARE_EDGE_COLOR = "lime"
SELECTED_MARKER_COLOR = "LIME"
ELLIPSE_EDGE_COLOR = "red"
RESET_ELLIPSE_EDGE_COLOR = "lime"
POLY_MARKER_SIZE = 3
