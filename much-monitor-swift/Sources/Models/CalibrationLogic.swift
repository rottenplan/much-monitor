import Foundation
import Accelerate

struct ColorSample {
    let target: RGB
    let measured: RGB
}

struct RGB {
    let r: Double
    let g: Double
    let b: Double
    
    // Helper to convert to array
    var array: [Double] { [r, g, b] }
}

class CalibrationLogic {
    private var samples: [ColorSample] = []
    private var ccm: [[Double]]?
    var targetColorSpace: String = "sRGB"
    
    // Dynamic Baseline
    private var blackLevel: RGB = RGB(r: 0, g: 0, b: 0)
    private var whiteLevel: RGB = RGB(r: 255, g: 255, b: 255)
    private var hasBaseline: Bool = false
    
    // Gamma Data
    private var graySamples: [(input: Double, output: Double)] = [] // Input 0-1, Output 0-1 (Luminance)
    
    func setBaseline(black: RGB, white: RGB) {
        self.blackLevel = black
        self.whiteLevel = white
        self.hasBaseline = true
        print("CalibrationLogic: Baseline Set. Black: \(black.r), White: \(white.r)")
    }
    
    func recordSample(target: RGB, measured: RGB, sensorModel: String = "Generic", colorSpace: String = "sRGB") {
        self.targetColorSpace = colorSpace
        // Apply pre-compensation based on sensor model
        let compensated = compensateSample(measured: measured, model: sensorModel)
        samples.append(ColorSample(target: target, measured: compensated))
    }
    
    func recordGraySample(targetLevel: Double, measured: RGB, sensorModel: String) {
        let compensated = compensateSample(measured: measured, model: sensorModel)
        
        // Convert to Luminance (Y)
        let y = 0.2126 * compensated.r + 0.7152 * compensated.g + 0.0722 * compensated.b
        
        // Normalize Y based on Black/White
        let blackY = 0.2126 * blackLevel.r + 0.7152 * blackLevel.g + 0.0722 * blackLevel.b
        let whiteY = 0.2126 * whiteLevel.r + 0.7152 * whiteLevel.g + 0.0722 * whiteLevel.b
        
        let normalizedY = (y - blackY) / (whiteY - blackY)
        graySamples.append((input: targetLevel, output: max(0.001, normalizedY)))
    }
    
    private func compensateSample(measured: RGB, model: String) -> RGB {
        var r = measured.r
        var g = measured.g
        var b = measured.b
        
        // 1. DYNAMIC BASELINE COMPENSATION
        // Formula: Norm = (Measured - Black) / (White - Black) * 255
        // Ideally, we treat 'white' as the mapped 255 point.
        
        if hasBaseline {
            // Function to map a single channel
            func mapChannel(_ val: Double, b: Double, w: Double) -> Double {
                let range = w - b
                if range < 1.0 { return val } // Avoid div by zero
                return ((val - b) / range) * 255.0
            }
            
            r = mapChannel(r, b: blackLevel.r, w: whiteLevel.r)
            g = mapChannel(g, b: blackLevel.g, w: whiteLevel.g)
            b = mapChannel(b, b: blackLevel.b, w: whiteLevel.b)
        }
        
        // 2. Sensor Compensation (Legacy/Tweaks)
        // Kept as secondary polish
        if model.contains("iPhone 11") {
            r *= 0.98
            b *= 1.02
        } else if model.contains("iPhone 12") {
            r *= 1.01
        }
        
        return RGB(r: min(255, max(0, r)), g: min(255, max(0, g)), b: min(255, max(0, b)))
    }
    
    // MARK: - Validation
    
    func validateSample(target: RGB, measured: RGB, sensorModel: String = "Generic") -> (isValid: Bool, message: String?) {
        // 0. Apply Compensation FIRST to normalize expectations
        let corrected = compensateSample(measured: measured, model: sensorModel)
        
        // 1. Luminance Check using Corrected Values
        // If Target is bright (>50), Measured must NOT be black (<10).
        let targetLum = 0.2126 * target.r + 0.7152 * target.g + 0.0722 * target.b
        let measureLum = 0.2126 * corrected.r + 0.7152 * corrected.g + 0.0722 * corrected.b
        
        if targetLum > 50 && measureLum < 5.0 {
            return (false, "Camera is Dark! (Check Lens / Light)")
        }
        
        // 2. Dominant Color Check (Loose)
        // Only run if saturation is decent (not gray/white)
        func getDominant(_ c: RGB) -> String {
            let maxVal = max(c.r, max(c.g, c.b))
            let minVal = min(c.r, min(c.g, c.b))
            
            if (maxVal - minVal) < 20 { return "Gray" }
            
            // Check for Secondary Colors (if two channels are high and close)
            // Magenta: High R, High B, Low G
            if c.r > 100 && c.b > 100 && c.g < (maxVal * 0.7) && abs(c.r - c.b) < 40 { return "Magenta" }
            // Yellow: High R, High G, Low B
            if c.r > 100 && c.g > 100 && c.b < (maxVal * 0.7) && abs(c.r - c.g) < 40 { return "Yellow" }
            // Cyan: High G, High B, Low R
            if c.g > 100 && c.b > 100 && c.r < (maxVal * 0.7) && abs(c.g - c.b) < 40 { return "Cyan" }
            
            if c.r > c.g && c.r > c.b { return "Red" }
            if c.g > c.r && c.g > c.b { return "Green" }
            if c.b > c.r && c.b > c.g { return "Blue" }
            return "Mixed"
        }
        
        let targetDom = getDominant(target)
        let measureDom = getDominant(corrected)
        
        // Relaxed Validation Logic
        if targetDom != "Gray" && targetDom != "Mixed" {
            // General Mismatch Logic
            var acceptable = [targetDom]
            
            // Allow Adjacent Colors
            switch targetDom {
            case "Red": acceptable.append(contentsOf: ["Magenta", "Yellow"])
            case "Green": acceptable.append(contentsOf: ["Yellow", "Cyan"])
            case "Blue": acceptable.append(contentsOf: ["Cyan", "Magenta"])
            case "Magenta": acceptable.append(contentsOf: ["Red", "Blue"])
            case "Yellow": acceptable.append(contentsOf: ["Red", "Green"])
            case "Cyan": acceptable.append(contentsOf: ["Green", "Blue"])
            default: break
            }
            
            if !acceptable.contains(measureDom) && measureDom != "Mixed" {
                 // Hard Fail only if completely opposite (e.g. Red Target but got Cyan/Green/Blue)
                 // Keeping it simple: If Target is Red, and we got Blue/Cyan/Green -> Fail
                 // But wait, Magenta is allowed.
                 // Let's rely on the Acceptable list.
                 // If measured is NOT in acceptable AND NOT "Mixed" -> Fail.
                 // Also ensure it's not Gray (Gray is allowed if saturation is low, but handled above)
                 if measureDom != "Gray" {
                     return (false, "Wrong Color! (Target: \(targetDom), Detect: \(measureDom))")
                 }
            }
        }
        
        return (true, nil)
    }
    
    func reset() {
        samples.removeAll()
        graySamples.removeAll()
        ccm = nil
        hasBaseline = false
    }
    
    // NEW: Validation for Screen Presence
    func validateBaseline() -> (isValid: Bool, message: String?) {
        guard hasBaseline else { return (false, "Baseline not set") }
        
        let b = blackLevel
        let w = whiteLevel
        
        // Luminance Y
        let yBlack = 0.2126 * b.r + 0.7152 * b.g + 0.0722 * b.b
        let yWhite = 0.2126 * w.r + 0.7152 * w.g + 0.0722 * w.b
        
        // Check 1: Contrast Range
        // If camera is on desk/static, delta will be small (noise)
        let delta = yWhite - yBlack
        if delta < 15.0 {
            return (false, "Camera does not see screen changes! Ensure camera is placed on the guide line.")
        }
        
        // Check 2: Signal Strength
        // If white is too dark, camera might be covered or off-angle
        if yWhite < 20.0 {
             return (false, "Camera is too dark! Increase monitor brightness or check camera position.")
        }
        
        return (true, nil)
    }
    
    func calculateGamma() -> Double {
        guard !graySamples.isEmpty else { return 2.2 } // Default
        
        // Simple log-log estimation or average log calculation
        // Gamma = log(Output) / log(Input)
        // We take average of calculated gammas for 25, 50, 75
        
        var totalGamma = 0.0
        var count = 0
        
        for s in graySamples {
            if s.input > 0 && s.output > 0 {
                let g = log(s.output) / log(s.input)
                // Filter wild values
                if g > 0.5 && g < 4.0 {
                    totalGamma += g
                    count += 1
                }
            }
        }
        
        return count > 0 ? totalGamma / Double(count) : 2.2
    }
    
    // MARK: - Core Math
    
    func computeCCM() -> [[Double]]? {
        // We need at least 3 samples to solve for 3x3
        guard samples.count >= 3 else { return nil }
        
        // Prepare matrices for Least Squares: A * X = B
        // Where A = Captured Colors (Rx3), B = Target Colors (Rx3), X = CCM (3x3)
        // Solved as X = (A^T * A)^-1 * A^T * B
        
        let subN = samples.count
        
        // 1. Construct A (Captured) and B (Target)
        var flatA = [Double]()
        var flatB = [Double]()
        
        for s in samples {
            flatA.append(contentsOf: [s.measured.r, s.measured.g, s.measured.b])
            flatB.append(contentsOf: [s.target.r, s.target.g, s.target.b])
        }
        
        // 2. Solve using Accelerate (LAAPACK dgels)
        // generic linear least squares problem: min || A * X - B ||
        
        // var a = flatA // Flattened Column-Major? Accelerate uses Column-Major mostly, but let's check.
        _ = flatA
        // Swift arrays are essentially row-major when interpreted as linear, but LAPACK expects Column-Major.
        // We need to transpose A and B because we perform A * X = B.
        // Actually, let's treat it as: Captured_Row * CCM = Target_Row
        // Transpose: CCM^T * Captured_Col = Target_Col
        // To use dgels, we solve A * X = B
        // Let's stick to simple row-based arrays and manual solver for 3x3 if Accelerate is too complex to bridge without wrappers.
        // Implementation of Pseudo-Inverse for 3x3 is hard. 
        // Let's use a simpler approach: The python logic uses np.linalg.lstsq.
        
        // Alternative: Simple per-channel gain if we assume diagonal matrix (good enough for basic white balance)
        // But we want full 3x3.
        
        // Let's implement a rudimentary linear regression or reuse a Swift Numerics pattern if available.
        // Since I cannot import external libraries, I will implement a basic Matrix math helper.
        
        let matrixA = Matrix(rows: subN, columns: 3, data: flatA) // Row-major
        let matrixB = Matrix(rows: subN, columns: 3, data: flatB)
        
        // X = (A^T * A)^-1 * A^T * B
        guard let at = matrixA.transpose() else { return nil }
        guard let at_a = at.multiply(matrixA) else { return nil }
        guard let inv_at_a = at_a.inverse3x3() else { return nil } // Only works if 3x3
        guard let pseudoInv = inv_at_a.multiply(at) else { return nil }
        guard let resultX = pseudoInv.multiply(matrixB) else { return nil }
        
        self.ccm = resultX.to2DArray()
        return self.ccm
    }
    
    func calculateDeltaE(_ c1: RGB, _ c2: RGB) -> Double {
        // Simple Euclidean Distance in RGB (as proxy for real DeltaE in this version)
        let r = c1.r - c2.r
        let g = c1.g - c2.g
        let b = c1.b - c2.b
        return sqrt(r*r + g*g + b*b)
    }
    
    // MARK: - Analysis
    
    func analyze() -> [String: Any]? {
        guard !samples.isEmpty else { return nil }
        
        // 0. DATA VALIDATION
        // Check if camera was seeing anything at all.
        let maxLuminance = samples.map { $0.measured.r + $0.measured.g + $0.measured.b }.max() ?? 0.0
        if maxLuminance < 5.0 {
            // Signal is essentially Black/Dark. Camera was likely covered or off.
            return [
                "grade": "INVALID",
                "avg_raw": 0.0,
                "avg_corrected": 0.0,
                "improvement": 0.0,
                "description": "ERROR: Camera captured pitch black image. Ensure lens is not covered and permissions are active.",
                "color_space": targetColorSpace,
                "csv_log": getLogCSV()
            ]
        }
        
        // 1. Compute CCM
        _ = computeCCM()
        
        // 2. Calculate Metrics
        var totalRawDE = 0.0
        var totalCorrectedDE = 0.0
        
        for s in samples {
            // Raw Error
            totalRawDE += calculateDeltaE(s.target, s.measured)
            
            // Corrected Error
            var corrected = s.measured
            if let mat = ccm {
                // Apply Matrix: 1x3 * 3x3
                let r = s.measured.r * mat[0][0] + s.measured.g * mat[1][0] + s.measured.b * mat[2][0]
                let g = s.measured.r * mat[0][1] + s.measured.g * mat[1][1] + s.measured.b * mat[2][1]
                let b = s.measured.r * mat[0][2] + s.measured.g * mat[1][2] + s.measured.b * mat[2][2]
                // Clip
                corrected = RGB(r: min(255, max(0, r)), g: min(255, max(0, g)), b: min(255, max(0, b)))
            }
            totalCorrectedDE += calculateDeltaE(s.target, corrected)
        }
        
        let avgRaw = totalRawDE / Double(samples.count)
        let avgCorr = totalCorrectedDE / Double(samples.count)
        let improvement = avgRaw > 0 ? ((avgRaw - avgCorr) / avgRaw) * 100.0 : 0.0
        
        // Grading
        let grade: String
        let desc: String
        
        if avgCorr < 2.0 {
            grade = "GRADE A (Professional)"
            desc = "Excellent accuracy suitable for professional color grading."
        } else if avgCorr < 5.0 {
            grade = "GRADE B (Good)"
            desc = "Good accuracy for general content creation and photography."
        } else if avgCorr < 10.0 {
            grade = "GRADE C (Fair)"
            desc = "Acceptable for daily use. Verify lighting conditions."
        } else {
            grade = "RECALIBRATE"
            desc = "Poor accuracy detected. Please ensure room is dark and camera is locked."
        }
        
        return [
            "avg_raw": avgRaw,
            "avg_corrected": avgCorr,
            "improvement": improvement,
            "grade": grade,
            "description": desc,
            "color_space": targetColorSpace,
            "detected_gamma": calculateGamma(),
            "csv_log": getLogCSV()
        ]
    }
    
    func getLogCSV() -> String {
        var csv = "Step,Target R,Target G,Target B,Measured R,Measured G,Measured B,DeltaE\n"
        
        for (index, sample) in samples.enumerated() {
            let t = sample.target
            let m = sample.measured
            let de = calculateDeltaE(t, m)
            
            let line = String(format: "%d,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.2f\n", 
                              index + 1, t.r, t.g, t.b, m.r, m.g, m.b, de)
            csv.append(line)
        }
        
        return csv
    }
}

// MARK: - Matrix Helper (Minimal Implementation)

struct Matrix {
    let rows: Int
    let columns: Int
    var data: [Double]
    
    init(rows: Int, columns: Int, data: [Double]) {
        self.rows = rows
        self.columns = columns
        self.data = data
    }
    
    func to2DArray() -> [[Double]] {
        var res = [[Double]]()
        for r in 0..<rows {
            let start = r * columns
            res.append(Array(data[start..<(start+columns)]))
        }
        return res
    }
    
    func multiply(_ other: Matrix) -> Matrix? {
        guard self.columns == other.rows else { return nil }
        var result = [Double](repeating: 0.0, count: self.rows * other.columns)
        
        for r in 0..<self.rows {
            for c in 0..<other.columns {
                var sum = 0.0
                for k in 0..<self.columns {
                    sum += self.data[r * self.columns + k] * other.data[k * other.columns + c]
                }
                result[r * other.columns + c] = sum
            }
        }
        
        return Matrix(rows: self.rows, columns: other.columns, data: result)
    }
    
    func transpose() -> Matrix? {
        var result = [Double](repeating: 0.0, count: rows * columns)
        for r in 0..<rows {
            for c in 0..<columns {
                result[c * rows + r] = data[r * columns + c]
            }
        }
        return Matrix(rows: columns, columns: rows, data: result)
    }
    
    func inverse3x3() -> Matrix? {
        guard rows == 3 && columns == 3 else { return nil }
        let m = data
        
        // Computed Determinant
        let det = m[0] * (m[4] * m[8] - m[5] * m[7]) -
                  m[1] * (m[3] * m[8] - m[5] * m[6]) +
                  m[2] * (m[3] * m[7] - m[4] * m[6])
        
        guard abs(det) > 1e-6 else { return nil }
        let invDet = 1.0 / det
        
        var res = [Double](repeating: 0, count: 9)
        res[0] = (m[4] * m[8] - m[5] * m[7]) * invDet
        res[1] = (m[2] * m[7] - m[1] * m[8]) * invDet
        res[2] = (m[1] * m[5] - m[2] * m[4]) * invDet
        res[3] = (m[5] * m[6] - m[3] * m[8]) * invDet
        res[4] = (m[0] * m[8] - m[2] * m[6]) * invDet
        res[5] = (m[2] * m[3] - m[0] * m[5]) * invDet
        res[6] = (m[3] * m[7] - m[4] * m[6]) * invDet
        res[7] = (m[1] * m[6] - m[0] * m[7]) * invDet
        res[8] = (m[0] * m[4] - m[1] * m[3]) * invDet
        
        return Matrix(rows: 3, columns: 3, data: res)
    }
}
