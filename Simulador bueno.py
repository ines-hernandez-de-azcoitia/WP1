import math
import matplotlib.pyplot as plt

# Crear una clase que se llame avión y tenga toda la información sobre el propio avión en diferente atributos
# Hay 15 atributos que salen directamente de la tabla del documento WP1-Simulator development

class Avion:
    def __init__(self, MLW, S, CD0_app, CD2_app, CD0_clean, CD2_clean, hp_desc,CTdesc_high, CTdesc_low, CTdesc_app, CT1, CT2, CT3, CF1, CF2):
        self.MLW = MLW                    # kg (Maximum Landing Weight)
        self.S = S                        # m^2 (Superficie del ala)
        self.CD0_app = CD0_app
        self.CD2_app = CD2_app
        self.CD0_clean = CD0_clean
        self.CD2_clean = CD2_clean
        self.hp_desc = hp_desc            # ft
        self.CTdesc_high = CTdesc_high
        self.CTdesc_low = CTdesc_low
        self.CTdesc_app = CTdesc_app
        self.CT1 = CT1                    # N
        self.CT2 = CT2                    # ft
        self.CT3 = CT3                    # 1/ft^2
        self.CF1 = CF1                    # kg/(s*N)
        self.CF2 = CF2                    # m/s

# Diccionario llamado AIRCRAFT, donde cada elemento es el conjunto del nombre del avión y la clase con su infomación
# Los diccionarios no los vimos en I1, pero su función es relativamente similar a un vector, excepto que cada elemento se compone de
    # dos partes --> key : value. En este en vez de llamar a la información por su posición en el "vector" se le asigna un nombre (key)
    # y este da la información a la que hace referencia (value)

AIRCRAFT = {
    'B767-300ER': Avion(145150.0, 283.50,0.01400, 0.04900, 0.01740, 0.04590,26418.0,0.064359, 0.055988, 0.12475,351670.0, 44673.0, 0.10129e-9,0.54005 / 60.0 / 1000.0,557.82 * 0.514444),
    'B777-300': Avion(237680.0, 428.04,0.01730, 0.04840, 0.01570, 0.04200,36122.0,0.044239, 0.041065, 0.092921,425770.0, 48987.0, 0.66146e-10,0.87843 / 60.0 / 1000.0,3689.7 * 0.514444),
    'B737': Avion(51710.0, 124.65,0.02700, 0.04410, 0.02350, 0.04450,30152.0,0.036336, 0.053395, 0.16440,145730.0, 55638.0, 0.14200e-10,0.94680 / 60.0 / 1000.0,100000.0 * 0.514444),
    'A320-212': Avion(64500.0, 122.60,0.02420, 0.04690, 0.02400, 0.03750,12398.0,0.045711, 0.027207, 0.13981,136050.0, 52238.0, 0.26637e-10,0.94000 / 60.0 / 1000.0,100000.0 * 0.514444),
    'A319-131': Avion(61000.0, 122.60,0.02840, 0.03760, 0.02800, 0.03100,27726.0,0.083084, 0.051765, 0.14767,139000.0, 58900.0, 0.57200e-14,0.68800 / 60.0 / 1000.0,1670.0 * 0.514444),
}

# CONSTANTES
G = 9.81  # gravedad (m/s^2)
T0 = 288.15  # Temperatura a nivel del mar (K)
P0 = 101325  # Presión a nivel del mar (Pa)
R_GAS = 287.058  # Constante específica del aire seco (J/(kg*K))
LAPSE_RATE = 0.0065  # Gradiente térmico troposférico (K/m)
M2FT = 3.281  # Factor de conversión metros a pies

# ==============================================================================
# LISTA DE VUELOS A SIMULAR
# Cada vuelo es un objeto de la clase Vuelo (igual que Avion, pero con los
# datos de entrada de la simulacion) en vez de un diccionario.
# El rango vertical de la simulacion (h_iaf_m / h_max_m) se da
# directamente en METROS: empieza en 1600 m y termina en 12000 m.
# (Las formulas internas de empuje siguen necesitando pies para las
# constantes de la BADA, eso no cambia: solo cambian los limites de la
# simulacion, que ahora se dan en metros directamente).
# ==============================================================================

# Crear una clase que se llame vuelos y tenga como atributos la información relevante para el gráfico
# Esta es el nombre del aircraft, el porcentaje de MLW y la altura del IAF (indica en clase como 1600m)

class Vuelo:
    def __init__(self, aircraft, MLW_percent, h_iaf_m=1600.0):
        self.aircraft = aircraft          # nombre del modelo (key de AIRCRAFT)
        self.MLW_percent = MLW_percent    # % del Maximum Landing Weight
        self.h_iaf_m = h_iaf_m            # Altura del Initial Approach Fix (m)

# Vector llamado FLIGHTS que tiene en cada posición la clase vuelo

FLIGHTS = [Vuelo('B767-300ER',100.0,1600.0), Vuelo('B767-300ER',80.0,1600.0),
Vuelo('B777-300',100.0,1600.0), Vuelo('B777-300',80.0,1600.0),
Vuelo('B737',100.0,1600.0),Vuelo('B737',80.0,1600.0),
Vuelo('A320-212',100.0,1600.0),Vuelo('A320-212',80.0,1600.0),
Vuelo('A319-131',100.0,1600.0),Vuelo('A319-131',80.0,1600.0),]

# Depende de la altura a la que está la aeronave la densidad del aire (MIRAR CALC)

def get_isa_density(h_m):
    """Calcula la densidad del aire ISA a una altitud h (m)."""
    if h_m <= 11000.0:
        T = T0 - LAPSE_RATE * h_m
        P = P0 * (T / T0) ** (G / (R_GAS * LAPSE_RATE))
    else:
        T_11k = T0 - LAPSE_RATE * 11000.0
        P_11k = P0 * (T_11k / T0) ** (G / (R_GAS * LAPSE_RATE))
        T = T_11k
        P = P_11k * math.exp(-G * (h_m - 11000.0) / (R_GAS * T))
    return P / (R_GAS * T)


# ==============================================================================
# FUNCIÓN MODULAR REQUERIDA: getCDO
# h_iaf_m y h_max_m se dan directamente en metros (limites de la simulacion).
# Internamente se sigue pasando a pies (hp_ft) solo donde lo exige la formula
# de empuje de la BADA (CT2, CT3, hp_desc siguen definidos en pies).
# La variable independiente de la integracion es la ALTURA (paso dh_m), no el tiempo.
# ==============================================================================

# Para simular el camino que baja cada avión debemos saber desde que altura parte (h_max_m) y hasta que altura hace una
    # bajada continua (hasta el IAF), teniendo en cuenta las condiciones de pesos al llegar.

def getCDO(aircraft_model, MLW_percent, h_iaf_m=1600.0, h_max_m=12000.0, dh_m=10.0):
    """
    Simula la trayectoria CDO hacia atrás desde el IAF hasta h_max_m,
    integrando en altura (sin variable de tiempo).
    Parámetros:
        aircraft_model (str): Nombre del modelo (ej. 'B767-300ER', 'A320-212', etc.)
        MLW_percent (float): Porcentaje del Maximum Landing Weight (ej. 80 o 100)
        h_iaf_m (float): Altitud de llegada al IAF en METROS (por defecto 1600 m)
        h_max_m (float): Altitud máxima donde finalizar la simulación en METROS (por defecto 12000 m)
        dh_m (float): Paso de integración en altura en METROS (por defecto 10 m)
    Retorna:
        x (list): Distancia horizontal en metros (x <= 0 respecto al IAF)
        h (list): Altitudes en metros
        m (list): Masa de la aeronave en kg
    """
    avion = AIRCRAFT[aircraft_model]

    # Condiciones iniciales para la integración hacia atrás (IAF at x=0)
    x_curr = 0.0
    h_curr = h_iaf_m
    m_curr = avion.MLW * (MLW_percent / 100.0)

    x_list, h_list, m_list = [x_curr], [h_curr], [m_curr]

    while h_curr < h_max_m:
        hp_ft = h_curr * M2FT
        rho = get_isa_density(h_curr)

        # Transición de configuración aerodinámica (Approach <= 6000 ft, Clean > 6000 ft)
        if hp_ft <= 6000.0:
            CD0 = avion.CD0_app
            CD2 = avion.CD2_app
            CTdesc = avion.CTdesc_app
        else:
            CD0 = avion.CD0_clean
            CD2 = avion.CD2_clean
            if hp_ft > avion.hp_desc:
                CTdesc = avion.CTdesc_high
            else:
                CTdesc = avion.CTdesc_low

        # Cálculo de empuje máximo y empuje en ralentí (Idle Thrust)
        Tmax = avion.CT1 * (1.0 - hp_ft / avion.CT2 + avion.CT3 * (hp_ft ** 2))
        T_idle = CTdesc * Tmax

        # Velocidad de Mínima Tasa de Descenso (v_minRoD)
        term_thrust = T_idle / (m_curr * G)
        inside_sqrt = term_thrust ** 2 + 12.0 * CD0 * CD2
        v_minRoD = math.sqrt((m_curr * G / (3.0 * rho * avion.S * CD0)) * (term_thrust + math.sqrt(inside_sqrt)))

        # Resistencia aerodinámica (Drag)
        D = 0.5 * rho * (v_minRoD ** 2) * avion.S * CD0 + (2.0 * CD2 * (m_curr * G) ** 2) / (
                    rho * avion.S * (v_minRoD ** 2))

        # Tasa de descenso (Rate of Descent)
        RoD = v_minRoD * (D - T_idle) / (m_curr * G)

        # Caudal de combustible (Fuel Flow)
        eta = avion.CF1 * (1.0 + v_minRoD / avion.CF2)
        FF = eta * T_idle

        # Paso de integración hacia atrás en ALTURA (dt = dh / RoD, por eso no hace falta el tiempo)
        h_next = h_curr + dh_m
        x_next = x_curr - v_minRoD * dh_m / RoD  # Distancia negativa alejándose del IAF
        m_next = m_curr + FF * dh_m / RoD  # La masa era mayor antes de consumir combustible

        x_list.append(x_next)
        h_list.append(h_next)
        m_list.append(m_next)

        h_curr, x_curr, m_curr = h_next, x_next, m_next

    return x_list, h_list, m_list

def run_all_flights(flights=FLIGHTS, h_max_m=12000.0):
    """
    Ejecuta getCDO para cada entrada de la lista `flights` y devuelve una lista
    de resultados, uno por vuelo, cada uno con sus listas x, h, m.
    """
    results = []
    for flight in flights:
        x, h, m = getCDO(
            aircraft_model=flight.aircraft,
            MLW_percent=flight.MLW_percent,
            h_iaf_m=flight.h_iaf_m,
            h_max_m=h_max_m
        )
        results.append({
            'aircraft': flight.aircraft,
            'MLW_percent': flight.MLW_percent,
            'x': x,
            'h': h,
            'm': m
        })
    return results


# Función de testing que muestra la información de los vuelos en la consola

def imprimir_pruebas(flight_results):
    print("AIRCRAFT (datos BADA cargados por avion)")

    for nombre, avion in AIRCRAFT.items():
        print(f"\n{nombre}")
        print(f"  MLW         = {avion.MLW} kg")
        print(f"  S           = {avion.S} m^2")
        print(f"  CD0_app     = {avion.CD0_app}")
        print(f"  CD2_app     = {avion.CD2_app}")
        print(f"  CD0_clean   = {avion.CD0_clean}")
        print(f"  CD2_clean   = {avion.CD2_clean}")
        print(f"  hp_desc     = {avion.hp_desc} ft")
        print(f"  CTdesc_high = {avion.CTdesc_high}")
        print(f"  CTdesc_low  = {avion.CTdesc_low}")
        print(f"  CTdesc_app  = {avion.CTdesc_app}")
        print(f"  CT1         = {avion.CT1} N")
        print(f"  CT2         = {avion.CT2} ft")
        print(f"  CT3         = {avion.CT3} 1/ft^2")
        print(f"  CF1         = {avion.CF1} kg/(s*N)")
        print(f"  CF2         = {avion.CF2} m/s")

    print("\n\n\n")
    print(f"FLIGHTS ({len(FLIGHTS)} vuelos configurados)")
    print("\n")
    for i, flight in enumerate(FLIGHTS):
        print(f"  [{i}] aircraft={flight.aircraft!r}  "
              f"MLW_percent={flight.MLW_percent}  "
              f"h_iaf_m={flight.h_iaf_m}")

    print("\n\n\n")
    print("PUNTOS DE DATOS RELEVANTES POR VUELO (salida de getCDO)")
    print("\n")
    for res in flight_results:
        n_puntos = len(res['h'])
        print(f"\n{res['aircraft']} [{int(res['MLW_percent'])}% MLW]")
        print(f"  numero de puntos simulados: {n_puntos}")
        print(f"  x -> inicio: {res['x'][0]:.2f} m   |  final: {res['x'][-1]:.2f} m")
        print(f"  h -> inicio: {res['h'][0]:.2f} m   |  final: {res['h'][-1]:.2f} m")
        print(f"  m -> inicio: {res['m'][0]:.2f} kg  |  final: {res['m'][-1]:.2f} kg")

# Ejecutador del código

if __name__ == '__main__':
    flight_results = run_all_flights(FLIGHTS)

    imprimir_pruebas(flight_results)

    plt.figure(figsize=(12, 7))
    for res in flight_results:
        label = f"{res['aircraft']} [{int(res['MLW_percent'])}% MLW]"
        plt.plot(res['x'], res['h'], label=label)

    plt.xlabel('Distancia horizontal al IAF, x [m]')
    plt.ylabel('Altitud de vuelo, h [m]')
    plt.title('Simulación de Perfiles CDO con Integración Hacia Atrás (BADA 3.10)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.show()