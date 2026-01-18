import tkinter as tk
import tkinter as tk
from tkinter import font
from PIL import Image, ImageDraw, ImageTk

class MonitorTestSuite:
    def __init__(self, root):
        self.root = root
        self.window = None
        self.canvas = None
        self.current_test_index = 0
        
        # Test sequences
        self.tests = [
            # 1. Start / Alignment
            ("Alignment & Geometry", self.draw_alignment),
            
            # 2. Defective Pixels (Solids)
            ("Dead Pixels: Black", lambda: self.draw_solid("#000000")),
            ("Dead Pixels: White", lambda: self.draw_solid("#FFFFFF")),
            ("Dead Pixels: Red",   lambda: self.draw_solid("#FF0000")),
            ("Dead Pixels: Green", lambda: self.draw_solid("#00FF00")),
            ("Dead Pixels: Blue",  lambda: self.draw_solid("#0000FF")),
            
            # 3. Uniformity (Grays)
            ("Uniformity: 25% Gray", lambda: self.draw_solid("#404040")),
            ("Uniformity: 50% Gray", lambda: self.draw_solid("#808080")),
            ("Uniformity: 75% Gray", lambda: self.draw_solid("#C0C0C0")),
            
            # 4. Gradients
            ("Gradients: RGB", self.draw_rgb_gradients),
            ("Gradients: Grayscale", self.draw_gray_gradient),
            
            # 5. Sharpness
            ("Sharpness & Text", self.draw_sharpness),
            
            # 6. Gamma (Simple Checkerboard)
            ("Gamma Check (2.2)", self.draw_gamma_check),
            
            # --- Lagom Style Tests ---
            ("Lagom: Black Level", self.draw_lagom_black_level),
            ("Lagom: White Saturation", self.draw_lagom_white_saturation),
            ("Lagom: Contrast Scales", self.draw_lagom_contrast),
            ("Lagom: Gamma Calibration", self.draw_lagom_gamma_test) # Uses PIL
        ]

    def start(self):
        """Launches the fullscreen test window."""
        self.window = tk.Toplevel(self.root)
        self.window.attributes("-fullscreen", True)
        self.window.configure(bg="black")
        
        # Canvas for drawing
        self.canvas = tk.Canvas(self.window, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind keys
        self.window.bind("<Right>", self.next_test)
        self.window.bind("<Left>", self.prev_test)
        self.window.bind("<Escape>", self.close)
        self.window.bind("<Button-1>", self.next_test) # Click to advance
        
        self.current_test_index = 0
        self.run_current_test()
        
        # Show initial helper text for 3 seconds
        self.show_toast("New: Lagom-style tests added. Press -> to explore.")

    def close(self, event=None):
        if self.window:
            self.window.destroy()
            self.window = None

    def next_test(self, event=None):
        self.current_test_index = (self.current_test_index + 1) % len(self.tests)
        self.run_current_test()

    def prev_test(self, event=None):
        self.current_test_index = (self.current_test_index - 1) % len(self.tests)
        self.run_current_test()

    def run_current_test(self):
        if not self.canvas:
            return
            
        # Clear canvas
        self.canvas.delete("all")
        self.canvas.configure(bg="black") # Reset bg
        
        # Get test info
        name, func = self.tests[self.current_test_index]
        print(f"Running Test: {name}")
        
        # Exec test
        func()
        
        # Draw label (fades out ideally, but static small label is fine)
        self.drawing_label(name)

    def drawing_label(self, text):
        # Small text at top left with shadow for visibility
        self.canvas.create_text(21, 21, text=text, anchor="nw", fill="black", font=("Arial", 12))
        self.canvas.create_text(20, 20, text=text, anchor="nw", fill="white", font=("Arial", 12))

    def show_toast(self, text):
        t = self.canvas.create_text(
            self.window.winfo_screenwidth()//2, 
            self.window.winfo_screenheight()//2,
            text=text, fill="white", font=("Arial", 24, "bold"), justify=tk.CENTER
        )
        self.window.after(3000, lambda: self.canvas.delete(t))

    # --- Test Patterns ---

    def draw_solid(self, color):
        self.canvas.configure(bg=color)

    def draw_alignment(self):
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        
        # Grid lines
        for x in range(0, w, 100):
            self.canvas.create_line(x, 0, x, h, fill="#333333")
        for y in range(0, h, 100):
            self.canvas.create_line(0, y, w, y, fill="#333333")
            
        # Center Circle
        cx, cy = w//2, h//2
        r = min(w, h) // 3
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="white", width=2)
        
        # Crosshair
        self.canvas.create_line(cx, 0, cx, h, fill="white", width=1)
        self.canvas.create_line(0, cy, w, cy, fill="white", width=1)
        
        # Border
        self.canvas.create_rectangle(2, 2, w-2, h-2, outline="red", width=2)
        
        # Circles in corners
        r2 = 50
        corners = [(r2, r2), (w-r2, r2), (w-r2, h-r2), (r2, h-r2)]
        for x, y in corners:
             self.canvas.create_oval(x-r2, y-r2, x+r2, y+r2, outline="yellow")

    def draw_rgb_gradients(self):
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        
        # Split height into 3 strips
        strip_h = h // 3
        
        # Only draw steps for performance (drawing 1920 lines is slow in Tkinter)
        steps = 256
        step_w = w / steps
        
        for i in range(steps):
            x1 = i * step_w
            x2 = (i+1) * step_w
            
            # Red
            hex_r = f"#{i:02x}0000"
            self.canvas.create_rectangle(x1, 0, x2, strip_h, fill=hex_r, outline="")
            
            # Green
            hex_g = f"#00{i:02x}00"
            self.canvas.create_rectangle(x1, strip_h, x2, strip_h*2, fill=hex_g, outline="")
            
            # Blue
            hex_b = f"#0000{i:02x}"
            self.canvas.create_rectangle(x1, strip_h*2, x2, h, fill=hex_b, outline="")

    def draw_gray_gradient(self):
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        
        steps = 256
        step_w = w / steps
        
        for i in range(steps):
            x1 = i * step_w
            x2 = (i+1) * step_w
            val = f"{i:02x}"
            color = f"#{val}{val}{val}"
            self.canvas.create_rectangle(x1, 0, x2, h, fill=color, outline="")

    def draw_sharpness(self):
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        self.canvas.configure(bg="white")
        
        text = "The quick brown fox jumps over the lazy dog. 1234567890"
        
        sizes = [8, 10, 12, 14, 18, 24, 36, 48, 72]
        y = 50
        
        for size in sizes:
            f = font.Font(family="Helvetica", size=-size) # Negative for pixels
            self.canvas.create_text(w//2, y, text=f"{size}px: {text}", font=f, fill="black")
            y += size + 20

    def draw_gamma_check(self):
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        cx = w // 2
        
        try:
            self.canvas.create_rectangle(0, 0, cx, h, fill="black")
            self.canvas.create_rectangle(0, 0, cx, h, fill="white", stipple="gray50") # 50% dither
        except:
            self.canvas.create_rectangle(0, 0, cx, h, fill="#808080")
            
        self.canvas.create_text(cx//2, 50, text="Dithered 50%", fill="red", font=("Arial", 20))
        
        # Solid Grays
        grays = [128, 160, 192]
        section_h = h // len(grays)
        for i, g in enumerate(grays):
            color = f"#{g:02x}{g:02x}{g:02x}"
            y1 = i * section_h
            y2 = (i+1) * section_h
            self.canvas.create_text(cx + 100, y1 + 50, text=f"Solid {g}", fill="white")
            self.canvas.create_rectangle(cx, y1, w, y2, fill=color, outline="")

    # --- Lagom Implementations ---

    def draw_lagom_black_level(self):
        """Draws 20 dark gray squares on black background."""
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        self.canvas.configure(bg="black")
        
        cols = 5
        rows = 4
        box_w = w // (cols + 2)
        box_h = h // (rows + 2)
        start_x = box_w
        start_y = box_h
        
        value = 1
        for r in range(rows):
            for c in range(cols):
                if value > 20: break
                
                x1 = start_x + c * box_w
                y1 = start_y + r * box_h
                x2 = x1 + box_w - 20
                y2 = y1 + box_h - 20
                
                # Color (v, v, v)
                hex_val = f"#{value:02x}{value:02x}{value:02x}"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=hex_val, outline="white")
                self.canvas.create_text(x1 + box_w//2, y1 + box_h//2, text=str(value), fill="white")
                
                value += 1
                
        self.canvas.create_text(w//2, 50, text="Black Level: Squares 1-5 might be invisible on untuned monitors.", fill="white", font=("Arial", 16))

    def draw_lagom_white_saturation(self):
        """Draws light gray squares on white background."""
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        self.canvas.configure(bg="white")
        
        # Lagom uses 200 - 254
        # Let's do 12 squares: 200, 210 ... 250, 251, 252, 253, 254
        values = [200, 210, 220, 230, 240, 245, 248, 250, 251, 252, 253, 254]
        
        cols = 4
        rows = 3
        box_w = w // (cols + 2)
        box_h = h // (rows + 2)
        start_x = box_w
        start_y = box_h
        
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= len(values): break
                v = values[idx]
                
                x1 = start_x + c * box_w
                y1 = start_y + r * box_h
                x2 = x1 + box_w - 20
                y2 = y1 + box_h - 20
                
                hex_val = f"#{v:02x}{v:02x}{v:02x}"
                # No outline, rely on contrast against white
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=hex_val, outline="")
                self.canvas.create_text(x1 + box_w//2, y1 + box_h//2, text=str(v), fill="black")
                
                idx += 1
        
        self.canvas.create_text(w//2, 50, text="White Saturation: Can you see 254?", fill="black", font=("Arial", 16))

    def draw_lagom_contrast(self):
        """Draws detailed step gradients for RGB."""
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        self.canvas.configure(bg="black")
        
        # 3 Strips: R, G, B
        strip_h = h // 3
        
        # 32 distinct steps: 0, 8, 16...
        steps = 32
        step_w = w / steps
        val_step = 256 / steps
        
        for i in range(steps):
            v_int = int(i * val_step)
            if v_int > 255: v_int = 255
            v_hex = f"{v_int:02x}"
            
            x1 = i * step_w
            x2 = (i+1) * step_w
            
            # Red Strip
            self.canvas.create_rectangle(x1, 0, x2, strip_h, fill=f"#{v_hex}0000", outline="")
            
            # Green Strip
            self.canvas.create_rectangle(x1, strip_h, x2, strip_h*2, fill=f"#00{v_hex}00", outline="")
            
            # Blue Strip
            self.canvas.create_rectangle(x1, strip_h*2, x2, h, fill=f"#0000{v_hex}", outline="")
            
            # Labels occasionally
            if i % 4 == 0:
                 self.canvas.create_text(x1+5, strip_h-10, text=str(v_int), fill="white", anchor="nw")

    def draw_lagom_gamma_test(self):
        """
        Draws precise Gamma calibration bands using PIL.
        (Gray, Red, Green, Blue)
        """
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        self.canvas.configure(bg="black")
        
        # Create a new PIL image
        img = Image.new("RGB", (w, h), (0, 0, 0))
        pixels = img.load()
        draw = ImageDraw.Draw(img)
        
        strips = 4
        strip_w = w // strips
        
        # Define Strip Colors (R, G, B factors)
        configs = [
            (1, 1, 1, "Gray"),
            (1, 0, 0, "Red"),
            (0, 1, 0, "Green"),
            (0, 0, 1, "Blue")
        ]
        
        # For each pixel row, determine dither value and solid gradient value
        # Dither: Alternating 0 and 255 lines (50% luminance physically)
        # Gradient: 0 at top? to 255 at bottom?
        # Lagom usually puts 'Target 50% luminance' (Gammas) at specific heights.
        
        # Let's map Y (height) to Value (0-255).
        # Top = 255, Bottom = 0? Or other way? 
        # Usually blending point for 2.2 is somewhat high.
        
        for x in range(w):
            col_idx = x // strip_w
            if col_idx >= 4: col_idx = 3
            
            rf, gf, bf, name = configs[col_idx]
            
            # Determine if this x is part of the 'solid' column or 'dither' column?
            # Lagom interleaves them or puts them side-by-side.
            # Simpler: 25% of strip width is Solid Gradient, 75% is Dither Background?
            
            in_strip_x = x % strip_w
            is_solid_bar = (in_strip_x > strip_w * 0.3) and (in_strip_x < strip_w * 0.7)
            
            if is_solid_bar:
                # Solid Gradient (0-255)
                # Let's make Top=255, Bottom=0
                val = int(255 * (1 - (x / w))) # Wait, Y is not available in outer loop logic for pixels easily if we loop y inside
                pass
            else:
                pass
                
        # Optimization: Don't loop pixels in Python! Too slow.
        # Use simple Draws.
        
        for i, (rf, gf, bf, name) in enumerate(configs):
            x_start = i * strip_w
            x_end = (i+1) * strip_w
            cx = x_start + strip_w // 2
            
            # 1. Fill Background with Dither (Scanlines)
            # Draw lines.
            for y in range(0, h, 2):
                # Black line (already 0)
                # White line (255) colorized
                c = (255*rf, 255*gf, 255*bf)
                draw.line([(x_start, y), (x_end, y)], fill=c)
                
            # 2. Draw Solid Gradient in Middle
            # We want to find where Dither (approx 50% light) matches Gradient.
            # Gradient goes from 0 to 255 (Top to Bottom).
            grad_w = int(strip_w * 0.3)
            gx1 = cx - grad_w // 2
            gx2 = cx + grad_w // 2
            
            # Draw gradient via lines
            for y in range(h):
                val = int(255 * (y / h)) # 0 at top, 255 at bottom.
                c = (int(val*rf), int(val*gf), int(val*bf))
                draw.line([(gx1, y), (gx2, y)], fill=c)
                
            # 3. Draw Gamma Markers
            # Formula: 0.5 = (Val / 255) ^ Gamma
            # (0.5)^(1/Gamma) = Val/255
            # Val = 255 * (0.5)^(1/Gamma)
            # Y corresponds to Val (y = h * (Val/255))
            
            gammas = [1.8, 2.2, 2.4]
            for g in gammas:
                target_val = 255 * (0.5**(1/g))
                y_pos = int(h * (target_val / 255))
                
                # Draw marker text
                draw.text((gx2 + 5, y_pos - 5), f"{g}", fill=(255,255,255))
                draw.line([(gx2, y_pos), (gx2+10, y_pos)], fill=(255,255,255))
                
        # Convert to Tkinter
        self.tk_gamma_img = ImageTk.PhotoImage(img) # Keep ref
        self.canvas.create_image(0, 0, image=self.tk_gamma_img, anchor="nw")
        
        self.canvas.create_text(w//2, 30, text="Gamma Calibration: The solid bar should blend into the stripes at 2.2", fill="white", font=("Arial", 16), justify=tk.CENTER)

