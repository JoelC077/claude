#!/usr/bin/env python3
"""Statistics for rr-data-and-money, stdlib only (no numpy/scipy).

Distributions: norm_cdf/sf/ppf (Acklam + Halley step), t_sf/t_ppf (incomplete beta), chi2_sf (incomplete gamma).
Intervals:     wilson (one proportion), newcombe (difference of two proportions), katz_rr (relative lift).
Tests:         two_prop (pooled z; Fisher exact when any expected cell < 10), fisher_exact, welch (summary
               stats), srm (chi-square vs planned split), holm.
Planning:      n_two_prop, n_means, n_rpu (single-price items: revenue per exposed user), mde_two_prop.
Sequential:    obf_bounds (O'Brien-Fleming by seeded simulation, any look spacing), obf_inflation, peek_fpr.
Resampling:    bootstrap_diff (per-user values, percentile CI).
`python3 statlib.py --help` prints this; `python3 statlib.py --demo` prints a few reference values.
"""
import math, random, sys

SQ2 = math.sqrt(2.0)


def norm_cdf(x):
    return 0.5 * math.erfc(-x / SQ2)


def norm_sf(x):
    return 0.5 * math.erfc(x / SQ2)


def norm_ppf(p):
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00)
    lo = 0.02425
    if p < lo or p > 1 - lo:
        q = math.sqrt(-2 * math.log(p if p < lo else 1 - p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        x = x if p < lo else -x
    else:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    e = norm_cdf(x) - p
    u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
    return x - u / (1 + x * u / 2)


def _betacf(a, b, x):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 500):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1) < 3e-16:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lb = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(lb) * _betacf(a, b, x) / a
    return 1 - math.exp(lb) * _betacf(b, a, 1 - x) / b


def t_sf2(t, df):
    """Two-sided p-value of Student t."""
    if df > 1e6:
        return 2 * norm_sf(abs(t))
    return betainc(df / 2, 0.5, df / (df + t * t))


def t_ppf(p, df):
    """Quantile of Student t by bisection (p > 0.5 typical)."""
    if df > 1e6:
        return norm_ppf(p)
    target = 2 * (1 - p) if p > 0.5 else 2 * p
    lo, hi = 0.0, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_sf2(mid, df) > target:
            lo = mid
        else:
            hi = mid
    x = (lo + hi) / 2
    return x if p > 0.5 else -x


def gammainc_q(a, x):
    """Regularized upper incomplete gamma Q(a, x)."""
    if x <= 0:
        return 1.0
    lg = -x + a * math.log(x) - math.lgamma(a)
    if x < a + 1:
        ap, s = a, 1.0 / a
        dd = s
        for _ in range(2000):
            ap += 1
            dd *= x / ap
            s += dd
            if abs(dd) < abs(s) * 1e-16:
                break
        return max(0.0, 1 - s * math.exp(lg))
    tiny = 1e-300
    b = x + 1 - a
    c, d = 1 / tiny, 1 / b
    h = d
    for i in range(1, 2000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1 / (d if abs(d) > tiny else tiny)
        c = b + an / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1) < 1e-16:
            break
    return math.exp(lg) * h


def chi2_sf(x, k):
    return gammainc_q(k / 2, x / 2)


# ------------------------------------------------------------------ intervals
def zcrit(conf):
    return norm_ppf(1 - (1 - conf) / 2)


def wilson(x, n, conf=0.95):
    if n <= 0:
        return (0.0, 1.0)
    z, p = zcrit(conf), x / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def newcombe(x1, n1, x2, n2, conf=0.95):
    """CI of p2 - p1 (Newcombe hybrid score, method 10)."""
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson(x1, n1, conf)
    l2, u2 = wilson(x2, n2, conf)
    d = p2 - p1
    return (d - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2), d + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2))


def katz_rr(x1, n1, x2, n2, conf=0.95):
    """CI of relative lift p2/p1 - 1 (log risk ratio; 0.5 added to zero cells)."""
    if x1 == 0 or x2 == 0:
        x1, x2, n1, n2 = x1 + 0.5, x2 + 0.5, n1 + 0.5, n2 + 0.5
    rr = (x2 / n2) / (x1 / n1)
    se = math.sqrt(max(0.0, 1 / x2 - 1 / n2 + 1 / x1 - 1 / n1))
    z = zcrit(conf)
    return (rr * math.exp(-z * se) - 1, rr * math.exp(z * se) - 1)


# ------------------------------------------------------------------ tests
def _lchoose(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_exact(x1, n1, x2, n2):
    """Two-sided Fisher exact p for [[x1, n1-x1], [x2, n2-x2]] (sum of tables no more likely than observed).
    Counts are rounded to integers (CSV readers hand floats)."""
    x1, n1, x2, n2 = (int(round(v)) for v in (x1, n1, x2, n2))
    k, N = x1 + x2, n1 + n2
    lo, hi = max(0, k - n2), min(k, n1)
    base = _lchoose(N, k)

    def lp(a):
        return _lchoose(n1, a) + _lchoose(n2, k - a) - base
    obs = lp(x1)
    p = sum(math.exp(lp(a)) for a in range(lo, hi + 1) if lp(a) <= obs + 1e-7)
    return min(1.0, p)


def two_prop(x1, n1, x2, n2, conf=0.95):
    """A = (x1, n1), B = (x2, n2). Returns a dict; 'p' is Fisher exact when any expected cell < 10."""
    p1, p2 = x1 / n1, x2 / n2
    pp = (x1 + x2) / (n1 + n2)
    se0 = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2)) if 0 < pp < 1 else 0.0
    z = (p2 - p1) / se0 if se0 > 0 else 0.0
    p_z = 2 * norm_sf(abs(z)) if se0 > 0 else 1.0
    exp_min = min(n1 * pp, n1 * (1 - pp), n2 * pp, n2 * (1 - pp))
    exact = exp_min < 10
    p_f = fisher_exact(x1, n1, x2, n2) if exact else None
    return {"pa": p1, "pb": p2, "diff": p2 - p1, "diff_ci": newcombe(x1, n1, x2, n2, conf),
            "lift": (p2 / p1 - 1) if p1 > 0 else None, "lift_ci": katz_rr(x1, n1, x2, n2, conf) if p1 > 0 else None,
            "z": z, "p": p_f if exact else p_z, "method": "fisher-exact" if exact else "pooled-z", "p_z": p_z}


def welch(m1, s1, n1, m2, s2, n2, conf=0.95):
    """Difference m2 - m1 from summary stats (mean, sd, n)."""
    v1, v2 = s1 * s1 / n1, s2 * s2 / n2
    se = math.sqrt(v1 + v2)
    df = (v1 + v2) ** 2 / ((v1 * v1 / (n1 - 1) if n1 > 1 else 0) + (v2 * v2 / (n2 - 1) if n2 > 1 else 0) or 1e-300)
    t = (m2 - m1) / se if se > 0 else 0.0
    q = t_ppf(1 - (1 - conf) / 2, df)
    return {"diff": m2 - m1, "diff_ci": (m2 - m1 - q * se, m2 - m1 + q * se), "t": t, "df": df,
            "p": t_sf2(t, df) if se > 0 else 1.0, "method": "welch-t"}


def srm(counts, weights):
    """Sample-ratio mismatch: chi-square of observed arm counts vs planned weights. p < 0.001 = broken split."""
    tot, wt = sum(counts), sum(weights)
    exp = [tot * w / wt for w in weights]
    chi = sum((o - e) ** 2 / e for o, e in zip(counts, exp) if e > 0)
    return {"chi2": chi, "df": len(counts) - 1, "p": chi2_sf(chi, len(counts) - 1), "expected": exp}


def holm(pvals):
    """Holm step-down adjusted p-values (same order as given)."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, run = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * pvals[i]))
        adj[i] = run
    return adj


# ------------------------------------------------------------------ planning
def n_two_prop(p1, p2, alpha=0.05, power=0.8, ratio=1.0, sides=2):
    """Per-arm sizes (nA, nB = ratio * nA) to detect p1 -> p2 (normal approximation, no continuity correction)."""
    if p1 == p2:
        return math.inf, math.inf
    za, zb = norm_ppf(1 - alpha / sides), norm_ppf(power)
    pbar = (p1 + ratio * p2) / (1 + ratio)
    num = (za * math.sqrt(pbar * (1 - pbar) * (1 + 1 / ratio)) +
           zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio)) ** 2
    n1 = num / (p1 - p2) ** 2
    return math.ceil(n1), math.ceil(n1 * ratio)


def n_means(delta, sd1, sd2=None, alpha=0.05, power=0.8, sides=2):
    sd2 = sd1 if sd2 is None else sd2
    za, zb = norm_ppf(1 - alpha / sides), norm_ppf(power)
    return math.ceil((za + zb) ** 2 * (sd1 ** 2 + sd2 ** 2) / delta ** 2) + 1


def n_rpu(price_a, conv_a, price_b, conv_b, alpha=0.05, power=0.8, sides=2):
    """Per-arm n for revenue per exposed user when each user buys at most once at a fixed price (game pass)."""
    ra, rb = price_a * conv_a, price_b * conv_b
    if ra == rb:
        return math.inf
    za, zb = norm_ppf(1 - alpha / sides), norm_ppf(power)
    var = price_a ** 2 * conv_a * (1 - conv_a) + price_b ** 2 * conv_b * (1 - conv_b)
    return math.ceil((za + zb) ** 2 * var / (ra - rb) ** 2)


def mde_two_prop(p1, n, alpha=0.05, power=0.8, up=True):
    """Smallest p2 (above p1 if up) detectable with n per arm."""
    lo, hi = (p1, 0.999999) if up else (1e-6, p1)
    for _ in range(100):
        mid = (lo + hi) / 2
        need = n_two_prop(p1, mid, alpha, power)[0]
        if (need > n) == up:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ------------------------------------------------------------------ sequential
def _paths(looks, sims, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(sims):
        s, prev, row = 0.0, 0.0, []
        for t in looks:
            s += rng.gauss(0.0, math.sqrt(t - prev))
            prev = t
            row.append(s)
        out.append(row)
    return out


def obf_bounds(looks, alpha=0.05, sims=200000, seed=20260928):
    """O'Brien-Fleming z-boundaries for information fractions `looks` (ascending, last = 1), two-sided alpha.
    Boundary at t is C/sqrt(t) where C is the (1-alpha) quantile of max_j |B(t_j)| of Brownian motion."""
    paths = _paths(looks, sims, seed)
    m = sorted(max(abs(s) for s in row) for row in paths)
    C = m[min(sims - 1, int(math.ceil((1 - alpha) * sims)) - 1)]
    return [C / math.sqrt(t) for t in looks]


def obf_inflation(looks, alpha=0.05, power=0.8, sims=100000, seed=7):
    """Max-sample inflation vs a fixed design with the same alpha and power."""
    bounds = obf_bounds(looks, alpha, sims=max(sims, 100000), seed=seed)
    C = bounds[-1]
    paths = _paths(looks, sims, seed + 1)
    target = norm_ppf(1 - alpha / 2) + norm_ppf(power)

    def pw(theta):
        return sum(1 for row in paths if any(abs(s + theta * t) >= C for s, t in zip(row, looks))) / sims
    lo, hi = target * 0.9, target * 1.3
    for _ in range(22):
        mid = (lo + hi) / 2
        if pw(mid) < power:
            lo = mid
        else:
            hi = mid
    return ((lo + hi) / 2 / target) ** 2


def peek_fpr(k, alpha=0.05, sims=40000, seed=11):
    """False-positive rate when a null test is checked at k equally spaced looks at the fixed-design threshold."""
    looks = [(i + 1) / k for i in range(k)]
    z = norm_ppf(1 - alpha / 2)
    paths = _paths(looks, sims, seed)
    return sum(1 for row in paths if any(abs(s) / math.sqrt(t) >= z for s, t in zip(row, looks))) / sims


def bootstrap_diff(a, b, B=2000, conf=0.95, seed=3):
    """Percentile CI of mean(b) - mean(a) from per-user values."""
    rng = random.Random(seed)
    na, nb = len(a), len(b)
    diffs = []
    for _ in range(B):
        sa = sum(a[rng.randrange(na)] for _ in range(na)) / na
        sb = sum(b[rng.randrange(nb)] for _ in range(nb)) / nb
        diffs.append(sb - sa)
    diffs.sort()
    lo = diffs[int((1 - conf) / 2 * B)]
    hi = diffs[min(B - 1, int((1 + conf) / 2 * B))]
    return sum(b) / nb - sum(a) / na, (lo, hi)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        print("norm_ppf(0.975) =", round(norm_ppf(0.975), 6))
        print("n_two_prop(0.10, 0.12) =", n_two_prop(0.10, 0.12))
        print("fisher tea [[3,1],[1,3]] p =", round(fisher_exact(3, 4, 1, 4), 4))
        print("chi2_sf(3.841, 1) =", round(chi2_sf(3.841, 1), 4))
        print("OBF 5 looks =", [round(x, 3) for x in obf_bounds([.2, .4, .6, .8, 1.0], sims=100000)])
        print("naive peeking FPR, 10 looks =", peek_fpr(10))
    else:
        print(__doc__)
