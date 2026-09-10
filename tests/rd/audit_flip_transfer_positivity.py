"""Positivity threshold of the PRODUCTION equal-step repair, with a realistic
vertex star.

Production map (residual_distribution_solver.c:2272-2320):
    w_i = m_i^+ / sum_P m_j^+ ,  D = sum_P dm_i U_i ,  U_i^+ = U_i^- - D/M
i.e. one common shift of the conserved vector over the whole flip patch.

The relevant geometric parameter is how much of each vertex's lumped mass the
flip cavity actually owns.  A vertex with n incident triangles of comparable
area owns 2/n of its mass in the cavity (diagonal endpoints) or 1/n (the other
two).  Codex's counterexample used m_out = 1/12, i.e. a vertex whose mass is
almost entirely inside the cavity -- much more fragile than a real mesh.
"""
from fractions import Fraction as F
import numpy as np

def threshold(n_star):
    """Exact worst-case density contrast r at which min rho_HO hits 0,
    for the unit-square checkerboard (1,r,1,r) and n_star incident triangles."""
    # cavity contributions (unit square, both triangles area 1/2)
    mP_m = [F(1,3), F(1,6), F(1,3), F(1,6)]
    mP_p = [F(1,6), F(1,3), F(1,6), F(1,3)]
    # exterior: remaining (n_star - 2) or (n_star - 1) triangles of area 1/2
    m_out = [F(n_star-2,6), F(n_star-1,6), F(n_star-2,6), F(n_star-1,6)]
    m_p = [a+b for a, b in zip(m_out, mP_p)]
    dm = [p-m for p, m in zip(mP_p, mP_m)]
    M = sum(m_p)
    # D = sum dm_i rho_i = (1/6)(2r-2) ; shift = D/M ; min rho = 1 - shift
    # 1 - ((r-1)/3)/M = 0  ->  r = 1 + 3M
    return 1 + 3*M

print("Exact worst-case (checkerboard-aligned) density contrast that makes the")
print("PRODUCTION repair produce a negative density:\n")
print(f"{'triangles per vertex':>21} {'patch mass M':>13} {'critical contrast r*':>21}")
for n in [3, 4, 5, 6, 7, 8]:
    mP_p = [F(1,6), F(1,3), F(1,6), F(1,3)]
    m_out = [F(n-2,6), F(n-1,6), F(n-2,6), F(n-1,6)]
    M = sum(a+b for a, b in zip(m_out, mP_p))
    print(f"{n:>21} {str(M):>13} {str(threshold(n)):>21}")
print()
print("Codex's counterexample used m_out = 1/12 per vertex (M = 4/3) -> r* = 5,")
print("which corresponds to a vertex owned almost entirely by the flip cavity.")
print("A regular 6-neighbour mesh gives M = 4 and r* = 13.")
print("Cascaded flips merged into one patch by the union-find in the C code")
print("raise |D| without raising M proportionally, and lower r* again.")
print()

# ---------------- random Euler patches with a realistic star ----------------
rng = np.random.default_rng(4)
GAMMA = 1.4

def admissible(Q, m):
    U = Q/m[:, None]
    if np.any(~np.isfinite(U)) or np.any(U[:, 0] <= 0):
        return False
    p = (GAMMA-1)*(U[:, 3]-0.5*(U[:, 1]**2+U[:, 2]**2)/U[:, 0])
    return bool(np.all(p > 0))

def sample(contrast, n_star):
    pts = np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]]) + rng.uniform(-.15,.15,(4,2))
    def area(i,j,k):
        a,b,c = pts[i],pts[j],pts[k]
        return .5*abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
    mPm = np.zeros(4); mPp = np.zeros(4)
    for t in [(0,1,2),(0,2,3)]:
        for k in t: mPm[k] += area(*t)/3
    for t in [(0,1,3),(1,2,3)]:
        for k in t: mPp[k] += area(*t)/3
    ncav = np.array([2,1,2,1])
    m_out = (n_star-ncav)*np.mean([area(0,1,2),area(0,2,3)])/3*rng.uniform(.8,1.2,4)
    lo = rng.uniform(0,1,4)
    rho = np.exp((lo-lo.min())/max(np.ptp(lo),1e-12)*np.log(contrast))
    pr = np.exp(rng.uniform(-.2,.2,4)); v = rng.normal(0,.3,(4,2))
    U = np.stack([rho, rho*v[:,0], rho*v[:,1], pr/(GAMMA-1)+.5*rho*(v**2).sum(1)],1)
    return U, mPm+m_out, mPp+m_out, m_out

def maps(U, mm, mp, mo):
    dm = mp-mm; D = dm@U; M = mp.sum()
    HO = (U - D/M)*mp[:,None]
    Ub = ((mm-mo)@U)/(mm-mo).sum()
    LO = mo[:,None]*U + (mp-mo)[:,None]*Ub[None,:]
    return HO, LO

print("Random admissible Euler flip patches, realistic 6-neighbour star, 4000 each")
print(f"{'contrast':>9} {'HO admissible':>15} {'LO admissible':>15} {'median alpha<1':>16}")
for c in [2., 4., 8., 13., 20., 50.]:
    okH = okL = 0; als = []
    for _ in range(4000):
        U, mm, mp, mo = sample(c, 6)
        HO, LO = maps(U, mm, mp, mo)
        aH = admissible(HO, mp); okH += aH; okL += admissible(LO, mp)
        if not aH:
            l, h = 0., 1.
            for _ in range(40):
                m = .5*(l+h)
                if admissible(m*HO+(1-m)*LO, mp): l = m
                else: h = m
            als.append(l)
    med = f"{np.median(als):.3f}" if als else "-"
    print(f"{c:>9.4g} {okH/4000:>15.4f} {okL/4000:>15.4f} {med:>16}")
