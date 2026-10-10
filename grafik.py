"""Shaders (ljus, dimma, himmel) och texturer som ritas av datorn vid start."""
import random
from PIL import Image, ImageDraw, ImageFilter
from ursina import Shader, Texture, Vec2

# ---- Mars-shadern: solljus, himmelsljus, hjälmlampa och dimma ---------------
_VERT = '''#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;
in vec2 p3d_MultiTexCoord0;
uniform vec2 texture_scale;
uniform vec2 texture_offset;
out vec2 uv;
out vec4 vcol;
out vec3 wnormal;
out vec3 wpos;
out vec3 lpos;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    wpos = (p3d_ModelMatrix * p3d_Vertex).xyz;
    lpos = p3d_Vertex.xyz;
    wnormal = mat3(p3d_ModelMatrix) * p3d_Normal;
    uv = p3d_MultiTexCoord0 * texture_scale + texture_offset;
    vcol = p3d_Color;
}'''

mars_shader = Shader(language=Shader.GLSL, name='mars_shader', vertex=_VERT, fragment='''#version 140
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform vec3 sun_dir;
uniform vec3 sun_color;
uniform vec3 ambient_color;
uniform float hemi_min;
uniform vec3 lamp_pos;
uniform vec3 lamp_dir;
uniform vec3 lamp_color;
uniform vec4 fog_color;
uniform float fog_start;
uniform float fog_end;
uniform vec3 camera_world_position;
in vec2 uv;
in vec4 vcol;
in vec3 wnormal;
in vec3 wpos;
out vec4 fragColor;
void main() {
    vec4 c = texture(p3d_Texture0, uv) * p3d_ColorScale * vcol;
    vec3 n = normalize(wnormal);
    float d = max(dot(n, -sun_dir), 0.0);
    float hemi = mix(hemi_min, 1.0, 0.5 + 0.5 * n.y);
    vec3 ljus = ambient_color * hemi + sun_color * d;
    vec3 L = lamp_pos - wpos;
    float dl = length(L);
    L /= dl;
    float spot = smoothstep(0.70, 0.93, dot(-L, lamp_dir));
    ljus += lamp_color * spot * max(dot(n, L), 0.0) / (1.0 + 0.012 * dl * dl);
    c.rgb *= ljus;
    float t = clamp((length(wpos - camera_world_position) - fog_start) / (fog_end - fog_start), 0.0, 1.0);
    c.rgb = mix(c.rgb, fog_color.rgb, t * fog_color.a);
    fragColor = c;
}''', default_input={'texture_scale': Vec2(1, 1), 'texture_offset': Vec2(0, 0)})

# ---- Självlysande saker (lampor, skärmar, laser) -----------------------------
glow_shader = Shader(language=Shader.GLSL, name='glow_shader', vertex=_VERT, fragment='''#version 140
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
in vec2 uv;
in vec4 vcol;
out vec4 fragColor;
void main() {
    fragColor = texture(p3d_Texture0, uv) * p3d_ColorScale * vcol;
}''', default_input={'texture_scale': Vec2(1, 1), 'texture_offset': Vec2(0, 0)})

# ---- Himlen: färgtoning, sol med sken och stjärnor på natten ----------------
sky_shader = Shader(language=Shader.GLSL, name='sky_shader', vertex=_VERT, fragment='''#version 140
uniform sampler2D p3d_Texture0;
uniform vec3 sun_dir;
uniform vec3 sky_top;
uniform vec3 sky_horizon;
uniform vec3 sun_glow;
uniform float star_amount;
in vec2 uv;
in vec3 lpos;
out vec4 fragColor;
void main() {
    vec3 d = normalize(lpos);
    float h = clamp(d.y, 0.0, 1.0);
    vec3 c = mix(sky_horizon, sky_top, pow(h, 0.55));
    float s = max(dot(d, -sun_dir), 0.0);
    c += sun_glow * (pow(s, 900.0) * 4.0 + pow(s, 40.0) * 0.45 + pow(s, 6.0) * 0.18);
    c += texture(p3d_Texture0, uv * vec2(3.0, 2.0)).rgb * star_amount * smoothstep(0.02, 0.25, d.y);
    fragColor = vec4(c, 1.0);
}''', default_input={'texture_scale': Vec2(1, 1), 'texture_offset': Vec2(0, 0)})


# ---- Texturer -----------------------------------------------------------------
def _tex(bild, filtering='bilinear'):
    return Texture(bild, filtering=filtering)


def mark_textur():
    """Kornig sand – läggs ovanpå markens färg."""
    brus = Image.effect_noise((256, 256), 70).filter(ImageFilter.GaussianBlur(0.7))
    grov = Image.effect_noise((32, 32), 60).resize((256, 256), Image.BICUBIC)
    bild = Image.blend(brus, grov, 0.45).point(lambda v: int(150 + v * 0.41))
    return _tex(Image.merge('RGB', (bild, bild, bild)), 'mipmap')


def panel_textur():
    """Svagt randig metall till väggar."""
    brus = Image.effect_noise((128, 128), 16).point(lambda v: int(205 + v * 0.2))
    return _tex(Image.merge('RGB', (brus, brus, brus)), 'mipmap')


def radar_bakgrund():
    s = 512
    bild = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(bild)
    d.ellipse((4, 4, s - 4, s - 4), fill=(2, 26, 14, 235), outline=(60, 255, 150, 255), width=6)
    for k in (1 / 3, 2 / 3):
        r = (s / 2 - 6) * k
        d.ellipse((s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r), outline=(40, 200, 110, 150), width=2)
    d.line((s / 2, 8, s / 2, s - 8), fill=(40, 200, 110, 120), width=2)
    d.line((8, s / 2, s - 8, s / 2), fill=(40, 200, 110, 120), width=2)
    return _tex(bild)


def radar_svep():
    s = 512
    bild = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(bild)
    for a in range(70):
        d.pieslice((8, 8, s - 8, s - 8), 270 - a - 1.5, 270 - a, fill=(80, 255, 160, int(150 * (1 - a / 70) ** 1.5)))
    return _tex(bild)


def klick_textur():
    """Mjuk rund fläck (radarprickar, damm, sken)."""
    g = Image.radial_gradient('L').point(lambda v: int(max(0, 255 - v * 1.45)))
    vit = Image.new('L', g.size, 255)
    return _tex(Image.merge('RGBA', (vit, vit, vit, g)))


def stjarn_textur():
    rnd = random.Random(3)
    bild = Image.new('RGB', (512, 512), (0, 0, 0))
    d = ImageDraw.Draw(bild)
    for _ in range(420):
        x, y, l = rnd.randrange(512), rnd.randrange(512), rnd.randrange(90, 255)
        d.point((x, y), fill=(l, l, min(255, l + 20)))
        if l > 235:
            d.point((x + 1, y), fill=(l // 2, l // 2, l // 2))
            d.point((x, y + 1), fill=(l // 2, l // 2, l // 2))
    return _tex(bild)
