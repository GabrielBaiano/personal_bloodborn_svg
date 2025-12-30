def generate_serrated_path(width, height, tooth_size=10):
    path = []
    # Start top-left
    x, y = 0, 0
    path.append(f"M {x},{y}")
    
    # Top edge
    while x < width:
        x += tooth_size
        if x > width: x = width
        path.append(f"L {x},{y + (tooth_size/2 if (x/tooth_size)%2==1 else 0)}") # Simple zigzag?
        # Better zigzag:
        # We need distinct teeth.
        # Let's do: down-diag, up-diag
        pass

    # Let's try a simpler approach for the string:
    # A generic zigzag function
    
    cmds = [f"M 0,0"]
    
    # Top: 0,0 to W,0
    # Zigzag pattern: l dx, dy l dx, -dy
    # We want the outer boundary to be roughly 0 and W/H?
    # Or should the teeth stick OUT? Let's make them stick OUT from a base box.
    # Base box: 10,10 to 590,790.
    
    # Let's write a standard zigzag generator
    x, y = 0, 0
    # Top edge
    tooth_w = 10
    tooth_h = 6
    
    # We are at 0,0.
    # Go right to 600
    # We will just alternate y between 0 and tooth_h
    
    current_x = 0
    current_y = 0
    cmds = [f"M {current_x},{current_y}"]
    
    # Top Edge
    while current_x < 600:
        current_x += tooth_w
        if current_x > 600: current_x = 600
        # Zig: y goes down
        cmds.append(f"L {current_x},{tooth_h}")
        current_x += tooth_w
        if current_x > 600: break
        # Zag: y goes up
        cmds.append(f"L {current_x},{0}")
        
    # We are at approx 600,0. 
    # Right Edge: down to 800
    current_y = 0
    current_x = 600
    # Ensure start at corner
    cmds.append(f"L {600},{0}")
    
    while current_y < 800:
        current_y += tooth_w
        if current_y > 800: current_y = 800
        cmds.append(f"L {600-tooth_h},{current_y}")
        current_y += tooth_w
        if current_y > 800: break
        cmds.append(f"L {600},{current_y}")

    # Bottom Edge: left to 0
    # current_y is 800, current_x is 600
    cmds.append(f"L {600},{800}")
    
    while current_x > 0:
        current_x -= tooth_w
        if current_x < 0: current_x = 0
        cmds.append(f"L {current_x},{800-tooth_h}")
        current_x -= tooth_w
        if current_x < 0: break
        cmds.append(f"L {current_x},{800}")

    # Left Edge: up to 0
    cmds.append(f"L {0},{800}")
    
    while current_y > 0:
        current_y -= tooth_w
        if current_y < 0: current_y = 0
        cmds.append(f"L {tooth_h},{current_y}")
        current_y -= tooth_w
        if current_y < 0: break
        cmds.append(f"L {0},{current_y}")
        
    cmds.append("Z")
    
    return " ".join(cmds)

print(generate_serrated_path(600, 800))
