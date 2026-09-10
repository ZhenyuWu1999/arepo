"""Why the equal-step repair looks clean on smooth tests, and where it stops.

Claim: the production high-order map U_i^+ = U_i^- - D/M with
D = sum_i (m_i^+ - m_i^-) U_i^- is EXACT for affine data, because the two
triangulations of the same cavity reproduce the same zeroth and first moments:
    sum_i dm_i = 0        and      sum_i dm_i x_i = 0.
Hence the transfer defect is O(h^2 * second derivative), and it only becomes
visible where the solution is under-resolved.
"""
import numpy as np
rng = np.random.default_rng(11)

def cavity_masses(pts, tris):
    m = np.zeros(len(pts))
    for t in tris:
        a, b, c = pts[list(t)]
        A = 0.5*abs((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]))
        for k in t:
            m[k] += A/3.0
    return m

max0 = max1 = maxaff = 0.0
maxquad = 0.0
for _ in range(20000):
    pts = np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]]) + rng.uniform(-.25,.25,(4,2))
    # keep the quad convex so both diagonals triangulate it
    def convex(P):
        s = []
        for i in range(4):
            a,b,c = P[i], P[(i+1)%4], P[(i+2)%4]
            s.append(np.sign((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])))
        return len(set(s)) == 1
    if not convex(pts):
        continue
    m_minus = cavity_masses(pts, [(0,1,2),(0,2,3)])
    m_plus  = cavity_masses(pts, [(0,1,3),(1,2,3)])
    dm = m_plus - m_minus
    max0 = max(max0, abs(dm.sum()))
    max1 = max(max1, np.abs(dm @ pts).max())
    # affine field
    g = rng.normal(size=2); c0 = rng.normal()
    Uaff = pts @ g + c0
    maxaff = max(maxaff, abs(dm @ Uaff))
    # quadratic field: defect should NOT vanish
    Uq = (pts[:,0]**2 + pts[:,0]*pts[:,1])
    maxquad = max(maxquad, abs(dm @ Uq))

print("20000 random convex flip cavities:")
print(f"  max |sum dm_i|            (zeroth moment) = {max0:.3e}")
print(f"  max |sum dm_i x_i|        (first moment)  = {max1:.3e}")
print(f"  max |D| for AFFINE data                   = {maxaff:.3e}   <- exact")
print(f"  max |D| for QUADRATIC data                = {maxquad:.3e}   <- O(h^2 u'')")
print()
print("So the transfer is second-order accurate and vanishes identically on")
print("linear states. Smooth benchmarks (Yee, Gresho, KH) therefore show tiny")
print("repair corrections; the map's positivity limit is only probed where the")
print("cavity is genuinely under-resolved (shock / contact inside one flip patch).")
