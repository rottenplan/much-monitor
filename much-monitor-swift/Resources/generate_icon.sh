
#!/bin/bash
ICONSET_DIR="AppIcon.iconset"
mkdir -p "$ICONSET_DIR"

SOURCE="AppLogo.png"

# Resize to standard sizes
sips -z 16 16     "$SOURCE" --out "$ICONSET_DIR/icon_16x16.png"
sips -z 32 32     "$SOURCE" --out "$ICONSET_DIR/icon_16x16@2x.png"
sips -z 32 32     "$SOURCE" --out "$ICONSET_DIR/icon_32x32.png"
sips -z 64 64     "$SOURCE" --out "$ICONSET_DIR/icon_32x32@2x.png"
sips -z 128 128   "$SOURCE" --out "$ICONSET_DIR/icon_128x128.png"
sips -z 256 256   "$SOURCE" --out "$ICONSET_DIR/icon_128x128@2x.png"
sips -z 256 256   "$SOURCE" --out "$ICONSET_DIR/icon_256x256.png"
sips -z 512 512   "$SOURCE" --out "$ICONSET_DIR/icon_256x256@2x.png"
sips -z 512 512   "$SOURCE" --out "$ICONSET_DIR/icon_512x512.png"
sips -z 1024 1024 "$SOURCE" --out "$ICONSET_DIR/icon_512x512@2x.png"

# Convert to icns
iconutil -c icns "$ICONSET_DIR"

# Cleanup
rm -rf "$ICONSET_DIR"

echo "AppIcon.icns created."
