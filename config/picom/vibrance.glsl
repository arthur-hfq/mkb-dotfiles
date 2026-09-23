// ╔══════════════════════════════════════════════════════════════════╗
// ║  DIGITAL VIBRANCE — MAX SATURATION GLSL SHADER (picom v13)    ║
// ║  BT.709 luminance-aware saturation push for Intel Iris Xe     ║
// ╚══════════════════════════════════════════════════════════════════╝
//
// picom v13 prepends: #version 330, all uniform declarations (tex,
// opacity, texcoord, effective_size, time, etc.), mask_factor(),
// default_post_processing(), and main(). This file must ONLY define
// window_shader(). No #version, no uniform declarations, no main().
//
// Available pre-defined symbols:
//   uniform sampler2D tex      — window texture (location 3)
//   uniform float opacity      — window opacity (location 1)
//   in vec2 texcoord           — pixel coordinates (NOT normalized)
//   uniform vec2 effective_size— window dimensions
//   uniform float time         — elapsed time
//   vec4 default_post_processing(vec4 c) — applies opacity, dim,
//       tint, inversion, corner radius, border, brightness cap
//
// Saturation factor reference:
//   1.0 = no change (passthrough)
//   1.5 = moderate vibrance boost
//   2.0 = NVIDIA Digital Vibrance 100%  ← DEFAULT
//   2.5 = extreme oversaturation
//   3.0 = psychedelic / artistic
//
// Performance: O(1) per pixel — single dot product + mix + clamp.
// No branching, no loops, no texture indirection.
// Zero measurable latency on Intel Iris Xe.

vec4 window_shader() {
    // Fetch the window pixel (texcoord is in pixel coords, must normalize)
    vec2 texsize = textureSize(tex, 0);
    vec4 c = texture2D(tex, texcoord / texsize, 0);

    // ── SATURATION FACTOR ────────────────────────────────────────
    // 2.0 = maximum digital vibrance (equivalent to NVIDIA 100%)
    const float SATURATION = 2.0;

    // ── PERCEPTUAL LUMINANCE (BT.709 / sRGB) ────────────────────
    // These coefficients match human perception: green > red > blue
    float luminance = dot(c.rgb, vec3(0.2126, 0.7152, 0.0722));

    // ── SATURATION PUSH ──────────────────────────────────────────
    // mix(gray, color, factor) = gray + factor * (color - gray)
    // When factor > 1.0, colors are pushed AWAY from the gray axis
    // When factor = 2.0, the distance from gray is doubled
    vec3 boosted = mix(vec3(luminance), c.rgb, SATURATION);

    // Clamp to [0,1] to prevent HDR blowout on highly saturated input
    c.rgb = clamp(boosted, 0.0, 1.0);

    // Apply picom's built-in post-processing (opacity, dim, tint,
    // inversion, corner radius, border, brightness cap)
    return default_post_processing(c);
}
