
import os

def generate_serrated_path(width, height, tooth_size=6):
    # Generates a path string for a box with serrated edges (zigzag)
    # Start top-left
    cmds = []
    
    # Top edge: 0,0 to W,0. Zigzag down.
    # Start at 0,0
    x, y = 0, 0
    cmds.append(f"M {x},{y}")
    
    # Top edge
    # We want teeth to go IN or OUT? Stamps usually have holes.
    # Let's simple zigzag: 0,0 -> 5,5 -> 10,0 -> 15,5 ...
    tooth_w = tooth_size
    tooth_h = tooth_size / 2
    
    # Top: x goes to width
    while x < width:
        # Down
        next_x = x + tooth_w/2
        if next_x > width: next_x = width
        cmds.append(f"L {next_x},{tooth_h}")
        x = next_x
        
        if x >= width: break
        
        # Up
        next_x = x + tooth_w/2
        if next_x > width: next_x = width
        cmds.append(f"L {next_x},{0}")
        x = next_x

    # Right edge: y goes to height. x is approx width.
    # We are at (width, 0)
    cmds.append(f"L {width},{0}")
    
    while y < height:
        next_y = y + tooth_w/2
        if next_y > height: next_y = height
        cmds.append(f"L {width-tooth_h},{next_y}")
        y = next_y
        
        if y >= height: break
        
        next_y = y + tooth_w/2
        if next_y > height: next_y = height
        cmds.append(f"L {width},{next_y}")
        y = next_y

    # Bottom edge: x goes to 0
    cmds.append(f"L {width},{height}")
    
    while x > 0:
        next_x = x - tooth_w/2
        if next_x < 0: next_x = 0
        cmds.append(f"L {next_x},{height-tooth_h}")
        x = next_x
        
        if x <= 0: break
        
        next_x = x - tooth_w/2
        if next_x < 0: next_x = 0
        cmds.append(f"L {next_x},{height}")
        x = next_x

    # Left edge: y goes to 0
    cmds.append(f"L {0},{height}")
    
    while y > 0:
        next_y = y - tooth_w/2
        if next_y < 0: next_y = 0
        cmds.append(f"L {tooth_h},{next_y}")
        y = next_y
        
        if y <= 0: break
        
        next_y = y - tooth_w/2
        if next_y < 0: next_y = 0
        cmds.append(f"L {0},{next_y}")
        y = next_y
        
    cmds.append("Z")
    return " ".join(cmds)

serrated_path = generate_serrated_path(600, 800, tooth_size=12)

svg_content = f"""<svg width="600" height="800" viewBox="0 0 600 800" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Noise Filter for textured background -->
    <filter id="noise" x="0%" y="0%" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/>
      <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.1 0"/>
      <feComposite operator="in" in2="SourceGraphic" result="monoNoise"/>
      <feBlend in="SourceGraphic" in2="monoNoise" mode="multiply" />
    </filter>
    
    <!-- Gradient for the footer area -->
    <linearGradient id="footerGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1a1a1a" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#0d0d0d" stop-opacity="1"/>
    </linearGradient>

    <!-- Gradient for main border -->
    <linearGradient id="borderGradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#555" />
        <stop offset="50%" stop-color="#888" />
        <stop offset="100%" stop-color="#555" />
    </linearGradient>
    
    <pattern id="diagonalHatch" width="10" height="10" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="10" style="stroke:black; stroke-width:1" />
    </pattern>
  </defs>

  <!-- Serrated Background -->
  <!-- Main dark background with transparency -->
  <path d="{serrated_path}" fill="#0a0a0a" opacity="0.85" />
  
  <!-- Noise texture overlay -->
  <path d="{serrated_path}" fill="#111111" filter="url(#noise)" opacity="0.6"/>
  
  <!-- Serrated Border Stroke -->
  <path d="{serrated_path}" fill="none" stroke="#333" stroke-width="2" />

  <!-- Inner Content Container (Inset to avoid teeth) -->
  <g transform="translate(15, 15)">
      <!-- Main Border Frame -->
      <!-- Outer metallic border -->
      <rect x="0" y="0" width="570" height="770" fill="none" stroke="url(#borderGradient)" stroke-width="3"/>
      
      <!-- Inner thin border -->
      <rect x="6" y="6" width="558" height="758" fill="none" stroke="#333" stroke-width="1"/>
    
      <!-- Top Decoration -->
      <g transform="translate(-10, 0)">
        <path d="M 40,40 Q 60,30 80,40 T 120,40 T 160,40 L 440,40 Q 480,30 500,40 T 540,40" stroke="#888" stroke-width="2" fill="none"/>
        <circle cx="35" cy="40" r="3" fill="#888" />
        <circle cx="545" cy="40" r="3" fill="#888" />
      </g>
    
      <!-- Section Separator 1 (Header) -->
      <g transform="translate(-10, 120)">
          <line x1="20" y1="0" x2="250" y2="0" stroke="#666" stroke-width="1.5" />
          <line x1="350" y1="0" x2="580" y2="0" stroke="#666" stroke-width="1.5" />
          <!-- Central ornament -->
          <path d="M 250,0 Q 275,-10 300,0 Q 325,10 350,0" stroke="#888" stroke-width="2" fill="none"/>
          <circle cx="300" cy="0" r="2" fill="#aaa" />
      </g>
    
      <!-- Section Separators -->
      <g transform="translate(-10, 0)">
          <g transform="translate(0, 200)"><line x1="20" y1="0" x2="580" y2="0" stroke="#333" stroke-width="1" /></g>
          <g transform="translate(0, 280)"><line x1="20" y1="0" x2="580" y2="0" stroke="#333" stroke-width="1" /></g>
          <g transform="translate(0, 360)"><line x1="20" y1="0" x2="580" y2="0" stroke="#333" stroke-width="1" /></g>
          <g transform="translate(0, 440)"><line x1="20" y1="0" x2="580" y2="0" stroke="#333" stroke-width="1" /></g>
          <g transform="translate(0, 520)"><line x1="20" y1="0" x2="580" y2="0" stroke="#333" stroke-width="1" /></g>
      </g>
      
      <!-- Bottom Decoration -->
      <g transform="translate(-10, 680)">
          <line x1="40" y1="0" x2="250" y2="0" stroke="#666" stroke-width="1.5" />
          <line x1="350" y1="0" x2="560" y2="0" stroke="#666" stroke-width="1.5" />
          <path d="M 250,0 Q 275,10 300,0 Q 325,-10 350,0" stroke="#888" stroke-width="2" fill="none"/>
          <circle cx="300" cy="0" r="2" fill="#aaa" />
      </g>
    
      <!-- Footer Area -->
      <rect x="4" y="700" width="562" height="66" fill="url(#footerGradient)" opacity="0.6"/>
      <g transform="translate(-10, 0)">
          <line x1="20" y1="700" x2="580" y2="700" stroke="#666" stroke-width="2" />
          <!-- Footer bottom decorative line -->
          <line x1="40" y1="750" x2="560" y2="750" stroke="#555" stroke-width="1" />
          <circle cx="560" cy="750" r="2" fill="#888" />
          <circle cx="40" cy="750" r="2" fill="#888" />
      </g>
  </g>

</svg>
"""

with open("bloodborne_menu.svg", "w") as f:
    f.write(svg_content)
    
print("Updated bloodborne_menu.svg")
