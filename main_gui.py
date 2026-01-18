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
        self.root.title("MUCH MONITOR PRO")
        self.root.geometry("600x750")
        self.root.configure(bg="#121212") # Deep Black Background
        
        self.logic = CalibrationLogic()
        self.camera = None
        self.preview_active = False
        self.camera_map = {}
        
        # Color Palette
        self.colors = {
            "bg": "#121212",
            "card": "#1E1E1E",
            "accent": "#007AFF",
            "accent_glow": "#00D1FF",
            "text": "#FFFFFF",
            "text_dim": "#AAAAAA",
            "success": "#34C759",
            "warning": "#FFCC00",
            "error": "#FF3B30"
        }
        
        self.setup_ui()
        self.refresh_cameras()
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom TScrollbar/Combobox style for Dark Theme
        style.configure("TCombobox", fieldbackground=self.colors["bg"], background=self.colors["card"], foreground="white", arrowcolor="white")
        style.map("TCombobox", fieldbackground=[('readonly', self.colors["bg"])], foreground=[('readonly', 'white')])

        # Main Scrollable / Padded Container
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg"], padx=30, pady=30)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. HEADER SECTION
        header_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        header_frame.pack(fill="x", pady=(0, 30))
        
        title_label = tk.Label(header_frame, text="MUCH MONITOR", font=("Inter", 24, "bold"), fg=self.colors["text"], bg=self.colors["bg"])
        title_label.pack(anchor="w")
        
        sub_title = tk.Label(header_frame, text="PROFESSIONAL COLOR CALIBRATOR v2.0", font=("Inter", 9, "bold"), fg=self.colors["accent_glow"], bg=self.colors["bg"])
        sub_title.pack(anchor="w", pady=(0, 5))
        
        separator = tk.Frame(header_frame, height=2, bg=self.colors["card"])
        separator.pack(fill="x", pady=5)

        # 2. CAMERA SELECTION CARD
        cam_card = tk.Frame(self.main_frame, bg=self.colors["card"], padx=20, pady=20, highlightthickness=1, highlightbackground="#333")
        cam_card.pack(fill="x", pady=10)
        
        tk.Label(cam_card, text="PILIH KAMERA SENSOR", font=("Inter", 10, "bold"), fg=self.colors["text_dim"], bg=self.colors["card"]).pack(anchor="w", pady=(0, 10))
        
        cam_select_frame = tk.Frame(cam_card, bg=self.colors["card"])
        cam_select_frame.pack(fill="x")
        
        self.cam_var = tk.StringVar() # Added this line as it was missing from the new setup_ui
        self.cam_combo = ttk.Combobox(cam_select_frame, textvariable=self.cam_var, state="readonly", font=("Inter", 11))
        self.cam_combo.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))
        
        self.refresh_btn = tk.Button(cam_select_frame, text="↺", font=("Inter", 14), command=self.refresh_cameras, bg="#333", fg="white", relief=tk.FLAT, borderwidth=0, cursor="hand2")
        self.refresh_btn.pack(side=tk.RIGHT)

        self.status_cam_label = tk.Label(cam_card, text="Mencari kamera...", font=("Inter", 9), fg=self.colors["warning"], bg=self.colors["card"])
        self.status_cam_label.pack(anchor="w", pady=(10, 0))

        # Mock Mode Checkbox (Re-added as it was removed in the new setup_ui)
        self.mock_var = tk.BooleanVar(value=False)
        self.mock_check = tk.Checkbutton(
            cam_card, 
            text="Gunakan Mock Camera (Untuk Testing)", 
            variable=self.mock_var,
            command=self.update_button_state, # Update button when toggled
            fg=self.colors["text_dim"], bg=self.colors["card"], 
            selectcolor="#333",
            activebackground=self.colors["card"],
            activeforeground=self.colors["accent_glow"],
            font=("Inter", 10)
        )
        self.mock_check.pack(anchor="w", pady=(10, 0))

        # 3. PRO TARGET SETTINGS CARD
        target_card = tk.Frame(self.main_frame, bg=self.colors["card"], padx=20, pady=20, highlightthickness=1, highlightbackground="#333")
        target_card.pack(fill="x", pady=10)
        
        tk.Label(target_card, text="TARGET KALIBRASI", font=("Inter", 10, "bold"), fg=self.colors["text_dim"], bg=self.colors["card"]).pack(anchor="w", pady=(0, 15))
        
        grid_frame = tk.Frame(target_card, bg=self.colors["card"])
        grid_frame.pack(fill="x")
        
        # WP
        tk.Label(grid_frame, text="White Point", font=("Inter", 9), fg=self.colors["text"], bg=self.colors["card"]).grid(row=0, column=0, sticky="w", pady=5)
        self.target_wp = ttk.Combobox(grid_frame, values=["D65 (6500K - Standard)", "D50 (5000K - Print)"], state="readonly", font=("Inter", 10))
        self.target_wp.current(0)
        self.target_wp.grid(row=0, column=1, sticky="ew", padx=(20, 0), pady=5)
        
        # Gamma
        tk.Label(grid_frame, text="Target Gamma", font=("Inter", 9), fg=self.colors["text"], bg=self.colors["card"]).grid(row=1, column=0, sticky="w", pady=5)
        self.target_gamma = ttk.Combobox(grid_frame, values=["2.2 (SDR Standard)", "2.4 (Video/Rec.709)"], state="readonly", font=("Inter", 10))
        self.target_gamma.current(0)
        self.target_gamma.grid(row=1, column=1, sticky="ew", padx=(20, 0), pady=5)
        
        grid_frame.columnconfigure(1, weight=1)

        # 4. ACTION SECTION
        action_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        action_frame.pack(fill="x", side=tk.BOTTOM, pady=20)

        self.start_button = tk.Button(
            action_frame,
            text="MULAI KALIBRASI PRO",
            command=self.start_calibration,
            bg=self.colors["accent"], fg="white",
            font=("Inter", 12, "bold"),
            padx=20, pady=15,
            relief=tk.FLAT,
            borderwidth=0,
            cursor="hand2",
            activebackground=self.colors["accent_glow"]
        )
        self.start_button.pack(fill="x")

        self.menubar_btn = tk.Button(
            action_frame,
            text="Launch StudioICC Companion (Menu Bar)",
            command=self.launch_menubar_helper,
            bg=self.colors["bg"], fg=self.colors["accent_glow"],
            font=("Inter", 9, "underline"),
            relief=tk.FLAT, borderwidth=0, cursor="hand2", pady=10,
            activebackground=self.colors["bg"]
        )
        self.menubar_btn.pack()

        # Environment Tips
        tips_frame = tk.LabelFrame(self.main_frame, text="Tips Persiapan", fg="#ccc", bg="#1e1e1e", font=("Arial", 10, "bold"), padx=10, pady=10)
        tips_frame.pack(pady=10, fill="x", padx=0) # Changed padx to 0 to align with other cards
        
        tips = [
            "• Matikan lampu ruangan (Gelapkan ruangan)",
            "• Bersihkan layar monitor dari debu/sidik jari",
            "• Set Brightness monitor ke level standar (50-100 cd/m2)",
            "• Matikan Mode Night Shift / True Tone"
        ]
        for tip in tips:
            tk.Label(tips_frame, text=tip, fg="#00d1ff", bg="#1e1e1e", font=("Arial", 9), justify=tk.LEFT).pack(anchor="w")

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
            padx=15, pady=10,
            borderwidth=2, relief=tk.RIDGE
        )
        self.status_label.place(relx=0.5, rely=0.1, anchor="center")
        self.status_label.lift()

        self.sub_status = tk.Label(
            self.calib_win,
            text="1. Sejajarkan lensa dengan kotak biru.\n2. PENTING: Tekan & Tahan layar iPhone untuk kunci FOCUS & EXPOSURE (AE/AF Lock).",
            fg="#00d1ff", bg="black",
            font=("Arial", 14, "bold"),
            justify=tk.CENTER,
            padx=15, pady=10,
            borderwidth=2, relief=tk.RIDGE
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
        # 0. Collect Targets
        wp_target = self.target_wp.get()
        gamma_target = float(self.target_gamma.get().split()[0])
        print(f"DEBUG: Starting Pro Calibration targeting {wp_target} and Gamma {gamma_target}")
        
        # 1. Professional Large Patch Set (~55 steps)
        # Macbeth-style Standard Colors
        macbeth = [
            (115, 82, 68), (194, 150, 130), (98, 122, 157), (129, 149, 65), (146, 128, 181), (121, 192, 185),
            (214, 126, 44), (80, 91, 166), (193, 130, 140), (94, 60, 108), (157, 188, 64), (224, 163, 46),
            (56, 61, 150), (70, 148, 73), (175, 54, 60), (231, 199, 31), (187, 86, 149), (8, 133, 161)
        ]
        
        # Primary & Secondary Saturation Sweeps (R, G, B, C, M, Y)
        sweeps = []
        bases = [(255,0,0), (0,255,0), (0,0,255), (0,255,255), (255,0,255), (255,255,0)]
        for b in bases:
            for s in [0.25, 0.5, 0.75, 1.0]:
                sweeps.append(tuple(int(c * s) for c in b))
        
        # High-Precision Grayscale Wedge (21 steps for buttery smooth gamma)
        grayscale = []
        for i in range(21):
            val = int(i * 12.75)
            grayscale.append((val, val, val))
            
        colors = macbeth + sweeps + grayscale
        
        total_steps = len(colors)
        for i, rgb in enumerate(colors):
            hex_color = '#%02x%02x%02x' % rgb
            self.overlay_canvas.configure(bg=hex_color)
            self.status_label.configure(text=f"Pro Calibration: Langkah {i+1}/{total_steps}")
            self.sub_status.configure(text=f"Membaca Warna {i+1} dari {total_steps}...")
            self.calib_win.update()
            
            # Allow camera to settle
            wait_time = 1.0 if i == 0 else 0.6
            time.sleep(wait_time)
            
            captured = self.camera.get_average_color()
            if captured:
                self.logic.record_sample(rgb, captured)
            
            time.sleep(0.1)

        # 4. Perform Calculation and Verification
        self.finish_calibration(wp_target, gamma_target)

    def finish_calibration(self, wp_target, gamma_target):
        if self.camera:
            self.camera.stop()
            
        metrics = self.logic.get_performance_metrics(wp_target=wp_target, gamma_target=gamma_target)
        self.calib_win.destroy()
        
        # Show custom result UI
        self.show_results_ui(metrics, wp_target, gamma_target)

    def show_results_ui(self, metrics, wp_target, gamma_target):
        """Displays a modern, dark-themed result summary with Save Options."""
        res_win = tk.Toplevel(self.root)
        res_win.title("Pro Calibration Results")
        res_win.geometry("650x650") # Slightly taller
        res_win.configure(bg="#1e1e1e")
        
        # Ensure window is in front
        res_win.lift()
        res_win.focus_force()
        res_win.grab_set()
        
        # Header
        tk.Label(res_win, text="Kalibrasi Pro Selesai", font=("Arial", 22, "bold"), bg="#1e1e1e", fg="white").pack(pady=(20, 5))
        
        # Target Info
        target_info = f"Target: {wp_target} | Gamma {gamma_target}"
        tk.Label(res_win, text=target_info, font=("Arial", 11), bg="#1e1e1e", fg="#888").pack(pady=(0, 5))
        
        tk.Label(res_win, text=metrics['grade'], font=("Arial", 16, "bold"), bg="#1e1e1e", fg="#00d1ff").pack(pady=(0, 15))
        
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
            wp_val = self.target_wp.get()
            gamma_val = float(self.target_gamma.get().split()[0])
            
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
            self.logic.generate_basic_icc(icc_path, wp_target=wp_val, gamma_target=gamma_val)
            
            self.logic.reset() # Clear data
            
            messagebox.showinfo("Berhasil", f"Profil ICC Pro berhasil disimpan ke:\n{icc_path}")
            res_win.destroy()
            
        def install_and_apply_action():
            from profile_manager import ProfileManager
            wp_val = self.target_wp.get()
            gamma_val = float(self.target_gamma.get().split()[0])

            # 1. Generate profile temporarily
            temp_icc = "temp_monitor_profile.icc"
            self.logic.generate_basic_icc(temp_icc, wp_target=wp_val, gamma_target=gamma_val)
            
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
