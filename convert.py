import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class HorizonMarkerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Horizon Marker")
        self.root.state('zoomed')  # Start the window maximized
        
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.image = None
        self.image_tk = None
        self.image_path = None
        self.coordinates = []
        self.az0_x = None

        self.menu = tk.Menu(root)
        self.root.config(menu=self.menu)
        
        self.file_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Image", command=self.open_image)
        self.file_menu.add_command(label="Save HRZ", command=self.save_hrz)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)
        
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<Button-3>", self.set_az0)
        self.root.bind("<Configure>", self.resize_image)

    def open_image(self):
        self.image_path = filedialog.askopenfilename()
        if not self.image_path:
            return
        self.image = Image.open(self.image_path)
        self.display_image()

    def display_image(self):
        if self.image:
            width, height = self.image.size
            ratio = min(self.canvas.winfo_width() / width, self.canvas.winfo_height() / height)
            new_size = (int(width * ratio), int(height * ratio))
            # Using the updated resampling method
            resized_image = self.image.resize(new_size, Image.Resampling.LANCZOS)
            self.image_tk = ImageTk.PhotoImage(resized_image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))


    def resize_image(self, event):
        self.display_image()

    def add_point(self, event):
        x, y = event.x, event.y
        if self.coordinates:
            last_x, last_y = self.coordinates[-1]
            self.canvas.create_line(last_x, last_y, x, y, fill='red')
        self.coordinates.append((x, y))
        self.canvas.create_oval(x-3, y-3, x+3, y+3, fill='red')
        
    def set_az0(self, event):
        self.az0_x = event.x
        if self.image:
            self.canvas.create_line(self.az0_x, 0, self.az0_x, self.image.height, fill='blue', dash=(4, 2))

    def calculate_azimuth(self, x):
        width = self.image.width
        if x >= self.az0_x:
            return (x - self.az0_x) / width * 360
        else:
            return 360 - ((self.az0_x - x) / width * 360)
        
    def save_hrz(self):
        if not self.coordinates or not self.image or self.az0_x is None:
            return
        
        width, height = self.image.size
        horizon_coordinates = []
        
        for x, y in self.coordinates:
            azimuth = self.calculate_azimuth(x)
            elevation = 90 - (y / height) * 180
            horizon_coordinates.append((azimuth, elevation))
        
        horizon_coordinates = sorted(horizon_coordinates, key=lambda coord: coord[0])
        if horizon_coordinates[0][0] != 0:
            first_elevation = horizon_coordinates[0][1]
            horizon_coordinates = [(0, first_elevation)] + horizon_coordinates

        hrz_path = filedialog.asksaveasfilename(defaultextension=".hrz", filetypes=[("HRZ files", "*.hrz")])
        if not hrz_path:
            return
        
        with open(hrz_path, 'w') as file:
            file.write("Az Alt\n")
            for azimuth, elevation in horizon_coordinates:
                file.write(f"{azimuth:.2f} {elevation:.2f}\n")
        
        print(f"Horizon file saved to {hrz_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HorizonMarkerApp(root)
    root.mainloop()
