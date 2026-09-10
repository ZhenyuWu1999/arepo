"""The production flip transfer is GUARANTEED to create a new extremum.

The map is a uniform shift of every patch node:  U_i^+ = U_i^- - D_P/M.
So for any component with D_P != 0, every node moves the same way and the
patch minimum (D>0) or maximum (D<0) is pushed outside its old range.  There
is no state for which this does not happen.  The only question is magnitude:

  smooth patch      -> D_P = O(h^2 |grad^2 U|)   -> excursion negligible
  interface ~ h     -> D_P = O(sum|dm| [U])      -> excursion ~ 0.1 [U]

That is a sharper statement than "the correction is 0.1[U]": it says the
correction is *sign-coherent and extremum-creating*, which is the signature
of the observed entropy excursion (log 2 section 71.4: 0.183 -> 0.655), not
of a diffusive price.

The low-order endpoint Q^L lies in the convex hull of the old patch states,
so it can never create an extremum.  A relaxed-DMP common-alpha therefore
separates the two regimes automatically.  Tested below.
"""
import numpy as np
rng = np.random.default_rng(5)
GAMMA = 1.4


def patch(h, mode, seed):
    r = np.random.default_rng(seed)
    pts = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])*h
    pts += r.uniform(-.12*h, .12*h, (4, 2))
    def A(i, j, k):
        a, b, c = pts[i], pts[j], pts[k]
        return .5*abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
    mPm = np.zeros(4); mPp = np.zeros(4)
    for t in [(0,1,2),(0,2,3)]:
        for k in t: mPm[k] += A(*t)/3
    for t in [(0,1,3),(1,2,3)]:
        for k in t: mPp[k] += A(*t)/3
    cav = A(0,1,2)+A(0,2,3)
    m_out = (6-np.array([2,1,2,1]))*(cav/2)/3
    if mode == "smooth":
        # resolved field: rho = 1 + 0.5*sin(k.x), k ~ O(1), so variation ~ h
        kv = r.normal(size=2); kv /= np.linalg.norm(kv)
        rho = 1.5 + 0.5*np.sin(2*np.pi*(pts@kv))
    else:
        # interface of width ~ h crossing the patch: near-jump between 1 and 2
        nv = r.normal(size=2); nv /= np.linalg.norm(nv)
        s = (pts@nv - np.mean(pts@nv))/h
        rho = 1.5 + 0.5*np.tanh(s/0.25)
    return pts, mPm+m_out, mPp+m_out, m_out, mPm, mPp, rho


def transfer(U, mm, mp, mo, mPm, mPp):
    dm = mp-mm; D = dm@U; M = mp.sum()
    HO = U - D/M
    Ub = (mPm@U)/mPm.sum()
    LO = (mo*U + mPp*Ub)/mp
    return HO, LO, D


def excursion(Unew, Uold):
    """how far outside the old patch range the new patch states go"""
    lo, hi = Uold.min(), Uold.max()
    return max(lo-Unew.min(), Unew.max()-hi, 0.0)


print("="*90)
print("1. Does the uniform shift always create a new extremum?  (500 patches each)")
print("="*90)
print(f"{'regime':10} {'h':>7} {'median |D_P|':>13} {'median excursion':>17} "
      f"{'excursion/[U]':>15} {'fraction >0':>12}")
for mode in ["smooth", "interface"]:
    for h in [0.04, 0.02, 0.01]:
        ex, dd, ru, pos = [], [], [], 0
        for i in range(500):
            pts, mm, mp, mo, mPm, mPp, U = patch(h, mode, i)
            HO, LO, D = transfer(U, mm, mp, mo, mPm, mPp)
            e = excursion(HO, U)
            ex.append(e); dd.append(abs(D)); pos += (e > 0)
            ru.append(e/max(U.max()-U.min(), 1e-12))
        print(f"{mode:10} {h:>7.3g} {np.median(dd):>13.3e} {np.median(ex):>17.3e} "
              f"{np.median(ru):>15.4f} {pos/500:>12.3f}")
print()
print("Smooth: excursion falls ~h^2 and is a negligible fraction of the local range.")
print("Interface: excursion stays a fixed ~10% of [U] and does NOT converge,")
print("because the interface is never resolved as h falls with fixed width ~h.")
print()

print("="*90)
print("2. Relaxed-DMP common alpha: does it separate the two regimes?")
print("="*90)
print("   bound: new patch states may leave the old patch range by at most")
print("   eps * [U]_patch, with eps = 0.02 (a fixed small tolerance).")
print()
EPS = 0.02
print(f"{'regime':10} {'h':>7} {'median alpha':>13} {'frac alpha=1':>13} "
      f"{'median max|dU|':>16}")
for mode in ["smooth", "interface"]:
    for h in [0.04, 0.02, 0.01]:
        als, mx = [], []
        for i in range(500):
            pts, mm, mp, mo, mPm, mPp, U = patch(h, mode, i)
            HO, LO, D = transfer(U, mm, mp, mo, mPm, mPp)
            tol = EPS*max(U.max()-U.min(), 1e-12)
            lo_, hi_ = 0., 1.
            if excursion(HO, U) <= tol:
                a = 1.0
            else:
                for _ in range(40):
                    m = .5*(lo_+hi_)
                    if excursion(m*HO+(1-m)*LO, U) <= tol: lo_ = m
                    else: hi_ = m
                a = lo_
            als.append(a); mx.append(np.abs((a*HO+(1-a)*LO)-U).max())
        als = np.array(als)
        print(f"{mode:10} {h:>7.3g} {np.median(als):>13.4f} "
              f"{np.mean(als >= 1.0):>13.3f} {np.median(mx):>16.4e}")
print()
print("Conservation is exact for every alpha (both endpoints are conservative),")
print("so the limiter costs nothing in the conserved totals.")
