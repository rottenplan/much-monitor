// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MuchMonitorPro",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "MuchMonitorPro", targets: ["MuchMonitorPro"])
    ],
    targets: [
        .executableTarget(
            name: "MuchMonitorPro",
            path: "Sources"
        )
    ]
)
