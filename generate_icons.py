#!/usr/bin/env python3
"""
Generate icon files (.ico, .icns, .png) from SVG
Requires: pip install cairosvg pillow
"""

import os
import sys
from pathlib import Path

try:
    import cairosvg
    from PIL import Image
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cairosvg", "pillow"])
    import cairosvg
    from PIL import Image

def generate_icons():
    svg_path = Path("frontend/public/icon.svg")
    output_dir = Path("frontend/public")
    
    if not svg_path.exists():
        print(f"SVG not found: {svg_path}")
        return
    
    # Sizes needed
    png_sizes = [16, 32, 48, 64, 128, 256, 512, 1024]
    ico_sizes = [16, 32, 48, 64, 128, 256]
    
    print("Generating PNG icons...")
    png_images = []
    for size in png_sizes:
        png_path = output_dir / f"icon-{size}.png"
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=size,
            output_height=size
        )
        png_images.append(Image.open(png_path))
        print(f"  ✓ {size}x{size}")
    
    # Generate .ico (Windows)
    print("Generating .ico...")
    ico_images = [Image.open(output_dir / f"icon-{size}.png") for size in ico_sizes]
    ico_images[0].save(
        output_dir / "icon.ico",
        format="ICO",
        sizes=[(img.width, img.height) for img in ico_images],
        append_images=ico_images[1:]
    )
    print("  ✓ icon.ico")
    
    # Generate .icns (macOS) - requires iconutil on macOS
    if sys.platform == "darwin":
        print("Generating .icns (macOS)...")
        iconset_dir = output_dir / "icon.iconset"
        iconset_dir.mkdir(exist_ok=True)
        
        icns_map = {
            16: "icon_16x16.png",
            32: "icon_16x16@2x.png",
            32: "icon_32x32.png",
            64: "icon_32x32@2x.png",
            128: "icon_128x128.png",
            256: "icon_128x128@2x.png",
            256: "icon_256x256.png",
            512: "icon_256x256@2x.png",
            512: "icon_512x512.png",
            1024: "icon_512x512@2x.png",
        }
        
        for size, name in icns_map.items():
            img = Image.open(output_dir / f"icon-{size}.png")
            img.save(iconset_dir / name)
        
        import subprocess
        subprocess.run(["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_dir / "icon.icns")])
        print("  ✓ icon.icns")
    
    print("\n✅ All icons generated!")
    print(f"Files in {output_dir}:")
    for f in sorted(output_dir.glob("icon*")):
        print(f"  {f.name}")

if __name__ == "__main__":
    generate_icons()