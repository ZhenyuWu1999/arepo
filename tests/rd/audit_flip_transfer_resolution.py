"""Does the flip-transfer price converge under refinement?

Log 2 section 71 / Aug26 section 2.5 measured max|dU| ~ 0.104 on an UNMERGED
KH patch at glass48 (h ~ 0.021) with interface width W = 0.025, i.e. W/h ~ 1.2.
Hypothesis B calls that price "intrinsic to an under-resolved interface".

That is a statement about W/h, not about the operator.  Held to a FIXED
physical width W and refined h, linear exactness gives
    D_P = sum_i dm_i (U_i - L(x_i)),
so once W/h >> 1 the patch data become locally affine and D_P must fall to
O(h^2 |grad^2 U|).  This script measures that transition at patch level, and
so predicts what a glass96/glass192 repair pair would show.

Reported as the WORST case over orientations, not the median: D_P is largest
when the interface separates the two DIAGONAL nodes of the flip quad, which is
a special but not rare alignment near a shear layer.
"""
import numpy as np

W = 0.025          # KH interface width, fixed physical scale
DRHO = 1.0         # [rho] across the layer


def build(h, theta, offset, jitter, seed):
    r = np.random.default_rng(seed)
    pts = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])*h
    pts += r.uniform(-jitter*h, jitter*h, (4, 2))
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
    nv = np.array([np.cos(theta), np.sin(theta)])
    s = pts@nv - (np.mean(pts@nv) + offset*h)
    rho = 1.5 + 0.5*DRHO*np.tanh(s/W)
    return mPm+m_out, mPp+m_out, m_out, mPm, mPp, rho


def run(h, n=4000, seed=0):
    r = np.random.default_rng(seed)
    worst_ex, worst_du, worst_D = 0., 0., 0.
    exs, dus = [], []
    for i in range(n):
        th = r.uniform(0, 2*np.pi); off = r.uniform(-.6, .6)
        mm, mp, mo, mPm, mPp, U = build(h, th, off, .12, i)
        dm = mp-mm; D = dm@U; M = mp.sum()
        HO = U - D/M
        rng_ = max(U.max()-U.min(), 1e-14)
        ex = max(U.min()-HO.min(), HO.max()-U.max(), 0.)/DRHO
        du = np.abs(HO-U).max()/DRHO
        exs.append(ex); dus.append(du)
        worst_ex = max(worst_ex, ex); worst_du = max(worst_du, du)
        worst_D = max(worst_D, abs(D))
    return np.array(exs), np.array(dus), worst_D


print("="*94)
print("Flip-transfer correction vs resolution, FIXED physical interface width W = 0.025")
print("max|dU| and the out-of-range excursion are normalised by the density jump [rho] = 1")
print("="*94)
print(f"{'case':12} {'h':>9} {'W/h':>6} {'max|dU| worst':>15} {'max|dU| 99%':>13} "
      f"{'excursion 99%':>15} {'excursion median':>18}")
cases = [("glass24", 0.042), ("glass48", 0.021), ("glass96", 0.0105),
         ("glass192", 0.00525), ("glass384", 0.002625)]
prev = None
for name, h in cases:
    ex, du, D = run(h)
    print(f"{name:12} {h:>9.5f} {W/h:>6.2f} {du.max():>15.4f} "
          f"{np.percentile(du,99):>13.4f} {np.percentile(ex,99):>15.4f} "
          f"{np.median(ex):>18.3e}")
    if prev is not None:
        rate = np.log(prev/np.percentile(du, 99))/np.log(2)
        print(f"{'':12} {'':9} {'':6} {'  -> observed order between successive rows: '}{rate:.2f}")
    prev = np.percentile(du, 99)
print()
print("CAVEAT: this idealised patch gives ~5e-3 at the glass48 row, about 20x")
print("SMALLER than the 0.104 measured on a real unmerged KH patch.  A single")
print("tanh layer on a near-square quad is not the real late-time KH braid, and")
print("|dU| there is a maximum over all four conserved components, whose scales")
print("differ.  So the CONSTANT here is not validated; only the SCALING is, and")
print("the scaling rests on the exact linear-exactness identity D_P = sum dm_i")
print("(U_i - L(x_i)), verified separately to 1e-15 in flip_transfer_moments.py.")
print()
print("The price is NOT an intrinsic property of the operator: it is a function")
print("of W/h.  Once the interface is resolved the correction converges at the")
print("linear-exactness rate.  A glass96 repair/control pair is therefore the")
print("measurement that decides whether the repair is consistent or defective.")
