"""Modellbyggare: sätter ihop många enkla former till EN 3D-modell.

Att slå ihop formerna till en enda modell gör spelet mycket snabbare än
om varje liten del vore ett eget objekt.
"""
import math
from ursina import Mesh


def _norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _mul(M, p):
    return (M[0][0] * p[0] + M[0][1] * p[1] + M[0][2] * p[2],
            M[1][0] * p[0] + M[1][1] * p[1] + M[1][2] * p[2],
            M[2][0] * p[0] + M[2][1] * p[1] + M[2][2] * p[2])


def euler(rx, ry, rz):
    """Rotationsmatris från vinklar i grader (först z, sedan x, sedan y)."""
    rx, ry, rz = math.radians(rx), math.radians(ry), math.radians(rz)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = ((1, 0, 0), (0, cx, -sx), (0, sx, cx))
    Y = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    Z = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))

    def mm(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return mm(Y, mm(X, Z))


def _rikta(d):
    """Matris som vrider y-axeln så att den pekar längs d."""
    y = _norm(d)
    ref = (0, 0, 1) if abs(y[2]) < 0.95 else (1, 0, 0)
    x = _norm(_cross(ref, y))
    z = _cross(x, y)
    return ((x[0], y[0], z[0]), (x[1], y[1], z[1]), (x[2], y[2], z[2]))


class Bygge:
    def __init__(self):
        self.v, self.n, self.c, self.uv, self.t = [], [], [], [], []

    def _add(self, verts, norms, uvs, tris, col, pos=(0, 0, 0), M=None, scale=(1, 1, 1)):
        bas = len(self.v)
        sx, sy, sz = scale
        for p, n in zip(verts, norms):
            p = (p[0] * sx, p[1] * sy, p[2] * sz)
            n = (n[0] / sx, n[1] / sy, n[2] / sz)
            if M is not None:
                p, n = _mul(M, p), _mul(M, n)
            self.v.append((p[0] + pos[0], p[1] + pos[1], p[2] + pos[2]))
            self.n.append(_norm(n))
        self.c.extend([col] * len(verts))
        self.uv.extend(uvs)
        self.t.extend(i + bas for i in tris)
        return self

    # ---- låda -------------------------------------------------------------
    def box(self, pos, size, col, rot=None):
        hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
        X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
        sidor = ((X, Z, Y, hx, hz, hy), (Y, X, Z, hy, hx, hz), (Z, Y, X, hz, hy, hx))
        verts, norms, tris = [], [], []
        for n, u, v, hn, hu, hv in sidor:
            for s in (1, -1):
                uu, vv, hu2, hv2 = (u, v, hu, hv) if s == 1 else (v, u, hv, hu)
                b = len(verts)
                for a, c in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    verts.append(tuple(n[i] * hn * s + uu[i] * hu2 * a + vv[i] * hv2 * c for i in range(3)))
                    norms.append(tuple(n[i] * s for i in range(3)))
                tris += [b, b + 1, b + 2, b, b + 2, b + 3]
        M = euler(*rot) if rot else None
        return self._add(verts, norms, [(0, 0)] * len(verts), tris, col, pos, M)

    # ---- svarvad form (profil som snurras runt y-axeln) ---------------------
    def lathe(self, profil, col, pos=(0, 0, 0), seg=12, rot=None, scale=(1, 1, 1), smooth=True, M=None):
        ringar, par = [], []
        k = len(profil)

        def seg_n(a, b):
            dr, dy = b[0] - a[0], b[1] - a[1]
            l = math.hypot(dr, dy) or 1.0
            return (dy / l, -dr / l)

        if smooth:
            for j, (r, y) in enumerate(profil):
                a, b = profil[max(j - 1, 0)], profil[min(j + 1, k - 1)]
                nr, ny = seg_n(a, b)
                ringar.append((r, y, nr, ny))
            par = [(j, j + 1) for j in range(k - 1)]
        else:
            for j in range(k - 1):
                nr, ny = seg_n(profil[j], profil[j + 1])
                ringar.append((profil[j][0], profil[j][1], nr, ny))
                ringar.append((profil[j + 1][0], profil[j + 1][1], nr, ny))
                par.append((2 * j, 2 * j + 1))

        verts, norms, uvs, tris = [], [], [], []
        m = len(ringar)
        for j, (r, y, nr, ny) in enumerate(ringar):
            for i in range(seg + 1):
                a = 2 * math.pi * i / seg
                ca, sa = math.cos(a), math.sin(a)
                verts.append((r * ca, y, r * sa))
                norms.append((nr * ca, ny, nr * sa))
                uvs.append((i / seg, j / max(m - 1, 1)))
        w = seg + 1
        for j0, j1 in par:
            for i in range(seg):
                a, b, c, d = j0 * w + i, j0 * w + i + 1, j1 * w + i + 1, j1 * w + i
                tris += [a, b, c, a, c, d]
        if M is None and rot:
            M = euler(*rot)
        return self._add(verts, norms, uvs, tris, col, pos, M, scale)

    # ---- klot / ägg -------------------------------------------------------
    def sphere(self, pos, r, col, seg=12, ringar=7, rot=None):
        if not isinstance(r, (tuple, list)):
            r = (r, r, r)
        prof = [(math.sin(math.pi * j / ringar), -math.cos(math.pi * j / ringar)) for j in range(ringar + 1)]
        return self.lathe(prof, col, pos, seg, rot, scale=r)

    # ---- cylinder / kon mellan två punkter ----------------------------------
    def cyl(self, p0, p1, r0, col, r1=None, seg=10, lock=True):
        r1 = r0 if r1 is None else r1
        d = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        L = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 0.001
        prof = [(r0, 0), (r1, L)]
        if lock:
            prof = [(0, 0)] + prof + [(0, L)]
        return self.lathe(prof, col, p0, seg, smooth=False, M=_rikta(d))

    # ---- kapsel (cylinder med runda ändar), bra för armar och ben -----------
    def capsule(self, p0, p1, r, col, seg=10, r1=None):
        r1 = r if r1 is None else r1
        d = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        L = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 0.001
        prof = [(r * math.sin(a), -r * math.cos(a)) for a in (0, math.pi / 6, math.pi / 3, math.pi / 2)]
        prof += [(r1 * math.sin(a), L - r1 * math.cos(a)) for a in (math.pi / 2, 2 * math.pi / 3, 5 * math.pi / 6, math.pi)]
        return self.lathe(prof, col, p0, seg, M=_rikta(d))

    # ---- rör genom flera punkter (kablar, horn) -----------------------------
    def tube(self, punkter, r, col, r_slut=None, seg=8):
        k = len(punkter) - 1
        r_slut = r if r_slut is None else r_slut
        for i in range(k):
            ra = r + (r_slut - r) * i / k
            rb = r + (r_slut - r) * (i + 1) / k
            self.capsule(punkter[i], punkter[i + 1], ra, col, seg, r1=rb)
        return self

    def mesh(self):
        return Mesh(vertices=self.v, triangles=self.t, normals=self.n, colors=self.c, uvs=self.uv, static=True)
