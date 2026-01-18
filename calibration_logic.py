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

    def get_performance_metrics(self):
        """Returns analysis data as a dictionary."""
        if not self.results:
            return None
            
        self.compute_ccm()
        
        total_delta = 0
        corrected_delta = 0
        
        for res in self.results:
            target = np.array(res['target'])
            captured = np.array(res['captured'])
            total_delta += self.calculate_delta_e(target, captured)
            
            if self.ccm is not None:
                corrected = np.dot(captured, self.ccm)
                corrected = np.clip(corrected, 0, 255)
                corrected_delta += self.calculate_delta_e(target, corrected)
        
        avg_delta = total_delta / len(self.results)
        avg_corrected = (corrected_delta / len(self.results)) if self.ccm is not None else avg_delta
        
        improvement = ((avg_delta - avg_corrected) / avg_delta) * 100 if avg_delta > 0 else 0
        
        # Determine grade
        if avg_corrected < 3:
            grade = "Excellent (Pro)"
            desc = "Sangat akurat, cocok untuk color grading."
        elif avg_corrected < 6:
            grade = "Good (Consumer)"
            desc = "Cukup baik untuk penggunaan harian."
        elif avg_corrected < 15:
            grade = "Fair"
            desc = "Warna mungkin sedikit meleset."
        else:
            grade = "Poor"
            desc = "Membutuhkan kalibrasi ulang atau panel terbatas."
            
        return {
            "avg_raw": avg_delta,
            "avg_corrected": avg_corrected,
            "improvement": improvement,
            "grade": grade,
            "description": desc
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

    def generate_basic_icc(self, filename="monitor_profile.icc"):
        """
        Generates a valid binary ICC v2 monitor profile based on measured data.
        """
        if not self.results:
            return False
            
        try:
            # 1. Extraction of Measured Data
            # Note: Since we don't have absolute XYZ, we assume Captured RGB of White maps to D50
            # and other primaries are relative to it.
            white_cap = next((r['captured'] for r in self.results if r['target'] == (255, 255, 255)), (255, 255, 255))
            red_cap   = next((r['captured'] for r in self.results if r['target'] == (255, 0, 0)), (255, 0, 0))
            green_cap = next((r['captured'] for r in self.results if r['target'] == (0, 255, 0)), (0, 255, 0))
            blue_cap  = next((r['captured'] for r in self.results if r['target'] == (0, 0, 255)), (0, 0, 255))
            
            # 2. Estimation of Gamma
            # We look at target (128, 128, 128) and (255, 255, 255)
            gray_cap = next((r['captured'] for r in self.results if r['target'] == (128, 128, 128)), (128, 128, 128))
            
            # Simple Gamma formula: Intensity = Digital ^ Gamma
            try:
                # Use mean of R,G,B to get luminance approximation
                measured_intensity = np.mean(gray_cap) / np.mean(white_cap)
                digital_ratio = 127.5 / 255.0
                estimated_gamma = math.log(measured_intensity) / math.log(digital_ratio)
                
                # SANITY CHECK: 
                # If camera auto-exposure is on, measured_intensity will be ~0.5, 
                # leading to Gamma ~1.0. Real monitors are usually 1.8 - 2.4.
                if estimated_gamma < 1.4 or estimated_gamma > 2.8:
                    print(f"Warning: Measured Gamma {estimated_gamma:.2f} seems unrealistic (possibly Camera Auto-Exposure interference).")
                    print("Defaulting to standard Gamma 2.2 for better profile stability.")
                    estimated_gamma = 2.2
                    
            except Exception as e:
                print(f"Gamma calculation failed: {e}. Defaulting to 2.2")
                estimated_gamma = 2.2
            
            print(f"Data-Driven ICC: Final Gamma used = {estimated_gamma:.2f}")

            generator = SimpleICCGenerator(description="MuchCalibrated Monitor", gamma=estimated_gamma)
            
            # Normalize measurements to approximated XYZ for PCS (White = D50)
            # D50 = (0.9642, 1.0000, 0.8249)
            norm = np.array(white_cap, dtype=float)
            if np.any(norm == 0): norm = np.array([255, 255, 255], dtype=float)
            
            def to_xyz(cap):
                # Naive approximation: Scale relative to measured white, then scale to D50
                rel = np.array(cap, dtype=float) / norm
                return (rel[0] * 0.9642, rel[1] * 1.0, rel[2] * 0.8249)

            generator.set_white_point(to_xyz(white_cap))
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
