import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from camera_handler import CameraHandler
from calibration_logic import CalibrationLogic
import time
import cv2
import os
import threading
from datetime import datetime

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

        self.status_cam_label = tk.Label(
            self.main_frame, 
            text="Mendeteksi kamera...", 
            fg="#00d1ff", bg="#1e1e1e", 
            font=("Arial", 10, "italic")
        )
        self.status_cam_label.pack(pady=5)

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
        self.start_button.pack(pady=(30, 10))

        # Launch Menu Bar Helper Button (StudioICC companion)
        self.menubar_btn = tk.Button(
            self.main_frame,
            text="Buka Menu Bar Helper (StudioICC Mode)",
            command=self.launch_menubar_helper,
            bg="#1e1e1e", fg="#00d1ff",
            font=("Arial", 11, "bold", "underline"),
            relief=tk.FLAT,
            activebackground="#1e1e1e",
            activeforeground="#fff",
            cursor="hand2"
        )
        self.menubar_btn.pack(pady=5)

    def launch_menubar_helper(self):
        """Launches the standalone menu bar app as a background process."""
        import subprocess
        import sys
        try:
            # Launch as a separate background process
            subprocess.Popen([sys.executable, "menubar_app.py"])
            messagebox.showinfo("StudioICC Mode", "Menu Bar Helper sedang berjalan!\nCari ikon 'MuchCalib' di pojok kanan atas layar.")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menjalankan Menu Bar Helper: {e}")

    def refresh_cameras(self):
        print("DEBUG: Refreshing cameras...")
        cameras_with_names = CameraHandler.get_available_cameras_with_names()
        print(f"DEBUG: Found cameras: {cameras_with_names}")
        self.camera_map = {}
        
        display_names = []
        iphone_indices = []
        
        for idx, name in cameras_with_names:
            display_name = f"{name} (Index: {idx})"
            self.camera_map[display_name] = idx
            display_names.append(display_name)
            if "iphone" in name.lower():
                iphone_indices.append(len(display_names) - 1)
        
        print(f"DEBUG: Display names: {display_names}")
            
        if not display_names:
            self.cam_combo['values'] = ("Tidak ada kamera terdeteksi",)
            self.cam_combo.current(0)
        else:
            self.cam_combo['values'] = display_names
            # Default to first iPhone found, or just the first camera
            if iphone_indices:
                print(f"DEBUG: Defaulting to iPhone at index {iphone_indices[0]}")
                self.cam_combo.current(iphone_indices[0])
                self.status_cam_label.config(text=f"iPhone Terdeteksi! ({len(display_names)} kamera total)", fg="#00FF00")
            else:
                self.cam_combo.current(0)
                self.status_cam_label.config(text=f"{len(display_names)} kamera ditemukan (Tidak ada iPhone)", fg="#FFA500")
        
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
        print(f"DEBUG: Selected camera '{selection}' -> Index {cam_index}")
            
        # Create handler instance
        self.camera = CameraHandler(camera_index=cam_index, mock_mode=is_mock)
        
        # Disable button and show loading status
        self.start_button.config(state=tk.DISABLED, text="Menghubungkan...")
        self.root.update()
        
        # Start connection in background thread
        threading.Thread(target=self.connect_camera_task, daemon=True).start()

    def connect_camera_task(self):
        """Background task to open camera."""
        success = self.camera.start()
        # Schedule result handling on main thread
        self.root.after(0, lambda: self.on_camera_connection_result(success))

    def on_camera_connection_result(self, success):
        """Handle connection result on main thread."""
        self.start_button.config(state=tk.NORMAL, text="Mulai Kalibrasi")
        
        if not success:
            messagebox.showerror(
                "Error", 
                "Gagal membuka kamera.\n\nPastikan kamera terhubung, tidak sedang digunakan aplikasi lain, dan izin diberikan."
            )
            return
        
        self.show_calibration_screen()

    def show_calibration_screen(self):
        self.calib_win = tk.Toplevel(self.root)
        self.calib_win.attributes("-fullscreen", True)
        self.calib_win.configure(bg="black")
        
        screen_w = self.calib_win.winfo_screenwidth()
        screen_h = self.calib_win.winfo_screenheight()
        
        # UI Container (Full Screen Canvas)
        self.overlay_canvas = tk.Canvas(self.calib_win, bg="white", highlightthickness=0)
        self.overlay_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Live Preview Label
        preview_w, preview_h = 400, 300
        self.preview_label = tk.Label(self.calib_win, bg="#1a1a1a", borderwidth=4, relief=tk.SOLID, text="Memuat Preview...", fg="white")
        self.preview_label.place(relx=0.5, rely=0.6, anchor="center") 
        self.preview_label.lift()
        
        # Center Target (Alignment Guide)
        guide_size = 300
        x1, y1 = (screen_w - guide_size)//2, (screen_h - guide_size)//4
        x2, y2 = x1 + guide_size, y1 + guide_size
        
        self.target_rect = self.overlay_canvas.create_rectangle(
            x1-5, y1-5, x2+5, y2+5, 
            outline="#007aff", width=5 # Thicker for visibility
        )
        
        # Self.patch is no longer a separate frame; we use overlay_canvas background
        self.patch = self.overlay_canvas 
        
        self.status_label = tk.Label(
            self.calib_win, 
            text="Langkah 1: Posisikan Kamera", 
            fg="#00d1ff", bg="black", # Contrast bg for label
            font=("Arial", 28, "bold"),
            padx=10, pady=5
        )
        self.status_label.place(relx=0.5, rely=0.1, anchor="center")
        self.status_label.lift()

        self.sub_status = tk.Label(
            self.calib_win,
            text="Pastikan lensa kamera sejajar dengan kotak biru di atas.\nLihat preview di bawah untuk memastikan posisi sudah pas.",
            fg="#00d1ff", bg="black",
            font=("Arial", 14),
            justify=tk.CENTER,
            padx=10, pady=5
        )
        self.sub_status.place(relx=0.5, rely=0.18, anchor="center")
        self.sub_status.lift()

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
        if not self.preview_active or not self.preview_label.winfo_exists():
            return
            
        frame = self.camera.get_frame()
        if frame is not None:
            # Resize for small preview
            try:
                # DEBUG: Log every 30 frames to avoid spamming but confirm it's alive
                if not hasattr(self, '_preview_count'): self._preview_count = 0
                self._preview_count += 1
                if self._preview_count % 30 == 0:
                    print(f"DEBUG: Frame received ({frame.shape[1]}x{frame.shape[0]})")

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((400, 300)) # Ukuran disesuaikan
                
                img_tk = ImageTk.PhotoImage(image=img)
                self.preview_label.img_tk = img_tk  # Reference
                self.preview_label.configure(image=img_tk, text="") # Clear text if image is shown
            except Exception as e:
                if self._preview_count % 30 == 0:
                    print(f"DEBUG: Error processing frame: {e}")
        else:
            # Show reconnecting message if frame is None
            try:
                if self._preview_count % 30 == 0:
                    print("DEBUG: get_frame returned None")
                self.preview_label.configure(image="", text="Signal Lost\nReconnecting...", fg="#00d1ff", bg="#333", font=("Arial", 14, "bold"))
            except:
                pass
        
        # Increase frequency for smoother preview
        self.root.after(15, self.update_preview)

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
            self.overlay_canvas.configure(bg=hex_color) # PATCH IS NOW CANVAS
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
            
        metrics = self.logic.get_performance_metrics()
        self.calib_win.destroy()
        
        # Show custom result UI (Deffer saving to UI)
        self.show_results_ui(metrics)

    def show_results_ui(self, metrics):
        """Displays a modern, dark-themed result summary with Save Options."""
        res_win = tk.Toplevel(self.root)
        res_win.title("Calibration Results")
        res_win.geometry("650x550")
        res_win.configure(bg="#1e1e1e")
        
        # Ensure window is in front and takes focus
        res_win.lift()
        res_win.focus_force()
        res_win.grab_set()
        
        # Header
        tk.Label(res_win, text="Kalibrasi Selesai", font=("Arial", 24, "bold"), bg="#1e1e1e", fg="white").pack(pady=(30, 5))
        tk.Label(res_win, text=metrics['grade'], font=("Arial", 16), bg="#1e1e1e", fg="#00d1ff").pack(pady=(0, 20))
        
        # Score Cards Frame
        score_frame = tk.Frame(res_win, bg="#1e1e1e")
        score_frame.pack(pady=10)
        
        # Before Card
        self._create_score_card(score_frame, "Sebelum (Raw Delta E)", f"{metrics['avg_raw']:.1f}", "#ff4444")
        
        # Arrow
        tk.Label(score_frame, text="→", font=("Arial", 30), bg="#1e1e1e", fg="#666").pack(side=tk.LEFT, padx=20)
        
        # After Card
        color = "#00FF00" if metrics['avg_corrected'] < 5 else "#FFA500"
        self._create_score_card(score_frame, "Sesudah (Terkoreksi)", f"{metrics['avg_corrected']:.1f}", color)
        
        # Details
        tk.Label(res_win, text=f"Peningkatan: +{metrics['improvement']:.1f}%", font=("Arial", 14), bg="#1e1e1e", fg="#aaaaaa").pack(pady=10)
        
        # --- Save Location Section ---
        save_frame = tk.LabelFrame(res_win, text="Lokasi Penyimpanan Profil", font=("Arial", 10, "bold"), bg="#1e1e1e", fg="#ccc", padx=10, pady=10)
        save_frame.pack(pady=20, padx=20, fill="x")
        
        # Default Path
        default_dir = os.path.join(os.getcwd(), "calibration_output")
        path_var = tk.StringVar(value=default_dir)
        
        entry_frame = tk.Frame(save_frame, bg="#1e1e1e")
        entry_frame.pack(fill="x")
        
        entry = tk.Entry(entry_frame, textvariable=path_var, bg="#333", fg="white", font=("Arial", 11), insertbackground="white")
        entry.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))
        
        def browse_folder():
            d = filedialog.askdirectory(initialdir=path_var.get())
            if d:
                path_var.set(d)
                
        tk.Button(entry_frame, text="Browse...", command=browse_folder, bg="#444", fg="black").pack(side=tk.RIGHT)

        # Action Buttons
        btn_frame = tk.Frame(res_win, bg="#1e1e1e")
        btn_frame.pack(pady=20)
        
        def save_action():
            target_dir = path_var.get()
            if not os.path.exists(target_dir):
                try:
                    os.makedirs(target_dir)
                except:
                    messagebox.showerror("Error", "Tidak bisa membuat direktori!")
                    return
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            icc_name = f"profile_{timestamp}.icc"
            
            # Save ICC profile
            icc_path = os.path.join(target_dir, icc_name)
            self.logic.generate_basic_icc(icc_path)
            
            self.logic.reset() # Clear data
            
            messagebox.showinfo("Berhasil", f"Profil ICC berhasil disimpan ke:\n{icc_path}")
            res_win.destroy()
            
        def install_and_apply_action():
            from profile_manager import ProfileManager
            # 1. Generate profile temporarily
            temp_icc = "temp_monitor_profile.icc"
            self.logic.generate_basic_icc(temp_icc)
            
            # 2. Install to system
            installed_path = ProfileManager.install_profile(temp_icc, "MuchCalibrated_Monitor.icc")
            if installed_path:
                # 3. Apply to display
                main_display = ProfileManager.get_main_display_id()
                if ProfileManager.set_display_profile(main_display, installed_path):
                    messagebox.showinfo("Berhasil", "Profil telah DIINSTAL dan DITERAPKAN ke layar Anda!")
                else:
                    messagebox.showwarning("Peringatan", "Profil diinstal tapi gagal diterapkan secara otomatis.\nSilakan pilih manual di System Settings > Displays.")
            
            # Cleanup temp and finish
            if os.path.exists(temp_icc): os.remove(temp_icc)
            self.logic.reset()
            res_win.destroy()

        def discard_action():
            if messagebox.askyesno("Discard?", "Apakah Anda yakin ingin membuang kalibrasi ini?"):
                self.logic.reset()
                res_win.destroy()
        
        tk.Button(btn_frame, text="Simpan Ke Folder...", command=save_action, 
                  bg="#444", fg="black", font=("Arial", 12), relief="flat", padx=15, pady=8).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="INSTAL & TERAPKAN (StudioICC Mode)", command=install_and_apply_action, 
                  bg="#00d1ff", fg="black", font=("Arial", 12, "bold"), relief="flat", padx=20, pady=8).pack(side=tk.LEFT, padx=5)
                  
        tk.Button(btn_frame, text="Buang", command=discard_action, 
                  bg="#1e1e1e", fg="#ff4444", font=("Arial", 12), relief="flat", padx=10, pady=8).pack(side=tk.LEFT, padx=5)

    def _create_score_card(self, parent, title, value, color):
        card = tk.Frame(parent, bg="#2a2a2a", padx=20, pady=15)
        card.pack(side=tk.LEFT)
        
        tk.Label(card, text=title, font=("Arial", 10), bg="#2a2a2a", fg="#bbb").pack()
        tk.Label(card, text=value, font=("Arial", 36, "bold"), bg="#2a2a2a", fg=color).pack()

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = CalibrationApp(root)
    root.mainloop()
