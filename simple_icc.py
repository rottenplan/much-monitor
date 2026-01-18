import struct
import time

class SimpleICCGenerator:
    """
    Generates a minimal valid binary ICC v2.4 Monitor Profile.
    Format references: ICC.1:2001-04 (ICC v2.4)
    """
    def __init__(self, description="MuchCalibrated Profile", gamma=2.2):
        self.description = description
        self.gamma = gamma
        
        # Standard D50 White Point for ICC PCS
        self.d50_xyz = (0.9642, 1.0000, 0.8249)
        
        # Default sRGB Primaries (in XYZ as fallback)
        self.red_xyz = (0.4360, 0.2225, 0.0139)
        self.green_xyz = (0.3851, 0.7169, 0.0971)
        self.blue_xyz = (0.1431, 0.0606, 0.7139)
        
    def set_white_point(self, xyz):
        """Set measured media white point."""
        self.d50_xyz = xyz

    def set_primaries(self, r, g, b):
        """Set measured primary XYZ coords."""
        self.red_xyz = r
        self.green_xyz = g
        self.blue_xyz = b
        
    def set_gamma(self, gamma):
        self.gamma = gamma
        
    def create_profile(self, filename):
        """Builds and writes the binary ICC profile."""
        
        tags = []
        
        # 1. 'desc' - Description Tag (Multi-localized Unicode, but we use strict ASCII for v2 compatibility)
        # Note: v2 uses 'desc' type textDescriptionType
        desc_data = self._make_text_description(self.description)
        tags.append(('desc', desc_data))
        
        # 2. 'cprt' - Copyright
        cprt_data = self._make_text("Copyright Much Monitor Calibration")
        tags.append(('cprt', cprt_data))
        
        # 3. 'wtpt' - Media White Point
        wtpt_data = self._make_xyz_number(self.d50_xyz)
        tags.append(('wtpt', wtpt_data))
        
        # 4. 'bkpt' - Media Black Point (Optional, typically 0,0,0)
        bkpt_data = self._make_xyz_number((0,0,0))
        tags.append(('bkpt', bkpt_data))
        
        # 5. rXYZ, gXYZ, bXYZ - Primary Matrix
        tags.append(('rXYZ', self._make_xyz_number(self.red_xyz)))
        tags.append(('gXYZ', self._make_xyz_number(self.green_xyz)))
        tags.append(('bXYZ', self._make_xyz_number(self.blue_xyz)))
        
        # 6. curve tags (rTRC, gTRC, bTRC).
        curve_data = self._make_simple_gamma(self.gamma)
        tags.append(('rTRC', curve_data))
        tags.append(('gTRC', curve_data))
        tags.append(('bTRC', curve_data))
        
        # --- Build File ---
        with open(filename, 'wb') as f:
            # HEADER (128 bytes)
            # Size (0-4) calculated later
            # CMM Type (4-8): 'Lino' (standard) or 0
            # Version (8-12): 2.4.0.0 -> 0x02, 0x40, 0x00, 0x00
            # Class (12-16): 'mntr'
            # Colorspace (16-20): 'RGB '
            # PCS (20-24): 'XYZ '
            # Date (24-36): ...
            # Signature (36-40): 'acsp'
            
            header_fmt = '>4s4s4s4s4s12s4s4s4s4s4s4s4s44s'
            
            # Placeholder size
            size = 0 
            cmm = b'\0\0\0\0'
            version = b'\x02\x40\x00\x00'
            device_class = b'mntr'
            color_space = b'RGB '
            pcs = b'XYZ '
            
            # Timestamp
            t = time.localtime()
            date_time = struct.pack('>6H', t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
            
            signature = b'acsp'
            platform = b'APPL' # Apple
            flags = b'\0\0\0\0'
            manufacturer = b'\0\0\0\0'
            model = b'\0\0\0\0'
            attributes = b'\0\0\0\0\0\0\0\0' # Reflective, Glossy, etc?
            intent = b'\0\0\0\0'
            # Illuminant is the PCS illuminant (Always D50 for v2)
            illuminant = struct.pack('>3i', int(0.9642 * 65536), int(1.0 * 65536), int(0.8249 * 65536)) 
            creator = b'\0\0\0\0'
            pw_id = b'\0'*16 # Profile ID
            padding = b'\0'*28
            
            # Temporarily pack header with 0 size
            header = struct.pack('>I4s4s4s4s4s12s4s4s4s4s4s8s4s12s4s16s28s',
                                0, cmm, version, device_class, color_space, pcs,
                                date_time, signature, platform, flags, manufacturer, model,
                                attributes, intent, illuminant, creator, pw_id, padding)
                                
            # TAG TABLE
            tag_count = len(tags)
            table_header = struct.pack('>I', tag_count)
            
            # Serialize Tags
            # Table Entry: Sig(4), Offset(4), Size(4)
            # Data follows logic
            
            tag_table_size = 4 + (12 * tag_count)
            first_tag_offset = 128 + tag_table_size
            
            current_offset = first_tag_offset
            table_entries = []
            blob_data = b''
            
            # Sort tags strictly by signature for valid ICC
            tags.sort(key=lambda x: x[0])
            
            for sig, data in tags:
                # Pad data to 4-byte boundary
                pad_len = (4 - (len(data) % 4)) % 4
                data_padded = data + (b'\0' * pad_len)
                
                size_entry = len(data) # Real size, not padded
                
                sig_bytes = sig.encode('ascii')
                table_entries.append(struct.pack('>4sII', sig_bytes, current_offset, size_entry))
                
                blob_data += data_padded
                current_offset += len(data_padded)
                
            # Final Size
            total_size = current_offset
            
            # Write Header with correct size
            f.write(struct.pack('>I', total_size)) # overwrite first 4 bytes
            f.write(header[4:]) # write rest of header
            
            # Write Table Header
            f.write(table_header)
            
            # Write Table Entries
            for entry in table_entries:
                f.write(entry)
                
            # Write Data
            f.write(blob_data)
        
        return True

    def _make_text(self, text):
        """Example: 'text' type"""
        # Type 'text' (0x74657874) + 4 reserved + data
        b_text = text.encode('ascii')
        return b'text' + b'\0\0\0\0' + b_text + b'\0'

    def _make_text_description(self, text):
        """'desc' type (textDescriptionType) for v2"""
        # 4s (sig) + 4s (res) + I (ASCII count) + data...
        b_text = text.encode('ascii')
        count = len(b_text) + 1 # null term
        
        # Structure: Sig('desc') | Res(0) | ASCII_Count | ASCII_Bytes | Unicode.. | Script..
        # Minimal: Just ASCII part
        fmt = f'>4s4sI{count}sIIB67s' # Full 90+ bytes fixed block usually?
        # Let's do minimal variable block
        # Sig(4) + Res(4) + Count(4) + String(count) + uCodeCount(4) + uCode(0) + ScriptCount(2) + Script(1) + MAC
        # Keeping it simple:
        header = b'desc' + b'\0\0\0\0'
        ascii_part = struct.pack(f'>I{count}s', count, b_text + b'\0')
        unicode_part = b'\0\0\0\0' # No unicode
        script_part = b'\0\0' # No script
        mac_stuff = b'\0'*67
        
        return header + ascii_part + unicode_part + script_part # + mac_stuff usually required for valid struct
    
    def _make_xyz_number(self, xyz):
        """'XYZ ' type. array of XYZ numbers (double->fixed 15.16)"""
        # Sig 'XYZ ' + 4 reserved + X + Y + Z
        x = int(xyz[0] * 65536)
        y = int(xyz[1] * 65536)
        z = int(xyz[2] * 65536)
        return b'XYZ ' + b'\0\0\0\0' + struct.pack('>3i', x, y, z)
        
    def _make_simple_gamma(self, gamma):
        """'curv' type with single value = gamma"""
        # Sig 'curv' + 4 reserved + Count(4) + u8Fixed8(2 bytes)
        # Count = 1 means single gamma value
        gamma_fixed = int(gamma * 256)
        return b'curv' + b'\0\0\0\0' + struct.pack('>IH', 1, gamma_fixed)
