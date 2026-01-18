import SwiftUI

struct ModernButtonStyle: ButtonStyle {
    let backgroundColor: Color
    @State private var isHovered = false
    
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .bold, design: .rounded))
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 10)
                    .fill(configuration.isPressed ? backgroundColor.opacity(0.8) : (isHovered ? backgroundColor.opacity(0.9) : backgroundColor))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(Color.white.opacity(0.1), lineWidth: 1)
            )
            .onHover { hovering in isHovered = hovering }
    }
}

struct ModernButton: View {
    let title: String
    let action: () -> Void
    var backgroundColor: Color = Color.blue
    var foregroundColor: Color = .white
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .foregroundColor(foregroundColor)
        }
        .buttonStyle(ModernButtonStyle(backgroundColor: backgroundColor))
    }
}
