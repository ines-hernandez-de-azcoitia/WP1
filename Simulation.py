import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# BASE DE DATOS BADA (Anexo B del SoW)
# Unidades convertidas al Sistema Internacional (SI)
# ==============================================================================
AIRCRAFT_DB = {
    'B767-300ER': {
        'MLW': 145150.0,  # kg (Maximum Landing Weight)
        'S': 283.50,  # m^2 (Superficie alar)
        'CD0_app': 0.01400,
        'CD2_app': 0.04900,
        'CD0_clean': 0.01740,
        'CD2_clean': 0.04590,
        'hp_desc': 26418.0,  # ft
        'CTdesc_high': 0.064359,
        'CTdesc_low': 0.055988,
        'CTdesc_app': 0.12475,
        'CT1': 351670.0,  # N
        'CT2': 44673.0,  # ft
        'CT3': 0.10129e-9,  # 1/ft^2
        'CF1': 0.54005 / 60.0 / 1000.0,  # kg/(min*kN) -> kg/(s*N)
        'CF2': 557.82 * 0.514444  # kt -> m/s
    },
    'B777-300': {
        'MLW': 237680.0,
        'S': 428.04,
        'CD0_app': 0.01730,
        'CD2_app': 0.04840,
        'CD0_clean': 0.01570,
        'CD2_clean': 0.04200,
        'hp_desc': 36122.0,
        'CTdesc_high': 0.044239,
        'CTdesc_low': 0.041065,
        'CTdesc_app': 0.092921,
        'CT1': 425770.0,
        'CT2': 48987.0,
        'CT3': 0.66146e-10,
        'CF1': 0.87843 / 60.0 / 1000.0,
        'CF2': 3689.7 * 0.514444
    },
    'B737': {
        'MLW': 51710.0,
        'S': 124.65,
        'CD0_app': 0.02700,
        'CD2_app': 0.04410,
        'CD0_clean': 0.02350,
        'CD2_clean': 0.04450,
        'hp_desc': 30152.0,
        'CTdesc_high': 0.036336,
        'CTdesc_low': 0.053395,
        'CTdesc_app': 0.16440,
        'CT1': 145730.0,
        'CT2': 55638.0,
        'CT3': 0.14200e-10,
        'CF1': 0.94680 / 60.0 / 1000.0,
        'CF2': 100000.0 * 0.514444
    },
    'A320-212': {
        'MLW': 64500.0,
        'S': 122.60,
        'CD0_app': 0.02420,
        'CD2_app': 0.04690,
        'CD0_clean': 0.02400,
        'CD2_clean': 0.03750,
        'hp_desc': 12398.0,
        'CTdesc_high': 0.045711,
        'CTdesc_low': 0.027207,
        'CTdesc_app': 0.13981,
        'CT1': 136050.0,
        'CT2': 52238.0,
        'CT3': 0.26637e-10,
        'CF1': 0.94000 / 60.0 / 1000.0,
        'CF2': 100000.0 * 0.514444
    },
    'A319-131': {
        'MLW': 61000.0,
        'S': 122.60,
        'CD0_app': 0.02840,
        'CD2_app': 0.03760,
        'CD0_clean': 0.02800,
        'CD2_clean': 0.03100,
        'hp_desc': 27726.0,
        'CTdesc_high': 0.083084,
        'CTdesc_low': 0.051765,
        'CTdesc_app': 0.14767,
        'CT1': 139000.0,
        'CT2': 58900.0,
        'CT3': 0.57200e-14,
        'CF1': 0.68800 / 60.0 / 1000.0,
        'CF2': 1670.0 * 0.514444
    }
}

# Constantes físicas y del modelo atmosférico ISA
G = 9.80665  # Aceleración de la gravedad (m/s^2)
T0 = 288.15  # Temperatura a nivel del mar (K)
P0 = 101325.0  # Presión a nivel del mar (Pa)
R_GAS = 287.058  # Constante específica del aire seco (J/(kg*K))
LAPSE_RATE = 0.0065  # Gradiente térmico troposférico (K/m)
M2FT = 3.28084  # Factor de conversión metros a pies
FT2M = 1.0 / M2FT  # Factor de conversión pies a metros


def get_isa_density(h_m):
    """Calcula la densidad del aire ISA a una altitud h (m)."""
    if h_m <= 11000.0:
        T = T0 - LAPSE_RATE * h_m
        P = P0 * (T / T0) ** (G / (R_GAS * LAPSE_RATE))
    else:
        T_11k = T0 - LAPSE_RATE * 11000.0
        P_11k = P0 * (T_11k / T0) ** (G / (R_GAS * LAPSE_RATE))
        T = T_11k
        P = P_11k * np.exp(-G * (h_m - 11000.0) / (R_GAS * T))
    return P / (R_GAS * T)


# ==============================================================================
# FUNCIÓN MODULAR REQUERIDA: getCDO
# ==============================================================================
def getCDO(aircraft_model, MLW_percent, h_iaf_ft=5000.0, FL_max=400.0):
    """
    Simula la trayectoria CDO hacia atrás desde el IAF hasta FL400.
    Parámetros:
        aircraft_model (str): Nombre del modelo (ej. 'B767-300ER', 'A320-212', etc.)
        MLW_percent (float): Porcentaje del Maximum Landing Weight (ej. 80 o 100)
        h_iaf_ft (float): Altitud de llegada al IAF en pies (por defecto 5000 ft)
        FL_max (float): Nivel de vuelo máximo donde finalizar la simulación (FL400)
    Retorna:
        x (np.ndarray): Vector de distancia horizontal en metros (x <= 0 respecto al IAF)
        h (np.ndarray): Vector de altitudes en metros
        t (np.ndarray): Vector de tiempo transcurrido en segundos
        m (np.ndarray): Vector de masa de la aeronave en kg
    """
    ac = AIRCRAFT_DB[aircraft_model]

    # Condiciones iniciales para la integración hacia atrás (IAF at x=0)
    x_curr = 0.0
    h_curr = h_iaf_ft * FT2M
    m_curr = ac['MLW'] * (MLW_percent / 100.0)
    t_curr = 0.0
    dt = 1.0  # Paso de integración = 1 segundo

    h_max_m = FL_max * 100.0 * FT2M

    x_list, h_list, t_list, m_list = [x_curr], [h_curr], [t_curr], [m_curr]

    while h_curr < h_max_m:
        hp_ft = h_curr * M2FT
        rho = get_isa_density(h_curr)

        # Transición de configuración aerodinámica (Approach <= 6000 ft, Clean > 6000 ft)
        if hp_ft <= 6000.0:
            CD0 = ac['CD0_app']
            CD2 = ac['CD2_app']
            CTdesc = ac['CTdesc_app']
        else:
            CD0 = ac['CD0_clean']
            CD2 = ac['CD2_clean']
            if hp_ft > ac['hp_desc']:
                CTdesc = ac['CTdesc_high']
            else:
                CTdesc = ac['CTdesc_low']

        # Cálculo de empuje máximo y empuje en ralentí (Idle Thrust)
        Tmax = ac['CT1'] * (1.0 - hp_ft / ac['CT2'] + ac['CT3'] * (hp_ft ** 2))
        T_idle = CTdesc * Tmax

        # Velocidad de Mínima Tasa de Descenso (v_minRoD)
        term_thrust = T_idle / (m_curr * G)
        inside_sqrt = term_thrust ** 2 + 12.0 * CD0 * CD2
        v_minRoD = np.sqrt((m_curr * G / (3.0 * rho * ac['S'] * CD0)) * (term_thrust + np.sqrt(inside_sqrt)))

        # Resistencia aerodinámica (Drag)
        D = 0.5 * rho * (v_minRoD ** 2) * ac['S'] * CD0 + (2.0 * CD2 * (m_curr * G) ** 2) / (
                    rho * ac['S'] * (v_minRoD ** 2))

        # Tasa de descenso (Rate of Descent)
        RoD = v_minRoD * (D - T_idle) / (m_curr * G)

        # Caudal de combustible (Fuel Flow)
        eta = ac['CF1'] * (1.0 + v_minRoD / ac['CF2'])
        FF = eta * T_idle

        # Paso de integración hacia atrás en el tiempo
        h_next = h_curr + RoD * dt
        x_next = x_curr - v_minRoD * dt  # Distancia negativa alejándose del IAF
        m_next = m_curr + FF * dt  # La masa era mayor antes de consumir combustible
        t_next = t_curr + dt

        x_list.append(x_next)
        h_list.append(h_next)
        t_list.append(t_next)
        m_list.append(m_next)

        h_curr, x_curr, m_curr, t_curr = h_next, x_next, m_next, t_next

    return np.array(x_list), np.array(h_list), np.array(t_list), np.array(m_list)


# ==============================================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN Y GENERACIÓN DE GRÁFICAS
# ==============================================================================
if __name__ == '__main__':
    plt.figure(figsize=(12, 7))

    # Recorremos todas las aeronaves y los dos niveles de masa (80% MLW y 100% MLW)
    for ac_name in AIRCRAFT_DB.keys():
        for weight_pct in [80.0, 100.0]:
            x, h, t, m = getCDO(ac_name, weight_pct, h_iaf_ft=5000.0)

            # Gráfica de distancia (km) vs altitud (m)
            plt.plot(x / 1000.0, h, label=f"{ac_name} [{int(weight_pct)}% MLW]")

    plt.xlabel('Distancia horizontal al IAF, x [km]')
    plt.ylabel('Altitud de vuelo, h [m]')
    plt.title('Simulación de Perfiles CDO con Integración Hacia Atrás (BADA 3.10)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.show()
