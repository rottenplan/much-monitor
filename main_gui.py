import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from camera_handler import CameraHandler
from calibration_logic import CalibrationLogic
import time
import cv2

class CalibrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Much Monitor Calibration")
        self.root.geometry("500x600")
        
        self.logic = CalibrationLogic()
        self.camera = None
        self.preview_active = False
        self.camera_map = {} # Maps display name to index
        
        self.setup_ui()
        self.update_button_state()
        self.refresh_cameras()
        
    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.label = tk.Label(
            self.main_frame, 
            text="Much Monitor Calibration", 
            fg="#00d1ff", bg="#1e1e1e", # Cyan color for title
            font=("Arial", 28, "bold")
        )
        self.label.pack(pady=(50, 20))
        
        self.info_text = tk.Label(
            self.main_frame,
            text="Siapkan kamera smartphone Anda (Continuity Camera).\nLetakkan kamera menghadap layar tepat di tengah.",
            fg="#00d1ff", bg="#1e1e1e", 
            font=("Arial", 12),
            justify=tk.CENTER
        )
        self.info_text.pack(pady=10)

        # Camera selection label (Centered and On Top)
        tk.Label(
            self.main_frame, 
            text="Pilih Kamera:", 
            fg="#00d1ff", bg="#1e1e1e", 
            font=("Arial", 12, "bold")
        ).pack(pady=(10, 5))

        # Camera selection controls frame
        cam_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        cam_frame.pack(pady=(0, 20))

        self.cam_var = tk.StringVar()
        self.cam_combo = ttk.Combobox(cam_frame, textvariable=self.cam_var, state="readonly", width=30)
        self.cam_combo.grid(row=0, column=0, padx=5)
        
        self.refresh_btn = tk.Button(cam_frame, text="Refresh", command=self.refresh_cameras, bg="#444444", fg="black", font=("Arial", 10, "bold"))
        self.refresh_btn.grid(row=0, column=1, padx=5)

        # Mock Mode Checkbox
        self.mock_var = tk.BooleanVar(value=False)
        self.mock_check = tk.Checkbutton(
            self.main_frame, 
            text="Gunakan Mock Camera (Untuk Testing)", 
            variable=self.mock_var,
            command=self.update_button_state, # Update button when toggled
            fg="#00d1ff", bg="#1e1e1e", 
            selectcolor="#333",
            activebackground="#1e1e1e",
            activeforeground="#00d1ff",
            font=("Arial", 11, "bold")
        )
        self.mock_check.pack(pady=5)

        self.perm_info = tk.Label(
            self.main_frame,
            text="PENTING: Pastikan Terminal/IDE memiliki izin Kamera di\nSystem Settings > Privacy & Security > Camera",
            fg="#00d1ff", bg="#1e1e1e", 
            font=("Arial", 11, "bold", "italic")
        )
        self.perm_info.pack(pady=10)
        
        self.start_button = tk.Button(
            self.main_frame,
            text="Mulai Kalibrasi",
            command=self.start_calibration,
            bg="#007aff", fg="black",
            font=("Arial", 16, "bold"),
            padx=40, pady=20,
            relief=tk.RAISED,
            cursor="hand2"
        )
        self.start_button.pack(pady=30)

    def refresh_cameras(self):
        cameras_with_names = CameraHandler.get_available_cameras_with_names()
        self.camera_map = {}
        
        display_names = []
        for idx, name in cameras_with_names:
            display_name = f"{name} (ID: {idx})"
            self.camera_map[display_name] = idx
            display_names.append(display_name)
            
        if not display_names:
            self.cam_combo['values'] = ("Tidak ada kamera terdeteksi",)
            self.cam_combo.current(0)
        else:
            self.cam_combo['values'] = display_names
            self.cam_combo.current(0)
        
        self.update_button_state()

    def update_button_state(self):
        is_mock = self.mock_var.get()
        selection = self.cam_var.get()
        
        # Check if button should be enabled
        has_camera = "Tidak ada" not in selection and selection != ""
        
        if is_mock or has_camera:
            self.start_button.config(state=tk.NORMAL, bg="#007aff")
        else:
            self.start_button.config(state=tk.DISABLED, bg="#444444")

    def start_calibration(self):
        is_mock = self.mock_var.get()
        selection = self.cam_var.get()
        
        if not is_mock and "Tidak ada" in selection:
            messagebox.showwarning("Peringatan", "Silakan hubungkan kamera terlebih dahulu atau gunakan Mock Mode.")
            return

        if is_mock:
            cam_index = 0
        else:
            # Retrieve index from map using full selection string
            cam_index = self.camera_map.get(selection, 0)
            
        self.camera = CameraHandler(camera_index=cam_index, mock_mode=is_mock)
        
        if not self.camera.start():
            messagebox.showerror(
                "Error", 
                "Gagal membuka kamera.\n\nPastikan kamera terhubung dan izin sudah diberikan."
            )
            return
        
        self.show_calibration_screen()

    def show_calibration_screen(self):
        self.calib_win = tk.Toplevel(self.root)
        self.calib_win.attributes("-fullscreen", True)
        self.calib_win.configure(bg="black")
        
        screen_w = self.calib_win.winfo_screenwidth()
        screen_h = self.calib_win.winfo_screenheight()
        
        # UI Container
        self.overlay_canvas = tk.Canvas(self.calib_win, bg="black", highlightthickness=0)
        self.overlay_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Live Preview Label (Slightly larger now)
        preview_w, preview_h = 400, 300
        self.preview_label = tk.Label(self.calib_win, bg="#1a1a1a", borderwidth=2, relief=tk.SOLID)
        self.preview_label.place(relx=0.5, rely=0.6, anchor="center") # Pindah ke tengah bawah patch
        
        # Center Target (Besar frame disesuaikan agar mudah membidik)
        patch_size = 300
        x1, y1 = (screen_w - patch_size)//2, (screen_h - patch_size)//4 # Geser sedikit ke atas
        x2, y2 = x1 + patch_size, y1 + patch_size
        
        self.target_rect = self.overlay_canvas.create_rectangle(
            x1-5, y1-5, x2+5, y2+5, 
            outline="#007aff", width=3
        )
        
        self.patch = tk.Frame(self.calib_win, bg="white", width=patch_size, height=patch_size)
        self.patch.place(x=x1, y=y1)
        
        self.status_label = tk.Label(
            self.calib_win, 
            text="Langkah 1: Posisikan Kamera", 
            fg="#00d1ff", bg="black",
            font=("Arial", 28, "bold")
        )
        self.status_label.place(relx=0.5, rely=0.1, anchor="center")

        self.sub_status = tk.Label(
            self.calib_win,
            text="Pastikan lensa kamera sejajar dengan kotak biru di atas.\nLihat preview di bawah untuk memastikan posisi sudah pas.",
            fg="#00d1ff", bg="black",
            font=("Arial", 14),
            justify=tk.CENTER
        )
        self.sub_status.place(relx=0.5, rely=0.18, anchor="center")

        # Instruction or Ready Signal
        self.ready_btn = tk.Button(
            self.calib_win,
            text="SAYA SUDAH SIAP, MULAI KALIBRASI",
            command=self.confirm_and_start,
            bg="#28a745", fg="black",
            font=("Arial", 18, "bold"),
            padx=40, pady=20,
            cursor="hand2"
        )
        self.ready_btn.place(relx=0.5, rely=0.85, anchor="center")
        
        self.preview_active = True
        self.update_preview()

    def update_preview(self):
        if not self.preview_active:
            return
            
        frame = self.camera.get_frame()
        if frame is not None:
            # Resize for small preview
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img.thumbnail((400, 300)) # Ukuran disesuaikan
            
            img_tk = ImageTk.PhotoImage(image=img)
            self.preview_label.img_tk = img_tk  # Reference
            self.preview_label.configure(image=img_tk)
        
        self.root.after(30, self.update_preview)

    def confirm_and_start(self):
        self.preview_active = False
        self.ready_btn.destroy()
        self.preview_label.destroy()
        self.sub_status.destroy()
        self.status_label.configure(text="Proses Kalibrasi Sedang Berjalan...")
        self.overlay_canvas.create_text(
            self.calib_win.winfo_screenwidth()//2, 
            self.calib_win.winfo_screenheight()//2 + 200,
            text="Mohon tidak menggerakkan kamera atau menutup aplikasi.",
            fill="#00d1ff", font=("Arial", 16, "italic"),
            tag="warning_text"
        )
        self.root.after(1000, self.run_sequence)

    def run_sequence(self):
        # Extended colors for CCM
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),          # Primaries
            (255, 255, 0), (0, 255, 255), (255, 0, 255),    # Secondaries
            (255, 255, 255), (128, 128, 128), (64, 64, 64), # Neutral
            (200, 100, 50), (50, 200, 100),                 # Skintone/Grass
            (25, 25, 25), (230, 230, 230)                   # Black level/Near White
        ]
        
        for rgb in colors:
            hex_color = '#%02x%02x%02x' % rgb
            self.patch.configure(bg=hex_color)
            self.status_label.configure(text=f"Membaca Warna: {rgb}")
            self.calib_win.update()
            
            time.sleep(1.2)
            captured = self.camera.get_average_color()
            if captured:
                self.logic.record_sample(rgb, captured)
            time.sleep(0.3)

        self.finish_calibration()

    def finish_calibration(self):
        if self.camera:
            self.camera.stop()
            
        report = self.logic.analyze()
        self.logic.export_ti3("calibration_data.ti3")
        self.logic.generate_basic_icc("color_correction.txt")
        
        self.calib_win.destroy()
        
        final_msg = f"HASIL ANALISIS:\n\n{report}\n\nData telah diekspor ke:\n- calibration_data.ti3\n- color_correction.txt\n\nAnda dapat menggunakan file ini di software profiling profesional."
        messagebox.showinfo("Kalibrasi Berhasil Diselesaikan", final_msg)
        self.logic.reset()

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = CalibrationApp(root)
    root.mainloop()
