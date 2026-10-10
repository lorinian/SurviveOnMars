"""MARS – Simon och Ralfs spel.

Mark Watney är strandsatt på Mars. Laga raketen, odla potatis, rädda
Daidalos robotar och överlev stormar och martianer.
"""
import os
import sys
import math

if 'GALLIUM_DRIVER' not in os.environ and os.path.exists('/dev/dxg'):
    os.environ['GALLIUM_DRIVER'] = 'd3d12'        # WSL: använd grafikkortet i stället för processorn

from ursina import *                              # noqa: E402,F401
from panda3d.core import TransparencyAttrib, ClockObject       # noqa: E402
import grafik                                     # noqa: E402
import modeller                                   # noqa: E402
from mesh_bygge import Bygge                      # noqa: E402

TEST = bool(os.environ.get('MARS_TEST'))

app = Ursina(title='MARS – Simon och Ralfs spel', development_mode=False, borderless=False,
             size=tuple(int(v) for v in os.environ.get('MARS_STORLEK', '1152x648').split('x')),
             vsync=False)
globalClock.setMode(ClockObject.MLimited)         # högst 60 bilder per sekund
globalClock.setFrameRate(int(os.environ.get('MARS_FPS', 60)))
for _namn, _pa in (('exit_button', False), ('fps_counter', True), ('cog_button', False)):
    if getattr(window, _namn, None):
        getattr(window, _namn).enabled = _pa
window.color = color.black
camera.fov = 78
camera.clip_plane_near = .12
camera.clip_plane_far = 2500

# ---- Världen ------------------------------------------------------------------
SOL = 360.0                    # en dag på Mars (en "sol") i sekunder
KANT = 430                     # så långt från basen kan man gå
HAB = (0.0, 0.0)
RAKET = (28.0, -24.0)
SKEPP = (-250.0, 210.0)
HAB_INNE = Vec3(5000, 0, 0)    # rummen ligger långt bort så att de inte syns utifrån
RAKET_INNE = Vec3(6000, 0, 0)
PLATT = [(HAB[0], HAB[1], 46, 100), (SKEPP[0], SKEPP[1], 24, 70)]

ROBOT_PLATS = {'Minus': (52, 66), 'Bulten': (SKEPP[0] + 15, SKEPP[1] - 9), 'Taurus': (SKEPP[0] + 5, SKEPP[1] + 19),
               'Kamina': (SKEPP[0] - 12, SKEPP[1] - 17), 'Lupus': (-140, 55), 'Gorgo': (-330, 95)}
ROBOT_KAN = {'Minus': 'visar raketdelar och lådor på radarn',
             'Bulten': 'lagar basen och din rymddräkt lite i taget',
             'Taurus': 'slåss mot martianer',
             'Kamina': 'får potatisen att växa dubbelt så fort',
             'Lupus': 'jagar martianer blixtsnabbt',
             'Gorgo': 'slåss mot martianer och skyddar basen i stormar'}
KRIGARE = {'Taurus': 1.3, 'Lupus': .8, 'Gorgo': 1.5}
DEL_PLATS = [(185, 125), (-85, -235), (300, -180), (115, 330), (-335, -100), (SKEPP[0] - 4, SKEPP[1] - 15)]

HAB_MOBLER = [(-1.8, 1.8, 4.55, 6), (6.5, 8, -3.1, -.1), (3.1, 6.9, 4.9, 6), (4.7, 7.3, -5.55, -4.25), (-7.6, -4.9, 4.2, 6)]
HAB_MOBLER += [(x - .8, x + .8, z - .95, z + .95) for x in modeller.ODLING_X for z in modeller.ODLING_Z]
RAKET_MOBLER = [(-2.7, 2.7, 2.35, 3.5), (-1.5, -.7, .8, 1.7), (.7, 1.5, .8, 1.7), (-3.5, -2.55, -2.3, -.7), (2.55, 3.5, -2.3, -.7)]


def hojd(x, z):
    """Markens höjd i punkten (x, z)."""
    h = (math.sin(x * .021 + 1.3) * math.cos(z * .017) * 7 + math.sin(x * .047 + z * .039) * 3
         + math.sin(x * .11 + 2) * math.cos(z * .13) * .9 + math.sin((x - z) * .008) * 5)
    for fx, fz, r0, r1 in PLATT:
        d = math.hypot(x - fx, z - fz)
        if d < r1:
            t = 0 if d < r0 else (d - r0) / (r1 - r0)
            h *= t * t * (3 - 2 * t)
    return h


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def v3(c):
    return Vec3(c[0], c[1], c[2])


def pa(e, v):
    """Slå på/av bara om det behövs (sparar tid)."""
    if e.enabled != v:
        e.enabled = v


def tyst(e):
    """Motorn behöver inte titta på den här varje bildruta."""
    e.ignore = True
    for c in e.children:
        tyst(c)


def ui_quad(**kw):
    e = Entity(model='quad', **kw)
    e.setTransparency(TransparencyAttrib.MAlpha)
    return e


class Sak:
    """Något man kan trycka E på."""

    def __init__(self, zon, pos, radie, text, gor):
        self.zon, self.pos, self.radie, self.text, self.gor, self.aktiv = zon, pos, radie, text, gor, True


class Radar:
    def __init__(self, tex, rackvidd, **kw):
        self.rackvidd = rackvidd
        self.rot = Entity(**kw)
        ui_quad(parent=self.rot, texture=tex['bg'])
        self.storm = ui_quad(parent=self.rot, texture=tex['klick'], color=color.rgba(1, .55, .15, 0), z=-.01, enabled=False)
        self.svep = ui_quad(parent=self.rot, texture=tex['svep'], z=-.02)
        self.prickar = [ui_quad(parent=self.rot, texture=tex['klick'], z=-.03, enabled=False) for _ in range(44)]

    def visa(self, lista, yaw, t, storm=None):
        self.svep.rotation_z = (t * 130) % 360
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        k = .5 / self.rackvidd
        for i, p in enumerate(self.prickar):
            if i >= len(lista):
                pa(p, False)
                continue
            dx, dz, col, st, kant = lista[i]
            x, y = (dx * c - dz * s) * k, (dx * s + dz * c) * k
            d = math.hypot(x, y)
            if d > .45:
                if not kant:
                    pa(p, False)
                    continue
                x, y, st = x * .45 / d, y * .45 / d, st * .7
            pa(p, True)
            p.setPos(x, y, -.03)
            p.setScale(st)
            if getattr(p, 'farg', None) != col:
                p.farg = p.color = col
        pa(self.storm, bool(storm))
        if storm:
            x, y, st, a = storm
            x, y = x * k, y * k
            d = math.hypot(x, y)
            if d > .5:
                x, y = x * .5 / d, y * .5 / d
            self.storm.x, self.storm.y, self.storm.scale = x, y, st
            self.storm.color = color.rgba(1, .5, .12, a)


class Spel:
    def __init__(self):
        self.rnd = application.base.render
        self.slump = random.Random(11)
        self.t = 0.0                  # speltid i sekunder
        self.anim = 0.0
        self.lage = 'titel'           # titel, spel, start (raketen lyfter), vinst, slut
        self.paus = False
        self.zon = 'ute'              # ute, hab, raket
        self.i_rover = False
        self.tredje = False
        self.pos = Vec3(0, 0, -17)
        self.yaw, self.pitch = 180.0, 0.0
        self.vy, self.luft = 0.0, 0.0
        self.gafas = 0.0
        self.ror_sig = False
        # hur Mark mår
        self.halsa, self.syre, self.drakt, self.mat, self.bas = 100.0, 100.0, 100.0, 80.0, 100.0
        self.matpaket, self.potatis, self.skrot = 6, 3, 2
        self.delar_burna, self.delar_klara = [], []
        self.dodade = 0
        self.skottcd = 0.0
        self.skak = 0.0
        self.rod = 0.0
        # väder
        self.nasta_storm, self.storm_slut = 150.0, 0.0
        self.storm = 0.0
        self.nasta_martian = 95.0
        self.medd = []
        self.prompt_sak = None
        self.panel_typ = None
        self.tick = 0.0
        self.varnat = {}

        self.tex = {'bg': grafik.radar_bakgrund(), 'svep': grafik.radar_svep(), 'klick': grafik.klick_textur()}
        self.hinder = []              # runda hinder ute: (x, z, radie)
        self.saker = []
        self._bygg_varld()
        self._bygg_figurer()
        self._bygg_hud()
        self._ljus(0)
        self.visa_panel('titel')
        if not TEST:
            mouse.locked = True

    # ==========================================================================
    # VÄRLDEN
    # ==========================================================================
    def _bygg_varld(self):
        sl = self.slump
        # --- marken ---
        N, S = 120, 470
        verts, norms, cols, uvs, tris = [], [], [], [], []
        for iz in range(N + 1):
            for ix in range(N + 1):
                x, z = -S + 2 * S * ix / N, -S + 2 * S * iz / N
                h = hojd(x, z)
                e = 2.5
                n = Vec3(hojd(x - e, z) - hojd(x + e, z), 2 * e, hojd(x, z - e) - hojd(x, z + e)).normalized()
                ton = .5 + .5 * math.sin(x * .045 + math.sin(z * .03) * 2) * math.cos(z * .052)
                c = mix((.74, .37, .20), (.50, .25, .15), ton)
                lj = .9 + max(-8, min(8, h)) * .014
                verts.append((x, h, z))
                norms.append((n.x, n.y, n.z))
                cols.append((c[0] * lj, c[1] * lj, c[2] * lj, 1))
                uvs.append((x / 7, z / 7))
        for iz in range(N):
            for ix in range(N):
                a = iz * (N + 1) + ix
                tris += [a, a + 1, a + N + 2, a, a + N + 2, a + N + 1]
        self.mark = Entity(model=Mesh(vertices=verts, triangles=tris, normals=norms, colors=cols, uvs=uvs),
                           shader=grafik.mars_shader, texture=grafik.mark_textur())
        Entity(model='plane', scale=6000, y=-18, color=color.rgba(.5, .26, .15, 1), shader=grafik.mars_shader)

        # --- himlen ---
        b = Bygge()
        b.sphere((0, 0, 0), 1, (1, 1, 1, 1), seg=24, ringar=16)
        self.himmel = Entity(model=b.mesh(), shader=grafik.sky_shader, scale=1200, texture=grafik.stjarn_textur())
        self.himmel.setTwoSided(True)
        self.himmel.setBin('background', 0)
        self.himmel.setDepthWrite(False)
        self.himmel.setDepthTest(False)

        # --- byggnader ---
        self.hab = modeller.hab_ute()
        self.hinder += [(0, 0, 9.7), (0, -10.3, 1.9), (10.6, 3.7, 2.4), (-10.6, -3, 1.7), (-7.5, 6.5, .5)]
        for ix in range(4):
            for iz in range(2):
                self.hinder.append((-18 - ix * 4.6, 6 + iz * 5, 2.2))
        self.raket = modeller.raket_ute()
        self.raket.position = (RAKET[0], 0, RAKET[1])
        self.hinder.append((RAKET[0], RAKET[1], 3.2))
        self.skepp = modeller.daidalos()
        self.skepp.position = (SKEPP[0], 0, SKEPP[1])
        self.skepp.rotation_y = 35
        self.hinder.append((SKEPP[0], SKEPP[1], 9.5))
        self.n_stora = len(self.hinder)
        ptex = grafik.panel_textur()
        self.hab_inne = modeller.hab_inne(ptex)
        self.hab_inne.position = HAB_INNE
        self.raket_inne = modeller.raket_inne(ptex)
        self.raket_inne.position = RAKET_INNE
        rs = self.hab_inne.radarskarm
        self.skarm_bg = Entity(parent=self.hab_inne, model='quad', texture=self.tex['bg'], shader=grafik.glow_shader,
                               position=(rs[0], rs[1], rs[2]), scale=2.05)
        self.skarm_svep = Entity(parent=self.hab_inne, model='quad', texture=self.tex['svep'], shader=grafik.glow_shader,
                                 position=(rs[0], rs[1], rs[2] - .02), scale=2.05)
        for e in (self.skarm_bg, self.skarm_svep):
            e.setTransparency(TransparencyAttrib.MAlpha)
        self.vaggtext = modeller.skylt('', self.hab_inne, (7.84, 2.0, 2.6), .14, 90, color.rgba(.5, 1, .6, 1))
        self.rakettext = modeller.skylt('', self.raket_inne, (0, 2.25, 3.36), .14, 0, color.rgba(.5, 1, .6, 1))

        # --- rovern ---
        self.rover = modeller.rover()
        self.rv = {'x': -15.0, 'z': -20.0, 'yaw': 25.0, 'fart': 0.0, 'batteri': 100.0}

        # --- stenar och berg ---
        viktiga = [(x, z) for x, z in DEL_PLATS] + list(ROBOT_PLATS.values()) + [(self.rv['x'], self.rv['z'])]
        b = Bygge()
        for _ in range(300):
            x, z = sl.uniform(-450, 450), sl.uniform(-450, 450)
            if math.hypot(x, z) < 48 or math.hypot(x - SKEPP[0], z - SKEPP[1]) < 28:
                continue
            if any(math.hypot(x - vx, z - vz) < 9 for vx, vz in viktiga):
                continue
            stor = sl.random() < .2
            r = sl.uniform(1.6, 4.2) if stor else sl.uniform(.3, 1.1)
            g = sl.uniform(.75, 1.1)
            col = (.46 * g, .26 * g, .17 * g, 1)
            b.sphere((x, hojd(x, z) + r * .2, z), (r * sl.uniform(.8, 1.3), r * sl.uniform(.5, .9), r * sl.uniform(.8, 1.3)),
                     col, seg=6, ringar=4, rot=(sl.uniform(-25, 25), sl.uniform(0, 360), sl.uniform(-25, 25)))
            if stor:
                self.hinder.append((x, z, r * .95))
        for i in range(16):
            a = i / 16 * math.tau + sl.uniform(-.1, .1)
            d = sl.uniform(560, 700)
            R, H = sl.uniform(90, 170), sl.uniform(50, 130)
            g = sl.uniform(.8, 1.05)
            b.lathe([(R, -18), (R * .62, H * .45), (R * .3, H * .82), (R * .1, H * .97), (0, H)], (.5 * g, .27 * g, .17 * g, 1),
                    pos=(math.cos(a) * d, 0, math.sin(a) * d), seg=7, rot=(0, sl.uniform(0, 360), 0),
                    scale=(sl.uniform(.8, 1.4), 1, sl.uniform(.8, 1.4)))
        Entity(model=b.mesh(), shader=grafik.mars_shader)

        # --- stormdamm ---
        self.damm = []
        for _ in range(34):
            e = Entity(model='quad', texture=self.tex['klick'], shader=grafik.glow_shader, billboard=True,
                       scale=sl.uniform(4, 10), enabled=False)
            e.setTransparency(TransparencyAttrib.MAlpha)
            e.setDepthWrite(False)
            e.rel = Vec3(sl.uniform(-20, 20), sl.uniform(-2, 7), sl.uniform(-20, 20))
            e.v = Vec3(sl.uniform(14, 22), sl.uniform(-.5, .5), sl.uniform(1, 6))
            self.damm.append(e)

        # --- laserstrålar ---
        self.stralar = []
        for _ in range(8):
            e = Entity(model='cube', shader=grafik.glow_shader, enabled=False)
            e.tid = 0
            self.stralar.append(e)

        # --- lådor med förnödenheter ---
        platser = [(14, -30), (-30, 22), (SKEPP[0] + 16, SKEPP[1] + 8), (SKEPP[0] - 16, SKEPP[1] + 4), (SKEPP[0] + 2, SKEPP[1] - 22)]
        while len(platser) < 22:
            x, z = sl.uniform(-400, 400), sl.uniform(-400, 400)
            if math.hypot(x, z) > 60 and all(math.hypot(x - hx, z - hz) > hr + 2 for hx, hz, hr in self.hinder):
                platser.append((x, z))
        self.lador = []
        for x, z in platser:
            e = modeller.lada()
            e.position, e.rotation_y = (x, hojd(x, z), z), sl.uniform(0, 360)
            self.lador.append(e)
            self.saker.append(Sak('ute', Vec3(x, 0, z), 3.0, lambda: 'Öppna lådan', lambda e=e: self._oppna_lada(e)))
            e.sak = self.saker[-1]

        # --- raketdelar ---
        self.delar = []
        for i, (x, z) in enumerate(DEL_PLATS):
            e = modeller.raketdel(i)
            e.position = (x, hojd(x, z) + .1, z)
            e.nr, e.tagen, e.storm = i, False, -1
            self.delar.append(e)
            self.saker.append(Sak('ute', Vec3(x, 0, z), 3.2, lambda i=i: 'Plocka upp ' + modeller.DELNAMN[i].lower(),
                                  lambda e=e: self._ta_del(e)))
            e.sak = self.saker[-1]

        # --- dörrar och instrument ---
        S_ = self.saker
        S_.append(Sak('ute', Vec3(0, 0, -13.2), 3.2, lambda: 'Gå in i basen', lambda: self.byt_zon('hab')))
        S_.append(Sak('ute', Vec3(RAKET[0], 0, RAKET[1] - 4.8), 3.2, lambda: 'Klättra in i raketen', lambda: self.byt_zon('raket')))
        self.rover_sak = Sak('ute', None, 4.6, lambda: 'Kör rovern', self._in_i_rover)
        S_.append(self.rover_sak)
        H = HAB_INNE
        S_.append(Sak('hab', H + Vec3(0, 0, -5.2), 2.3, lambda: 'Ta på rymddräkten och gå ut', lambda: self.byt_zon('ute')))
        S_.append(Sak('hab', H + Vec3(0, 0, 4.2), 2.6, lambda: 'Titta på väderradarn', lambda: self.visa_panel('radar')))
        S_.append(Sak('hab', H + Vec3(7.3, 0, 2.6), 2.4, lambda: 'Titta på basstatus', lambda: self.visa_panel('bas')))
        S_.append(Sak('hab', H + Vec3(6.0, 0, -1.6), 2.4, self._laga_text, self._laga_drakt))
        S_.append(Sak('hab', H + Vec3(5.4, 0, 4.4), 2.3, self._at_text, self.at))
        S_.append(Sak('hab', H + Vec3(5.9, 0, -3.8), 2.2, lambda: 'Sov till i morgon', self._sov))
        self.odling = []
        for x in modeller.ODLING_X:
            for z in modeller.ODLING_Z:
                p = modeller.potatisplanta()
                p.parent, p.position, p.enabled = self.hab_inne, (x, .75, z), False
                ruta = {'planta': p, 'lage': 'tom', 'prog': 0.0}
                self.odling.append(ruta)
                S_.append(Sak('hab', H + Vec3(x, 0, z), 2.1, lambda r=ruta: self._odla_text(r), lambda r=ruta: self._odla(r)))
        R = RAKET_INNE
        S_.append(Sak('raket', R + Vec3(0, 0, -2.8), 2.2, lambda: 'Gå ut ur raketen', lambda: self.byt_zon('ute')))
        S_.append(Sak('raket', R + Vec3(0, 0, 1.9), 2.4, self._raket_text, self._raket_gor))

    def _bygg_figurer(self):
        self.mark_fig = modeller.astronaut()
        self.mark_fig.enabled = False
        self.borr = modeller.laserborr()
        self.borr.parent = camera
        self.borr.position = (.33, -.3, .75)
        self.robotar = []
        for f in modeller.ROBOTAR:
            e = f()
            x, z = ROBOT_PLATS[e.namn]
            e.px, e.pz, e.raddad, e.cd, e.fas, e.rorde = x, z, False, 0.0, self.slump.uniform(0, 6), True
            e.position = (x, hojd(x, z), z)
            e.rotation = (0, self.slump.uniform(0, 360), 14)
            e.ogon.enabled = False
            e.skylt.text = e.namn + ' (avstängd)'
            self.robotar.append(e)
            self.saker.append(Sak('ute', Vec3(x, 0, z), 4.0, lambda e=e: 'Starta om ' + e.namn, lambda e=e: self._radda(e)))
            e.sak = self.saker[-1]
        self.martianer = []

    # ==========================================================================
    # HUD – ALLA INSTRUMENT PÅ SKÄRMEN
    # ==========================================================================
    def _bygg_hud(self):
        ui = camera.ui
        self.rodskarm = ui_quad(parent=ui, color=color.rgba(1, 0, 0, 0), scale=(2, 1.1), z=.9, enabled=False)
        self.hud = Entity(parent=ui)
        gron = color.rgba(.5, 1, .65, 1)
        self.staplar = {}
        rader = [('HÄLSA', (.95, .25, .25)), ('SYRE', (.3, .8, 1)), ('DRÄKT', (.92, .92, .92)), ('MAT', (1, .65, .2)),
                 ('BAS', (.4, .95, .45)), ('ROVER', (1, .9, .3))]
        for i, (namn, c) in enumerate(rader):
            y = -.26 - i * .037
            Text(parent=self.hud, text=namn, position=(-.865, y + .012), scale=.75, color=gron)
            ui_quad(parent=self.hud, color=color.rgba(0, 0, 0, .55), scale=(.2, .02), position=(-.775, y), origin=(-.5, 0))
            f = ui_quad(parent=self.hud, color=color.rgba(c[0], c[1], c[2], 1), scale=(.2, .014), position=(-.775, y),
                        origin=(-.5, 0), z=-.01)
            f.bas = c
            self.staplar[namn] = f
        ui_quad(parent=self.hud, color=color.rgba(0, .06, .04, .5), scale=(.34, .135), position=(-.71, .425))
        self.info = [Text(parent=self.hud, text='', position=(-.865, .48 - i * .0235), scale=.8, color=gron) for i in range(4)]
        self.radar = Radar(self.tex, 150, parent=self.hud, position=(.725, .32), scale=.3)
        self.radartext = Text(parent=self.hud, text='RADAR 150 m', position=(.725, .155), origin=(0, 0), scale=.7, color=gron)
        ui_quad(parent=self.hud, color=color.rgba(0, .06, .04, .5), scale=(.27, .15), position=(.74, -.39))
        self.inv = [Text(parent=self.hud, text='', position=(.62, -.325 - i * .0235), scale=.8, color=gron) for i in range(5)]
        self.mal = Text(parent=self.hud, text='', position=(0, .485), origin=(0, .5), scale=.85, color=color.rgba(1, .9, .6, 1))
        self.loggtext = Text(parent=self.hud, text='', position=(0, .43), origin=(0, .5), scale=.85, color=color.white)
        self.varning = Text(parent=self.hud, text='', position=(0, .2), origin=(0, 0), scale=1.6, color=color.rgba(1, .25, .2, 1))
        self.prompt = Text(parent=self.hud, text='', position=(0, -.17), origin=(0, 0), scale=1.15, color=color.rgba(1, 1, .6, 1))
        self.sikte = Text(parent=self.hud, text='+', position=(0, .008), origin=(0, 0), scale=1.2, color=color.rgba(1, 1, 1, .7))
        # helskärms-paneler (instrument man tittar närmare på)
        self.panel = Entity(parent=ui, z=-1, enabled=False)
        ui_quad(parent=self.panel, color=color.rgba(0, .05, .035, .985), scale=(1.5, .9))
        ui_quad(parent=self.panel, color=color.rgba(.3, 1, .6, .8), scale=(1.5, .004), y=.36, z=-.01)
        self.p_titel = Text(parent=self.panel, text='', position=(0, .41), origin=(0, 0), scale=1.7, color=gron, z=-.02)
        self.p_text = Text(parent=self.panel, text='', position=(-.7, .33), scale=.95, color=color.white, z=-.02)
        self.p_fot = Text(parent=self.panel, text='', position=(0, -.41), origin=(0, 0), scale=.95, color=color.rgba(1, 1, .6, 1), z=-.02)
        self.storradar = Radar(self.tex, 600, parent=self.panel, position=(.36, -.03), scale=.62, z=-.02)
        self.svart = ui_quad(parent=ui, color=color.rgba(0, 0, 0, 0), scale=(2, 1.1), z=-2, enabled=False)
        self.svart_a = 0.0
        self._txt = {}

    def satt(self, t, s):
        """Byt text bara om den har ändrats – att rita om text är långsamt."""
        if isinstance(t, list):                      # en textrad per Text ger skarpast bokstäver
            for rad, text in zip(t, s.split('\n')):
                self.satt(rad, text)
            return
        if self._txt.get(id(t)) != s:
            self._txt[id(t)] = s
            t.text = s

    def sag(self, text, tid=6):
        self.medd.append([text, tid])
        self.medd = self.medd[-4:]

    def visa_panel(self, typ):
        self.panel_typ = typ
        self.panel.enabled = typ is not None
        self.hud.enabled = typ is None
        self.storradar.rot.enabled = typ == 'radar'
        if typ:
            self._panel_text()

    def _vader_text(self):
        if self.storm > 0:
            return 'STORM! Sök skydd!'
        kvar = self.nasta_storm - self.t
        if kvar < 75:
            return f'Storm om {int(kvar)} s'
        return 'Klart'

    def _panel_text(self):
        typ = self.panel_typ
        fot = '[E] eller [Esc] stänger'
        if typ == 'titel':
            titel = 'M A R S'
            text = ('Du är astronauten Mark Watney. Din besättning trodde att du dog i stormen\n'
                    'och åkte hem. Nu är du ensam på Mars.\n\n'
                    '  •  Laga raketen: hitta de 6 raketdelarna och bär dem till raketen.\n'
                    '  •  Odla potatis i basen. Annars tar maten slut.\n'
                    '  •  Rymdskeppet Daidalos kom för att rädda dig – men kraschade.\n'
                    '      Hitta robotarna Minus, Bulten, Taurus, Kamina, Lupus och Gorgo.\n'
                    '  •  Går rymddräkten eller basen sönder dör du. Akta dig för stormar\n'
                    '      och martianer!\n\n'
                    'W A S D  gå            Mus (eller piltangenter)  titta        Shift  spring\n'
                    'Mellanslag  hoppa      E  använd / öppna / gå in             F  ät\n'
                    'Vänster musknapp  skjut med laserborren      V  se Mark utifrån\n'
                    'H  hjälp       M  släpp musen       F11  helskärm       Esc  paus')
            fot = 'Tryck ENTER för att börja'
        elif typ == 'hjalp' or typ == 'paus':
            titel = 'PAUS' if typ == 'paus' else 'HJÄLP'
            text = ('W A S D  gå / köra rovern          Mus eller piltangenter  titta\n'
                    'Shift  spring                       Mellanslag  hoppa\n'
                    'E  använd, öppna, gå in och ut      F  ät (bara inomhus eller i rovern)\n'
                    'Vänster musknapp  laserborr         V  se Mark utifrån\n'
                    'M  släpp/fånga musen                F11  helskärm\n\n'
                    'TIPS\n'
                    '  •  Syret i dräkten räcker i ungefär 4 minuter. Det fylls på i basen,\n'
                    '      i raketen och i rovern.\n'
                    '  •  Titta på väderradarn i basen – den varnar för stormar i god tid.\n'
                    '  •  Lådorna ute på Mars innehåller mat och skrot. Skrot lagar dräkt och bas.\n'
                    '  •  Gröna ljuspelare visar var raketdelarna ligger.\n'
                    '  •  Robotarna hjälper dig när du har startat om dem.')
            fot = '[Esc] fortsätt     [Q] avsluta spelet' if typ == 'paus' else fot
        elif typ == 'radar':
            titel = 'VÄDERRADAR'
            kvar = self.nasta_storm - self.t
            dag = self._dag()
            if self.storm > 0:
                prognos = f'SANDSTORM PÅGÅR\nBeräknas avta om {int(max(0, self.storm_slut - self.t))} s'
            elif kvar < 150:
                prognos = f'SANDSTORM NÄRMAR SIG\nfrån väster – framme om {int(kvar)} s'
            else:
                prognos = f'Inga stormar i närheten.\nNästa väntas om ca {int(kvar / 15)} timmar.'
            text = (f'SOL {self._sol()}   KL {self._klocka()}\n\n{prognos}\n\n'
                    f'Temperatur   {int(-78 + 55 * dag - 12 * self.storm)} °C\n'
                    f'Vind         {int(5 + 3 * math.sin(self.t * .05) + 30 * self.storm)} m/s\n'
                    f'Lufttryck    {6.1 + .4 * math.sin(self.t * .02) - 1.5 * self.storm:.1f} mbar\n'
                    f'Sikt         {int(520 - 480 * self.storm)} m\n\n'
                    'Radarn når 600 m. Norr är uppåt.\n\n'
                    '  vit      basen\n  blå      raketen och rovern\n  röd      martianer\n'
                    '  orange   storm\n  ljusblå  robotar\n  grön     raketdelar (kräver Minus)')
        elif typ == 'bas':
            titel = 'BASSTATUS'
            sol = 0 if self.storm > .3 else int(100 * self._dag())
            text = (f'Basens skal        {int(self.bas)} %\n'
                    f'Syregenerator      {"OK" if self.bas > 25 else "LÄCKER!"}\n'
                    f'Solpaneler         {sol} %\n'
                    f'Lufttryck inne     {int(60 + self.bas * .41)} kPa\n'
                    f'Temperatur inne    {int(14 + self.bas * .07)} °C\n\n'
                    f'Odlingslådor       {sum(1 for r in self.odling if r["lage"] != "tom")} av 6 används\n'
                    f'Matpaket           {self.matpaket}\n'
                    f'Potatis            {self.potatis}\n'
                    f'Skrot              {self.skrot}\n\n'
                    'Stormar och martianer skadar basen.\nOm skalet når 0 % spricker basen.')
            fot = '[F] laga basen med 1 skrot (+25 %)      [E] stänger'
        elif typ == 'raket':
            titel = 'RAKETENS DATOR'
            rader = []
            for i, n in enumerate(modeller.DELNAMN):
                st = 'INSTALLERAD' if i in self.delar_klara else ('bär du på' if i in self.delar_burna else 'SAKNAS')
                rader.append(f'  {"[x]" if i in self.delar_klara else "[  ]"}   {n:<20} {st}')
            text = 'Raketen kan inte starta förrän alla delar sitter på plats.\n\n' + '\n'.join(rader)
        elif typ in ('slut', 'vinst'):
            raddade = sum(1 for r in self.robotar if r.raddad)
            titel = 'DU KLARADE DET!' if typ == 'vinst' else 'MARK KLARADE SIG INTE'
            text = (self.slutorsak + '\n\n'
                    f'Du överlevde {self._sol()} sol på Mars.\n'
                    f'Robotar räddade:       {raddade} av 6\n'
                    f'Raketdelar på plats:   {len(self.delar_klara)} av 6\n'
                    f'Martianer besegrade:   {self.dodade}\n')
            fot = '[R] spela igen      [Q] avsluta'
        else:
            return
        self.satt(self.p_titel, titel)
        self.satt(self.p_text, text)
        self.satt(self.p_fot, fot)

    # ==========================================================================
    # TID OCH LJUS
    # ==========================================================================
    def _timme(self):
        return (8 + self.t / SOL * 24) % 24

    def _klocka(self):
        h = self._timme()
        return f'{int(h):02d}:{int(h % 1 * 60):02d}'

    def _sol(self):
        return 1 + int((SOL / 3 + self.t) / SOL)

    def _dag(self):
        return max(0.0, min(1.0, math.sin((self._timme() - 6) / 12 * math.pi) * 4 + .2))

    def _ljus(self, dt):
        r = self.rnd
        a = (self._timme() - 6) / 12 * math.pi
        dag = self._dag()
        sol = Vec3(math.cos(a) * .9, math.sin(a), .38).normalized()
        self.sol_rikt = -sol
        lag = max(0.0, 1 - abs(math.sin(a)) * 3) * (1 if math.sin(a) > -.25 else 0)     # solen nära horisonten
        topp = mix((.012, .014, .035), (.50, .36, .30), dag)
        hor = mix((.05, .045, .075), (.86, .64, .44), dag)
        hor = mix(hor, (.42, .46, .62), lag * .55 * dag)          # blå solnedgång, som på riktiga Mars
        glod = mix((1, .9, .72), (.45, .65, 1.0), lag)
        solf = mix((0, 0, 0), (1.08, .95, .82), dag)
        amb = mix((.20, .21, .30), (.60, .52, .49), dag)
        I = self.storm
        if I > 0:
            ljus = .35 + .65 * dag
            dammf = (.58 * ljus, .34 * ljus, .17 * ljus)
            topp, hor = mix(topp, dammf, I * .9), mix(hor, dammf, I)
            solf = mix(solf, (0, 0, 0), I * .8)
            amb = mix(amb, (.42 * ljus, .27 * ljus, .16 * ljus), I * .8)
            glod = mix(glod, (0, 0, 0), I)
        self.horisont = hor
        lampa = (0, 0, 0)
        if self.zon == 'ute':
            if dag < .4 or I > .5:
                lampa = (2.4, 2.25, 2.0)
            r.setShaderInput('sun_dir', self.sol_rikt)
            r.setShaderInput('sun_color', v3(solf))
            r.setShaderInput('ambient_color', v3(amb))
            r.setShaderInput('fog_color', Vec4(hor[0], hor[1], hor[2], .96))
            r.setShaderInput('fog_start', 55 - 53 * I)
            r.setShaderInput('fog_end', 540 - 500 * I)
            r.setShaderInput('hemi_min', .38)
        else:
            flimmer = 1 - .25 * I * (math.sin(self.anim * 23) > .6)
            r.setShaderInput('sun_dir', Vec3(-.25, -.85, .45).normalized())
            r.setShaderInput('sun_color', Vec3(.42, .42, .4) * flimmer)
            r.setShaderInput('ambient_color', Vec3(.72, .72, .74) * flimmer)
            r.setShaderInput('fog_color', Vec4(0, 0, 0, 0))
            r.setShaderInput('fog_start', 1e5)
            r.setShaderInput('fog_end', 2e5)
            r.setShaderInput('hemi_min', .8)
            for f in self.hab_inne.fonster + self.raket_inne.fonster:
                f.color = color.rgba(hor[0], hor[1], hor[2], 1)
        if self.i_rover:
            rv = self.rv
            fr = Vec3(math.sin(math.radians(rv['yaw'])), -.12, math.cos(math.radians(rv['yaw']))).normalized()
            r.setShaderInput('lamp_pos', Vec3(rv['x'], self.rover.y + 1.4, rv['z']) + fr * 2.6)
            r.setShaderInput('lamp_dir', fr)
        else:
            r.setShaderInput('lamp_pos', camera.world_position)
            r.setShaderInput('lamp_dir', camera.forward)
        r.setShaderInput('lamp_color', v3(lampa))
        r.setShaderInput('sky_top', v3(topp))
        r.setShaderInput('sky_horizon', v3(hor))
        r.setShaderInput('sun_glow', v3(glod) * dag)
        r.setShaderInput('star_amount', (1 - dag) * (1 - I))
        r.setShaderInput('camera_world_position', camera.world_position)
        self.himmel.position = camera.world_position

    # ==========================================================================
    # HANDLINGAR
    # ==========================================================================
    def byt_zon(self, zon):
        if zon == 'ute' and self.drakt <= 0:
            self.sag('Rymddräkten är trasig! Laga den i verkstaden innan du går ut.')
            return
        fran = self.zon
        self.zon = zon
        self.svart_a = 1.0
        self.vy = self.luft = 0
        if zon == 'hab':
            self.pos, self.yaw = HAB_INNE + Vec3(0, 0, -4.2), 0
            self.sag('Luftslussen stängd. Du kan ta av dig hjälmen.', 4)
        elif zon == 'raket':
            self.pos, self.yaw = RAKET_INNE + Vec3(0, 0, -2.2), 0
        elif fran == 'raket':
            self.pos, self.yaw = Vec3(RAKET[0], 0, RAKET[1] - 6.2), 180
        else:
            self.pos, self.yaw = Vec3(0, 0, -15), 180
            self.sag('Rymddräkten på. Syret räcker i ungefär 4 minuter.', 4)
        self.pitch = 0

    def _oppna_lada(self, e):
        e.sak.aktiv = False
        self.lador.remove(e)
        destroy(e)
        sl = self.slump
        m, s, p = sl.choice((0, 1, 1, 2)), sl.choice((0, 1, 1, 2)), sl.choice((0, 0, 0, 2))
        if m + s + p == 0:
            m = 1
        self.matpaket += m
        self.skrot += s
        self.potatis += p
        fynd = [f'{n} {namn}' for n, namn in ((m, 'matpaket'), (s, 'skrot'), (p, 'potatisar')) if n]
        self.sag('Du hittade ' + ' och '.join(fynd) + '!')

    def _ta_del(self, e):
        e.sak.aktiv = False
        e.tagen = True
        e.enabled = False
        self.delar_burna.append(e.nr)
        self.sag(f'Du hittade: {modeller.DELNAMN[e.nr].upper()}! Bär den till raketen.', 8)

    def _radda(self, e):
        e.sak.aktiv = False
        e.raddad = True
        e.rotation = (0, e.rotation_y, 0)
        e.ogon.enabled = True
        e.skylt.text = e.namn
        self.sag(f'{e.namn} vaknar! {e.namn} {ROBOT_KAN[e.namn]}.', 9)
        if e.namn == 'Minus':
            self.sag('Minus: "Daidalos kraschade i NORDVÄST. Mina vänner ligger kvar där!"', 12)
        if all(r.raddad for r in self.robotar):
            self.sag('Alla sex robotarna är räddade!', 9)

    def _in_i_rover(self):
        self.i_rover = True
        self.yaw = self.rv['yaw']
        self.pitch = 12
        self.sag('Du kör rovern. Här inne fylls syret på. [E] kliver ur.', 5)

    def _ur_rover(self):
        rv = self.rv
        self.i_rover = False
        y = math.radians(rv['yaw'])
        self.pos = Vec3(rv['x'] + math.cos(y) * 3.3, 0, rv['z'] - math.sin(y) * 3.3)
        rv['fart'] = 0

    def _at_text(self):
        if self.matpaket > 0:
            return f'Ät ett matpaket ({self.matpaket} kvar)'
        if self.potatis > 0:
            return f'Ät en potatis ({self.potatis} kvar)'
        return 'Maten är slut – odla potatis!'

    def at(self):
        if self.zon == 'ute' and not self.i_rover:
            self.sag('Du kan inte äta med hjälmen på! Gå in i basen eller rovern.')
        elif self.mat > 92:
            self.sag('Du är redan mätt.', 3)
        elif self.matpaket > 0:
            self.matpaket -= 1
            self.mat = min(100, self.mat + 40)
            self.sag('Du åt ett matpaket.', 3)
        elif self.potatis > 0:
            self.potatis -= 1
            self.mat = min(100, self.mat + 22)
            self.sag('Du åt en potatis. Lite ketchup hade varit gott.', 3)
        else:
            self.sag('Du har ingen mat! Leta i lådor eller skörda potatis.')

    def _laga_text(self):
        if self.drakt >= 99:
            return 'Rymddräkten är hel'
        if self.skrot > 0:
            return f'Laga rymddräkten (1 skrot, +35 %)'
        return 'Nödlaga dräkten med silvertejp' if self.drakt < 25 else 'Inget skrot att laga dräkten med'

    def _laga_drakt(self):
        if self.drakt >= 99:
            return
        if self.skrot > 0:
            self.skrot -= 1
            self.drakt = min(100, self.drakt + 35)
            self.sag('Du lagade rymddräkten.', 3)
        elif self.drakt < 25:
            self.drakt = 25
            self.sag('Silvertejp löser allt. Dräkten håller – nätt och jämnt.', 4)

    def _laga_bas(self):
        if self.bas >= 99:
            self.sag('Basen är redan hel.', 3)
        elif self.skrot > 0:
            self.skrot -= 1
            self.bas = min(100, self.bas + 25)
            self.sag('Du lagade basens skal.', 3)
        else:
            self.sag('Du har inget skrot. Leta i lådorna ute på Mars.')

    def _odla_text(self, r):
        if r['lage'] == 'tom':
            return f'Plantera en potatis ({self.potatis} kvar)' if self.potatis > 0 else 'Ingen potatis att plantera'
        if r['lage'] == 'klar':
            return 'Skörda potatisen!'
        return f'Potatisen växer... {int(r["prog"] * 100)} %'

    def _odla(self, r):
        if r['lage'] == 'tom' and self.potatis > 0:
            self.potatis -= 1
            r['lage'], r['prog'] = 'vaxer', 0.0
            r['planta'].enabled = True
            r['planta'].scale = .1
            self.sag('Du planterade en potatis.', 3)
        elif r['lage'] == 'klar':
            r['lage'] = 'tom'
            r['planta'].enabled = False
            self.potatis += 4
            self.sag('Skörd! Du fick 4 potatisar.', 4)

    def _sov(self):
        h = self._timme()
        if 6 <= h < 19:
            self.sag('Du är inte trött än. Kom tillbaka efter klockan 19.', 4)
            return
        sek = ((6.5 - h) % 24) / 24 * SOL
        self.t += sek
        for r in self.odling:
            if r['lage'] == 'vaxer':
                r['prog'] += sek / self._vaxtid()
        self.mat = max(5, self.mat - 14)
        self.halsa = min(100, self.halsa + 40)
        self.storm, self.storm_slut = 0, 0
        if self.nasta_storm < self.t + 50:
            self.nasta_storm = self.t + 50 + self.slump.uniform(0, 60)
        self.nasta_martian = max(self.nasta_martian, self.t + 25)
        self.svart_a = 1.6
        self.sag(f'Du sov gott. God morgon – det är sol {self._sol()}.', 6)

    def _vaxtid(self):
        return 95 if self._har('Kamina') else 190

    def _har(self, namn):
        return any(r.raddad and r.namn == namn for r in self.robotar)

    def _raket_text(self):
        if self.delar_burna:
            return f'Installera {len(self.delar_burna)} raketdel(ar)'
        if len(self.delar_klara) == 6:
            return 'STARTA RAKETEN OCH ÅK HEM!'
        return 'Titta på raketens dator'

    def _raket_gor(self):
        if self.delar_burna:
            for i in self.delar_burna:
                self.sag(f'{modeller.DELNAMN[i]} installerad.', 5)
            self.delar_klara += self.delar_burna
            self.delar_burna = []
            if len(self.delar_klara) == 6:
                self.sag('RAKETEN ÄR LAGAD! Tryck E vid datorn igen för att starta.', 10)
        elif len(self.delar_klara) == 6:
            self._starta_raket()
        else:
            self.visa_panel('raket')

    def _starta_raket(self):
        self.lage = 'start'
        self.start_t = 0.0
        self.zon, self.i_rover = 'ute', False
        self.hud.enabled = False
        self.mark_fig.enabled = False
        self.borr.enabled = False
        for r in self.robotar:
            if r.raddad:
                r.enabled = False
        for m in self.martianer:
            m.enabled = False

    def do(self, orsak):
        if self.lage != 'spel':
            return
        self.lage = 'slut'
        self.slutorsak = orsak
        self.visa_panel('slut')
        mouse.locked = False

    def _anvand(self):
        if self.i_rover:
            self._ur_rover()
        elif self.prompt_sak:
            self.prompt_sak.gor()

    def _skjut(self):
        if self.skottcd > 0:
            return
        self.skottcd = .32
        o, d = camera.world_position, camera.forward
        bast, traff = 75.0, None
        for m in self.martianer:
            if m.dod > 0:
                continue
            v = Vec3(m.px, m.y + 1.4, m.pz) - o
            t = v.dot(d)
            if 0 < t < bast and (v - d * t).length() < 1.0:
                bast, traff = t, m
        start = o + camera.right * .33 - camera.up * .28 + d * 1.0
        self._strale(start, o + d * bast, color.rgba(1, .25, .15, 1))
        if traff:
            self._skada(traff, 1)

    def _strale(self, a, b, col):
        for e in self.stralar:
            if not e.enabled:
                e.enabled = True
                e.position = (a + b) / 2
                e.look_at(b)
                e.scale = (.05, .05, (b - a).length())
                e.color, e.tid = col, .09
                return

    def _skada(self, m, n):
        m.hp -= n
        m.blink = .15
        if m.hp <= 0 and m.dod <= 0:
            m.dod = .001
            self.dodade += 1
            if self.slump.random() < .35:
                self.skrot += 1
                self.sag('Martianen tappade lite skrot.', 3)

    # ==========================================================================
    # TANGENTER
    # ==========================================================================
    def input(self, key):
        if key == 'f11':
            window.fullscreen = not window.fullscreen
        if key == 'm':
            mouse.locked = not mouse.locked
        if self.lage == 'titel':
            if key in ('enter', 'space', 'left mouse down'):
                self.lage = 'spel'
                self.visa_panel(None)
                self.sag('Sol 1. Hitta raketdelarna och håll dig vid liv.', 8)
                self.sag('En svag radiosignal hörs i nordost, nära basen...', 10)
            return
        if self.lage in ('slut', 'vinst'):
            if key == 'r':
                os.execv(sys.executable, [sys.executable] + sys.argv)
            if key == 'q':
                application.quit()
            return
        if self.lage != 'spel':
            return
        if self.paus:
            if key == 'escape':
                self.paus = False
                self.visa_panel(None)
                if not TEST:
                    mouse.locked = True
            elif key == 'q':
                application.quit()
            return
        if self.panel_typ:
            if key in ('e', 'escape', 'left mouse down', 'enter'):
                self.visa_panel(None)
            elif key == 'f' and self.panel_typ == 'bas':
                self._laga_bas()
            return
        if key == 'escape':
            self.paus = True
            self.visa_panel('paus')
            mouse.locked = False
        elif key == 'e':
            self._anvand()
        elif key == 'left mouse down':
            if self.zon == 'ute' and not self.i_rover:
                self._skjut()
            else:
                self._anvand()
        elif key == 'f':
            self.at()
        elif key == 'v':
            self.tredje = not self.tredje
        elif key in ('h', 'f1'):
            self.visa_panel('hjalp')
        elif key == 'space' and self.luft <= 0 and not self.i_rover:
            self.vy = 4.3

    # ==========================================================================
    # UPPDATERING – KÖRS VARJE BILDRUTA
    # ==========================================================================
    def update(self):
        dt = min(time.dt, .05)
        self.anim += dt
        pa(self.svart, self.svart_a > 0)
        if self.svart_a > 0:
            self.svart.color = color.rgba(0, 0, 0, min(1, self.svart_a))
            self.svart_a = max(0, self.svart_a - dt * 1.6)
        if self.lage == 'titel':
            a = self.anim * .08
            camera.position = Vec3(math.sin(a) * 34, 7, math.cos(a) * -34)
            camera.look_at(Vec3(4, 3, -4))
            pa(self.borr, False)
            self._ljus(dt)
            return
        if self.lage == 'start':
            self._raketstart(dt)
            self._ljus(dt)
            return
        if self.lage in ('slut', 'vinst') or self.paus:
            return
        self.t += dt
        self._vader(dt)
        if self.panel_typ is None:
            self._titta(dt)
            if self.i_rover:
                self._kor(dt)
            else:
                self._ga(dt)
        self._rover_fysik(dt)
        self._robotar(dt)
        self._martianer(dt)
        self._overlevnad(dt)
        self._kamera(dt)
        self._ljus(dt)
        self._effekter(dt)
        self.tick -= dt
        if self.tick <= 0:
            self.tick = .12
            self._hitta_sak()
            self._hud()

    def _titta(self, dt):
        if mouse.locked:
            self.yaw += mouse.velocity[0] * 48
            self.pitch -= mouse.velocity[1] * 48
        self.yaw += (held_keys['right arrow'] - held_keys['left arrow']) * 95 * dt
        self.pitch += (held_keys['down arrow'] - held_keys['up arrow']) * 70 * dt
        self.pitch = max(-85, min(85, self.pitch))

    def _knuffa(self, x, z, r, hinder):
        for hx, hz, hr in hinder:
            dx, dz = x - hx, z - hz
            d = math.hypot(dx, dz)
            if d < hr + r:
                d = d or .01
                x, z = hx + dx / d * (hr + r), hz + dz / d * (hr + r)
        return x, z

    def _ga(self, dt):
        fram, sida = held_keys['w'] - held_keys['s'], held_keys['d'] - held_keys['a']
        spring = (held_keys['shift'] or held_keys['left shift']) and self.zon == 'ute'
        fart = 9.5 if spring else 6.0
        if self.zon != 'ute':
            fart = 4.5
        y = math.radians(self.yaw)
        dx = math.sin(y) * fram + math.cos(y) * sida
        dz = math.cos(y) * fram - math.sin(y) * sida
        l = math.hypot(dx, dz)
        self.ror_sig = l > 0
        if l > 0:
            dx, dz = dx / l * fart * dt, dz / l * fart * dt
            self.gafas += fart * dt * 1.5
        x, z = self.pos.x + dx, self.pos.z + dz
        if self.zon == 'ute':
            x, z = self._knuffa(x, z, .5, self.hinder)
            x, z = self._knuffa(x, z, .5, [(self.rv['x'], self.rv['z'], 2.4)])
            x, z = max(-KANT, min(KANT, x)), max(-KANT, min(KANT, z))
            mark = hojd(x, z)
            g = 3.7                                      # tyngdkraften på Mars – man hoppar högt!
        else:
            c, (bx, bz), mobler = (HAB_INNE, (7.5, 5.5), HAB_MOBLER) if self.zon == 'hab' else (RAKET_INNE, (3.1, 3.1), RAKET_MOBLER)
            lx, lz = max(-bx, min(bx, x - c.x)), max(-bz, min(bz, z - c.z))
            for x0, x1, z0, z1 in mobler:
                x0, x1, z0, z1 = x0 - .35, x1 + .35, z0 - .35, z1 + .35
                if x0 < lx < x1 and z0 < lz < z1:
                    ut = min((lx - x0, 0), (x1 - lx, 1), (lz - z0, 2), (z1 - lz, 3))[1]
                    lx, lz = (x0, lz) if ut == 0 else (x1, lz) if ut == 1 else (lx, z0) if ut == 2 else (lx, z1)
            x, z, mark, g = c.x + lx, c.z + lz, 0, 9.0
        self.luft += self.vy * dt
        self.vy -= g * dt
        if self.luft <= 0:
            self.luft, self.vy = 0, 0
        self.pos = Vec3(x, mark + self.luft, z)

    def _kor(self, dt):
        rv = self.rv
        gas, styr = held_keys['w'] - held_keys['s'], held_keys['d'] - held_keys['a']
        topp = 17 if rv['batteri'] > 0 else 3
        mal = gas * topp if gas >= 0 else gas * 7
        rv['fart'] += max(-9 * dt, min(9 * dt, mal - rv['fart']))
        sv = styr * 62 * dt * max(-1, min(1, rv['fart'] / 6))
        rv['yaw'] += sv
        self.yaw += sv
        rv['batteri'] = max(0, rv['batteri'] - abs(rv['fart']) / 17 * .26 * dt)

    def _rover_fysik(self, dt):
        rv = self.rv
        if not self.i_rover:
            rv['fart'] *= max(0, 1 - 3 * dt)
        y = math.radians(rv['yaw'])
        fx, fz = math.sin(y), math.cos(y)
        if abs(rv['fart']) > .01:
            x, z = rv['x'] + fx * rv['fart'] * dt, rv['z'] + fz * rv['fart'] * dt
            x, z = self._knuffa(x, z, 2.3, self.hinder)
            rv['x'], rv['z'] = max(-KANT, min(KANT, x)), max(-KANT, min(KANT, z))
            for h in self.rover.hjul:
                h.rotation_x += rv['fart'] * dt * 95
        x, z = rv['x'], rv['z']
        h0 = hojd(x, z)
        self.rover.position = (x, h0, z)
        lut = math.degrees(math.atan2(hojd(x - fx * 2, z - fz * 2) - hojd(x + fx * 2, z + fz * 2), 4))
        roll = math.degrees(math.atan2(hojd(x + fz * 1.3, z - fx * 1.3) - hojd(x - fz * 1.3, z + fx * 1.3), 2.6))
        self.rover.rotation = (lut, rv['yaw'], roll)
        self.rover_sak.pos = Vec3(x, 0, z)
        nara_bas = math.hypot(x, z) < 35
        rv['batteri'] = min(100, rv['batteri'] + dt * (4 if nara_bas else 0) + dt * .35 * self._dag() * (1 - self.storm))
        if self.i_rover:
            self.pos = Vec3(x, h0, z)

    def _kamera(self, dt):
        y, p = math.radians(self.yaw), math.radians(self.pitch)
        fram = Vec3(math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p))
        oga = self.pos + Vec3(0, 1.72, 0)
        ute = self.zon == 'ute'
        if self.i_rover:
            kam = self.pos + Vec3(0, 2.6, 0) - fram * 10.5
            kam.y = max(kam.y, hojd(kam.x, kam.z) + .6)
        elif self.tredje:
            kam = oga - fram * 4.6 + Vec3(0, .5, 0)
            if ute:
                kam.y = max(kam.y, hojd(kam.x, kam.z) + .4)
            else:
                c, bx, bz = (HAB_INNE, 7.7, 5.7) if self.zon == 'hab' else (RAKET_INNE, 3.3, 3.3)
                kam = Vec3(max(c.x - bx, min(c.x + bx, kam.x)), max(.3, min(3.0, kam.y)), max(c.z - bz, min(c.z + bz, kam.z)))
        else:
            kam = oga
        if self.skak > 0:
            self.skak -= dt
            kam += Vec3(random.uniform(-1, 1), random.uniform(-1, 1), 0) * self.skak * .25
        camera.position = kam
        camera.rotation = (self.pitch, self.yaw, 0)
        fig = self.mark_fig
        pa(fig, self.tredje and not self.i_rover)
        if fig.enabled:
            fig.position, fig.rotation_y = self.pos, self.yaw
            modeller.ga(fig, self.gafas, 1 if self.ror_sig else 0)
        pa(self.borr, ute and not self.tredje and not self.i_rover)
        pa(self.sikte, ute and not self.i_rover)

    # ---- väder ---------------------------------------------------------------
    def _vader(self, dt):
        if self.storm_slut == 0 and self.t >= self.nasta_storm:
            self.storm_slut = self.t + self.slump.uniform(55, 85)
            self.sag('SANDSTORM! Ta skydd i basen eller rovern!', 8)
        if self.storm_slut > 0:
            in_, ut = self.t - self.nasta_storm, self.storm_slut - self.t
            self.storm = max(0.0, min(1.0, in_ / 8, ut / 8))
            if ut <= 0:
                self.storm, self.storm_slut = 0.0, 0
                self.nasta_storm = self.t + self.slump.uniform(170, 290)
                self.sag('Stormen har dragit förbi.', 5)
        elif self.nasta_storm - self.t < 60 and not self.varnat.get(self.nasta_storm):
            self.varnat[self.nasta_storm] = True
            self.sag('Varning: sandstorm närmar sig från väster. Framme om en minut!', 8)

    # ---- robotarna -----------------------------------------------------------
    def _robotar(self, dt):
        ute = self.zon == 'ute'
        if ute:
            ax, az, ayaw = self.pos.x, self.pos.z, self.yaw
        elif self.zon == 'hab':
            ax, az, ayaw = 0, -16, 180
        else:
            ax, az, ayaw = RAKET[0], RAKET[1] - 8, 180
        foljare = [r for r in self.robotar if r.raddad]
        n = len(foljare)
        for i, r in enumerate(foljare):
            r.cd -= dt
            v = math.radians(ayaw + 180 + (i - (n - 1) / 2) * 38)
            avst = 4.5 + (i % 2) * 2.5 + (2 if self.i_rover else 0)
            mx, mz = ax + math.sin(v) * avst, az + math.cos(v) * avst
            fiende = None
            if r.namn in KRIGARE:
                nara = 38.0
                for m in self.martianer:
                    d = math.hypot(m.px - r.px, m.pz - r.pz)
                    if m.dod <= 0 and d < nara:
                        nara, fiende = d, m
                if fiende:
                    mx, mz = fiende.px, fiende.pz
                    if nara < 9 and r.cd <= 0:
                        r.cd = KRIGARE[r.namn]
                        self._strale(Vec3(r.px, r.y + r.hojd * .8, r.pz), Vec3(fiende.px, fiende.y + 1.4, fiende.pz),
                                     color.rgba(.3, .9, 1, 1))
                        self._skada(fiende, 1)
            dx, dz = mx - r.px, mz - r.pz
            d = math.hypot(dx, dz)
            stopp = 5 if fiende else 1.2
            fart = 0
            if d > stopp:
                fart = min((d - stopp) * 2 + 1, 32 if d > 60 else 22 if d > 22 else 10)
                if r.namn == 'Lupus':
                    fart *= 1.4
                r.px += dx / d * fart * dt
                r.pz += dz / d * fart * dt
                r.px, r.pz = self._knuffa(r.px, r.pz, 1.0, self.hinder[:self.n_stora])
                r.setH(math.degrees(math.atan2(dx, dz)))
                r.fas += fart * dt * 1.3
            elif fiende:
                r.setH(math.degrees(math.atan2(dx, dz)))
            svavar = getattr(r, 'svavar', False)
            if fart or svavar or r.rorde:
                sv = .12 * math.sin(self.anim * 2 + i) + .15 if svavar else 0
                r.setPos(r.px, hojd(r.px, r.pz) + sv, r.pz)
                modeller.ga(r, r.fas, min(1, fart / 4))
            r.rorde = fart > 0
        for r in self.robotar:
            pa(r.skylt, ute and math.hypot(r.px - self.pos.x, r.pz - self.pos.z) < 70)
            if not r.raddad:
                pa(r.ogon, math.sin(self.anim * 3 + r.fas) > .93)          # blinkar svagt till ibland

    # ---- martianerna ---------------------------------------------------------
    def _martianer(self, dt):
        sl = self.slump
        ute = self.zon == 'ute'
        natt = self._dag() < .4
        if self.t >= self.nasta_martian:
            self.nasta_martian = self.t + (sl.uniform(22, 38) if natt else sl.uniform(55, 85))
            if len(self.martianer) < min(7, 2 + self._sol()):
                ax, az = (self.pos.x, self.pos.z) if ute else HAB
                v, d = sl.uniform(0, math.tau), sl.uniform(75, 105)
                m = modeller.martian()
                m.px = max(-KANT, min(KANT, ax + math.cos(v) * d))
                m.pz = max(-KANT, min(KANT, az + math.sin(v) * d))
                m.hp, m.cd, m.fas, m.dod, m.blink, m.rod = 3, 1.0, 0.0, 0.0, 0.0, False
                tyst(m)
                self.martianer.append(m)
                if len(self.martianer) == 1 and not self.varnat.get('martian'):
                    self.varnat['martian'] = True
                    self.sag('Något rör sig därute... MARTIANER! Skjut med laserborren.', 9)
        for m in list(self.martianer):
            if m.dod > 0:                                # faller ihop
                m.dod += dt
                m.rotation_x = -min(90, m.dod * 220)
                m.y -= dt * .9
                if m.dod > 1.4:
                    self.martianer.remove(m)
                    destroy(m)
                continue
            m.cd -= dt
            m.blink -= dt
            if (m.blink > 0) != m.rod:
                m.rod = m.blink > 0
                m.ogon.color = color.rgba(1, .2, .1, 1) if m.rod else color.white
            jagar = ute and math.hypot(m.px - self.pos.x, m.pz - self.pos.z) < 150
            if jagar:
                mx, mz, stopp = self.pos.x, self.pos.z, (3.6 if self.i_rover else 1.5)
            else:
                d = math.hypot(m.px, m.pz) or 1
                mx, mz, stopp = m.px / d * 10.6, m.pz / d * 10.6, .6
            dx, dz = mx - m.px, mz - m.pz
            d = math.hypot(dx, dz) or .01
            fart = 0
            if d > stopp:
                fart = 5.6 if natt else 4.6
                m.px += dx / d * fart * dt
                m.pz += dz / d * fart * dt
                m.px, m.pz = self._knuffa(m.px, m.pz, .6, self.hinder[:self.n_stora])
                m.fas += fart * dt * 1.4
            elif m.cd <= 0:
                m.cd = 1.3
                m.fas += 2
                if not jagar:
                    self.bas -= 2
                    if not self.varnat.get('basattack', 0) > self.t:
                        self.varnat['basattack'] = self.t + 15
                        self.sag('Martianer river i basens skal! Jaga bort dem!', 6)
                elif self.i_rover:
                    self.rv['batteri'] = max(0, self.rv['batteri'] - 5)
                    self.skak = .3
                else:
                    self.drakt -= 7
                    self.skak, self.rod = .35, .5
            m.setH(math.degrees(math.atan2(dx, dz)))
            m.setPos(m.px, hojd(m.px, m.pz), m.pz)
            modeller.ga(m, m.fas, 1 if fart else .4)
            if fart == 0:
                for arm in m.armar:
                    arm.setP(-75 + 40 * math.sin(self.anim * 9))

    # ---- syre, mat, dräkt och bas -----------------------------------------
    def _overlevnad(self, dt):
        ute_till_fots = self.zon == 'ute' and not self.i_rover
        I = self.storm
        if ute_till_fots:
            spring = (held_keys['shift'] or held_keys['left shift']) and self.ror_sig
            self.syre -= dt * .42 * (1.6 if spring else 1)
            if I > .2:
                self.drakt -= dt * .7 * I
        elif self.i_rover:
            self.syre = min(100, self.syre + dt * 9)
        else:
            self.syre = min(100, self.syre + dt * 30)
        self.mat = max(0, self.mat - dt * 100 / 600)
        self.bas -= dt * (.012 + I * (.07 if self._har('Gorgo') else .14))
        if self._har('Bulten'):
            self.bas = min(100, self.bas + dt * .1)
            self.drakt = min(100, self.drakt + dt * .25)
        self.syre = max(0, self.syre)
        if self.syre <= 0:
            self.halsa -= dt * 9
        if self.mat <= 0:
            self.halsa -= dt * 1.5
        if self.syre > 0 and self.mat > 35:
            self.halsa = min(100, self.halsa + dt * 1.0)
        for r in self.odling:
            if r['lage'] == 'vaxer':
                r['prog'] += dt / self._vaxtid()
            if r['lage'] != 'tom':
                if r['prog'] >= 1:
                    r['prog'], r['lage'] = 1.0, 'klar'
                r['planta'].scale = .15 + .85 * r['prog']
        if self.bas <= 0:
            self.bas = 0
            self.do('Basens skal sprack och all luft försvann.')
        elif self.drakt <= 0 and self.zon == 'ute':
            self.drakt = 0
            self.do('Rymddräkten gick sönder ute på Mars.')
        elif self.halsa <= 0:
            self.do('Syret tog slut.' if self.syre <= 0 else 'Maten tog slut.')
        self.drakt = max(0, self.drakt)

    # ---- effekter: damm, strålar, delar ------------------------------------
    def _effekter(self, dt):
        I = self.storm if self.zon == 'ute' else 0
        ljus = .35 + .65 * self._dag()
        dammfarg = color.rgba(.8 * ljus, .5 * ljus, .28 * ljus, .2 * I)
        kam = camera.world_position
        for e in self.damm:
            pa(e, I > .02)
            if I > .02:
                e.rel += e.v * dt
                if e.rel.x > 20:
                    e.rel.x -= 40
                if e.rel.z > 20:
                    e.rel.z -= 40
                e.rel.y = max(-2, min(7, e.rel.y))
                e.setPos(kam.x + e.rel.x, kam.y + e.rel.y, kam.z + e.rel.z)
                e.color = dammfarg
        for e in self.stralar:
            if e.enabled:
                e.tid -= dt
                e.enabled = e.tid > 0
        if self.zon == 'ute':
            for d in self.delar:
                if not d.tagen:
                    d.setH(self.anim * 30)
                    if d.storm != self.storm:
                        d.storm = self.storm
                        d.strale.color = color.rgba(1, 1, 1, .35 * (1 - self.storm))
            pa(self.skepp.lampor, math.sin(self.anim * 7) > -.3 or math.sin(self.anim * 1.3) > .5)
        elif self.zon == 'hab':
            self.skarm_svep.setR((self.anim * 130) % 360)
        self.rod = max(0, self.rod - dt)
        a = self.rod * .7 + (.12 if self.halsa < 30 else 0)
        pa(self.rodskarm, a > 0)
        if a > 0:
            self.rodskarm.color = color.rgba(1, 0, 0, a)

    def _raketstart(self, dt):
        self.start_t += dt
        t = self.start_t
        stig = max(0, t - 3)
        self.raket.y = 1.6 * stig * stig
        self.raket.flamma.enabled = t > 2.4
        self.raket.flamma.scale_y = 1 + .15 * math.sin(t * 40)
        mal = Vec3(RAKET[0], 6 + self.raket.y * .85, RAKET[1])
        camera.position = Vec3(RAKET[0] - 24 + random.uniform(-1, 1) * (.12 if t > 2.4 else 0), 2.2, RAKET[1] - 30)
        camera.look_at(mal)
        if t < 3:
            self.satt(self.varning_start, str(3 - int(t)))
        else:
            self.satt(self.varning_start, '')
        if t > 12:
            self.lage = 'vinst'
            n = sum(1 for r in self.robotar if r.raddad)
            self.slutorsak = ('Raketen lyfte från Mars och Mark är på väg hem till jorden!\n'
                              + ('Alla sex robotarna från Daidalos följde med.' if n == 6 else
                                 f'{n} av Daidalos robotar följde med hem.' if n else 'Men robotarna från Daidalos blev kvar...'))
            self.visa_panel('vinst')
            mouse.locked = False

    # ---- vad kan man trycka E på just nu? ----------------------------------
    def _hitta_sak(self):
        self.prompt_sak = None
        if self.i_rover or self.panel_typ:
            return
        y = math.radians(self.yaw)
        fx, fz = math.sin(y), math.cos(y)
        bast = -9
        for s in self.saker:
            if not s.aktiv or s.zon != self.zon or s.pos is None:
                continue
            dx, dz = s.pos.x - self.pos.x, s.pos.z - self.pos.z
            d = math.hypot(dx, dz)
            if d > s.radie:
                continue
            rikt = (dx * fx + dz * fz) / (d or 1)
            if rikt < .15 and d > 1.4:
                continue
            p = rikt - d * .08
            if p > bast:
                bast, self.prompt_sak = p, s

    # ---- uppdatera instrumenten --------------------------------------------
    def _hud(self):
        varden = {'HÄLSA': self.halsa, 'SYRE': self.syre, 'DRÄKT': self.drakt, 'MAT': self.mat, 'BAS': self.bas,
                  'ROVER': self.rv['batteri']}
        blink = math.sin(self.anim * 10) > 0
        for namn, f in self.staplar.items():
            v = max(0, min(100, varden[namn]))
            f.scale_x = .2 * v / 100
            c = (1, .15, .1) if (v < 25 and blink) else f.bas
            f.color = color.rgba(c[0], c[1], c[2], 1)
        dag, I = self._dag(), self.storm
        self.satt(self.info, f'SOL {self._sol()}    {self._klocka()}\n'
                             f'Väder: {self._vader_text()}\n'
                             f'Temp: {int(-78 + 55 * dag - 12 * I)} °C\n'
                             f'Vind: {int(5 + 3 * math.sin(self.t * .05) + 30 * I)} m/s')
        self.satt(self.inv, (f'Matpaket   {self.matpaket}\nPotatis    {self.potatis}\nSkrot      {self.skrot}\n'
                         f'Raketdelar {len(self.delar_klara)}/6' + (f' (+{len(self.delar_burna)})' if self.delar_burna else '')
                         + f'\nRobotar    {sum(1 for r in self.robotar if r.raddad)}/6'))
        if len(self.delar_klara) == 6:
            self.satt(self.mal, 'UPPDRAG: Gå in i raketen och starta den!')
        elif self.delar_burna:
            self.satt(self.mal, 'UPPDRAG: Bär raketdelarna till raketen och installera dem')
        else:
            self.satt(self.mal, 'UPPDRAG: Hitta raketdelarna (gröna ljuspelare) och rädda robotarna')
        for m in self.medd:
            m[1] -= .12
        self.medd = [m for m in self.medd if m[1] > 0]
        self.satt(self.loggtext, '\n'.join(m[0] for m in self.medd))
        v = ''
        if blink:
            if self.syre < 22 and self.zon == 'ute':
                v = 'SYRET TAR SLUT!'
            elif self.drakt < 30:
                v = 'DRÄKTEN LÄCKER!'
            elif self.bas < 25:
                v = 'BASEN HÅLLER PÅ ATT SPRICKA!'
            elif I > .3 and self.zon == 'ute' and not self.i_rover:
                v = 'STORM! SÖK SKYDD!'
            elif self.mat < 12:
                v = 'DU SVÄLTER – ÄT NÅGOT!'
        self.satt(self.varning, v)
        self.prompt.y = -.36 if self.i_rover else -.17
        if self.i_rover:
            self.satt(self.prompt, f'[E] Kliv ur rovern      {int(abs(self.rv["fart"]) * 3.6)} km/h')
        elif self.prompt_sak and not self.panel_typ:
            self.satt(self.prompt, '[E] ' + self.prompt_sak.text())
        else:
            self.satt(self.prompt, '')
        # radarn
        px, pz = self.pos.x, self.pos.z
        if self.zon != 'ute':
            px, pz = (HAB[0], HAB[1] - 10) if self.zon == 'hab' else (RAKET[0], RAKET[1] - 4)
        minus = self._har('Minus')
        L = [(HAB[0] - px, HAB[1] - pz, color.white, .09, True),
             (RAKET[0] - px, RAKET[1] - pz, color.rgba(.3, .6, 1, 1), .08, True),
             (self.rv['x'] - px, self.rv['z'] - pz, color.rgba(.3, .6, 1, 1), .06, True)]
        if minus:
            L.append((SKEPP[0] - px, SKEPP[1] - pz, color.rgba(.8, .5, 1, 1), .08, True))
            L += [(d.x - px, d.z - pz, color.rgba(.3, 1, .4, 1), .07, True) for d in self.delar if not d.tagen]
            L += [(e.x - px, e.z - pz, color.rgba(1, .9, .4, 1), .04, False) for e in self.lador]
        L += [(m.px - px, m.pz - pz, color.rgba(1, .15, .1, 1), .07, False) for m in self.martianer if m.dod <= 0]
        for r in self.robotar:
            if r.raddad or blink:
                L.append((r.px - px, r.pz - pz, color.rgba(.4, .9, 1, 1), .055, False))
        self.radar.visa(L, self.yaw, self.anim)
        if self.panel_typ:
            self._panel_text()
            if self.panel_typ == 'radar':
                kvar = self.nasta_storm - self.t
                storm = None
                if I > 0:
                    storm = (0, 0, 1.0, .35 + .2 * math.sin(self.anim * 4))
                elif kvar < 150:
                    storm = (-kvar * 5 - 60, 40, .55, .5)
                L.append((0, 0, color.rgba(1, 1, 1, 1), .03, False))
                self.storradar.visa(L, 0, self.anim, storm)
        sol = 0 if I > .3 else int(100 * dag)
        if self.zon == 'hab':
            self.satt(self.vaggtext, f'SKAL    {int(self.bas):3d} %\nSYRE    {"OK" if self.bas > 25 else "LÄCKA"}\n'
                                     f'SOL-EL  {sol:3d} %\nVÄDER   {"STORM" if I > 0 else "KLART"}\n'
                                     f'SOL {self._sol()}  {self._klocka()}')
        elif self.zon == 'raket':
            self.satt(self.rakettext, f'DELAR INSTALLERADE  {len(self.delar_klara)} / 6\n\n'
                                      + ('KLAR FÖR START' if len(self.delar_klara) == 6 else 'KAN INTE STARTA'))


spel = Spel()
spel.varning_start = Text(parent=camera.ui, text='', origin=(0, 0), scale=6, color=color.white)
for _e in list(scene.entities):
    if not hasattr(_e, 'update'):
        _e.ignore = True
_motor = Entity()
_motor.update = spel.update
_motor.input = spel.input
