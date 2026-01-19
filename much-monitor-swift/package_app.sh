#!/bin/bash

APP_NAME="MuchMonitorPro"
APP_DIR="$HOME/Documents/$APP_NAME.app"
EXECUTABLE_PATH=".build/release/$APP_NAME"

echo "Packaging $APP_NAME..."

# 1. Create Directory Structure
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# 2. Copy Executable
if [ -f "$EXECUTABLE_PATH" ]; then
    cp "$EXECUTABLE_PATH" "$APP_DIR/Contents/MacOS/$APP_NAME"
    chmod +x "$APP_DIR/Contents/MacOS/$APP_NAME"
    echo "Executable copied."
else
    echo "Error: Executable not found at $EXECUTABLE_PATH. Did the build succeed?"
    exit 1
fi

# 2b. Copy Resources
if [ -f "Resources/AppIcon.icns" ]; then
    cp "Resources/AppIcon.icns" "$APP_DIR/Contents/Resources/"
    echo "AppIcon copied."
fi
if [ -f "Resources/AppLogo.png" ]; then
    cp "Resources/AppLogo.png" "$APP_DIR/Contents/Resources/"
    echo "AppLogo copied."
fi

# 3. Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.muchdas.$APP_NAME</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSCameraUsageDescription</key>
    <string>Aplikasi ini membutuhkan akses kamera untuk melakukan kalibrasi monitor.</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>Aplikasi ini membutuhkan akses mikrofon (jika diperlukan oleh sistem kamera).</string>
</dict>
</plist>
EOF

echo "Info.plist created."

# 4. Clean up attributes (optional but good practice)
xattr -cr "$APP_DIR"

echo "Success! App saved to: $APP_DIR"
open -R "$APP_DIR"
