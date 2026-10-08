import numpy as np
from Base_simulator import getCDO


# CONSTANTES

NM2M=1852                          # De millas náuticas a metros
T_ENTRADA_S=(11*3600)+(45*60)    # 11:45:00 en segundos desde las 00:00:00 (hora de llegada al primer WP de cada STAR)
SEP_S=120                          # Separación en el IAF del Scenario 2 (2 minutos)


# CLASE LLEGADA

# Cada llegada es un avión (con su % de MLW en el IAF) que vuela una STAR concreta hacia el IAF (SLL, 6000 ft)
# La distancia es la suma de los tramos TF de la STAR (AIP de ENAIRE, AD 2-LEBL STAR 3.4 - 3.6) desde el primer WP hasta el IAF
# Los atributos de abajo (alt_entrada_m, ...) se rellenan después con los cálculos

class Llegada:
    def __init__(self, aircraft, star, MLW_percent, dist_nm):
        self.aircraft = aircraft          # Nombre del modelo
        self.star = star                  # nombre del STAR
        self.MLW_percent = MLW_percent    # % del Maximum Landing Weight
        self.dist_nm = dist_nm            # Del primer WP de la STAR al IAF (NM)
        self.alt_entrada_m = None         # Altitud en el primer WP (la que da el CDO) (m)
        self.tiempo_s = None              # Tiempo del primer WP al IAF (s)
        self.toa_iaf_1 = None             # Hora de llegada al IAF en el Scenario 1 (s)
        self.orden = None                 # posición en la secuencia (1 = primero)
        self.sep_prev_1 = None            # s, separación con el anterior en el IAF (Scenario 1)
        self.toa_iaf_2 = None             # s, hora de llegada al IAF en el Scenario 2
        self.retraso_2 = None             # s, retraso aplicado (negativo = adelanto)
        self.toa_entrada_2 = None         # s, hora de llegada al primer WP en el Scenario 2

# Orden y datos del SoW v1.2. Todas las STAR acaban en SLL (IAF) con restricción +6000 ft
LLEGADAS = [
    Llegada("B767-300ER", "ALBER1Z", 80,  19.5 + 22.4 + 10.5 + 6.9 + 10.4),    # ALBER-CUTXE-UTHAN-ENJUC-UCREQ-SLL
    Llegada("B737",       "PUMAL1Z", 100, 11.8 + 14.2 + 5.9 + 8.7 + 10.4),     # PUMAL-BERGA-KOSIT-MAMUK-UCREQ-SLL
    Llegada("B777-300",   "MARTA3Z", 100, 21.3 + 26.3 + 21.2 + 17.5 + 10.0),   # MARTA-EBROX-RES-VLA-BL463-SLL
    Llegada("B767-300ER", "MATEX3Z", 80,  28.6 + 25.3 + 21.2 + 17.5 + 10.0),   # MATEX-SENIA-RES-VLA-BL463-SLL
    Llegada("A319-131",   "LOBAR2W", 80,  36.7 + 35.0 + 10.0),                 # LOBAR-PEKIS-BL461-SLL
    Llegada("A320-212",   "CASPE2W", 100, 41.0 + 20.1 + 17.5 + 10.0),          # CASPE-MECUH-VIBOK-BL461-SLL
]


# FUNCIONES

# Pasa segundos desde las 00:00:00 a texto HH:MM:SS

def hms(segundos):
    s = int(round(segundos))
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"

# Para una llegada, simula su CDO y mira a qué altura y cuánto tiempo antes del IAF estaba cuando le quedaban dist_nm
# getCDO devuelve x (<= 0), h y t (<= 0) desde el IAF hacia atrás. np.interp necesita la x creciente, por eso se dan la vuelta las listas

def calcular_cdo(llegada):
    x, h, m, t = getCDO(llegada.aircraft, llegada.MLW_percent)
    d = llegada.dist_nm * NM2M
    if d > -x[-1]:
        raise ValueError(f"{llegada.star}: la STAR ({d:.0f} m) es mas larga que el CDO simulado ({-x[-1]:.0f} m)")
    llegada.alt_entrada_m = float(np.interp(-d, x[::-1], h[::-1]))
    llegada.tiempo_s = float(-np.interp(-d, x[::-1], t[::-1]))

# Función auxiliar para ordenar según la hora de llegada al IAF del Scenario 1

def clave_toa1(llegada):
    return llegada.toa_iaf_1

# SCENARIO 1: todos llegan al primer WP a las 11:45:00

def escenario_1():
    for ll in LLEGADAS:
        calcular_cdo(ll)
        ll.toa_iaf_1 = T_ENTRADA_S + ll.tiempo_s

    secuencia = sorted(LLEGADAS, key=clave_toa1)
    for i, ll in enumerate(secuencia):
        ll.orden = i + 1
        if i > 0:
            ll.sep_prev_1 = ll.toa_iaf_1 - secuencia[i - 1].toa_iaf_1
    return secuencia

# SCENARIO 2: 2 minutos exactos en el IAF, mismo orden y sin tocar al primero
# Con el orden fijo y el primero sin ajuste, la solución es única: toa_k = toa_primero + 120 * (k-1)
# El tiempo del primer WP al IAF de cada avión no cambia, así que el retraso en el IAF es el mismo que en el primer WP

def escenario_2(secuencia):
    t_primero = secuencia[0].toa_iaf_1
    for i, ll in enumerate(secuencia):
        ll.toa_iaf_2 = t_primero + i * SEP_S
        ll.retraso_2 = ll.toa_iaf_2 - ll.toa_iaf_1
        ll.toa_entrada_2 = T_ENTRADA_S + ll.retraso_2

def imprimir_escenario_1():
    print("SCENARIO 1: llegada simultanea al primer WP a las 11:45:00")
    print(f"{'Aircraft':<11}{'STAR':<9}{'%MLW':>5}{'Dist[km]':>10}{'Alt WP[m]':>11}{'Tiempo[s]':>11}{'ToA IAF':>10}{'Orden':>7}{'Sep[s]':>8}")
    for ll in LLEGADAS:
        sep = "-" if ll.sep_prev_1 is None else f"{ll.sep_prev_1:.0f}"
        print(f"{ll.aircraft:<11}{ll.star:<9}{ll.MLW_percent:>5}{ll.dist_nm * NM2M / 1000:>10.1f}{ll.alt_entrada_m:>11.0f}"
              f"{ll.tiempo_s:>11.0f}{hms(ll.toa_iaf_1):>10}{ll.orden:>7}{sep:>8}")

def imprimir_escenario_2():
    print("\nSCENARIO 2: 2 minutos exactos en el IAF, mismo orden")
    print(f"{'Aircraft':<11}{'STAR':<9}{'%MLW':>5}{'Orden':>7}{'Alt WP[m]':>11}{'ToA IAF 2':>11}{'Retraso[s]':>12}{'ToA WP 2':>10}")
    for ll in LLEGADAS:
        print(f"{ll.aircraft:<11}{ll.star:<9}{ll.MLW_percent:>5}{ll.orden:>7}{ll.alt_entrada_m:>11.0f}"
              f"{hms(ll.toa_iaf_2):>11}{ll.retraso_2:>+12.0f}{hms(ll.toa_entrada_2):>10}")


# ACCIONADOR DEL CÓDIGO

if __name__ == "__main__":
    secuencia = escenario_1()
    escenario_2(secuencia)

    imprimir_escenario_1()
    imprimir_escenario_2()