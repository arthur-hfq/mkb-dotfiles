-- ~/.config/conky/draw_nodes.lua
require 'cairo'
require 'math'

function conky_draw_network_graph()
    if conky_window == nil then return end
    local cs = cairo_xlib_surface_create(conky_window.display, conky_window.drawable, conky_window.visual, conky_window.width, conky_window.height)
    local cr = cairo_create(cs)
    
    local xc = conky_window.width / 2
    local yc = conky_window.height / 2
    
    local time = os.clock()
    
    -- Draw edges (chords)
    cairo_set_source_rgba(cr, 160/255, 160/255, 160/255, 1) -- #a0a0a0
    cairo_set_line_width(cr, 1)
    
    local nodes = {
        {x = xc + math.cos(time*0.2)*100, y = yc + math.sin(time*0.2)*100, r=4, c={0, 0x55/255, 1}},
        {x = xc + math.cos(time*0.3 + 2)*80, y = yc + math.sin(time*0.3 + 2)*80, r=4, c={0, 0xaa/255, 0x55/255}},
        {x = xc + math.cos(time*0.1 + 4)*120, y = yc + math.sin(time*0.1 + 4)*120, r=4, c={1, 0x33/255, 0}},
        {x = xc + math.cos(time*0.4 + 1)*50, y = yc + math.sin(time*0.4 + 1)*50, r=4, c={0, 0x55/255, 1}},
        {x = xc + math.cos(time*0.15 + 3)*140, y = yc + math.sin(time*0.15 + 3)*140, r=4, c={0, 0xaa/255, 0x55/255}}
    }
    
    for i=1,#nodes do
        for j=i+1,#nodes do
            cairo_move_to(cr, nodes[i].x, nodes[i].y)
            cairo_line_to(cr, nodes[j].x, nodes[j].y)
            cairo_stroke(cr)
        end
    end
    
    -- Draw nodes and labels
    for i=1,#nodes do
        cairo_set_source_rgba(cr, nodes[i].c[1], nodes[i].c[2], nodes[i].c[3], 1)
        cairo_arc(cr, nodes[i].x, nodes[i].y, nodes[i].r, 0, 2*math.pi)
        cairo_fill(cr)
        
        cairo_set_source_rgba(cr, 17/255, 17/255, 17/255, 1) -- #111111
        cairo_select_font_face(cr, "JetBrains Mono", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)
        cairo_set_font_size(cr, 8)
        cairo_move_to(cr, nodes[i].x + 8, nodes[i].y + 3)
        cairo_show_text(cr, string.format("ND-%02d", i))
    end
    
    cairo_destroy(cr)
    cairo_surface_destroy(cs)
end
