import numpy as np
from PyQt5.QtWidgets import QMainWindow
from constants import *
from matplotlib.lines import Line2D
import numpy as np
from PyQt5.QtWidgets import QMainWindow
from matplotlib.lines import Line2D

class Scale(QMainWindow):
    def __init__(self, dcm,figure,ax,canvas):
        super().__init__()
        self.dcm = dcm
        self.fig = figure
        self.ax = ax
        self.canvas = canvas
        self.lines = []
        self.zoomFactor = 1.0
        self.draw_scale(self.zoomFactor)
        

    def calculate_points(self):
        image_rows=self.dcm.Rows
        image_cols = self.dcm.Columns

        # Vertical Scale
        temp_vertical = image_rows /8
        start_point_vertical = np.zeros(2,dtype = float)
        end_point_vertical = np.zeros(2,dtype = float)
            
        start_point_vertical[1] = image_rows/2 - temp_vertical
        end_point_vertical[1] = image_rows/2 + temp_vertical
            
        start_point_vertical[0] = image_cols -15
        end_point_vertical[0] = image_cols -15
            
        # Horizontal Scale
        temp_horizontal = image_cols /8
        start_point_horizontal = np.zeros(2,dtype = float)
        end_point_horizontal = np.zeros(2,dtype = float)
            
        start_point_horizontal[0] = image_cols/2 - temp_horizontal
        end_point_horizontal[0] = image_cols/2 + temp_horizontal
            
        start_point_horizontal[1] = image_rows -15
        end_point_horizontal[1] = image_rows - 15
            
        return start_point_vertical, end_point_vertical, start_point_horizontal, end_point_horizontal

    def draw_scale(self,zoomFactor = 1.0):
        self.zoomFactor=zoomFactor
        for line in self.lines:
            line.remove()
        self.lines.clear()
        # print(self.zoomFactor)
        px,py = self.dcm.PixelSpacing
        start_point_vertical, end_point_vertical, start_point_horizontal, end_point_horizontal = self.calculate_points()
        rows = self.dcm.Rows
        cols = self.dcm.Columns
    
        vertical_ticks = []
        horizontal_ticks = []
                 
        # Calculate the length in cm for vertical line
        vertical_length_pixels = end_point_vertical[1] - start_point_vertical[1]
        horizontal_length_pixels = end_point_horizontal[0] - start_point_horizontal[0]

        vertical_pixels_per_cm = 10 / py
        horizontal_pixels_per_cm = 10 / px

        vertical_num_ticks = int((vertical_length_pixels / self.zoomFactor) / vertical_pixels_per_cm)
        horizontal_num_ticks = int((horizontal_length_pixels / self.zoomFactor) / horizontal_pixels_per_cm)

        
        # Calculate vertical and horizontal base line and apply normalisation to it
        vertical_line =  ([start_point_vertical[0]/cols, end_point_vertical[0]/cols], [start_point_vertical[1]/rows, (start_point_vertical[1] + (vertical_num_ticks * vertical_pixels_per_cm * self.zoomFactor))/rows])
        horizontal_line = ([start_point_horizontal[0]/cols, (start_point_horizontal[0] + (horizontal_num_ticks * horizontal_pixels_per_cm * self.zoomFactor))/cols], [start_point_horizontal[1]/rows, end_point_horizontal[1]/rows])    

        
        for i in range(vertical_num_ticks+1):
            tick_y = start_point_vertical[1] + (i * vertical_pixels_per_cm * self.zoomFactor)  # Adjusted for zoom
            vertical_ticks.append(([(start_point_vertical[0] - 2.5)/cols, start_point_vertical[0]/cols], [tick_y/rows, tick_y/rows]))       
            
        
        # Draw the tick marks for the horizontal line
        # line_coords = [vertical_line,horizontal_line]
        # for x_coords,y_coords in line_coords:
        #     y_coord = [1 - value for value in y_coords]  # To adjust the top-bottom position
        #     lines =  Line2D(x_coords,y_coord, transform=self.fig.transFigure, color=SCALE_COLOR, linewidth=1)
        #     self.lines.append(lines)
        #     self.fig.add_artist(lines)

        vertical_coords = vertical_line[0], [1 - value for value in vertical_line[1]]  # Adjust top-bottom position
        vertical_line_artist = Line2D(vertical_coords[0], vertical_coords[1], transform=self.fig.transFigure, color=SCALE_COLOR, linewidth=0.8)
        self.lines.append(vertical_line_artist)
        self.fig.add_artist(vertical_line_artist)


        for x_coords,y_coords in vertical_ticks:
            y_coords = [1 - value for value in y_coords]  # To adjust the top-bottom position
            vt_line =  Line2D(x_coords,y_coords, transform=self.fig.transFigure, color=SCALE_COLOR, linewidth=0.8)
            self.lines.append(vt_line)
            self.fig.add_artist(vt_line)

        # # For horizontal
        # for i in range(horizontal_num_ticks + 1):
        #     tick_x = start_point_horizontal[0] + (i * horizontal_pixels_per_cm * self.zoomFactor) # Change 10 to the pixel length representing 1 cm
        #     horizontal_ticks.append(([tick_x/cols, tick_x/cols], [(start_point_horizontal[1] - 2.5)/rows, start_point_horizontal[1]/rows]))

        # horizontal_coords = horizontal_line[0], [1 - value for value in horizontal_line[1]]  # Adjust top-bottom position
        # horizontal_line_artist = Line2D(horizontal_coords[0], horizontal_coords[1], transform=self.ax.transAxes, color=SCALE_COLOR, linewidth=0.8)
        # self.lines.append(horizontal_line_artist)

        # self.fig.add_artist(horizontal_line_artist)

        # for x_coords,y_coords in horizontal_ticks:
        #     y_coords = [1 - value for value in y_coords]  # To adjust the top-bottom position
        #     ht_line =  Line2D(x_coords,y_coords, transform=self.ax.transAxes, color=SCALE_COLOR, linewidth=0.8)
        #     self.lines.append(ht_line)
        #     self.fig.add_artist(ht_line)

        self.canvas.draw_idle()

        return 0