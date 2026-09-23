/*
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  vibrance-ctm — Hardware-Level Digital Vibrance via DRM CTM    ║
 * ║  For Intel Iris Xe (i915) on X11                               ║
 * ║                                                                ║
 * ║  Sets the Color Transformation Matrix on the CRTC to boost     ║
 * ║  saturation at the display pipeline level. Zero GPU overhead.  ║
 * ║                                                                ║
 * ║  Compile:                                                      ║
 * ║    gcc -O2 -o vibrance-ctm vibrance-ctm.c $(pkg-config         ║
 * ║        --cflags --libs libdrm) -lm                             ║
 * ║                                                                ║
 * ║  Usage:                                                        ║
 * ║    ./vibrance-ctm [saturation]    (default: 2.0)               ║
 * ║    ./vibrance-ctm 1.0             (reset to normal)            ║
 * ║    ./vibrance-ctm 2.0             (max digital vibrance)       ║
 * ║    ./vibrance-ctm 2.5             (extreme oversaturation)     ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdint.h>
#include <xf86drm.h>
#include <xf86drmMode.h>

/*
 * DRM CTM uses S31.32 sign-magnitude fixed-point:
 *   Bit 63:    sign (0 = positive, 1 = negative)
 *   Bits 62–32: integer part (31 bits)
 *   Bits 31–0:  fractional part (32 bits)
 *
 * This is NOT two's complement — it's sign-magnitude.
 */
static uint64_t double_to_s31_32(double val)
{
    uint64_t sign = 0;

    if (val < 0.0) {
        sign = 1ULL << 63;
        val = -val;
    }

    /* Clamp the integer part to 31 bits (max ~2 billion — more than enough) */
    uint64_t integer = (uint64_t)val;
    if (integer > 0x7FFFFFFFULL)
        integer = 0x7FFFFFFFULL;

    double frac = val - (double)integer;
    uint64_t frac_bits = (uint64_t)round(frac * 4294967296.0); /* 2^32 */

    /* Handle rounding overflow: 0.9999... rounds up to 1.0 */
    if (frac_bits >= (1ULL << 32)) {
        integer++;
        frac_bits = 0;
    }

    return sign | (integer << 32) | frac_bits;
}

/*
 * Build a 3×3 saturation matrix using BT.709 luminance coefficients.
 *
 *   M = (1-s) * [Lr Lg Lb]   + s * I
 *               [Lr Lg Lb]
 *               [Lr Lg Lb]
 *
 * Where:
 *   Lr = 0.2126, Lg = 0.7152, Lb = 0.0722  (BT.709)
 *   s  = saturation factor
 *   I  = identity matrix
 *
 * At s=1.0: identity (no change)
 * At s=2.0: each color's distance from its luminance is doubled
 */
static void build_saturation_ctm(double sat, uint64_t ctm[9])
{
    static const double Lr = 0.2126;
    static const double Lg = 0.7152;
    static const double Lb = 0.0722;

    double matrix[9] = {
        (1.0 - sat) * Lr + sat,  (1.0 - sat) * Lg,        (1.0 - sat) * Lb,
        (1.0 - sat) * Lr,        (1.0 - sat) * Lg + sat,   (1.0 - sat) * Lb,
        (1.0 - sat) * Lr,        (1.0 - sat) * Lg,         (1.0 - sat) * Lb + sat,
    };

    printf("Saturation matrix (factor = %.2f):\n", sat);
    for (int row = 0; row < 3; row++) {
        printf("  [%+8.4f  %+8.4f  %+8.4f]\n",
               matrix[row * 3], matrix[row * 3 + 1], matrix[row * 3 + 2]);
    }
    printf("\n");

    for (int i = 0; i < 9; i++)
        ctm[i] = double_to_s31_32(matrix[i]);
}

/*
 * Try to open the DRM render node / primary node.
 * On Intel Iris Xe systems, this is typically /dev/dri/card0 or card1.
 */
static int open_drm_device(void)
{
    const char *paths[] = {
        "/dev/dri/card0",
        "/dev/dri/card1",
        "/dev/dri/card2",
        NULL
    };

    for (int i = 0; paths[i]; i++) {
        int fd = open(paths[i], O_RDWR | O_CLOEXEC);
        if (fd >= 0) {
            /* Verify this device has modesetting resources */
            drmModeRes *res = drmModeGetResources(fd);
            if (res) {
                drmModeFreeResources(res);
                printf("Opened DRM device: %s\n", paths[i]);
                return fd;
            }
            close(fd);
        }
    }

    fprintf(stderr, "Error: Could not open any DRM device.\n");
    fprintf(stderr, "Ensure you are in the 'video' group or run as root.\n");
    return -1;
}

/*
 * Find and set the CTM property on every active CRTC.
 *
 * The CTM (Color Transformation Matrix) is a DRM blob property on CRTCs.
 * We create a new blob containing our saturation matrix and assign it.
 */
static int set_ctm_on_crtcs(int fd, uint64_t ctm[9])
{
    drmModeRes *res = drmModeGetResources(fd);
    if (!res) {
        fprintf(stderr, "Error: drmModeGetResources failed: %s\n",
                strerror(errno));
        return -1;
    }

    int success_count = 0;

    for (int i = 0; i < res->count_crtcs; i++) {
        drmModeCrtc *crtc = drmModeGetCrtc(fd, res->crtcs[i]);
        if (!crtc)
            continue;

        /* Skip inactive CRTCs (no mode set) */
        if (!crtc->mode_valid) {
            drmModeFreeCrtc(crtc);
            continue;
        }

        /* Enumerate CRTC properties to find "CTM" */
        drmModeObjectProperties *props = drmModeObjectGetProperties(
            fd, crtc->crtc_id, DRM_MODE_OBJECT_CRTC);
        if (!props) {
            drmModeFreeCrtc(crtc);
            continue;
        }

        for (uint32_t j = 0; j < props->count_props; j++) {
            drmModePropertyRes *prop = drmModeGetProperty(fd, props->props[j]);
            if (!prop)
                continue;

            if (strcmp(prop->name, "CTM") == 0) {
                /* Create a blob containing our 9×uint64 CTM data (72 bytes) */
                uint32_t blob_id = 0;
                int ret = drmModeCreatePropertyBlob(fd, ctm,
                                                     9 * sizeof(uint64_t),
                                                     &blob_id);
                if (ret) {
                    fprintf(stderr, "Error: Failed to create CTM blob "
                            "on CRTC %u: %s\n",
                            crtc->crtc_id, strerror(errno));
                    fprintf(stderr, "  → You may need to run as root or "
                            "use the picom shader method instead.\n");
                } else {
                    ret = drmModeObjectSetProperty(
                        fd, crtc->crtc_id, DRM_MODE_OBJECT_CRTC,
                        prop->prop_id, blob_id);

                    if (ret) {
                        fprintf(stderr, "Error: Failed to set CTM on "
                                "CRTC %u: %s\n",
                                crtc->crtc_id, strerror(errno));
                        fprintf(stderr, "  → X11 holds DRM master. Try: "
                                "sudo ./vibrance-ctm\n");
                        drmModeDestroyPropertyBlob(fd, blob_id);
                    } else {
                        printf("✓ CTM applied to CRTC %u (blob_id=%u)\n",
                               crtc->crtc_id, blob_id);
                        success_count++;
                        /*
                         * Do NOT destroy the blob — the CRTC references it.
                         * The kernel holds its own refcount; blob persists
                         * even after we close the fd.
                         */
                    }
                }
            }
            drmModeFreeProperty(prop);
        }
        drmModeFreeObjectProperties(props);
        drmModeFreeCrtc(crtc);
    }

    drmModeFreeResources(res);

    if (success_count == 0) {
        fprintf(stderr, "\nNo CTM was applied. Possible causes:\n");
        fprintf(stderr, "  1. No active display found\n");
        fprintf(stderr, "  2. DRM master held by X server (try sudo)\n");
        fprintf(stderr, "  3. Driver doesn't expose CTM property\n");
        return -1;
    }

    return 0;
}

int main(int argc, char *argv[])
{
    double saturation = 2.0;

    if (argc > 1) {
        if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
            printf("Usage: %s [saturation_factor]\n\n", argv[0]);
            printf("  saturation_factor:\n");
            printf("    1.0  = normal (identity / no change)\n");
            printf("    1.5  = moderate vibrance boost\n");
            printf("    2.0  = max digital vibrance (default)\n");
            printf("    2.5  = extreme oversaturation\n");
            printf("    0.0  = full desaturation (grayscale)\n\n");
            printf("Sets the DRM Color Transformation Matrix on all active\n");
            printf("CRTCs to boost display saturation at the hardware level.\n");
            printf("Zero GPU overhead. Works with Intel i915/Xe drivers.\n");
            return 0;
        }

        saturation = atof(argv[1]);
        if (saturation < 0.0 || saturation > 10.0) {
            fprintf(stderr, "Warning: saturation %.2f is extreme. "
                    "Clamping to [0.0, 10.0].\n", saturation);
            if (saturation < 0.0) saturation = 0.0;
            if (saturation > 10.0) saturation = 10.0;
        }
    }

    /* Build the 3×3 saturation matrix in S31.32 fixed-point */
    uint64_t ctm[9];
    build_saturation_ctm(saturation, ctm);

    /* Open DRM device */
    int fd = open_drm_device();
    if (fd < 0)
        return 1;

    /* Apply CTM to all active CRTCs */
    int ret = set_ctm_on_crtcs(fd, ctm);

    close(fd);

    if (ret == 0)
        printf("\nDigital vibrance set to %.0f%% "
               "(saturation factor: %.2f)\n",
               saturation * 50.0, saturation);

    return ret ? 1 : 0;
}
