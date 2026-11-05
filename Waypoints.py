import matplotlib.pyplot as plt
from Base_simulator import getCDO


# CONSTANTS

NM2M = 1852      # NM --> m
FT2M = 0.3048    # ft --> m
GREEN = "#2e7d32"
RED = "#c62828"

# Dictionary named COLORS, every element has the aircraft as its key and a color as value

COLORS = {"B767-300ER": "#1f4e79", "B777-300": "#a31f34", "B737": "#2e7d32","A320-212": "#e08a00", "A319-131": "#6a3d9a"}


# CLASSES

# Class that has waypoint information and if it complies

class Waypoint:
    def __init__(self, name, dist, fl_min, fl_max):
        self.name = name          # Nombre del waypoint
        self.dist = dist          # Distancia al IAF (NM)
        self.fl_min = fl_min      # FL mínimo del AIP
        self.fl_max = fl_max      # FL máximo del AIP
        self.fl_cdo = None        # FL al que pasa el CDO por este waypoint
        self.ok = None            # True si cumple la ventana

# Class for the path the aircraft will follow with its waypoints

class Path:
    def __init__(self, star, aircraft, MLW_percent, waypoints):
        self.star = star
        self.aircraft = aircraft
        self.MLW_percent = MLW_percent
        self.waypoints = waypoints


# Vector named STARS with the previous class

STARS = [
    Path("ALBER1Z", "B767-300ER", 80, [
        Waypoint("ALBER", 69.7, 110, 250), Waypoint("ENJUC", 17.3, 80, None), Waypoint("UCREQ", 10.4, None, 100)]),
    Path("PUMAL1Z", "B737", 100, [
        Waypoint("PUMAL", 51.0, 130, 250), Waypoint("BERGA", 39.2, 120, None), Waypoint("MAMUK", 19.1, 80, None),
        Waypoint("UCREQ", 10.4, None, 100)]),
    Path("MARTA3Z", "B777-300", 100, [
        Waypoint("MARTA", 96.3, None, 240), Waypoint("EBROX", 75.0, 100, None), Waypoint("BL463", 10.0, None, 100)]),
    Path("MATEX3Z", "B767-300ER", 80, [
        Waypoint("MATEX", 102.6, None, 280), Waypoint("SENIA", 74.0, 100, None), Waypoint("BL463", 10.0, None, 100)]),
    Path("LOBAR2W", "A319-131", 80, [
        Waypoint("LOBAR", 81.7, None, 280), Waypoint("PEKIS", 45.0, 160, 200), Waypoint("BL461", 10.0, None, 100)]),
    Path("CASPE2W", "A320-212", 100, [
        Waypoint("CASPE", 88.6, None, 280), Waypoint("MECUH", 47.6, 160, 200), Waypoint("VIBOK", 27.5, None, 150),
        Waypoint("BL461", 10.0, None, 100)]),
]


# FUNCTIONS

# Gives the FL of CDO

def get_fl_at(x, h, dist_nm):
    d=dist_nm*NM2M
    i=0
    while x[i]>-d:
        i+=1
    return h[i]/FT2M/100

# Cheks if the FL is inside the window of a waypoint

def is_ok(fl, fl_min, fl_max):
    if (fl_min is not None and fl<fl_min) or (fl_max is not None and fl>fl_max):
        return False
    return True

# Returns position and uses previous functions

def check_star(star_check):
    x, h, m, t = getCDO(star_check.aircraft, star_check.MLW_percent)
    for wp in star_check.waypoints:
        wp.fl_cdo = get_fl_at(x, h, wp.dist)
        wp.ok = is_ok(wp.fl_cdo, wp.fl_min, wp.fl_max)
    return x, h

# Plot the path of an aircraft starting at its STAR entry points

def plot_star(star_check, x, h):
    entry_dist = star_check.waypoints[0].dist

    x_nm = []
    h_fl = []
    for i in range(len(x)):
        if x[i]/NM2M >=-entry_dist-0.5:      # solo hasta el punto de entrada
            x_nm.append(x[i]/NM2M)
            h_fl.append(h[i] / FT2M / 100)

    plt.figure(figsize=(8, 5))
    plt.plot(x_nm, h_fl, color=COLORS[star_check.aircraft], linewidth=1.5)

    for i, wp in enumerate(star_check.waypoints):
        color = GREEN if wp.ok else RED
        marker = "o" if i==0 else "s"   # Starts with a circle waypoints with a square
        plt.plot(-wp.dist, wp.fl_cdo, marker, color=color, markeredgecolor="black", markersize=7, zorder=5)
        plt.text(-wp.dist, wp.fl_cdo + 10, wp.name, ha="center", fontsize=8)

    # Legend props
    plt.plot([], [], "o", color=GREEN, markeredgecolor="black", label="Compliant")
    plt.plot([], [], "o", color=RED, markeredgecolor="black", label="Non-compliant")

    plt.xlim(-entry_dist - 4, 4)
    plt.ylim(bottom=0)
    plt.xlabel("Distance to the IAF (NM)")
    plt.ylabel("Altitude (FL)")
    plt.title(f"{star_check.star} - {star_check.aircraft} ({star_check.MLW_percent}% MLW)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()

# Testing shown on the console

def print_star(star_check):
    print(f"\n{star_check.star} ({star_check.aircraft}, {star_check.MLW_percent}% MLW)")
    print(f"  {'WP':<8}{'Dist[NM]':>9}{'FL CDO':>8}{'FL min':>8}{'FL max':>8}{'Works?':>8}")
    for wp in star_check.waypoints:
        result ="YES" if wp.ok else "NO"
        print(f"  {wp.name:<8}{wp.dist:>9.1f}{wp.fl_cdo:>8.0f}{limit_text(wp.fl_min):>8}{limit_text(wp.fl_max):>8}{result:>8}")

def limit_text(value):
    if value is None:
        return "-"
    return str(value)


# CODE STARTER

if __name__ == "__main__":
    for star_check in STARS:
        x, h = check_star(star_check)
        print_star(star_check)
        plot_star(star_check, x, h)
    plt.show()