import math
import matplotlib.pyplot as plt


# CLASES Y RELLENARLAS

# Clase que tiene toda la información sobre el aircraft en diferentes atributos
# Hay 15 atributos que salen directamente de la tabla del documento WP1-Simulator development

class Aircraft:
    def __init__(self, MLW, S, CD0_app, CD2_app, CD0_clean, CD2_clean, hp_desc,CTdesc_high, CTdesc_low, CTdesc_app, CT1, CT2, CT3, CF1, CF2):
        self.MLW = MLW                    # kg
        self.S = S                        # Superfície del ala (m^2)
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

# Diccionario llamado AIRCRAFT, donde cada elemento es el conjunto del nombre del aircraft y la clase con su información
# Los diccionarios no los vimos en I1, pero su función es relativamente similar a un vector, excepto que cada elemento se compone de
    # dos partes --> key:value. En este en vez de llamar a la información por su posición en el "vector" se le asigna un nombre (key)
    # y este da la información a la que hace referencia (value)

AIRCRAFT = {
    "B767-300ER": Aircraft(145150, 283.5,0.014, 0.049, 0.0174, 0.0459,26418,0.064359, 0.055988, 0.12475,351670, 44673, 0.10129e-9,0.54005,557.82),
    "B777-300": Aircraft(237680, 428.04,0.0173, 0.0484, 0.0157, 0.042,36122,0.044239, 0.041065, 0.092921,425770, 48987, 0.66146e-10,0.87843,3689.7),
    "B737": Aircraft(51710, 124.65,0.027, 0.0441, 0.0235, 0.0445,30152,0.036336, 0.053395, 0.16440,145730, 55638, 0.14200e-10,0.94680,100000),
    "A320-212": Aircraft(64500, 122.6,0.0242, 0.0469, 0.024, 0.0375,12398,0.045711, 0.027207, 0.13981,136050, 52238, 0.26637e-10,0.94000,100000),
    "A319-131": Aircraft(61000, 122.6,0.0284, 0.0376, 0.028, 0.031,27726,0.083084, 0.051765, 0.14767,139000, 58900, 0.57200e-14,0.68800,1670),
}

# Clase que tiene como atributos la información relevante para el gráfico

class Flight:
    def __init__(self, aircraft, MLW_percent):
        self.aircraft = aircraft          # Key de AIRCRAFT
        self.MLW_percent = MLW_percent

# Vector llamado FLIGHTS que tiene en cada posición la clase vuelo

FLIGHTS = [Flight("B767-300ER",100), Flight("B767-300ER",80),
Flight("B777-300",100), Flight("B777-300",80),
Flight("B737",100),Flight("B737",80),
Flight("A320-212",100),Flight("A320-212",80),
Flight("A319-131",100),Flight("A319-131",80)]


# CONSTANTES

G = 9.81
T0 = 288.15             # Temperatura a nivel del mar (K)
P0 = 101325             # Presión a nivel del mar (Pa)
R_GAS = 287.058         # Constante específica del aire seco (J/(kg*K))
LAPSE_RATE = 0.0065     # Gradiente térmico troposférico (K/m)
FT2M = 0.3048           # De ft a m
KT2MS = 0.514444        # De kts a m/s
H_IAF = 1600            # Altura del IAF (m)
H_MAX = 12000           # Altura máxima donde termina la simulación (m)


# FUNCIONES

# Depende de la altura a la que está la aeronave la densidad del aire cambia. No es lo mismo volar a 12000 m que a 1600 m
    # y, por lo tanto, debemos tener eso en cuenta
# El cálculo es el siguiente: por debajo de la troposfera (11000 m) la temperatura baja linealmente y la presión sigue
    # una fórmula específica, pero en la troposfera se mantiene la temperatura constante y la presión se le añade una
    # expresión con exponencial
# Con esta información de presión y temperatura asumimos/tratamos el aire como un gas ideal y, por lo tanto, usamos una
    # variación de la fórmula PV=nRT

def get_isa_density(h_m):
    if h_m <= 11000:
        T=T0-LAPSE_RATE*h_m
        P=P0*(T/ T0)**(G/(R_GAS*LAPSE_RATE))
    else:
        T_11k=T0-LAPSE_RATE*11000   # Temperatura parada en el 216.65 K
        P_11k=P0*(T_11k/T0)**(G/(R_GAS*LAPSE_RATE))
        T=T_11k
        P=P_11k*math.exp(-G*(h_m-11000)/(R_GAS*T))
    return P/(R_GAS*T)

# Para simular el camino que baja cada avión debemos saber desde qué altura parte (h_max_m) y hasta qué altura hace una
    # bajada continua (hasta el IAF), teniendo en cuenta las condiciones de pesos al llegar.
# Los cálculos irán en el siguiente orden: thrust, velocidad mínima de RoD, drag, RoD, fuel flow y el
    # conjunto de altura posición, peso y tiempo.

def getCDO(aircraft_model, MLW_percent):
    avion = AIRCRAFT[aircraft_model]

    # Conversión de unidades
    hp_desc_m=avion.hp_desc*FT2M  # ft -> m
    CT2=avion.CT2*FT2M  # ft -> m
    CT3=avion.CT3/(FT2M**2)  # 1/ft^2 -> 1/m^2
    CF1=avion.CF1/(60*1000)  # kg/(min*kN) -> kg/(s*N)
    CF2=avion.CF2*KT2MS  # knots -> m/s

    # Condiciones iniciales
    x_now=0
    h_now=H_IAF
    m_now=avion.MLW*(MLW_percent/100)
    t_now=0

    x_list, h_list, m_list, t_list=[x_now], [h_now], [m_now], [t_now]

    while h_now<H_MAX:
        density=get_isa_density(h_now)
        area=avion.S
        CT1=avion.CT1

        if h_now<(6000*FT2M):  # Configuración de aproximación (solo por debajo del IAF)
            CD0=avion.CD0_app
            CD2=avion.CD2_app
            CTdesc=avion.CTdesc_app
        else:
            CD0=avion.CD0_clean
            CD2=avion.CD2_clean
            if h_now>hp_desc_m:  # Si estamos en altura de descenso high...
                CTdesc=avion.CTdesc_high
            else:  # O en la low
                CTdesc=avion.CTdesc_low

        # Thrust
        Tmax=CT1*(1-(h_now/CT2)+(CT3*(h_now**2)))
        T_desc=CTdesc*Tmax

        # Velocidad mínima RoD
        term_thrust=T_desc/(m_now*G)
        v_minRoD=math.sqrt(((m_now*G)/(3*density*area*CD0))*(term_thrust+math.sqrt((term_thrust**2)+12*CD0*CD2)))

        # Drag
        CL=(2*m_now*G)/(density*area*(v_minRoD**2))
        D=0.5*density*(v_minRoD**2)*area*(CD0+(CD2*CL**2))

        # RoD
        RoD=v_minRoD*(D-T_desc)/(m_now*G)

        # Fuel flow
        FF=CF1*(1+v_minRoD/CF2)*T_desc

        # Conjunto para los vectores (multiplicamos por 1 para representar el movimiento en 1 segundo, aunque numéricamente sea irrelevante)
        h_next=h_now+RoD*1
        x_next=x_now-v_minRoD*1
        m_next= m_now+FF*1
        t_next=t_now-1

        x_list.append(x_next)
        h_list.append(h_next)
        m_list.append(m_next)
        t_list.append(t_next)

        h_now, x_now, m_now, t_now=h_next, x_next, m_next, t_next

    return x_list, h_list, m_list, t_list

# Ejecuta getCOD para cada vuelo que se encuentra en la lista FLIGHTS y devuelve una lista con los resultados

def run_all_flights():
    flights=FLIGHTS
    results=[]
    for flight in flights:
        x, h, m, t=getCDO(flight.aircraft, flight.MLW_percent)
        results.append({"aircraft": flight.aircraft, "MLW_percent": flight.MLW_percent, "x": x, "h": h, "m": m, "t": t})
    return results

# Función de testing que muestra información relevante en la consola (BORRAR LUEGO SI ES NECESARIO)

def testing(flight_results):
    print("AIRCRAFTS")
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

    print("\n\n")
    print(f"{len(FLIGHTS)} FLIGHTS")
    print("\n")
    for i, flight in enumerate(FLIGHTS):
        print(f" [{i}] aircraft={flight.aircraft!r} " f"MLW_percent={flight.MLW_percent}")

    print("\n\n")
    print("DATOS INICIO/FINAL")
    for res in flight_results:
        n_puntos = len(res["h"])
        print(f"\n{res["aircraft"]} [{int(res["MLW_percent"])}% MLW]")
        print(f"  numero de puntos simulados: {n_puntos}")
        print(f"  x -> inicio: {res["x"][0]:.2f} m   |  final: {res["x"][-1]:.2f} m")
        print(f"  h -> inicio: {res["h"][0]:.2f} m   |  final: {res["h"][-1]:.2f} m")
        print(f"  m -> inicio: {res["m"][0]:.2f} kg  |  final: {res["m"][-1]:.2f} kg")
        print(f"  t -> inicio: {res["t"][0]:.2f} s   |  final: {res["t"][-1]:.2f} s")


# ACCIONADOR DEL CÓDIGO

if __name__ == "__main__":
    flight_results = run_all_flights()

    testing(flight_results)

    plt.figure(figsize=(12, 7))
    for res in flight_results:
        label = f"{res["aircraft"]} [{int(res["MLW_percent"])}% MLW]"
        plt.plot(res["x"], res["h"], label=label)

    plt.xlabel("x(m)")
    plt.ylabel("h(m)")
    plt.title("CDO simulation")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.show()