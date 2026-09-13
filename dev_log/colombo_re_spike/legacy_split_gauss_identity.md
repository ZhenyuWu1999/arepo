# Can legacy split be extended with Gauss? (2026-09-12)

This is an algebraic follow-up to log3 §31, not a new native fluid campaign.
The ideal-gas Euler/Roe formulas match the existing code definitions; the
check is an independent Python calculation, not a compiled native-operator test.

Write U_h=sum psi_i U_i, Z_h=sum psi_i Z_i, and U_Z=U(Z_h). Define

\[
 P_R=\sum_iK_i^{phys}\widehat U_i
     =\oint_{\partial T}F(U_Z)n\,ds,
 \qquad B=\int_T\sigma_h\cdot\nabla U_h\,dA.
\]

The old split is Phi_R=P_R-B. U and F are quadratic in Roe parameters Z.
Thus F(U_Z) is quadratic along a straight edge: Gauss2 already integrates
it exactly. Gauss3/5 on the same Z_h reproduce P_R in exact arithmetic;
they do not supply a new truncation-error or stability correction.

An effective correction can instead change the physical-flux interpolant:

\[
 \delta\Phi_{R\to U}^{(q)}=
 \sum_e\ell_e\sum_rw_r
 [F((1-s_r)U_a+s_rU_b)-F(U((1-s_r)Z_a+s_rZ_b))]n_e.
\]

For q>=2 Gauss--Legendre, the second term is exactly P_R, so

\[
 \boxed{\Phi_R+\delta\Phi_{R\to U}^{(q)}
 =\sum_e\ell_e\sum_rw_rF(U_h(s_r))n_e-B
 =\Phi_{G_q,U}.}
\]

This preserves the old assembly as an implementation route but gives the
same spatial residual as current conservative-P1-U Gauss. Retaining the
same K split, F1 and time/topology algorithm makes it the same mathematical
method, not a third independently improved scheme. Floating-point assembly
order can still change long-time pointwise trajectories.

The correction is not the existing nodal-contour-to-Gauss helper. Relative
to nodal contour, mass-flux quadrature is already exact and its correction
vanishes. Relative to linear Z, momentum m=Z0*Zv is quadratic, whereas
momentum in U_h is linear; the physical mass-flux integrals can differ.
All four components must be included in the Roe-to-Gauss correction.
Nor should F be evaluated on the auxiliary Uhat as though Uhat were U_h:
Uhat_i=(dU/dZ)(Zbar)Z_i is a linearisation vector, with Uhat=2U for a
uniform state by homogeneity, not the represented physical nodal state.

Frame bookkeeping also matters. With constant boost b and U'=G(b)U,
the directly recomputed physical-flux correction obeys

\[
 \delta\Phi'_{direct}=G(b)\left[
 \delta\Phi-\oint(b\cdot n)(U_h-U_Z)ds\right].
\]

It is not by itself just G deltaPhi: the two physical fluxes transform with
different state interpolants. The existing legacy co-moving path already
transforms the laboratory split correction. A safe route is to form the
complete corrected residual in laboratory coordinates, then transform that
total (or add G deltaPhi to the consistently transformed old total). Simply
adding the directly recomputed primed physical-flux difference while retaining
every old split term would leave an extra term. Current direct Gauss-U
assembly already avoids that redundant bookkeeping.

`tests/rd/test_legacy_split_gauss_identity.py` checks200 random admissible
Euler-state triples and affine triangles, q=2/3/5, using independently
constructed Jacobians and edge quadrature. Maximum absolute defects:

- Roe matrix physical total versus Gauss-on-Z:1.24345e-14.
- Full-vector corrected split versus direct Gauss-on-U:1.24345e-14.
- Explicit boosted correction identity including the extra term:1.22125e-14.

The sampled correction's mass component reaches .6274 in these arbitrary
unit-scale random states, demonstrating it is not identically zero; this is
not a KH/Sod error measurement. Output:
`/Users/zhenyuwu/arepo_rd/local_runs/legacy_split_gauss_identity_20260912/algebra.json`.
No solver, thesis, timestep or native test was changed/run in this follow-up.
