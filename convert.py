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

        self.resized_width = None
        self.resized_height = None

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
        file_types = [
            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("GIF files", "*.gif"),
            ("All files", "*.*")
        ]
        self.image_path = filedialog.askopenfilename(filetypes=file_types)
        if not self.image_path:
            return
        self.image = Image.open(self.image_path)
        self.display_image()

    def display_image(self):
        if self.image:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            width, height = self.image.size
            scale_w = canvas_width / width
            scale_h = canvas_height / height
            scale = min(scale_w, scale_h)
            new_size = (int(width * scale), int(height * scale))
            self.resized_width, self.resized_height = new_size
            resized_image = self.image.resize(new_size, Image.Resampling.LANCZOS)            
            self.image_tk = ImageTk.PhotoImage(resized_image)
            self.canvas.create_image((canvas_width - new_size[0]) // 2, (canvas_height - new_size[1]) // 2, anchor=tk.NW, image=self.image_tk)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))


    def resize_image(self, event):
        self.display_image()

    def add_point(self, event):
        x, y = event.x, event.y
        self.coordinates.append((x, y))
        if len(self.coordinates) > 1:
            last_x, last_y = self.coordinates[-2]
            self.canvas.create_line(last_x, last_y, x, y, fill='red')
        self.canvas.create_oval(x-3, y-3, x+3, y+3, fill='red')

    # Store the x-coordinate of the azimuth origin and draw a vertical line at that x-coordinate with a label
    def set_az0(self, event):
        self.az0_x = event.x
        if self.image:
            self.canvas.create_line(self.az0_x, 0, self.az0_x, self.canvas.winfo_height(), fill='green', dash=(4, 2))
            self.canvas.create_text(self.az0_x + 10, 10, text="Az=0", fill='green')

    def calculate_azimuth(self, x):
        width = self.resized_width
        # Calculate azimuth: Determine the angular displacement of a point from the designated zero point (az0_x) relative to the image width.
        # The modulus operation ensures proper wrapping at the image boundaries to maintain a continuous 360-degree range. The result is scaled to degrees.
        azimuth = ((x - self.az0_x) % width) / width * 360  # Convert pixel offset to degrees, accounting for circular image wrap-around.

        return round(azimuth)

    def save_hrz(self):
        if not self.coordinates or not self.image or self.az0_x is None:
            return
        
        height = self.resized_height
        vertical_fov = 180

        # Split the coordinates into two lists based on whether they are left or right of the meridian
        horizon_coordinates_left_of_meridian = []
        horizon_coordinates_right_of_meridian = []
        for x, y in self.coordinates:
            azimuth = self.calculate_azimuth(x)
            elevation = ((height / 2 - y) / (height / 2) * (vertical_fov / 2))
            
            if x < self.az0_x:
                horizon_coordinates_left_of_meridian.append((azimuth, elevation))
            else:
                horizon_coordinates_right_of_meridian.append((azimuth, elevation))
        
        # Merge the two lists
        horizon_coordinates = horizon_coordinates_right_of_meridian + horizon_coordinates_left_of_meridian

        # Deduplicate consecutive azimuths
        deduplicated_horizon_coordinates = []
        for i, (azimuth, elevation) in enumerate(horizon_coordinates):
            if i == 0 or azimuth != horizon_coordinates[i-1][0]:
                deduplicated_horizon_coordinates.append((azimuth, elevation))

        # Ensure that the first azimuth is 0 by changing the first azimuth to 0
        if deduplicated_horizon_coordinates[0][0] != 0:
            deduplicated_horizon_coordinates[0] = (0, deduplicated_horizon_coordinates[0][1])

        hrz_path = filedialog.asksaveasfilename(defaultextension=".hrz", filetypes=[("HRZ files", "*.hrz")])
        if not hrz_path:
            return
        
        with open(hrz_path, 'w') as file:
            for azimuth, elevation in deduplicated_horizon_coordinates:
                file.write(f"{azimuth} {elevation:.1f}\n")
    
        print(f"Horizon file saved to {hrz_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = HorizonMarkerApp(root)
    root.mainloop()
