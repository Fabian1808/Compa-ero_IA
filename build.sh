#!/bin/bash
# Build script for AI Workmate desktop app
# Run this from the root of the repository

set -e

echo "🚀 Building AI Workmate Desktop App"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found"
        exit 1
    fi
    
    if ! command -v cargo &> /dev/null; then
        print_error "Rust/Cargo not found. Install from https://rustup.rs/"
        exit 1
    fi
    
    if ! command -v pyinstaller &> /dev/null; then
        print_error "PyInstaller not found. Run: pip install pyinstaller"
        exit 1
    fi
    
    print_success "All prerequisites found"
}

# Build backend binary
build_backend() {
    print_step "Building backend binary with PyInstaller..."
    
    cd backend
    
    # Clean previous builds
    rm -rf build dist *.spec.bak
    
    # Run PyInstaller
    pyinstaller ai-workmate-backend.spec --clean --noconfirm
    
    if [ ! -f "dist/ai-workmate-backend" ] && [ ! -f "dist/ai-workmate-backend.exe" ]; then
        print_error "Backend binary not found after build"
        exit 1
    fi
    
    print_success "Backend binary built"
    cd ..
}

# Build frontend
build_frontend() {
    print_step "Building frontend..."
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_step "Installing npm dependencies..."
        npm install
    fi
    
    # Build for production
    npm run build
    
    if [ ! -d "dist" ]; then
        print_error "Frontend build failed"
        exit 1
    fi
    
    print_success "Frontend built"
    cd ..
}

# Build Tauri app
build_tauri() {
    print_step "Building Tauri app..."
    
    cd tauri
    
    # Build release
    cargo tauri build
    
    print_success "Tauri app built"
    cd ..
}

# Main
main() {
    echo "========================================"
    echo "  AI Workmate - Desktop App Builder"
    echo "========================================"
    echo ""
    
    check_prerequisites
    
    # Parse arguments
    BUILD_BACKEND=true
    BUILD_FRONTEND=true
    BUILD_TAURI=true
    
    for arg in "$@"; do
        case $arg in
            --backend-only)
                BUILD_FRONTEND=false
                BUILD_TAURI=false
                ;;
            --frontend-only)
                BUILD_BACKEND=false
                BUILD_TAURI=false
                ;;
            --tauri-only)
                BUILD_BACKEND=false
                BUILD_FRONTEND=false
                ;;
        esac
    done
    
    if [ "$BUILD_BACKEND" = true ]; then
        build_backend
    fi
    
    if [ "$BUILD_FRONTEND" = true ]; then
        build_frontend
    fi
    
    if [ "$BUILD_TAURI" = true ]; then
        build_tauri
    fi
    
    echo ""
    echo "========================================"
    echo -e "${GREEN}Build completed successfully!${NC}"
    echo "========================================"
    echo ""
    echo "Output files:"
    
    if [ -f "tauri/target/release/bundle/msi/AI Workmate_0.1.0_x64.msi" ]; then
        echo "  Windows MSI: tauri/target/release/bundle/msi/AI Workmate_0.1.0_x64.msi"
    fi
    
    if [ -f "tauri/target/release/bundle/nsis/AI Workmate_0.1.0_x64-setup.exe" ]; then
        echo "  Windows NSIS: tauri/target/release/bundle/nsis/AI Workmate_0.1.0_x64-setup.exe"
    fi
    
    if [ -f "tauri/target/release/bundle/dmg/AI Workmate_0.1.0_aarch64.dmg" ] || [ -f "tauri/target/release/bundle/dmg/AI Workmate_0.1.0_x64.dmg" ]; then
        echo "  macOS DMG: tauri/target/release/bundle/dmg/"
    fi
    
    if [ -f "tauri/target/release/bundle/appimage/AI Workmate_0.1.0_amd64.AppImage" ]; then
        echo "  Linux AppImage: tauri/target/release/bundle/appimage/"
    fi
    
    echo ""
    echo "To distribute: share the .msi (Windows), .dmg (macOS), or .AppImage (Linux)"
}

main "$@"