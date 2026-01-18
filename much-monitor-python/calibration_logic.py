import math
import numpy as np
from simple_icc import SimpleICCGenerator

class CalibrationLogic:
    def __init__(self):
        self.results = []
        self.ccm = None

    def record_sample(self, target_rgb, captured_rgb):
        """Menyimpan data sampel untuk analisis."""
        self.results.append({
            'target': target_rgb,
            'captured': captured_rgb
        })

    def calculate_delta_e(self, color1, color2):
        """Kalkulasi jarak warna sederhana (Euclidean distance di ruang RGB)."""
        r_diff = color1[0] - color2[0]
        g_diff = color1[1] - color2[1]
        b_diff = color1[2] - color2[2]
        return math.sqrt(r_diff**2 + g_diff**2 + b_diff**2)

    def compute_ccm(self):
        """
        Calculates a 3x3 Color Correction Matrix (CCM) using least squares.
        TargetColors = CapturedColors * CCM
        """
        if len(self.results) < 3:
            return None
        
        # Prepare matrices
        captured_mat = np.array([r['captured'] for r in self.results], dtype=float)
        target_mat = np.array([r['target'] for r in self.results], dtype=float)
        
        # Add column of ones for offset if needed, but for color we usually stick to 3x3
        # Use pseudo-inverse for least squares
        self.ccm, residuals, rank, s = np.linalg.lstsq(captured_mat, target_mat, rcond=None)
        return self.ccm

    def get_performance_metrics(self, wp_target="D65", gamma_target=2.2):
        """Returns analysis data as a dictionary with Pro metrics."""
        if not self.results:
            return None
            
        self.compute_ccm()
        
        # Bradford Transformation Matrices for Chromatic Adaptation
        # Target White Points in XYZ
        WP_XYZ = {
            "D65": np.array([0.95047, 1.00000, 1.08883]),
            "D50": np.array([0.96422, 1.00000, 0.82521])
        }
        
        target_key = "D65" if "D65" in wp_target else "D50"
        target_xyz = WP_XYZ[target_key]
        
        total_delta = 0
        corrected_delta = 0
        
        for res in self.results:
            target = np.array(res['target'])
            captured = np.array(res['captured'])
            
            # Raw Delta-E (Euclidean in RGB as proxy if no full profile yet)
            total_delta += self.calculate_delta_e(target, captured)
            
            if self.ccm is not None:
                # 1. Apply CCM
                corrected = np.dot(captured, self.ccm)
                corrected = np.clip(corrected, 0, 255)
                
                # 2. Simplifikasi Chromatic Adaptation (Gain adjustment)
                # In a real pro app, we'd convert to Lab and use CIEDE2000.
                # Here we use Euclidean distance in RGB after CCM.
                corrected_delta += self.calculate_delta_e(target, corrected)
        
        avg_delta = total_delta / len(self.results)
        avg_corrected = (corrected_delta / len(self.results)) if self.ccm is not None else avg_delta
        
        improvement = ((avg_delta - avg_corrected) / avg_delta) * 100 if avg_delta > 0 else 0
        
        # Grading based on Pro standards (Average Delta-E < 2 is Pro)
        if avg_corrected < 2:
            grade = "Professional (Grade A)"
            desc = "Akurasi warna luar biasa, siap untuk grading profesional."
        elif avg_corrected < 4:
            grade = "Excellent (Grade B)"
            desc = "Sangat baik untuk desain grafis dan edit foto."
        elif avg_corrected < 8:
            grade = "Fair (Grade C)"
            desc = "Cukup untuk penggunaan umum, namun ada sedikit pergeseran warna."
        else:
            grade = "Needs Recalibration"
            desc = "Akurasi rendah. Cek pencahayaan ruangan atau posisi kamera."
            
        return {
            "avg_raw": avg_delta,
            "avg_corrected": avg_corrected,
            "improvement": improvement,
            "grade": grade,
            "description": desc,
            "wp_target": target_key,
            "gamma_target": gamma_target
        }

    def analyze(self):
        """Menganalisis hasil dan memberikan saran sederhana (Legacy)."""
        metrics = self.get_performance_metrics()
        if not metrics:
            return "Tidak ada data sampel."
            
        report = f"Average RGB Error (Raw): {metrics['avg_raw']:.2f}\n"
        report += f"Average RGB Error (Corrected): {metrics['avg_corrected']:.2f}\n"
        report += f"Estimated accuracy improvement: {metrics['improvement']:.1f}%\n\n"
        report += metrics['description']
            
        return report

    def export_ti3(self, filename="calibration_data.ti3"):
        """Eksport data ke format .ti3 (Argyll CMS)."""
        if not self.results:
            return False
            
        with open(filename, "w") as f:
            f.write("CTI3\n\n")
            f.write("DESCRIPTOR \"Argyll Device RGB measurements\"\n")
            f.write("ORIGIN \"Python Monitor Calibrator\"\n")
            f.write("DEVICE_CLASS \"DISPLAY\"\n")
            f.write("COLOR_REP \"RGB\"\n\n")
            
            f.write("NUMBER_OF_FIELDS 6\n")
            f.write("BEGIN_DATA_FORMAT\n")
            f.write("RGB_R RGB_G RGB_B SAMPLE_ID XYZ_X XYZ_Y XYZ_Z\n")
            f.write("END_DATA_FORMAT\n\n")
            
            f.write(f"NUMBER_OF_SETS {len(self.results)}\n")
            f.write("BEGIN_DATA\n")
            for i, res in enumerate(self.results):
                target = res['target']
                # Mocking XYZ from captured RGB for now (simplifikasi)
                # In real world, we'd use a better conversion or measure XYZ directly
                cap = res['captured']
                # Simplifikasi: menggunakan captured RGB sebagai pendekatan XYZ 0-100
                f.write(f"{target[0]/255:.4f} {target[1]/255:.4f} {target[2]/255:.4f} {i+1} {cap[0]} {cap[1]} {cap[2]}\n")
            f.write("END_DATA\n")
        return True

    def generate_basic_icc(self, filename="monitor_profile.icc", wp_target="D65", gamma_target=2.2):
        """
        Generates a valid binary ICC v2 monitor profile based on measured data
        and user Pro targets.
        """
        if not self.results:
            return False
            
        try:
            # 1. Extraction of Measured Data
            # Target White Points in XYZ
            WP_XYZ = {
                "D65": np.array([0.95047, 1.00000, 1.08883]),
                "D50": np.array([0.96422, 1.00000, 0.82521])
            }
            target_key = "D65" if "D65" in wp_target else "D50"
            dest_wp = WP_XYZ[target_key]
            
            white_cap = next((r['captured'] for r in self.results if r['target'] == (255, 255, 255)), (255, 255, 255))
            red_cap   = next((r['captured'] for r in self.results if r['target'] == (255, 0, 0)), (255, 0, 0))
            green_cap = next((r['captured'] for r in self.results if r['target'] == (0, 255, 0)), (0, 255, 0))
            blue_cap  = next((r['captured'] for r in self.results if r['target'] == (0, 0, 255)), (0, 0, 255))
            
            # 2. Estimation of Gamma using multi-step grayscale
            gray_samples = [r for r in self.results if r['target'][0] == r['target'][1] == r['target'][2]]
            gray_samples = sorted(gray_samples, key=lambda x: x['target'][0])
            
            estimated_gamma = 2.2 # Start with robust default
            
            if len(gray_samples) >= 5:
                try:
                    # We want to fit y = x^gamma where y is measured ratio and x is target ratio
                    # log(y) = gamma * log(x)
                    x_data = [] 
                    y_data = []
                    
                    norm_val = np.mean(white_cap) if np.mean(white_cap) > 0 else 255.0
                    
                    for s in gray_samples:
                        x = s['target'][0] / 255.0
                        y = np.mean(s['captured']) / norm_val
                        # Filter for stable range (avoid near-black noise and clipping)
                        if 0.1 < x < 0.95 and y > 0.05:
                            x_data.append(x)
                            y_data.append(y)
                    
                    if len(x_data) >= 3:
                        log_x = np.log(x_data)
                        log_y = np.log(y_data)
                        # Linear regression: slope is gamma
                        slope, intercept = np.polyfit(log_x, log_y, 1)
                        estimated_gamma = slope
                        print(f"DEBUG: Regressed Gamma = {estimated_gamma:.2f}")
                except Exception as e:
                    print(f"Warning: Gamma regression failed: {e}")
            
            # SANITY CHECK: 
            if estimated_gamma < 1.2 or estimated_gamma > 2.8:
                print(f"Warning: Measured Gamma {estimated_gamma:.2f} seems unrealistic. Using 2.2")
                estimated_gamma = 2.2
            
            print(f"Pro ICC: Target Gamma = {gamma_target:.2f} | WP = {target_key}")

            generator = SimpleICCGenerator(description=f"MuchPro {target_key} G{gamma_target}", gamma=gamma_target)
            
            # Normalize measurements to approximated XYZ for PCS (White = PCS D50)
            # and use it as the Media White Point
            norm = np.array(white_cap, dtype=float)
            if np.any(norm == 0): norm = np.array([255, 255, 255], dtype=float)
            
            def to_xyz(cap):
                # Scale relative to measured white, then scale to target white point
                rel = np.array(cap, dtype=float) / norm
                return (rel[0] * dest_wp[0], rel[1] * dest_wp[1], rel[2] * dest_wp[2])

            generator.set_white_point(dest_wp) # Set Target White Point
            generator.set_primaries(to_xyz(red_cap), to_xyz(green_cap), to_xyz(blue_cap))
            
            generator.create_profile(filename)
            return True
        except Exception as e:
            print(f"Failed to generate ICC: {e}")
            import traceback
            traceback.print_exc()
            return False

    def reset(self):
        self.results = []
        self.ccm = None
