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

class ModernButton(tk.Label):
    """A custom flat button designed with tk.Label for perfect macOS aesthetics."""
    def __init__(self, parent, text, command, bg="#007AFF", fg="white", font=("Inter", 11, "bold"), pady=12, **kwargs):
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font, pady=pady, cursor="hand2", **kwargs)
        self.command = command
        self.default_bg = bg
        self.hover_bg = self._adjust_brightness(bg, 1.15)
        self.pressed_bg = self._adjust_brightness(bg, 0.8)
        
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.configure(bg=self.hover_bg)

    def _on_leave(self, e):
        self.configure(bg=self.default_bg)

    def _on_press(self, e):
        self.configure(bg=self.pressed_bg)

    def _on_release(self, e):
        self.configure(bg=self.hover_bg)
        self.command()

    def _adjust_brightness(self, hex_color, factor):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(min(255, int(c * factor)) for c in rgb)
        return '#%02x%02x%02x' % new_rgb

class CalibrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MUCH MONITOR PRO")
        self.root.geometry("600x750")
        self.root.minsize(550, 700) # Prevents making the window too small
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
        
        self.mock_var = tk.BooleanVar(value=False)
        
        self.setup_ui()
        self.refresh_cameras()
        
    def setup_ui(self):
        # 1. THEME & GLOBAL STYLE
        style = ttk.Style()
        style.theme_use('clam')
        
        # Deep Black Canvas style for Combobox
        style.configure("TCombobox", fieldbackground="#0F0F0F", background="#1E1E1E", foreground="#FFFFFF", arrowcolor="#FFFFFF", borderwidth=0)
        style.map("TCombobox", 
            fieldbackground=[('readonly', "#0F0F0F"), ('focus', "#1A1A1A")], 
            foreground=[('readonly', 'white')],
            selectbackground=[('!disabled', "#007AFF")],
            selectforeground=[('!disabled', "white")]
        )

        self.main_container = tk.Frame(self.root, bg="#080808", padx=40, pady=25)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 2. BRANDING / HEADER
        header_frame = tk.Frame(self.main_container, bg="#080808")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="MUCH MONITOR", font=("Inter", 32, "bold"), fg="#FFFFFF", bg="#080808")
        title_label.pack(anchor="w")
        
        sub_title = tk.Label(header_frame, text="PRO COLOR ENGINE v2.0", font=("Inter", 12, "bold"), fg="#00D1FF", bg="#080808")
        sub_title.pack(anchor="w", pady=(0, 5))
        
        # Subtle accent line
        tk.Frame(header_frame, height=2, bg="#1A1A1A").pack(fill="x", pady=(10, 0))

        # 3. CAMERA ENGINE CARD (Borderless Elevation)
        cam_card = tk.Frame(self.main_container, bg="#121212", padx=25, pady=25)
        cam_card.pack(fill="x", pady=10)
        
        tk.Label(cam_card, text="KAMERA SENSOR", font=("Inter", 11, "bold"), fg="#555555", bg="#121212").pack(anchor="w", pady=(0, 15))
        
        combo_row = tk.Frame(cam_card, bg="#121212")
        combo_row.pack(fill="x")
        
        self.cam_var = tk.StringVar()
        self.cam_combo = ttk.Combobox(combo_row, textvariable=self.cam_var, state="readonly", font=("Inter", 13))
        self.cam_combo.pack(side=tk.LEFT, fill="x", expand=True)
        
        # Custom Tiny Refresh Button using ModernButton logic internally but smaller
        self.refresh_btn = tk.Label(combo_row, text="↺", font=("Inter", 16), bg="#1E1E1E", fg="white", width=3, cursor="hand2")
        self.refresh_btn.pack(side=tk.RIGHT, padx=(15, 0))
        self.refresh_btn.bind("<Button-1>", lambda e: self.refresh_cameras())

        self.status_cam_label = tk.Label(cam_card, text="Checking camera connectivity...", font=("Inter", 11), fg="#FFCC00", bg="#121212")
        self.status_cam_label.pack(anchor="w", pady=(12, 0))

        # Mock Mode
        self.mock_check = tk.Checkbutton(
            cam_card, text="Gunakan Mock Camera (Testing)", 
            variable=self.mock_var, command=self.update_button_state,
            fg="#666", bg="#121212", activeforeground="#00D1FF", activebackground="#121212",
            selectcolor="#080808", font=("Inter", 9), borderwidth=0, highlightthickness=0
        )
        self.mock_check.pack(anchor="w", pady=(10, 0))

        # 4. TARGET PARAMETERS CARD
        param_card = tk.Frame(self.main_container, bg="#121212", padx=25, pady=25)
        param_card.pack(fill="x", pady=10)
        
        tk.Label(param_card, text="TARGET PARAMETER", font=("Inter", 11, "bold"), fg="#555555", bg="#121212").pack(anchor="w", pady=(0, 15))
        
        grid = tk.Frame(param_card, bg="#121212")
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        
        # White Point
        tk.Label(grid, text="White Point", font=("Inter", 12), fg="#DDD", bg="#121212").grid(row=0, column=0, sticky="w", pady=8)
        self.target_wp = ttk.Combobox(grid, values=["D65 (6500K)", "D50 (5000K)"], state="readonly", font=("Inter", 12))
        self.target_wp.current(0)
        self.target_wp.grid(row=0, column=1, sticky="ew", padx=(30, 0))
        
        # Gamma
        tk.Label(grid, text="Gamma", font=("Inter", 12), fg="#DDD", bg="#121212").grid(row=1, column=0, sticky="w", pady=8)
        self.target_gamma = ttk.Combobox(grid, values=["2.2 (SDR)", "2.4 (Video)"], state="readonly", font=("Inter", 12))
        self.target_gamma.current(0)
        self.target_gamma.grid(row=1, column=1, sticky="ew", padx=(30, 0))

        # 5. ENVIRONMENT TIPS (Low Profile)
        tips_card = tk.Frame(self.main_container, bg="#0E0E0E", padx=20, pady=15)
        tips_card.pack(fill="x", pady=(20, 0))
        
        tk.Label(tips_card, text="PRO TIPS: Redupkan lampu & bersihkan layar monitor.", font=("Inter", 11, "italic"), fg="#666", bg="#0E0E0E").pack()

        # 6. ACTION DASHBOARD
        action_frame = tk.Frame(self.main_container, bg="#080808")
        action_frame.pack(fill="x", side=tk.BOTTOM)

        self.start_button = ModernButton(
            action_frame, 
            text="MULAI KALIBRASI PRO", 
            command=self.start_calibration,
            bg="#007AFF",
            font=("Inter", 14, "bold")
        )
        self.start_button.pack(fill="x", pady=(0, 10))

        self.menubar_btn = ModernButton(
            action_frame,
            text="Launch StudioICC Companion",
            command=self.launch_menubar_helper,
            bg="#181818", fg="#00D1FF", font=("Inter", 11, "bold"), pady=8
        )
        self.menubar_btn.pack(fill="x")


    def launch_menubar_helper(self):
        """Launches the standalone menu bar app and shows a premium workstation-grade alert."""
        import subprocess
        import sys
        try:
            subprocess.Popen([sys.executable, "menubar_app.py"])
            
            # Iteration 3: Glow-Top Premium Alert
            alert = tk.Toplevel(self.root)
            alert.overrideredirect(True)
            alert.attributes("-topmost", True)
            alert.configure(bg="#0F0F0F", highlightthickness=1, highlightbackground="#222")
            
            # Position
            w, h = 380, 240
            sx = (self.root.winfo_screenwidth() - w) // 2
            sy = (self.root.winfo_screenheight() - h) // 2
            alert.geometry(f"{w}x{h}+{sx}+{sy}")
            
            # 1. Glow Top Bar
            glow_bar = tk.Frame(alert, height=4, bg="#00D1FF")
            glow_bar.pack(fill="x")
            
            content = tk.Frame(alert, bg="#0F0F0F", padx=30, pady=25)
            content.pack(fill="both", expand=True)
            
            # 2. Stylized Icon with glow effect (via color)
            tk.Label(content, text="✦", font=("Inter", 36), fg="#00D1FF", bg="#0F0F0F").pack()
            
            # 3. Typography overhauls
            tk.Label(content, text="STUDIO ICC ENGINE AKTIF", font=("Inter", 13, "bold"), fg="white", bg="#0F0F0F", pady=10).pack()
            tk.Label(content, text="Ikon 'MuchCalib' kini muncul di menu bar\ndipojok kanan atas layar Anda.", font=("Inter", 11), fg="#888", bg="#0F0F0F", justify="center").pack()
            
            # 4. Interactive Footer Action
            footer = tk.Frame(content, bg="#0F0F0F")
            footer.pack(fill="x", side="bottom", pady=(20, 0))
            
            ModernButton(footer, text="SIAP", command=alert.destroy, bg="#1A1A1A", fg="#00D1FF", font=("Inter", 12, "bold"), pady=22).pack(fill="x")
            
            alert.grab_set()
            alert.focus_force()
            
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menjalankan Helper: {e}")

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
        
        # 4. SIDEBAR (Unified Control Station)
        self.sidebar = tk.Frame(self.calib_win, bg="black")
        self.sidebar.place(relx=0.98, rely=0.98, anchor="se")

        # Live Preview Label (Now in sidebar)
        preview_w, preview_h = 320, 240
        self.preview_label = tk.Label(self.sidebar, bg="#111111", highlightthickness=1, highlightbackground="#333333", text="Memuat Preview...", fg="white")
        self.preview_label.pack(fill="x", pady=(0, 10))
        
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
        
        # 5. INFO PANEL (Unified Station-Style Box, now in sidebar)
        self.info_panel = tk.Frame(self.sidebar, bg="#111111", padx=20, pady=20, highlightthickness=1, highlightbackground="#333333")
        self.info_panel.pack(fill="x")
        
        self.status_label = tk.Label(
            self.info_panel, 
            text="Langkah 1: Posisikan Kamera", 
            fg="#00D1FF", bg="#111111",
            font=("Inter", 20, "bold"),
            justify=tk.RIGHT
        )
        self.status_label.pack(anchor="e")

        self.sub_status = tk.Label(
            self.info_panel,
            text="Sejajarkan lensa dengan kotak biru.\nTekan & Tahan layar iPhone untuk kunci FOCUS & EXPOSURE.",
            fg="#888888", bg="#111111",
            font=("Inter", 10),
            justify=tk.RIGHT
        )
        self.sub_status.pack(anchor="e", pady=(5, 0))
        
        self.warning_label = tk.Label(
            self.info_panel,
            text="",
            fg="#555555", bg="#111111",
            font=("Inter", 9, "italic"),
            justify=tk.RIGHT
        )
        self.warning_label.pack(anchor="e", pady=(10, 0))

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
                img.thumbnail((320, 240)) # Ukuran disesuaikan sidebar
                
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
        self.status_label.configure(text="Persiapan Kalibrasi...")
        self.warning_label.configure(text="Mohon tidak menggerakkan kamera atau menutup aplikasi.")
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
                # Visual Indicator: Flash green checkmark
                original_text = self.sub_status.cget("text")
                self.sub_status.configure(text=f"✓ Data Terbaca ({i+1}/{total_steps})", fg="#34C759")
                self.info_panel.configure(highlightbackground="#34C759") # Flash border green too
                self.calib_win.update()
                time.sleep(0.2) # Show feedback for 200ms
                self.sub_status.configure(fg="#888888")
                self.info_panel.configure(highlightbackground="#333333") # Reset border
            
            time.sleep(0.05)

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
        res_win.title("MuchPro Analysis")
        res_win.geometry("480x680")
        res_win.configure(bg="#080808")
        
        res_win.lift()
        res_win.focus_force()
        res_win.grab_set()
        
        content = tk.Frame(res_win, bg="#080808", padx=30, pady=30)
        content.pack(fill=tk.BOTH, expand=True)

        # Header
        tk.Label(content, text="ANALISIS SELESAI", font=("Inter", 10, "bold"), fg="#00D1FF", bg="#080808").pack(pady=(0, 5))
        tk.Label(content, text=metrics['grade'], font=("Inter", 18, "bold"), bg="#080808", fg="white").pack(pady=(0, 15))
        
        # Target Info Badge
        target_badge = tk.Frame(content, bg="#1A1A1A", padx=12, pady=6)
        target_badge.pack(pady=(0, 20))
        tk.Label(target_badge, text=f"TARGET: {wp_target}  •  GAMMA {gamma_target}", font=("Inter", 8, "bold"), bg="#1A1A1A", fg="#888").pack()

        # Score Row
        score_row = tk.Frame(content, bg="#080808")
        score_row.pack(fill="x", pady=10)
        
        self._create_score_card(score_row, "RAW DELTA-E", f"{metrics['avg_raw']:.1f}", "#444")
        tk.Label(score_row, text="→", font=("Inter", 20), bg="#080808", fg="#222").pack(side=tk.LEFT, padx=15)
        
        corrected_color = "#34C759" if metrics['avg_corrected'] < 2.0 else "#007AFF"
        self._create_score_card(score_row, "PRO-CAL DELTA-E", f"{metrics['avg_corrected']:.1f}", corrected_color)
        
        # Description
        tk.Label(content, text=metrics['description'], font=("Inter", 11), bg="#080808", fg="#888", wraplength=400, pady=15).pack()

        # --- Save Location Section ---
        save_frame = tk.LabelFrame(content, text="Lokasi Penyimpanan Profil", font=("Arial", 9, "bold"), bg="#080808", fg="#ccc", padx=10, pady=8)
        save_frame.pack(pady=15, padx=0, fill="x") # Adjusted padx to 0 to match content frame

        # Default Path
        default_dir = os.path.join(os.getcwd(), "calibration_output")
        path_var = tk.StringVar(value=default_dir)
        
        entry_frame = tk.Frame(save_frame, bg="#080808")
        entry_frame.pack(fill="x")
        
        entry = tk.Entry(entry_frame, textvariable=path_var, bg="#333", fg="white", font=("Arial", 11), insertbackground="white")
        entry.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))
        
        def browse_folder():
            d = filedialog.askdirectory(initialdir=path_var.get())
            if d:
                path_var.set(d)
                
        tk.Button(entry_frame, text="Browse...", command=browse_folder, bg="#444", fg="black").pack(side=tk.RIGHT)

        # Action Buttons
        btn_frame = tk.Frame(content, bg="#080808")
        btn_frame.pack(fill="x", pady=15)

        
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
            self.logic.reset()
            res_win.destroy()
        
        ModernButton(btn_frame, text="SIMPAN PROFIL (.ICC)", command=lambda: save_action(), bg="#00D1FF", fg="black").pack(fill="x", pady=5)
        ModernButton(btn_frame, text="INSTAL & TERAPKAN (StudioICC Mode)", command=lambda: install_and_apply_action(), bg="#007AFF", fg="white").pack(fill="x", pady=5)
        ModernButton(btn_frame, text="BUANG & ULANGI", command=lambda: discard_action(), bg="#1A1A1A", fg="white").pack(fill="x", pady=5)


    def _create_score_card(self, parent, title, value, color):
        """Creates a modern flat score card."""
        card = tk.Frame(parent, bg="#121212", padx=15, pady=15)
        card.pack(side=tk.LEFT, expand=True, fill="both")
        
        tk.Label(card, text=title, font=("Inter", 7, "bold"), fg="#555", bg="#121212").pack()
        tk.Label(card, text=value, font=("Inter", 24, "bold"), fg=color, bg="#121212").pack(pady=8)

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = CalibrationApp(root)
    root.mainloop()
