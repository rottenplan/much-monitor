import math
import numpy as np

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

    def analyze(self):
        """Menganalisis hasil dan memberikan saran sederhana."""
        if not self.results:
            return "Tidak ada data sampel."

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
        avg_corrected_delta = (corrected_delta / len(self.results)) if self.ccm is not None else avg_delta
        
        report = f"Average RGB Error (Raw): {avg_delta:.2f}\n"
        if self.ccm is not None:
            report += f"Average RGB Error (Corrected): {avg_corrected_delta:.2f}\n"
            improvement = ((avg_delta - avg_corrected_delta) / avg_delta) * 100 if avg_delta > 0 else 0
            report += f"Estimated accuracy improvement: {improvement:.1f}%\n\n"
        
        if avg_corrected_delta < 5:
            report += "Kualitas warna Monitor sangat baik setelah koreksi."
        elif avg_corrected_delta < 15:
            report += "Kualitas warna Monitor cukup baik dengan profil koreksi."
        else:
            report += "Monitor membutuhkan kalibrasi lebih lanjut atau monitor memiliki gamut rendah."
            
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

    def generate_basic_icc(self, filename="color_correction.txt"):
        """
        Menghasilkan file koreksi yang lebih lengkap termasuk CCM.
        """
        if not self.results:
            return False
            
        # Mencari sample 'White' (255,255,255)
        white_sample = next((r for r in self.results if r['target'] == (255, 255, 255)), None)
        
        with open(filename, "w") as f:
            f.write("# Monitor Correction Data (Advanced)\n\n")
            
            if white_sample:
                target = white_sample['target']
                captured = white_sample['captured']
                r_gain = target[0] / max(captured[0], 1)
                g_gain = target[1] / max(captured[1], 1)
                b_gain = target[2] / max(captured[2], 1)
                f.write(f"WHITEBALANCE_GAIN: {r_gain:.4f}, {g_gain:.4f}, {b_gain:.4f}\n\n")
            
            if self.ccm is not None:
                f.write("COLOR_CORRECTION_MATRIX (3x3):\n")
                for row in self.ccm:
                    f.write(f"{row[0]:.4f} {row[1]:.4f} {row[2]:.4f}\n")
                f.write("\n# Koreksi Target = [R, G, B] * Matrix\n")
                
            f.write("\n# Gunakan data ini untuk software profiling atau kalibrasi software.\n")
        return True

    def reset(self):
        self.results = []
        self.ccm = None
