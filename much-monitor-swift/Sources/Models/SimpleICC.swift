import Foundation

class SimpleICC {
    var description: String
    var gamma: Double
    
    // Standard D50 White Point for ICC PCS
    private var d50XYZ: (Double, Double, Double) = (0.9642, 1.0000, 0.8249)
    
    // Default sRGB Primaries
    private var redXYZ: (Double, Double, Double) = (0.4360, 0.2225, 0.0139)
    private var greenXYZ: (Double, Double, Double) = (0.3851, 0.7169, 0.0971)
    private var blueXYZ: (Double, Double, Double) = (0.1431, 0.0606, 0.7139)

    init(description: String = "MuchCalibrated Profile", gamma: Double = 2.2) {
        self.description = description
        self.gamma = gamma
    }
    
    func setPrimaries(red: (Double, Double, Double), green: (Double, Double, Double), blue: (Double, Double, Double)) {
        self.redXYZ = red
        self.greenXYZ = green
        self.blueXYZ = blue
    }
    
    func createProfile(url: URL) -> Bool {
        var tags: [(String, Data)] = []
        
        // 1. 'desc' - Description
        tags.append(("desc", makeTextDescription(description)))
        
        // 2. 'cprt' - Copyright
        tags.append(("cprt", makeText("Copyright Much Monitor Calibration")))
        
        // 3. 'wtpt' - Media White Point
        tags.append(("wtpt", makeXYZNumber(d50XYZ)))
        
        // 4. 'bkpt' - Media Black Point
        tags.append(("bkpt", makeXYZNumber((0,0,0))))
        
        // 5. Primaries
        tags.append(("rXYZ", makeXYZNumber(redXYZ)))
        tags.append(("gXYZ", makeXYZNumber(greenXYZ)))
        tags.append(("bXYZ", makeXYZNumber(blueXYZ)))
        
        // 6. Gamma Curves
        let curveData = makeSimpleGamma(gamma)
        tags.append(("rTRC", curveData))
        tags.append(("gTRC", curveData))
        tags.append(("bTRC", curveData))
        
        // Sort tags by signature
        tags.sort { $0.0 < $1.0 }
        
        var bodyData = Data()
        var tagTable = Data()
        
        let tagCount = UInt32(tags.count)
        tagTable.append(contentsOf: withUnsafeBytes(of: tagCount.bigEndian) { Data($0) })
        
        let headerSize: UInt32 = 128
        let tableHeaderSize: UInt32 = 4
        let tableEntrySize: UInt32 = 12
        let firstTagOffset = headerSize + tableHeaderSize + (UInt32(tags.count) * tableEntrySize)
        
        var currentOffset = firstTagOffset
        
        for (sig, data) in tags {
            // Sig (4 bytes)
            tagTable.append(sig.data(using: .ascii)!)
            
            // Offset (4 bytes)
            tagTable.append(contentsOf: withUnsafeBytes(of: currentOffset.bigEndian) { Data($0) })
            
            // Size (4 bytes)
            let size = UInt32(data.count)
            tagTable.append(contentsOf: withUnsafeBytes(of: size.bigEndian) { Data($0) })
            
            bodyData.append(data)
            
            // Padding to 4-byte boundary
            let padding = (4 - (data.count % 4)) % 4
            if padding > 0 {
                bodyData.append(Data(repeating: 0, count: padding))
                currentOffset += UInt32(data.count + padding)
            } else {
                currentOffset += UInt32(data.count)
            }
        }
        
        let totalSize = currentOffset
        var header = Data(repeating: 0, count: Int(headerSize))
        
        // Write size to header
        header.replaceSubrange(0..<4, with: withUnsafeBytes(of: totalSize.bigEndian) { Data($0) })
        
        // Version 2.4.0.0
        header.replaceSubrange(8..<12, with: Data([0x02, 0x40, 0x00, 0x00]))
        
        // Class 'mntr', ColorSpace 'RGB ', PCS 'XYZ '
        header.replaceSubrange(12..<16, with: "mntr".data(using: .ascii)!)
        header.replaceSubrange(16..<20, with: "RGB ".data(using: .ascii)!)
        header.replaceSubrange(20..<24, with: "XYZ ".data(using: .ascii)!)
        
        // Date
        let date = Date()
        let calendar = Calendar.current
        let components = calendar.dateComponents([.year, .month, .day, .hour, .minute, .second], from: date)
        var dateData = Data()
        dateData.append(contentsOf: withUnsafeBytes(of: UInt16(components.year!).bigEndian) { Data($0) })
        dateData.append(contentsOf: withUnsafeBytes(of: UInt16(components.month!).bigEndian) { Data($0) })
        dateData.append(contentsOf: withUnsafeBytes(of: UInt16(components.day!).bigEndian) { Data($0) })
        dateData.append(contentsOf: withUnsafeBytes(of: UInt16(components.hour!).bigEndian) { Data($0) })
        dateData.append(contentsOf: withUnsafeBytes(of: UInt16(components.minute!).bigEndian) { Data($0) })
        dateData.append(contentsOf: withUnsafeBytes(of: UInt16(components.second!).bigEndian) { Data($0) })
        header.replaceSubrange(24..<36, with: dateData)
        
        // Signature 'acsp'
        header.replaceSubrange(36..<40, with: "acsp".data(using: .ascii)!)
        
        // Platform 'APPL'
        header.replaceSubrange(40..<44, with: "APPL".data(using: .ascii)!)
        
        // Illuminant D50 (PCS)
        let illX = UInt32(0.9642 * 65536).bigEndian
        let illY = UInt32(1.0000 * 65536).bigEndian
        let illZ = UInt32(0.8249 * 65536).bigEndian
        header.replaceSubrange(68..<72, with: withUnsafeBytes(of: illX) { Data($0) })
        header.replaceSubrange(72..<76, with: withUnsafeBytes(of: illY) { Data($0) })
        header.replaceSubrange(76..<80, with: withUnsafeBytes(of: illZ) { Data($0) })
        
        var finalData = header
        finalData.append(tagTable)
        finalData.append(bodyData)
        
        do {
            try finalData.write(to: url)
            return true
        } catch {
            print("Failed to write ICC: \(error)")
            return false
        }
    }
    
    private func makeText(_ text: String) -> Data {
        var data = "text".data(using: .ascii)!
        data.append(contentsOf: [0, 0, 0, 0]) // Reserved
        data.append(text.data(using: .ascii)!)
        data.append(0) // Null term
        return data
    }
    
    private func makeTextDescription(_ text: String) -> Data {
        var data = "desc".data(using: .ascii)!
        data.append(contentsOf: [0, 0, 0, 0]) // Reserved
        
        let ascii = text.data(using: .ascii)!
        let count = UInt32(ascii.count + 1).bigEndian
        data.append(contentsOf: withUnsafeBytes(of: count) { Data($0) })
        data.append(ascii)
        data.append(0) // Null term
        
        // Unicode & Script parts (simplified)
        data.append(contentsOf: [0, 0, 0, 0]) // Unicode count
        data.append(contentsOf: [0, 0]) // Script count
        data.append(0) // Script data
        data.append(contentsOf: [0x00, 0x00]) // MAC?
        
        data.append(Data(repeating: 0, count: 67)) // Padding
        
        return data
    }
    
    private func makeXYZNumber(_ xyz: (Double, Double, Double)) -> Data {
        var data = "XYZ ".data(using: .ascii)!
        data.append(contentsOf: [0, 0, 0, 0]) // Reserved
        
        let x = Int32(xyz.0 * 65536).bigEndian
        let y = Int32(xyz.1 * 65536).bigEndian
        let z = Int32(xyz.2 * 65536).bigEndian
        
        data.append(contentsOf: withUnsafeBytes(of: x) { Data($0) })
        data.append(contentsOf: withUnsafeBytes(of: y) { Data($0) })
        data.append(contentsOf: withUnsafeBytes(of: z) { Data($0) })
        
        return data
    }
    
    private func makeSimpleGamma(_ gamma: Double) -> Data {
        var data = "curv".data(using: .ascii)!
        data.append(contentsOf: [0, 0, 0, 0]) // Reserved
        
        let count = UInt32(1).bigEndian
        let gValue = UInt16(gamma * 256).bigEndian
        
        data.append(contentsOf: withUnsafeBytes(of: count) { Data($0) })
        data.append(contentsOf: withUnsafeBytes(of: gValue) { Data($0) })
        
        return data
    }
}
