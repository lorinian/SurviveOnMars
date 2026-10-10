"""Alla figurer och byggnader, hopsatta av former från mesh_bygge."""
import math
from ursina import Entity, Text, color
from panda3d.core import TransparencyAttrib
from mesh_bygge import Bygge
from grafik import mars_shader, glow_shader

VIT = (.93, .93, .90, 1)
ORANGE = (.95, .42, .08, 1)
GRA = (.42, .43, .47, 1)
LJUSGRA = (.68, .69, .72, 1)
MORK = (.10, .10, .12, 1)
SOLBLA = (.07, .11, .38, 1)
GLAS = (.08, .14, .24, 1)
ODLING_X = (-7.05, -4.2)          # odlingslådornas platser inne i basen
ODLING_Z = (-4.2, -1.8, .6)


def ent(b, **kw):
    return Entity(model=b.mesh(), shader=mars_shader, **kw)


def glow(b, **kw):
    return Entity(model=b.mesh(), shader=glow_shader, **kw)


def genomskinlig(e):
    e.setTransparency(TransparencyAttrib.MAlpha)
    e.setDepthWrite(False)
    return e


def skylt(text, parent, pos, storlek=.25, roty=0, farg=color.white, billboard=False):
    t = Text(text=text, parent=parent, position=pos, rotation_y=roty, scale=storlek * 40,
             origin=(0, 0), color=farg)
    if billboard:
        t.billboard = True
    return t


def ga(fig, fas, styrka=1.0):
    """Gång-animation: svänger armar och ben."""
    s = math.sin(fas) * styrka
    for i, ben in enumerate(getattr(fig, 'ben', [])):
        ben.setP(s * fig.steg * (1 if i % 2 == 0 else -1))
    for i, arm in enumerate(getattr(fig, 'armar', [])):
        arm.setP(-s * fig.steg * .8 * (1 if i % 2 == 0 else -1) + fig.arm_vila)


# =============================================================================
# MARK WATNEY
# =============================================================================
def astronaut():
    rot = Entity()
    b = Bygge()
    b.lathe([(0, .93), (.22, .95), (.26, 1.12), (.30, 1.36), (.28, 1.50), (.15, 1.58), (0, 1.59)], VIT, scale=(1, 1, .78))
    b.sphere((0, .95, 0), (.25, .15, .2), VIT)
    b.lathe([(.265, 1.02), (.275, 1.08)], ORANGE, scale=(1, 1, .78), smooth=False)
    b.box((0, 1.28, -.29), (.48, .66, .24), LJUSGRA)                  # ryggsäck med syre
    b.box((0, 1.28, -.415), (.3, .5, .02), ORANGE)
    b.capsule((-.14, 1.0, -.44), (-.14, 1.5, -.44), .055, GRA)
    b.capsule((.14, 1.0, -.44), (.14, 1.5, -.44), .055, GRA)
    b.box((0, 1.30, .225), (.27, .19, .08), GRA)                       # bröstpanel
    b.box((-.07, 1.33, .27), (.04, .04, .02), (.9, .1, .1, 1))
    b.box((0, 1.33, .27), (.04, .04, .02), (.1, .9, .2, 1))
    b.box((.07, 1.33, .27), (.04, .04, .02), (.2, .5, 1, 1))
    b.box((0, 1.26, .27), (.18, .04, .02), MORK)
    b.cyl((0, 1.55, 0), (0, 1.63, 0), .18, GRA, seg=14)                # halsring
    b.sphere((0, 1.80, -.01), (.235, .24, .245), VIT, seg=16, ringar=10)   # hjälm
    b.sphere((0, 1.80, .075), (.19, .175, .185), (.50, .34, .08, 1), seg=16, ringar=10)  # guldvisir
    b.sphere((.07, 1.87, .22), (.05, .03, .02), (1, .9, .6, 1))        # reflex i visiret
    b.box((0, 2.0, .1), (.16, .05, .08), GRA)                          # hjälmlampa
    for sx in (-1, 1):
        b.sphere((sx * .34, 1.46, 0), .13, ORANGE)
    ent(b, parent=rot)

    def arm(sx):
        a = Bygge()
        a.capsule((0, 0, 0), (sx * .03, -.30, 0), .088, VIT)
        a.lathe([(.085, -.03), (.085, .03)], ORANGE, pos=(sx * .03, -.31, 0), smooth=False)
        a.capsule((sx * .03, -.31, 0), (sx * .04, -.58, .05), .076, VIT)
        a.sphere((sx * .04, -.67, .06), (.085, .095, .085), GRA)
        return ent(a, parent=rot, position=(sx * .37, 1.45, 0))

    def ben(sx):
        a = Bygge()
        a.capsule((0, 0, 0), (0, -.42, 0), .115, VIT)
        a.lathe([(.105, -.03), (.105, .03)], ORANGE, pos=(0, -.44, 0), smooth=False)
        a.capsule((0, -.44, 0), (0, -.80, 0), .098, VIT)
        a.box((0, -.87, .05), (.21, .15, .36), GRA)
        a.box((0, -.94, .05), (.23, .04, .38), MORK)
        return ent(a, parent=rot, position=(sx * .14, .95, 0))

    rot.armar = [arm(-1), arm(1)]
    rot.ben = [ben(-1), ben(1)]
    rot.steg, rot.arm_vila = 32, 0
    return rot


def laserborr():
    """Verktyget Mark håller i – en laserborr som också funkar mot martianer."""
    b = Bygge()
    b.box((0, 0, 0), (.09, .11, .42), GRA)
    b.cyl((0, .01, .2), (0, .01, .48), .028, MORK)
    b.box((0, -.11, -.1), (.06, .16, .08), MORK, rot=(15, 0, 0))
    b.box((0, .07, -.02), (.05, .03, .2), ORANGE)
    e = ent(b)
    g = Bygge()
    g.sphere((0, .01, .49), .02, (1, .2, .1, 1))
    g.box((0, .09, -.02), (.03, .012, .1), (.2, 1, .4, 1))
    glow(g, parent=e)
    return e


# =============================================================================
# MARTIAN
# =============================================================================
def martian():
    H = (.50, .62, .42, 1)
    M = (.33, .42, .29, 1)
    L = (.62, .70, .50, 1)
    rot = Entity()
    b = Bygge()
    b.lathe([(0, 1.02), (.15, 1.05), (.17, 1.25), (.25, 1.58), (.21, 1.74), (.08, 1.82), (0, 1.83)], H, scale=(1, 1, .68))
    for i in range(4):                                                   # revben
        b.lathe([(.175 + i * .022, 1.2 + i * .1), (.19 + i * .022, 1.23 + i * .1), (.175 + i * .022, 1.26 + i * .1)], M,
                scale=(1, 1, .7))
    b.sphere((0, 1.04, 0), (.2, .13, .15), M)
    b.capsule((0, 1.8, 0), (0, 2.0, .03), .055, M)
    b.sphere((0, 2.2, -.06), (.23, .25, .31), H, seg=14, ringar=9)       # stor skalle
    b.sphere((0, 2.06, .1), (.13, .13, .15), L)                          # käke
    b.sphere((0, 2.30, -.2), (.17, .15, .22), M)
    b.box((0, 1.99, .2), (.09, .012, .03), MORK)                         # mun
    for i in range(5):                                                   # taggar längs ryggen
        b.cyl((0, 1.25 + i * .12, -.14 - .02 * math.sin(i)), (0, 1.33 + i * .12, -.27), .035, M, r1=0, seg=5)
    ent(b, parent=rot)
    o = Bygge()
    for sx in (-1, 1):
        o.sphere((sx * .105, 2.15, .19), (.075, .1, .05), (.75, 1, .25, 1), rot=(0, sx * 25, sx * 18))
    rot.ogon = glow(o, parent=rot)

    def arm(sx):
        a = Bygge()
        a.sphere((0, 0, 0), .085, M)
        a.capsule((0, 0, 0), (sx * .06, -.5, -.02), .05, H)
        a.capsule((sx * .06, -.5, -.02), (sx * .04, -.98, .14), .04, H)
        for k in (-1, 0, 1):                                             # tre klor
            a.cyl((sx * .04, -.98, .14), (sx * .04 + k * .06, -1.18, .22), .02, MORK, r1=0, seg=5)
        return ent(a, parent=rot, position=(sx * .29, 1.68, 0))

    def ben(sx):
        a = Bygge()
        a.capsule((0, 0, 0), (0, -.5, .14), .075, H)
        a.capsule((0, -.5, .14), (0, -.93, -.05), .05, H)
        a.capsule((0, -.93, -.05), (0, -.99, .2), .05, M)
        return ent(a, parent=rot, position=(sx * .12, 1.03, 0))

    rot.armar = [arm(-1), arm(1)]
    rot.ben = [ben(-1), ben(1)]
    rot.steg, rot.arm_vila = 38, -35
    return rot


# =============================================================================
# DAIDALOS ROBOTAR
# =============================================================================
def _robot(namn, hojd):
    rot = Entity()
    rot.namn, rot.hojd = namn, hojd
    rot.ben, rot.armar, rot.steg, rot.arm_vila = [], [], 30, 0
    rot.skylt = skylt(namn, rot, (0, hojd + .3, 0), .15, farg=color.rgba(.6, .9, 1, 1), billboard=True)
    return rot


def robot_minus():
    B, V = (.16, .42, .92, 1), (.9, .92, .95, 1)
    r = _robot('Minus', 1.2)
    b = Bygge()
    b.sphere((0, .5, 0), .33, B, seg=14, ringar=9)
    b.lathe([(.335, .44), (.345, .5), (.335, .56)], V, seg=14)
    b.cyl((-.13, .17, 0), (.13, .17, 0), .17, MORK, seg=12)             # hjul
    b.cyl((-.15, .17, 0), (.15, .17, 0), .08, LJUSGRA, seg=8)
    b.lathe([(.22, .78), (.22, .86), (.17, .97), (0, 1.02)], V, seg=12)  # huvud
    b.cyl((0, .7, 0), (0, .8, 0), .12, GRA)
    b.cyl((.08, 1.0, -.05), (.1, 1.28, -.08), .012, GRA, seg=5)
    b.box((0, .5, .31), (.2, .12, .05), MORK)
    ent(b, parent=r)
    for sx in (-1, 1):
        a = Bygge()
        a.capsule((0, 0, 0), (sx * .05, -.2, .08), .04, GRA)
        a.sphere((sx * .05, -.24, .1), .055, V)
        r.armar.append(ent(a, parent=r, position=(sx * .35, .55, 0)))
    g = Bygge()
    g.sphere((0, .87, .18), (.1, .1, .05), (.3, .95, 1, 1))
    g.sphere((.1, 1.29, -.08), .03, (1, .2, .2, 1))
    r.ogon = glow(g, parent=r)
    return r


def robot_bulten():
    G, S = (.95, .72, .08, 1), (.6, .62, .66, 1)
    r = _robot('Bulten', 1.55)
    b = Bygge()
    for i in range(5):                                                   # gängad kropp
        b.lathe([(.2, .3 + i * .07), (.25, .335 + i * .07), (.2, .37 + i * .07)], S, seg=12, smooth=False)
    b.lathe([(0, .64), (.36, .64), (.36, 1.1), (0, 1.1)], G, seg=6, smooth=False)       # sexkantig kropp
    b.lathe([(0, 1.1), (.46, 1.1), (.46, 1.32), (.3, 1.4), (0, 1.4)], S, seg=6, smooth=False)  # skalle som en mutter
    b.box((0, .9, .32), (.3, .16, .04), MORK)
    b.box((0, 1.46, 0), (.06, .12, .5), S)                               # skåra i huvudet
    ent(b, parent=r)
    for sx in (-1, 1):
        a = Bygge()
        a.sphere((0, 0, 0), .09, S)
        a.capsule((0, 0, 0), (sx * .08, -.3, .05), .055, G)
        a.capsule((sx * .08, -.3, .05), (sx * .08, -.5, .25), .045, S)
        if sx == 1:                                                      # skiftnyckel
            a.box((.08, -.52, .42), (.05, .05, .3), S)
            a.box((.08, -.52, .6), (.05, .16, .08), S)
        else:
            a.sphere((-.08, -.52, .29), .07, MORK)
        r.armar.append(ent(a, parent=r, position=(sx * .42, 1.0, 0)))
        l = Bygge()
        l.capsule((0, 0, 0), (0, -.2, 0), .07, S)
        l.box((0, -.25, .05), (.16, .1, .28), MORK)
        r.ben.append(ent(l, parent=r, position=(sx * .14, .3, 0)))
    g = Bygge()
    for sx in (-1, 1):
        g.sphere((sx * .12, 1.21, .4), (.07, .06, .03), (1, .95, .5, 1))
    r.ogon = glow(g, parent=r)
    return r


def robot_taurus():
    R, D, V = (.72, .10, .08, 1), (.16, .16, .19, 1), (.92, .9, .84, 1)
    r = _robot('Taurus', 2.75)
    b = Bygge()
    b.lathe([(0, 1.25), (.42, 1.3), (.62, 1.75), (.72, 2.1), (.5, 2.3), (0, 2.34)], R, seg=10, scale=(1, 1, .7))
    b.lathe([(0, .95), (.3, .98), (.36, 1.3), (0, 1.32)], D, seg=10, scale=(1, 1, .8))
    b.sphere((0, 1.0, 0), (.4, .2, .3), R)
    b.box((0, 1.85, .43), (.6, .35, .06), D)                             # bröstplåt
    b.sphere((0, 2.42, .2), (.25, .23, .3), R, seg=10)                   # tjurhuvud
    b.box((0, 2.33, .5), (.22, .16, .16), D)                             # nos
    b.lathe([(.05, 0), (.065, .02), (.05, .04)], (.9, .75, .2, 1), pos=(0, 2.24, .57), seg=8, rot=(90, 0, 0))  # nosring
    for sx in (-1, 1):                                                   # horn
        b.tube([(sx * .2, 2.5, .15), (sx * .45, 2.58, .2), (sx * .62, 2.75, .28), (sx * .64, 2.95, .34)], .07, V, r_slut=.01)
        b.sphere((sx * .78, 2.12, 0), .27, D)                            # axlar
    ent(b, parent=r)
    for sx in (-1, 1):
        a = Bygge()
        a.capsule((0, 0, 0), (sx * .1, -.55, 0), .16, R)
        a.capsule((sx * .1, -.6, 0), (sx * .1, -1.05, .12), .19, D)
        a.sphere((sx * .1, -1.2, .14), (.22, .2, .22), R)
        r.armar.append(ent(a, parent=r, position=(sx * .82, 2.1, 0)))
        l = Bygge()
        l.capsule((0, 0, 0), (0, -.42, .04), .17, D)
        l.capsule((0, -.45, .04), (0, -.8, 0), .15, R)
        l.box((0, -.9, .08), (.34, .2, .5), D)
        r.ben.append(ent(l, parent=r, position=(sx * .27, 1.0, 0)))
    g = Bygge()
    for sx in (-1, 1):
        g.sphere((sx * .12, 2.47, .46), (.06, .035, .03), (1, .55, .1, 1))
    g.box((0, 1.85, .465), (.3, .06, .02), (1, .4, .1, 1))
    r.ogon = glow(g, parent=r)
    r.steg = 26
    return r


def robot_kamina():
    V, T = (.95, .95, .97, 1), (.08, .72, .68, 1)
    r = _robot('Kamina', 2.15)
    b = Bygge()
    b.lathe([(0, .28), (.08, .3), (.2, .6), (.3, .95), (.24, 1.08), (0, 1.1)], V, seg=14)        # svävande kjol
    b.lathe([(.205, .6), (.305, .95)], T, seg=14)
    b.lathe([(0, 1.08), (.13, 1.1), (.2, 1.42), (.22, 1.55), (.1, 1.64), (0, 1.65)], V, seg=12, scale=(1, 1, .75))
    b.lathe([(.14, 1.12), (.16, 1.2)], T, seg=12, scale=(1, 1, .75))
    b.capsule((0, 1.62, 0), (0, 1.72, 0), .05, GRA)
    b.sphere((0, 1.88, 0), (.17, .2, .19), V, seg=14, ringar=9)
    b.tube([(0, 2.05, -.05), (0, 2.12, -.2), (0, 2.0, -.36)], .05, T, r_slut=.02)     # "hästsvans"
    ent(b, parent=r)
    for sx in (-1, 1):
        a = Bygge()
        a.sphere((0, 0, 0), .07, T)
        a.capsule((0, 0, 0), (sx * .06, -.36, 0), .04, V)
        a.capsule((sx * .06, -.36, 0), (sx * .05, -.68, .1), .033, V)
        a.sphere((sx * .05, -.73, .11), .045, T)
        r.armar.append(ent(a, parent=r, position=(sx * .25, 1.5, 0)))
    g = Bygge()
    g.lathe([(.172, 1.86), (.176, 1.93)], (.3, 1, .95, 1), seg=14)       # lysande visir
    g.lathe([(.02, .2), (.2, .22)], (.3, 1, .95, 1), seg=14)             # svävarring
    g.sphere((0, 1.35, .17), (.04, .04, .02), (.3, 1, .95, 1))
    r.ogon = glow(g, parent=r)
    r.svavar = True
    return r


def robot_lupus():
    S, D = (.50, .53, .60, 1), (.17, .18, .22, 1)
    r = _robot('Lupus', 1.5)
    b = Bygge()
    b.capsule((0, .82, -.45), (0, .88, .42), .21, S, seg=12, r1=.25)
    b.capsule((0, .82, -.45), (0, .8, -.1), .16, D)
    b.capsule((0, .95, .5), (0, 1.15, .72), .13, D)
    b.sphere((0, 1.2, .8), (.16, .15, .2), S)
    b.capsule((0, 1.15, .9), (0, 1.1, 1.14), .085, S, r1=.06)
    b.sphere((0, 1.11, 1.2), .04, MORK)
    b.box((0, 1.06, 1.02), (.1, .02, .22), D)                            # käke
    for sx in (-1, 1):
        b.cyl((sx * .1, 1.3, .72), (sx * .13, 1.5, .68), .06, D, r1=0, seg=5)   # öron
    b.tube([(0, .9, -.6), (0, 1.0, -.85), (0, 1.18, -1.05)], .07, S, r_slut=.02)    # svans
    for i in range(4):
        b.box((0, 1.08, -.3 + i * .2), (.05, .06, .12), D)               # ryggplåtar
    ent(b, parent=r)
    for sz in (.4, -.42):
        for sx in (-1, 1):
            l = Bygge()
            l.sphere((0, 0, 0), .1, D)
            l.capsule((0, 0, 0), (0, -.38, -.07), .07, S)
            l.capsule((0, -.38, -.07), (0, -.72, .03), .048, D)
            l.sphere((0, -.76, .06), (.07, .05, .1), S)
            r.ben.append(ent(l, parent=r, position=(sx * .2, .8, sz)))
    r.ben = [r.ben[0], r.ben[1], r.ben[3], r.ben[2]]                     # diagonal trav
    g = Bygge()
    for sx in (-1, 1):
        g.sphere((sx * .09, 1.24, .96), (.035, .025, .03), (1, .15, .1, 1))
    r.ogon = glow(g, parent=r)
    r.steg = 34
    return r


def robot_gorgo():
    G, D, M = (.13, .34, .19, 1), (.10, .10, .12, 1), (.5, .52, .5, 1)
    r = _robot('Gorgo', 2.9)
    b = Bygge()
    for sx in (-1, 1):                                                   # larvband
        b.box((sx * .72, .32, 0), (.42, .5, 1.3), D)
        b.cyl((sx * .93, .32, .65), (sx * .51, .32, .65), .25, D, seg=10)
        b.cyl((sx * .93, .32, -.65), (sx * .51, .32, -.65), .25, D, seg=10)
        for k in (-.5, 0, .5):
            b.cyl((sx * .95, .32, k), (sx * .93, .32, k), .15, M, seg=8)
    b.lathe([(0, .45), (.62, .5), (.8, 1.1), (.72, 1.6), (.45, 1.85), (0, 1.9)], G, seg=8)
    b.lathe([(.8, 1.05), (.84, 1.12), (.8, 1.19)], M, seg=8)
    b.sphere((0, 2.05, 0), (.4, .36, .4), G, seg=12)
    b.box((0, 1.3, .72), (.5, .5, .08), D)
    orm = []
    for i in range(7):                                                   # "ormar" på huvudet, som Gorgon
        a = math.radians(-90 + i * 30)
        cx, cz = math.cos(a), -.12
        sy = math.sin(a) * -1
        p = [(cx * .3, 2.2 + sy * .1, cz), (cx * .55, 2.45 + sy * .2, cz - .1), (cx * .7, 2.75 + sy * .1, cz + .12),
             (cx * .62, 2.92 + sy * .05, cz + .32)]
        b.tube(p, .055, D, r_slut=.035, seg=6)
        orm.append(p[-1])
    ent(b, parent=r)
    for sx in (-1, 1):
        a = Bygge()
        a.sphere((0, 0, 0), .2, D)
        a.capsule((0, 0, 0), (sx * .15, -.5, .1), .14, G)
        a.capsule((sx * .15, -.5, .1), (sx * .15, -.75, .6), .12, D)
        a.box((sx * .15 - .09, -.78, .85), (.06, .16, .4), M, rot=(0, -12, 0))     # klo
        a.box((sx * .15 + .09, -.78, .85), (.06, .16, .4), M, rot=(0, 12, 0))
        r.armar.append(ent(a, parent=r, position=(sx * .85, 1.55, 0)))
    g = Bygge()
    for p in orm:
        g.sphere(p, .05, (.4, 1, .3, 1))
    for x in (-.17, 0, .17):
        g.sphere((x, 2.1, .37), (.06, .05, .03), (1, .9, .2, 1))
    r.ogon = glow(g, parent=r)
    r.steg = 14
    return r


ROBOTAR = [robot_minus, robot_bulten, robot_taurus, robot_kamina, robot_lupus, robot_gorgo]


# =============================================================================
# RYMDBASEN (HAB) – UTSIDAN
# =============================================================================
def hab_ute():
    DUK = (.90, .88, .83, 1)
    rot = Entity()
    b = Bygge()
    b.lathe([(9.3, 0), (9.3, .35), (9.0, .35)], GRA, seg=28, smooth=False)
    b.lathe([(9, .3), (9, 2.3), (8.6, 3.5), (7, 4.7), (4, 5.45), (0, 5.7)], DUK, seg=28)
    b.lathe([(9.04, 1.9), (9.04, 2.25)], ORANGE, seg=28, smooth=False)
    for i in range(14):                                                  # spännband över duken
        a = 2 * math.pi * i / 14
        c, s = math.cos(a), math.sin(a)
        b.tube([(9.05 * c, 2.3, 9.05 * s), (8.65 * c, 3.5, 8.65 * s), (7.05 * c, 4.72, 7.05 * s), (4.05 * c, 5.48, 4.05 * s)],
               .07, LJUSGRA, seg=5)
    b.cyl((0, 5.6, 0), (0, 6.1, 0), .9, GRA, seg=12)
    # luftsluss mot söder
    b.cyl((0, 1.25, -8.2), (0, 1.25, -12), 1.75, DUK, seg=18)
    b.lathe([(1.8, 0), (1.9, .2), (1.8, .4)], ORANGE, pos=(0, 1.25, -12), seg=18, rot=(90, 0, 0))
    b.box((0, 1.15, -12.03), (1.25, 2.1, .1), GRA)
    b.box((0, 1.5, -12.09), (.5, .4, .04), GLAS)
    b.box((.45, 1.1, -12.1), (.08, .3, .06), ORANGE)
    b.box((0, .06, -13.2), (2.4, .12, 2.4), GRA)                         # ramp
    # tankar och rör
    for i in range(3):
        b.capsule((10.6, .8, 2 + i * 1.7), (10.6, 3.0, 2 + i * 1.7), .7, LJUSGRA, seg=12)
        b.lathe([(.72, 1.8), (.72, 2.0)], ORANGE, pos=(10.6, 0, 2 + i * 1.7), smooth=False)
    b.tube([(10.6, 3.6, 2), (10.6, 4.1, 3.7), (9.5, 4.1, 3.7), (8.2, 3.9, 3.2)], .12, GRA)
    b.box((-10.6, .9, -3), (1.6, 1.8, 2.6), LJUSGRA)                     # generator
    b.box((-10.6, 1.95, -3), (1.7, .12, 2.7), GRA)
    # antennmast med parabol
    b.cyl((-7.5, 0, 6.5), (-7.5, 9, 6.5), .12, GRA)
    b.lathe([(0, 0), (.7, .12), (1.3, .45), (1.6, .9)], VIT, pos=(-7.5, 9, 6.5), seg=14, rot=(-50, 30, 0))
    b.cyl((-7.5, 9, 6.5), (-7.1, 9.9, 7.3), .04, GRA)
    # solpaneler
    for ix in range(4):
        for iz in range(2):
            x, z = -18 - ix * 4.6, 6 + iz * 5
            b.box((x, 1.5, z), (4.2, .1, 2.8), SOLBLA, rot=(-28, 0, 0))
            b.box((x, 1.47, z), (4.35, .06, 2.95), LJUSGRA, rot=(-28, 0, 0))
            b.cyl((x - 1.5, 0, z), (x - 1.5, 1.4, z), .07, GRA)
            b.cyl((x + 1.5, 0, z), (x + 1.5, 1.4, z), .07, GRA)
    ent(b, parent=rot)
    g = Bygge()
    for a in (35, 75, 145, 215, 255, 325):                               # upplysta fönster
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        g.sphere((8.85 * c, 2.9, 8.85 * s), (.55, .4, .55), (1, .85, .5, 1))
    g.sphere((0, 2.75, -12.1), .14, (.2, 1, .3, 1))
    g.sphere((-7.5, 9.1, 6.5), .1, (1, .15, .1, 1))
    glow(g, parent=rot)
    return rot


# =============================================================================
# RYMDBASEN – INSIDAN (rum 16 x 12 meter)
# =============================================================================
def hab_inne(panel_tex):
    VAGG, GOLV = (.84, .85, .87, 1), (.47, .49, .53, 1)
    rot = Entity()
    b = Bygge()
    b.box((0, -.1, 0), (16, .2, 12), GOLV)
    for i in range(-7, 8, 2):
        b.box((i, .003, 0), (.05, .01, 12), (.36, .38, .41, 1))
    for i in range(-5, 6, 2):
        b.box((0, .003, i), (16, .01, .05), (.36, .38, .41, 1))
    b.box((0, 3.7, 0), (16, .2, 12), (.78, .79, .8, 1))
    b.box((0, 1.8, 6.1), (16, 3.6, .2), VAGG)
    b.box((0, 1.8, -6.1), (16, 3.6, .2), VAGG)
    b.box((8.1, 1.8, 0), (.2, 3.6, 12), VAGG)
    b.box((-8.1, 1.8, 0), (.2, 3.6, 12), VAGG)
    for x in range(-8, 9, 2):                                            # väggribbor
        b.box((x, 1.8, 5.96), (.14, 3.6, .1), LJUSGRA)
        b.box((x, 1.8, -5.96), (.14, 3.6, .1), LJUSGRA)
    for z in range(-6, 7, 2):
        b.box((7.96, 1.8, z), (.1, 3.6, .14), LJUSGRA)
        b.box((-7.96, 1.8, z), (.1, 3.6, .14), LJUSGRA)
    b.box((0, .25, 5.95), (16, .5, .12), GRA)
    b.box((0, .25, -5.95), (16, .5, .12), GRA)
    b.box((0, 3.3, 0), (16, .2, .2), LJUSGRA)                            # takbalk
    # luftsluss (söder)
    b.box((0, 1.25, -5.9), (2.2, 2.6, .25), ORANGE)
    b.box((0, 1.15, -5.8), (1.5, 2.3, .2), GRA)
    b.box((0, 1.6, -5.68), (.6, .45, .04), GLAS)
    b.cyl((.5, 1.1, -5.7), (.5, 1.1, -5.6), .12, MORK)
    # väderradar-konsol (norr)
    b.box((0, .5, 5.2), (3.6, 1.0, 1.3), (.25, .27, .31, 1))
    b.box((0, 1.05, 5.0), (3.4, .12, .8), (.16, .17, .2, 1), rot=(-18, 0, 0))
    b.box((0, 2.2, 5.92), (3.0, 2.3, .14), MORK)
    for i in range(8):
        b.box((-1.4 + i * .4, 1.13, 4.95), (.22, .05, .14),
              [(.9, .2, .1, 1), (.2, .8, .3, 1), (.9, .8, .2, 1), (.2, .5, .9, 1)][i % 4], rot=(-18, 0, 0))
    b.cyl((0, 0, 3.9), (0, .55, 3.9), .22, GRA)                          # stol
    b.cyl((0, .55, 3.9), (0, .68, 3.9), .34, (.2, .3, .6, 1), seg=12)
    # basstatus + verkstad (öster)
    b.box((7.92, 2.0, 2.6), (.12, 1.8, 2.8), MORK)
    b.box((7.2, .5, -1.6), (1.4, 1.0, 3.0), (.5, .42, .3, 1))
    b.box((7.2, 1.03, -1.6), (1.5, .08, 3.1), GRA)
    b.box((7.85, 1.9, -1.6), (.1, 1.3, 2.8), (.55, .56, .6, 1))
    for i, z in enumerate((-2.6, -2.0, -1.3, -.7)):                      # verktyg på väggen
        b.box((7.75, 1.9, z), (.05, .7 - i * .1, .1), [ORANGE, LJUSGRA, (.8, .1, .1, 1), LJUSGRA][i])
    b.box((7.1, 1.2, -2.3), (.5, .25, .4), (.8, .1, .1, 1))
    b.cyl((7.1, 1.07, -1.1), (7.1, 1.4, -1.1), .13, (.2, .5, .9, 1))
    # matförråd (nordost)
    b.box((5.6, 1.1, 5.4), (2.6, 2.2, 1.0), VIT)
    b.box((5.6, 1.1, 4.88), (.06, 2.1, .04), GRA)
    b.box((5.6, 2.3, 5.4), (2.7, .12, 1.1), ORANGE)
    for sx in (-.25, .25):
        b.box((5.6 + sx, 1.2, 4.86), (.06, .4, .06), GRA)
    for i in range(3):
        b.box((3.6 + i * .05, .3 + i * .6, 5.4), (.9, .58, .9), [VIT, ORANGE, VIT][i])     # matlådor
    # säng (sydost)
    b.box((5.9, .3, -4.9), (2.4, .5, 1.3), LJUSGRA)
    b.box((5.9, .6, -4.9), (2.3, .16, 1.2), (.2, .32, .62, 1))
    b.box((6.8, .72, -4.9), (.5, .14, .9), VIT)
    b.box((7.2, .9, -4.9), (.12, 1.2, 1.4), GRA)
    # syregenerator (nordväst)
    b.capsule((-6.8, .7, 4.9), (-6.8, 2.5, 4.9), .7, LJUSGRA, seg=14)
    b.lathe([(.72, 1.4), (.72, 1.65)], (.2, .5, .9, 1), pos=(-6.8, 0, 4.9), smooth=False, seg=14)
    b.tube([(-6.8, 3.1, 4.9), (-6.8, 3.4, 4.9), (-5, 3.4, 4.9), (-5, 3.4, 2)], .09, GRA)
    b.box((-5.4, .6, 5.3), (1.0, 1.2, .9), GRA)
    # potatisodling (väster): 6 lådor
    for ix, x in enumerate(ODLING_X):
        for iz, z in enumerate(ODLING_Z):
            b.box((x, .35, z), (1.6, .7, 1.9), LJUSGRA)
            b.box((x, .72, z), (1.45, .06, 1.75), (.25, .16, .1, 1))
            for dx in (-.75, .75):
                b.cyl((x + dx, .7, z - .9), (x + dx, 2.3, z - .9), .03, GRA, seg=5)
            b.box((x, 2.3, z - .9), (1.6, .06, .06), GRA)
            b.box((x, 2.3, z), (1.5, .06, .5), GRA)
    # fönsterramar (söder)
    for x in (-4.5, 4.5):
        b.box((x, 2.0, -5.94), (2.6, 1.5, .1), GRA)
    e = ent(b, parent=rot)
    e.texture = panel_tex
    g = Bygge()
    for x in (-4, 4):
        for z in (-3, 3):
            g.box((x, 3.58, z), (2.4, .05, .5), (1, 1, .95, 1))          # taklampor
    for x in ODLING_X:
        for z in ODLING_Z:
            g.box((x, 2.26, z), (1.3, .03, .4), (1, .45, .95, 1))        # växtlampor
    g.box((0, 2.75, -5.75), (.9, .14, .04), (.2, 1, .3, 1))
    g.sphere((-6.8, 1.52, 4.19), .07, (.3, 1, .5, 1))
    glow(g, parent=rot)
    rot.radarskarm = (0, 2.2, 5.84)
    rot.fonster = []
    for x in (-4.5, 4.5):
        f = Bygge()
        f.box((x, 2.0, -5.9), (2.3, 1.2, .06), (1, 1, 1, 1))
        rot.fonster.append(glow(f, parent=rot))
    skylt('VÄDERRADAR', rot, (0, 3.45, 5.8), .16, farg=color.rgba(.4, 1, .6, 1))
    skylt('BASSTATUS', rot, (7.84, 3.05, 2.6), .14, 90, color.rgba(.4, 1, .6, 1))
    skylt('VERKSTAD', rot, (7.78, 2.75, -1.6), .14, 90, color.rgba(1, .6, .2, 1))
    skylt('MATFÖRRÅD', rot, (5.6, 2.55, 4.85), .14, 0, color.rgba(1, .6, .2, 1))
    skylt('POTATISODLING', rot, (-7.84, 3.05, -1.8), .16, -90, color.rgba(.5, 1, .4, 1))
    skylt('SYRE', rot, (-6.8, 3.0, 4.15), .14, 0, color.rgba(.5, .8, 1, 1))
    skylt('LUFTSLUSS', rot, (0, 3.0, -5.74), .14, 180, color.rgba(.3, 1, .4, 1))
    skylt('SOVPLATS', rot, (5.9, 2.2, -5.84), .14, 180, color.rgba(.6, .7, 1, 1))
    return rot


def potatisplanta():
    GR, GR2, ST = (.16, .5, .14, 1), (.24, .62, .18, 1), (.3, .45, .15, 1)
    b = Bygge()
    for i in range(9):
        a = i * 2.4
        rr = .18 + (i % 3) * .16
        x, z = math.cos(a) * rr, math.sin(a) * rr * 1.1
        h = .35 + (i % 4) * .1
        b.cyl((x * .5, 0, z * .5), (x, h, z), .02, ST, seg=4)
        b.sphere((x, h, z), (.17, .05, .12), GR if i % 2 else GR2, seg=6, ringar=4, rot=(0, math.degrees(a), 20))
        b.sphere((x * .8, h * .7, z * .8 + .08), (.12, .04, .1), GR2 if i % 2 else GR, seg=6, ringar=4, rot=(15, 40 * i, 0))
    for i in range(3):
        b.sphere((-.3 + i * .3, .03, .25 - i * .2), (.1, .07, .08), (.72, .58, .36, 1), seg=6, ringar=4)
    return ent(b)


# =============================================================================
# RAKETEN
# =============================================================================
def raket_ute():
    rot = Entity()
    b = Bygge()
    b.lathe([(0, 2.3), (2.5, 2.3), (2.9, 3.2), (2.75, 6.8), (2.05, 10.4), (1.25, 12.9), (.5, 14.2), (0, 14.5)], VIT, seg=18)
    b.lathe([(2.52, 2.3), (2.93, 3.2), (2.93, 3.5)], MORK, seg=18, smooth=False)
    b.lathe([(2.77, 6.6), (2.72, 7.0)], ORANGE, seg=18, smooth=False)
    b.lathe([(2.08, 10.3), (2.0, 10.7)], ORANGE, seg=18, smooth=False)
    b.lathe([(.5, 2.4), (.8, 1.6), (1.35, .85), (1.45, .7)], (.2, .2, .22, 1), seg=14)       # motor
    b.lathe([(1.45, .7), (1.3, .9), (.75, 1.65), (.45, 2.4)], (.3, .12, .05, 1), seg=14)     # insidan av munstycket
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.cyl((sx * 2.0, 3.6, sz * 2.0), (sx * 4.0, .15, sz * 4.0), .15, GRA)
            b.cyl((sx * 1.8, 2.4, sz * 1.8), (sx * 3.4, 1.2, sz * 3.4), .09, GRA)
            b.cyl((sx * 4.0, 0, sz * 4.0), (sx * 4.0, .15, sz * 4.0), .55, MORK, seg=10)
    for a in (0, 90, 180):                                               # fönster
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        b.sphere((2.3 * c, 9.2, 2.3 * s), (.42, .42, .42), GLAS)
    # lucka mot söder + stege
    b.box((0, 4.5, -2.9), (1.3, 2.0, .18), ORANGE)
    b.box((0, 4.5, -2.98), (1.05, 1.75, .12), GRA)
    b.box((0, 4.9, -3.05), (.4, .35, .04), GLAS)
    b.box((0, 3.45, -3.5), (1.5, .1, 1.3), GRA)                          # plattform
    for sx in (-.4, .4):
        b.cyl((sx, 0, -4.4), (sx, 3.5, -4.05), .045, LJUSGRA, seg=6)
    for i in range(9):
        b.cyl((-.4, .35 + i * .38, -4.36 + i * .038), (.4, .35 + i * .38, -4.36 + i * .038), .035, LJUSGRA, seg=6)
    # skador: sot och trasig plåt
    b.sphere((2.5, 5.2, 1.3), (.3, 1.1, .9), (.12, .1, .09, 1), rot=(0, -28, 0))
    b.sphere((-1.9, 8.2, 1.6), (.3, .8, .7), (.12, .1, .09, 1), rot=(0, 40, 0))
    b.box((-2.9, 4.6, .6), (.1, 1.4, 1.1), LJUSGRA, rot=(0, 0, 24))
    b.box((-2.75, 4.9, .6), (.1, .9, .8), MORK)
    ent(b, parent=rot)
    f = Bygge()
    f.lathe([(1.2, .8), (1.6, -1.5), (1.0, -6), (0, -11)], (1, .6, .15, 1), seg=12)
    f.lathe([(.7, .8), (.8, -1.5), (.4, -4), (0, -6.5)], (1, 1, .8, 1), seg=10)
    rot.flamma = glow(f, parent=rot, enabled=False)
    g = Bygge()
    g.sphere((0, 14.55, 0), .12, (1, .15, .1, 1))
    g.sphere((0, 5.75, -2.95), .12, (.2, 1, .3, 1))
    glow(g, parent=rot)
    return rot


def raket_inne(panel_tex):
    rot = Entity()
    b = Bygge()
    VAGG = (.8, .81, .84, 1)
    b.box((0, -.1, 0), (7, .2, 7), (.4, .42, .46, 1))
    b.box((0, 3.3, 0), (7, .2, 7), (.7, .7, .72, 1))
    b.box((0, 1.6, 3.6), (7, 3.2, .2), VAGG)
    b.box((0, 1.6, -3.6), (7, 3.2, .2), VAGG)
    b.box((3.6, 1.6, 0), (.2, 3.2, 7), VAGG)
    b.box((-3.6, 1.6, 0), (.2, 3.2, 7), VAGG)
    for k in (-3.45, 3.45):
        for j in (-2, 0, 2):
            b.box((k, 1.6, j), (.12, 3.2, .16), LJUSGRA)
            b.box((j, 1.6, k), (.16, 3.2, .12), LJUSGRA)
    b.box((0, 1.15, -3.42), (1.5, 2.3, .16), ORANGE)                     # lucka
    b.box((0, 1.1, -3.36), (1.2, 2.0, .14), GRA)
    b.box((0, .55, 2.9), (5.4, 1.1, 1.1), (.24, .26, .3, 1))             # instrumentbräda
    b.box((0, 1.2, 2.75), (5.2, .14, .9), (.15, .16, .19, 1), rot=(-20, 0, 0))
    b.box((0, 2.25, 3.44), (3.4, 1.7, .12), MORK)
    for i in range(12):
        b.box((-2.2 + i * .4, 1.3, 2.7), (.2, .05, .13),
              [(.9, .2, .1, 1), (.2, .8, .3, 1), (.9, .8, .2, 1), (.2, .5, .9, 1)][i % 4], rot=(-20, 0, 0))
    for sx in (-1.1, 1.1):                                               # stolar
        b.box((sx, .45, 1.3), (.8, .2, .8), (.2, .22, .28, 1))
        b.box((sx, 1.1, .92), (.8, 1.3, .18), (.2, .22, .28, 1), rot=(12, 0, 0))
        b.box((sx, 1.85, .78), (.4, .3, .16), ORANGE, rot=(12, 0, 0))
        b.cyl((sx, 0, 1.3), (sx, .4, 1.3), .15, GRA)
    b.box((-3.0, .5, -1.5), (.9, 1.0, 1.6), LJUSGRA)
    b.box((3.0, .9, -1.5), (.9, 1.8, 1.6), LJUSGRA)
    e = ent(b, parent=rot)
    e.texture = panel_tex
    g = Bygge()
    g.box((0, 3.18, 0), (3, .04, .5), (1, 1, .95, 1))
    g.box((-2.2, 2.3, 3.4), (.7, .5, .04), (.2, .8, 1, 1))
    g.box((2.2, 2.3, 3.4), (.7, .5, .04), (1, .6, .2, 1))
    glow(g, parent=rot)
    rot.fonster = []
    for sx in (-3.46, 3.46):
        f = Bygge()
        f.box((sx, 2.0, 1.0), (.05, .9, 1.6), (1, 1, 1, 1))
        rot.fonster.append(glow(f, parent=rot))
    skylt('ARES – RAKETENS DATOR', rot, (0, 3.02, 3.36), .13, farg=color.rgba(.4, 1, .6, 1))
    skylt('UTGÅNG', rot, (0, 2.65, -3.3), .13, 180, color.rgba(.3, 1, .4, 1))
    return rot


# =============================================================================
# ROVERN
# =============================================================================
def rover():
    rot = Entity()
    b = Bygge()
    b.box((0, .95, 0), (2.0, .3, 4.8), GRA)
    b.box((0, 1.75, .55), (2.1, 1.3, 2.7), VIT)
    b.sphere((0, 2.4, .55), (1.05, .28, 1.35), VIT)
    b.box((0, 1.25, .55), (2.14, .14, 2.74), ORANGE)
    b.box((0, 1.95, 1.93), (1.8, .75, .06), GLAS, rot=(-14, 0, 0))       # vindruta
    for sx in (-1, 1):
        b.box((sx * 1.06, 1.95, .9), (.04, .6, 1.3), GLAS)
        b.box((sx * 1.06, 1.75, -.35), (.05, 1.2, .7), LJUSGRA)          # dörr
    b.box((0, 1.45, -1.6), (1.9, .7, 1.5), LJUSGRA)                      # lastutrymme
    b.box((0, 1.85, -1.6), (1.7, .12, 1.3), ORANGE)
    b.capsule((-.5, 2.0, -1.2), (-.5, 2.0, -2.0), .25, VIT)              # syretank
    for sx in (-.9, .9):
        for sz in (-.5, 1.5):
            b.cyl((sx, 2.4, sz), (sx, 2.75, sz), .04, GRA, seg=5)
    b.box((0, 2.78, .5), (2.5, .07, 2.5), SOLBLA)                        # solpanel
    b.box((0, 2.75, .5), (2.6, .04, 2.6), LJUSGRA)
    b.cyl((.8, 2.0, -2.0), (.8, 3.6, -2.0), .04, GRA, seg=5)             # antenn
    b.lathe([(0, 0), (.25, .05), (.42, .2)], VIT, pos=(.8, 3.6, -2.0), rot=(-40, 0, 0), seg=10)
    b.box((0, 1.0, 2.45), (2.0, .25, .15), MORK)                         # stötfångare
    for sx in (-1, 1):
        for z in (1.7, 0, -1.7):
            b.cyl((sx * .9, .95, z), (sx * 1.25, .6, z), .08, GRA, seg=6)
    ent(b, parent=rot)
    g = Bygge()
    for sx in (-.7, .7):
        g.sphere((sx, 1.15, 2.42), (.16, .12, .06), (1, .95, .7, 1))
        g.sphere((sx, 1.15, -2.42), (.12, .08, .04), (1, .1, .05, 1))
    glow(g, parent=rot)
    rot.hjul = []
    for sx in (-1, 1):
        for z in (1.7, 0, -1.7):
            h = Bygge()
            h.lathe([(0, -.22), (.42, -.22), (.6, -.15), (.6, .15), (.42, .22), (0, .22)], (.13, .13, .15, 1), seg=12,
                    smooth=False, rot=(0, 0, 90))
            for k in range(12):                                          # däckmönster
                a = math.radians(k * 30)
                h.box((0, math.cos(a) * .6, math.sin(a) * .6), (.34, .05, .1), (.2, .2, .22, 1), rot=(k * 30, 0, 0))
            h.box((sx * .23, 0, 0), (.02, .5, .12), LJUSGRA)
            h.box((sx * .23, 0, 0), (.02, .12, .5), LJUSGRA)
            rot.hjul.append(ent(h, parent=rot, position=(sx * 1.3, .6, z)))
    return rot


# =============================================================================
# DAIDALOS – ROBOTARNAS KRASCHADE SKEPP
# =============================================================================
def daidalos():
    SKROV, SKROV2 = (.46, .52, .64, 1), (.28, .31, .4, 1)
    rot = Entity()
    skepp = Entity(parent=rot, position=(0, 1.6, 0), rotation=(13, 0, -9))
    b = Bygge()
    b.lathe([(0, -1.5), (5, -1.25), (9, -.2), (9.4, .35), (7.2, 1.5), (3.6, 2.5), (0, 2.8)], SKROV, seg=22)
    b.lathe([(9.42, .1), (9.55, .35), (9.42, .6)], (.85, .7, .2, 1), seg=22)
    b.lathe([(3.7, 2.45), (3.2, 3.1), (2.0, 3.6), (0, 3.8)], (.15, .5, .6, 1), seg=14)       # kupol
    for a in range(0, 360, 45):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        b.box((6.2 * c, 1.9, 6.2 * s), (2.2, .1, .9), SKROV2, rot=(0, -a, -22))
    for sx in (-3, 0, 3):                                                # motorer
        b.cyl((sx, .4, -8.2), (sx, .5, -11), 1.1, SKROV2, r1=1.35, seg=12)
        b.cyl((sx, .5, -11), (sx, .5, -11.05), 1.0, (.05, .05, .06, 1), seg=12)
    b.box((-9.5, .6, 1), (5, .25, 3), SKROV2, rot=(0, 15, 40))           # avbruten vinge
    b.box((0, 1.6, 9.35), (1.5, 2.1, .2), MORK)                          # öppen lucka
    b.sphere((5, 1.6, 4.5), (1.8, .5, 1.5), (.08, .07, .07, 1), rot=(0, 30, 20))   # brännskada
    b.sphere((-4, 2.0, -3), (1.4, .4, 1.9), (.08, .07, .07, 1), rot=(0, 0, -18))
    ent(b, parent=skepp)
    g = Bygge()
    for a in range(0, 360, 30):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        g.sphere((9.5 * c, .35, 9.5 * s), .16, (.3, .9, 1, 1))
    rot.lampor = glow(g, parent=skepp)
    d = Bygge()                                                          # vrakdelar och bränd mark runt om
    d.lathe([(17, .04), (0, .04)], (.2, .12, .09, 1), seg=20, smooth=False)
    skrot = [(-13, 6, 2.5, 20), (12, -9, 1.8, 50), (15, 5, 1.2, 80), (-6, -14, 2.0, 130), (4, 15, 1.5, 200), (-15, -5, 1.0, 10)]
    for x, z, s, a in skrot:
        d.box((x, s * .25, z), (s * 1.6, s * .15, s), SKROV, rot=(a * .3, a, 25))
        d.box((x + s, s * .2, z + .6), (s * .5, s * .4, s * .5), SKROV2, rot=(a, 30, a * .5))
    d.cyl((11, 0, 10), (11, 5, 10), .06, LJUSGRA, seg=6)                 # svensk flagga
    d.box((12.0, 4.4, 10), (2.0, 1.2, .04), (.0, .32, .62, 1))
    d.box((12.0, 4.4, 10), (2.04, .22, .06), (1, .8, 0, 1))
    d.box((11.65, 4.4, 10), (.22, 1.24, .06), (1, .8, 0, 1))
    ent(d, parent=rot)
    skylt('DAIDALOS', rot, (0, 7.2, 0), .7, farg=color.rgba(.5, .9, 1, 1), billboard=True)
    return rot


# =============================================================================
# SAKER ATT HITTA
# =============================================================================
def lada():
    b = Bygge()
    b.box((0, .4, 0), (1.0, .8, .8), VIT)
    b.box((0, .4, 0), (1.03, .16, .83), ORANGE)
    b.box((0, .82, 0), (1.06, .08, .86), LJUSGRA)
    b.box((0, .62, -.41), (.3, .12, .03), MORK)
    return ent(b)


DELNAMN = ['Motormunstycke', 'Bränslepump', 'Navigationsdator', 'Värmesköld', 'Antenn', 'Reaktorkärna']


def raketdel(i):
    rot = Entity()
    b, g = Bygge(), Bygge()
    if i == 0:
        b.lathe([(.18, 1.0), (.3, .6), (.55, .2), (.6, .1)], (.3, .3, .33, 1), seg=14)
        b.lathe([(.6, .1), (.52, .22), (.27, .6), (.15, 1.0)], (.45, .2, .1, 1), seg=14)
        b.cyl((0, 1.0, 0), (0, 1.2, 0), .25, LJUSGRA)
    elif i == 1:
        b.capsule((0, .3, 0), (0, .9, 0), .28, ORANGE, seg=12)
        b.tube([(.25, .5, 0), (.5, .5, 0), (.5, 1.0, 0), (.1, 1.2, 0)], .06, LJUSGRA)
        b.cyl((0, 0, 0), (0, .15, 0), .38, GRA)
    elif i == 2:
        b.box((0, .45, 0), (.8, .6, .5), (.2, .22, .26, 1))
        b.box((0, .1, 0), (.9, .12, .6), GRA)
        g.box((0, .5, -.26), (.6, .35, .02), (.2, 1, .5, 1))
    elif i == 3:
        b.lathe([(0, .1), (.5, .16), (.8, .34), (.86, .5)], (.14, .12, .12, 1), seg=14)
        b.lathe([(.86, .5), (.78, .42), (.5, .28), (0, .22)], (.6, .45, .3, 1), seg=14)
    elif i == 4:
        for k in range(3):
            a = math.radians(k * 120)
            b.cyl((math.cos(a) * .45, 0, math.sin(a) * .45), (0, .8, 0), .03, GRA, seg=5)
        b.lathe([(0, 0), (.3, .06), (.55, .22), (.65, .42)], VIT, pos=(0, .8, 0), rot=(-35, 0, 0), seg=12)
        b.cyl((0, .8, 0), (0, 1.15, .25), .025, GRA, seg=5)
    else:
        for k in range(4):
            a = math.radians(k * 90 + 45)
            b.cyl((math.cos(a) * .32, 0, math.sin(a) * .32), (math.cos(a) * .32, 1.1, math.sin(a) * .32), .035, GRA, seg=5)
        b.cyl((0, 0, 0), (0, .12, 0), .42, GRA)
        b.cyl((0, 1.0, 0), (0, 1.12, 0), .42, GRA)
        g.capsule((0, .3, 0), (0, .85, 0), .2, (.3, .95, 1, 1))
    ent(b, parent=rot)
    if g.v:
        glow(g, parent=rot)
    s = Bygge()                                                          # ljuspelare så att delen syns på håll
    s.cyl((0, 1.5, 0), (0, 45, 0), .12, (.3, 1, .5, 1), seg=6, lock=False)
    rot.strale = genomskinlig(glow(s, parent=rot, color=color.rgba(1, 1, 1, .35)))
    return rot
