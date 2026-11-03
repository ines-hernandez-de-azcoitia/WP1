import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from Base_simulator import getCDO

FT = 0.3048
# STAR, aircraft, % MLW, distance first WP -> IAF (NM)
ARR = [("ALBER1Z", "B767-300ER", 80, 69.7), ("PUMAL1Z", "B737", 100, 51.0),
       ("MARTA3Z", "B777-300", 100, 96.3), ("MATEX3Z", "B767-300ER", 80, 102.6),
       ("LOBAR2W", "A319-131", 80, 81.7), ("CASPE2W", "A320-212", 100, 88.6)]
# AIP altitude window at the entry point (FL): (minimum, maximum), None = no limit
WIN = {"ALBER1Z": (110, 250), "PUMAL1Z": (130, 250), "MARTA3Z": (None, 240),
       "MATEX3Z": (None, 280), "LOBAR2W": (None, 280), "CASPE2W": (None, 280)}
# Intermediate waypoints (name, distance to IAF in NM, min FL, max FL)
WP = {"ALBER1Z": [("ENJUC", 17.3, 80, None), ("UCREQ", 10.4, None, 100)],
      "PUMAL1Z": [("BERGA", 39.2, 120, None), ("MAMUK", 19.1, 80, None), ("UCREQ", 10.4, None, 100)],
      "MARTA3Z": [("EBROX", 75.0, 100, None), ("BL463", 10.0, None, 100)],
      "MATEX3Z": [("SENIA", 74.0, 100, None), ("BL463", 10.0, None, 100)],
      "LOBAR2W": [("PEKIS", 45.0, 160, 200), ("BL461", 10.0, None, 100)],
      "CASPE2W": [("MECUH", 47.6, 160, 200), ("VIBOK", 27.5, None, 150), ("BL461", 10.0, None, 100)]}
COL = {"B767-300ER": "#1f4e79", "B777-300": "#a31f34", "B737": "#2e7d32",
       "A320-212": "#e08a00", "A319-131": "#6a3d9a"}
GREEN, RED = "#2e7d32", "#c62828"

def fl_at(traj, dist_nm):
    #Altitude (FL) at a given distance to the IAF
    x, h = traj[0], traj[1]
    return float(np.interp(-dist_nm * 1852, x[::-1], h[::-1])) / FT / 100

def ok(fl, lo, hi):
    return (lo is None or fl >= lo) and (hi is None or fl <= hi)

traj = {(a, p): tuple(np.array(z) for z in getCDO(a, p)) for _, a, p, _ in ARR}

fig, axs = plt.subplots(2, 3, figsize=(7.16, 4.3), sharey=True)
for ax, (star, a, p, d) in zip(axs.flat, ARR):
    x, h = traj[(a, p)][0] / 1852, traj[(a, p)][1] / FT / 100      # NM, FL
    m = x >= -d - 0.5                                               # only the STAR length
    ax.plot(x[m], h[m], color=COL[a], lw=1.3)
    fl_e = fl_at(traj[(a, p)], d)                                   # entry point
    ax.plot(-d, fl_e, "o", ms=4.5, mfc=GREEN if ok(fl_e, *WIN[star]) else RED,
            mec="k", mew=0.5, zorder=5)
    for name, dd, lo, hi in WP[star]:                               # intermediate WPs
        fl = fl_at(traj[(a, p)], dd)
        ax.plot(-dd, fl, "s", ms=3.5, mfc=GREEN if ok(fl, lo, hi) else RED,
                mec="k", mew=0.4, zorder=5)
    ax.set_title(f"{star} – {a} ({p}% MLW)", fontsize=7.5)
    ax.set_xlim(-d - 4, 4); ax.set_ylim(0, 420); ax.grid(alpha=0.25, lw=0.4)
for ax in axs[1]: ax.set_xlabel("Distance to the IAF (NM)")
for ax in axs[:, 0]: ax.set_ylabel("Altitude (FL)")
fig.legend(handles=[
    Line2D([0], [0], marker="o", mfc=RED, mec="k", ls="", ms=4, label="Entry point: non-compliant"),
    Line2D([0], [0], marker="o", mfc=GREEN, mec="k", ls="", ms=4, label="Entry point: compliant"),
    Line2D([0], [0], marker="s", mfc=RED, mec="k", ls="", ms=3.5, label="Intermediate WP: non-compliant"),
    Line2D([0], [0], marker="s", mfc=GREEN, mec="k", ls="", ms=3.5, label="Intermediate WP: compliant")],
    loc="lower center", ncol=2, fontsize=6.5, frameon=False)
fig.tight_layout(rect=(0, 0.09, 1, 1), pad=0.4)
fig.savefig("Fig3_altitude_compliance.png", dpi=300)