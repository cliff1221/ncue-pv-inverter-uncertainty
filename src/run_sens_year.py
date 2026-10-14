import sys, time, json
import numpy as np, pandas as pd
import sens_year as sens
import os
P = os.environ.get('OUTP', 'yr')
from SALib.sample import sobol as ssample
from SALib.analyze import sobol as sanalyze
F, B = sens.FACTORS, sens.BASE
names = list(F)

# ---- 1. satu-faktor-per-waktu (OAT) dari baseline ----
e0, _ = sens.run(B)
rows = []
for n in names:
    kind, spec = F[n]
    opts = spec if kind == "cat" else [spec[0], spec[1]]
    for o in opts:
        p = dict(B); p[n] = o
        e, c = sens.run(p)
        rows.append(dict(faktor=n, nilai=str(o), E_kWh=e, selisih_persen=(e / e0 - 1) * 100, clip_kWh=c))
oat = pd.DataFrame(rows); oat.to_csv(f"outputs/{P}_sens_oat.csv", index=False)
print(oat.round(3).to_string(index=False)); sys.stdout.flush()

# ---- 2. Sobol ----
problem = dict(num_vars=len(names), names=names, bounds=[[0, 1]] * len(names))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1024
X = ssample.sample(problem, N, calc_second_order=False, seed=7)
def decode(u):
    p = dict(B)
    for n, v in zip(names, u):
        kind, spec = F[n]
        if kind == "cat": p[n] = spec[min(int(v * len(spec)), len(spec) - 1)]
        else: p[n] = spec[0] + v * (spec[1] - spec[0])
    return p
t0 = time.time(); E = np.empty(len(X)); C = np.empty(len(X))
for i, u in enumerate(X):
    E[i], C[i] = sens.run(decode(u))
print("selesai %d run dalam %.0f s" % (len(X), time.time() - t0)); sys.stdout.flush()
np.save(f"outputs/{P}_sens_E.npy", E); np.save(f"outputs/{P}_sens_C.npy", C)
Si = sanalyze.analyze(problem, E, calc_second_order=False, seed=7, print_to_console=False)
S = pd.DataFrame(dict(faktor=names, S1=Si["S1"], S1_ci=Si["S1_conf"], ST=Si["ST"], ST_ci=Si["ST_conf"]))
S.sort_values("ST", ascending=False).to_csv(f"outputs/{P}_sens_sobol.csv", index=False)
print(S.sort_values("ST", ascending=False).round(3).to_string(index=False))
# distribusi dari 2N sampel acak murni (matriks A dan B)
base_draws = np.concatenate([E[: 0]])  # placeholder
