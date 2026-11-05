from Base_simulator import getCDO


# CONSTANTS

NM2M=1852                      # MN --> m
T_ARRIVAL=(11*3600)+(45*60)    # 11:45:00 in seconds
SEP=120                        # 2 min separation for Scenario 2


# CLASSES

# Every arrival is an aircraft with its information

class Arrival:
    def __init__(self, aircraft, star, MLW_percent, dist):
        self.aircraft=aircraft         
        self.star=star                  
        self.MLW_percent=MLW_percent   
        self.dist=dist                  # From the first WP to the IAF (NM)
        self.alt_wp=None                # m
        self.time=None                  # Time from the WP to the IAF (s)
        self.toa_iaf_1=None            
        self.order=None
        self.sep_prev_1=None           
        self.toa_iaf_2=None            
        self.delay_2=None               
        self.toa_wp_2=None              

# Vector named ARRIVALS with the previous class

ARRIVALS = [
    Arrival("B767-300ER","ALBER1Z",80,19.5+22.4+10.5+6.9+10.4),    # ALBER-CUTXE-UTHAN-ENJUC-UCREQ-SLL
    Arrival("B737","PUMAL1Z",100, 11.8+14.2+5.9+8.7+10.4),     # PUMAL-BERGA-KOSIT-MAMUK-UCREQ-SLL
    Arrival("B777-300","MARTA3Z",100,21.3+26.3+21.2+17.5+10),     # MARTA-EBROX-RES-VLA-BL463-SLL
    Arrival("B767-300ER","MATEX3Z",80,28.6+25.3+21.2+17.5+10),     # MATEX-SENIA-RES-VLA-BL463-SLL
    Arrival("A319-131","LOBAR2W",80,36.7+35+10),                 # LOBAR-PEKIS-BL461-SLL
    Arrival("A320-212","CASPE2W",100,41.0+20.1+17.5+10),          # CASPE-MECUH-VIBOK-BL461-SLL
]


# FUNCTIONS

# Creates the HH:MM:SS format

def hms(seconds):
    s=int(round(seconds))
    return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

# Simulates the CDO and looks at the time and altitude at the distance from WP to IAF

def calc_cdo(arrival):
    x, h, m, t=getCDO(arrival.aircraft, arrival.MLW_percent)
    d=arrival.dist*NM2M
    # Busca un valor de i donde la distáncia de STAR-IAF sea igual o muy aproximada a un punto simulado
    # Ese punto i tiene la altura y cuanto tiempo se tarda en llegar (porque el número de puntos simulados=segundos pasados)
    i=0
    while x[i]>-d:
        i+=1
    arrival.alt_wp=h[i]
    arrival.time=-t[i]

# Arriving order

def key_toa_1(arrival):
    return arrival.toa_iaf_1


# SCENARIO 1

def scenario_1():
    for arrival in ARRIVALS:
        calc_cdo(arrival)
        arrival.toa_iaf_1=T_ARRIVAL+arrival.time

    sequence=sorted(ARRIVALS,key=key_toa_1)

    for i, arrival in enumerate(sequence):
        arrival.order=i+1
        if i>0:
            arrival.sep_prev_1=arrival.toa_iaf_1-sequence[i-1].toa_iaf_1
    return sequence

def print_scenario_1():
    print("SCENARIO 1: all arrivals to first WP at 11:45:00")
    print(f"{'Aircraft':<11}{'STAR':<9}{'%MLW':>5}{'Dist[km]':>10}{'Alt WP[m]':>11}{'Tiempo[s]':>11}{'ToA IAF':>10}{'order':>7}{'Sep[s]':>8}")
    for arrival in ARRIVALS:
        sep = "-" if arrival.sep_prev_1 is None else f"{arrival.sep_prev_1:.0f}"
        print(f"{arrival.aircraft:<11}{arrival.star:<9}{arrival.MLW_percent:>5}{arrival.dist * NM2M / 1000:>10.1f}{arrival.alt_wp:>11.0f}"
              f"{arrival.time:>11.0f}{hms(arrival.toa_iaf_1):>10}{arrival.order:>7}{sep:>8}")


# SCENARIO 2

def scenario_2(sequence):
    t_first=sequence[0].toa_iaf_1
    for i, arrival in enumerate(sequence):
        arrival.toa_iaf_2=t_first+i*SEP
        arrival.delay_2=arrival.toa_iaf_2-arrival.toa_iaf_1 # Delay en negativo y early en positivo
        arrival.toa_wp_2=T_ARRIVAL+arrival.delay_2

def print_scenario_2():
    print("\nSCENARIO 2: 2 minutes each IAF, same order")
    print(f"{'Aircraft':<11}{'STAR':<9}{'%MLW':>5}{'order':>7}{'Alt WP[m]':>11}{'ToA IAF 2':>11}{'Retraso[s]':>12}{'ToA WP 2':>10}")
    for arrival in ARRIVALS:
        print(f"{arrival.aircraft:<11}{arrival.star:<9}{arrival.MLW_percent:>5}{arrival.order:>7}{arrival.alt_wp:>11.0f}"
              f"{hms(arrival.toa_iaf_2):>11}{arrival.delay_2:>+12.0f}{hms(arrival.toa_wp_2):>10}")


# CODE STARTER

if __name__ == "__main__":
    sequence=scenario_1()
    scenario_2(sequence)

    print_scenario_1()
    print_scenario_2()