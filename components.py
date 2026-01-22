import customtkinter as ctk
from config import COLOR_ACCENT_MAIN, COLOR_SURFACE, COLOR_GRID

class LineChart(ctk.CTkCanvas):
    def __init__(self, master, width=300, height=100, line_color=COLOR_ACCENT_MAIN, line_color2=None, auto_scale=False, **kwargs):
        mode = ctk.get_appearance_mode()
        idx = 1 if mode == "Dark" else 0
        
        super().__init__(master, width=width, height=height, highlightthickness=0, bg=COLOR_SURFACE[idx], **kwargs)
        
        self.line_color_tuple = line_color
        self.current_line_color = line_color[idx]
        
        self.line_color2_tuple = line_color2
        self.current_line_color2 = line_color2[idx] if line_color2 else None
        
        self.grid_color = COLOR_GRID[idx]
        self.auto_scale = auto_scale
        
        self.data = [0] * 60
        self.data2 = [0] * 60 if line_color2 else None
        
        self.width = width
        self.height = height

    def update_theme(self, mode):
        idx = 1 if mode == "Dark" else 0
        self.configure(bg=COLOR_SURFACE[idx])
        self.current_line_color = self.line_color_tuple[idx]
        if self.line_color2_tuple:
            self.current_line_color2 = self.line_color2_tuple[idx]
        self.grid_color = COLOR_GRID[idx]
        self.draw()

    def add_value(self, value, value2=None):
        self.data.pop(0)
        self.data.append(value)
        
        if self.data2 is not None and value2 is not None:
            self.data2.pop(0)
            self.data2.append(value2)
            
        self.draw()

    def draw(self):
        self.delete("all")
        
        max_val = 100
        if self.auto_scale:
            all_vals = self.data + (self.data2 if self.data2 else [])
            m = max(all_vals) if all_vals else 0
            if m > 100: max_val = m * 1.2
            elif m > 10: max_val = 100
            else: max_val = 10

        x_gap = self.width / (len(self.data) - 1)
        
        for i in range(1, 5):
            y = i * (self.height / 5)
            self.create_line(0, y, self.width, y, fill=self.grid_color, dash=(2, 4))

        def _plot(data_list, color):
            points = []
            for i, val in enumerate(data_list):
                x = i * x_gap
                if val < 0: val = 0
                y = self.height - (val / max_val * self.height)
                points.append(x)
                points.append(y)
            if len(points) > 2:
                self.create_line(points, fill=color, width=4, stipple="gray50", smooth=True)
                self.create_line(points, fill=color, width=2, smooth=True)

        if self.data2: _plot(self.data2, self.current_line_color2)
        _plot(self.data, self.current_line_color)