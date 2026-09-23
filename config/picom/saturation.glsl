#version 330
in vec2 texcoord;
uniform sampler2D tex;
uniform float opacity;
out vec4 color;

void main() {
    vec4 c = texture(tex, texcoord);
    // Rec. 709 luma values
    float luminance = dot(c.rgb, vec3(0.2126, 0.7152, 0.0722));
    
    // Saturation factor. 1.0 is normal. 
    // Digital Vibrance default is 50%. 80% is roughly a 1.6x boost.
    float saturation = 1.6; 
    
    c.rgb = mix(vec3(luminance), c.rgb, saturation);
    c *= opacity;
    color = c;
}
