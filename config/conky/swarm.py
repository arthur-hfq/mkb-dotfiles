#!/usr/bin/env python3
import cairo
import math
import time
import os
import random

WIDTH, HEIGHT = 1000, 1000
NUM_NODES = 120

# Pre-calculate a perfect sphere of points (Fibonacci sphere)
nodes = []
phi = math.pi * (3. - math.sqrt(5.))  # golden angle
for i in range(NUM_NODES):
    y = 1 - (i / float(NUM_NODES - 1)) * 2 
    radius = math.sqrt(1 - y * y)
    theta = phi * i
    x = math.cos(theta) * radius
    z = math.sin(theta) * radius
    
    # Randomly assign colors from the Markab palette
    color = random.choice([
        (0, 0x55/255.0, 1.0),            # Accent Blue
        (0, 0xaa/255.0, 0x55/255.0),     # Accent Green
        (1.0, 0x33/255.0, 0),            # Accent Red
        (17/255.0, 17/255.0, 17/255.0)   # Dark Charcoal
    ])
    nodes.append({'x': x, 'y': y, 'z': z, 'c': color})

while True:
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    cr = cairo.Context(surface)
    
    t = time.time() * 0.2 # Rotation speed
    
    # Calculate 3D rotation
    projected = []
    for n in nodes:
        # Y-Axis Rotation
        x1 = n['x'] * math.cos(t) - n['z'] * math.sin(t)
        z1 = n['x'] * math.sin(t) + n['z'] * math.cos(t)
        y1 = n['y']
        
        # X-Axis Rotation
        y2 = y1 * math.cos(t*0.6) - z1 * math.sin(t*0.6)
        z2 = y1 * math.sin(t*0.6) + z1 * math.cos(t*0.6)
        x2 = x1
        
        # 2D Projection (Globe scale: 350px radius)
        scale = 350
        px = (WIDTH / 2) + (x2 * scale)
        py = (HEIGHT / 2) + (y2 * scale)
        
        projected.append({'px': px, 'py': py, 'pz': z2, 'c': n['c'], 'orig': n})
        
    # Sort by depth (Z) for correct rendering
    projected.sort(key=lambda item: item['pz'])
    
    # 1. Draw core lines (Dandelion effect)
    cr.set_line_width(0.3)
    cr.set_source_rgba(160/255.0, 160/255.0, 160/255.0, 0.15)
    for p in projected:
        cr.move_to(WIDTH/2, HEIGHT/2)
        cr.line_to(p['px'], p['py'])
        cr.stroke()

    # 2. Draw surface web (Linking nearby nodes)
    cr.set_line_width(0.5)
    for i in range(NUM_NODES):
        for j in range(i+1, NUM_NODES):
            dx = projected[i]['orig']['x'] - projected[j]['orig']['x']
            dy = projected[i]['orig']['y'] - projected[j]['orig']['y']
            dz = projected[i]['orig']['z'] - projected[j]['orig']['z']
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # If nodes are close, draw a link
            if dist < 0.4:
                z_avg = (projected[i]['pz'] + projected[j]['pz']) / 2
                alpha = max(0.05, min(0.6, (z_avg + 1) / 2)) # Hide nodes in the back
                cr.set_source_rgba(160/255.0, 160/255.0, 160/255.0, alpha)
                cr.move_to(projected[i]['px'], projected[i]['py'])
                cr.line_to(projected[j]['px'], projected[j]['py'])
                cr.stroke()

    # 3. Draw nodes (dots)
    for p in projected:
        alpha = max(0.1, min(1.0, (p['pz'] + 1) / 2))
        cr.set_source_rgba(p['c'][0], p['c'][1], p['c'][2], alpha)
        cr.arc(p['px'], p['py'], 3, 0, 2*math.pi)
        cr.fill()
        
    surface.write_to_png("/dev/shm/nodes_tmp.png")
    os.rename("/dev/shm/nodes_tmp.png", "/dev/shm/nodes.png")
    time.sleep(1.1)
