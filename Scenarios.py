import numpy as np
from Base_simulator import getCDO


# CONSTANTES

NM2M=1852                          # De millas náuticas a metros
T_ARRIVAL=(11*3600)+(45*60)    # 11:45:00 en seconds desde las 00:00:00 (hora de arrival al primer WP de cada STAR)
SEP=120                          # Separación en el IAF del Scenario 2 (2 minutos)


# CLASE LLEGADA

# Cada arrival es un avión (con su % de MLW en el IAF) que vuela una STAR concreta hacia el IAF (SLL, 6000 ft)
# La distancia es la suma de los tramos TF de la STAR (AIP de ENAIRE, AD 2-LEBL STAR 3.4 - 3.6) desde el primer WP hasta el IAF
# Los atributos de abajo (alt_wp, ...) se rellenan después con los cálculos

class Arrival:
    def __init__(self, aircraft, star, MLW_percent, dist):
        self.aircraft=aircraft          # Nombre del modelo
        self.star=star                  # nombre del STAR
        self.MLW_percent=MLW_percent    # % del Maximum Landing Weight
        self.dist=dist                  # Del primer WP de la STAR al IAF (NM)
        self.alt_wp=None          # Altitud en el primer WP (la que da el CDO) (m)
        self.time=None                  # Tiempo del primer WP al IAF (s)
        self.toa_iaf_1=None             # Hora de arrival al IAF en el Scenario 1 (s)
        self.order=None                 # Posición en la sequence
        self.sep_prev_1=None            # s, separación con el anterior en el IAF (Scenario 1)
        self.toa_iaf_2=None             # s, hora de arrival al IAF en el Scenario 2
        self.delay_2=None               # s, retraso aplicado (negativo = adelanto)
        self.toa_wp_2=None        # s, hora de arrival al primer WP en el Scenario 2

# Vector llamado ARRIVALS que tiene en cada posición la clase vuelo
# La distancia es la suma de las distancias entre diferentes waypoints hasta el IAF (a 6000 ft)
ARRIVALS = [
    Arrival("B767-300ER", "ALBER1Z", 80,  19.5+22.4+10.5+6.9+10.4),    # ALBER-CUTXE-UTHAN-ENJUC-UCREQ-SLL
    Arrival("B737",       "PUMAL1Z", 100, 11.8+14.2+5.9+8.7+10.4),     # PUMAL-BERGA-KOSIT-MAMUK-UCREQ-SLL
    Arrival("B777-300",   "MARTA3Z", 100, 21.3+26.3+21.2+17.5+10),   # MARTA-EBROX-RES-VLA-BL463-SLL
    Arrival("B767-300ER", "MATEX3Z", 80,  28.6+25.3+21.2+17.5+10),   # MATEX-SENIA-RES-VLA-BL463-SLL
    Arrival("A319-131",   "LOBAR2W", 80,  36.7+35+10),                 # LOBAR-PEKIS-BL461-SLL
    Arrival("A320-212",   "CASPE2W", 100, 41.0+20.1+17.5+10),          # CASPE-MECUH-VIBOK-BL461-SLL
]


# FUNCIONES

# Pasa los seconds al formato de HH:MM:SS

def hms(seconds):
    s=int(round(seconds))
    return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

# Para una arrival, simula su CDO y mira a qué altura y cuánto tiempo antes del IAF estaba cuando le quedaban dist
# getCDO devuelve x (<= 0), h y t (<= 0) desde el IAF hacia atrás. np.interp necesita la x creciente, por eso se dan la vuelta las listas

def calcular_cdo(arrival):
    x, h, m, t=getCDO(arrival.aircraft, arrival.MLW_percent)
    d=arrival.dist*NM2M
    if d>-x[-1]:
        raise ValueError(f"{arrival.star}: la STAR ({d:.0f} m) es mas larga que el CDO simulado ({-x[-1]:.0f} m)")
    # Usando la función de interpolar de numpy
    arrival.alt_wp=float(np.interp(-d,x[::-1],h[::-1]))
    arrival.time=float(-np.interp(-d,x[::-1],t[::-1]))

# Función que atribuye el orden de llegada al IAF en el scenario 1

def key_toa_1(arrival):
    return arrival.toa_iaf_1


# SCENARIO 1: todos llegan al primer WP a las 11:45:00

def escenario_1():
    for arrival in ARRIVALS:
        calcular_cdo(arrival)
        arrival.toa_iaf_1=T_ARRIVAL+arrival.time

    sequence=sorted(ARRIVALS,key=key_toa_1)  # La key indica el parametro que usamos para ordenar las arrivals (la posición)

    for i, arrival in enumerate(sequence):
        arrival.order=i+1
        if i>0:
            arrival.sep_prev_1=arrival.toa_iaf_1-sequence[i-1].toa_iaf_1
    return sequence


# SCENARIO 2: 2 minutos exactos en el IAF, mismo order de llegada que en scenario 1

def escenario_2(sequence):
    t_first=sequence[0].toa_iaf_1
    for i, arrival in enumerate(sequence):
        arrival.toa_iaf_2=t_first+i*SEP
        arrival.delay_2=arrival.toa_iaf_2-arrival.toa_iaf_1 # Delay en negativo y early en positivo
        arrival.toa_wp_2=T_ARRIVAL+arrival.delay_2

def scenario_1():
    print("SCENARIO 1: arrival simultanea al primer WP a las 11:45:00")
    print(f"{'Aircraft':<11}{'STAR':<9}{'%MLW':>5}{'Dist[km]':>10}{'Alt WP[m]':>11}{'Tiempo[s]':>11}{'ToA IAF':>10}{'order':>7}{'Sep[s]':>8}")
    for arrival in ARRIVALS:
        sep = "-" if arrival.sep_prev_1 is None else f"{arrival.sep_prev_1:.0f}"
        print(f"{arrival.aircraft:<11}{arrival.star:<9}{arrival.MLW_percent:>5}{arrival.dist * NM2M / 1000:>10.1f}{arrival.alt_wp:>11.0f}"
              f"{arrival.time:>11.0f}{hms(arrival.toa_iaf_1):>10}{arrival.order:>7}{sep:>8}")

def scenario_2():
    print("\nSCENARIO 2: 2 minutos exactos en el IAF, mismo order")
    print(f"{'Aircraft':<11}{'STAR':<9}{'%MLW':>5}{'order':>7}{'Alt WP[m]':>11}{'ToA IAF 2':>11}{'Retraso[s]':>12}{'ToA WP 2':>10}")
    for arrival in ARRIVALS:
        print(f"{arrival.aircraft:<11}{arrival.star:<9}{arrival.MLW_percent:>5}{arrival.order:>7}{arrival.alt_wp:>11.0f}"
              f"{hms(arrival.toa_iaf_2):>11}{arrival.delay_2:>+12.0f}{hms(arrival.toa_wp_2):>10}")


# ACCIONADOR DEL CÓDIGO

if __name__ == "__main__":
    sequence=escenario_1()
    escenario_2(sequence)

    scenario_1()
    scenario_2()