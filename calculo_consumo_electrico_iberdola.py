# EJEMPLO DE USO
# Supongamos que tenemos una maquina de vending de Coca-cola que consume 105 Watios por hora
# Queremos calcular el gasto que supondria tenerlo conectado durante el mes de Julio de 2025
# python3 calculo_consumo_electrico_iberdola.py --kwh 0.105 --mes 7 --anio 2025
# https://selectra.es/energia/empresas/tarifas-luz/30-td

from datetime import datetime, timedelta
import calendar
import argparse

# Impuestos
porcentaje_impuesto_electrico = 0.051127  # 5,1127%
porcentaje_iva = 0.21                     # 21%

class Tarifa30TD:
    def __init__(self, potencia_kw, precios_kwh, precios_potencia):
        self.potencia_kw = potencia_kw
        self.precios_kwh = precios_kwh  # Dict P1-P6
        self.precios_potencia = precios_potencia  # Dict P1-P6
        self.estaciones = {
            'alta': [1, 2, 7, 12], # Temporada alta: meses con mayor consumo electrico: Enero, Febrero y Diciembre por la calefacción, Julio por el Aire Acondicionado
            'media-alta': [3, 11],
            'media': [6, 8, 9],
            'baja': [4, 5, 10]
        }
        self.horarios = {
            'alta': {
                'P6': [(0, 8)],
                'P1': [(9, 14), (18, 22)],
                'P2': [(8, 9), (14, 18), (22, 24)]
            },
            'media-alta': {
                'P6': [(0, 8)],
                'P2': [(9, 14), (18, 22)],
                'P3': [(8, 9), (14, 18), (22, 24)]
            },
            'media': {
                'P6': [(0, 8)],
                'P3': [(9, 14), (18, 22)],
                'P4': [(8, 9), (14, 18), (22, 24)]
            },
            'baja': {
                'P6': [(0, 8)],
                'P4': [(9, 14), (18, 22)],
                'P5': [(8, 9), (14, 18), (22, 24)]
            }
        }

        # Festivos 2025 para Madrid (nacionales + autonómicos + locales)
        self.festivos = [
            datetime(2025,1,1),    # Año Nuevo
            datetime(2025,1,6),    # Reyes
            datetime(2025,4,17),   # Jueves Santo
            datetime(2025,4,18),   # Viernes Santo
            datetime(2025,5,1),    # Día del Trabajo
            datetime(2025,5,2),    # Comunidad de Madrid
            datetime(2025,5,15),   # San Isidro (local)
            datetime(2025,7,25),   # Santiago Apóstol
            datetime(2025,8,15),   # Asunción
            datetime(2025,11,1),   # Todos los Santos
            datetime(2025,11,10),  # Almudena (local trasladado)
            datetime(2025,12,6),   # Constitución
            datetime(2025,12,8),   # Inmaculada
            datetime(2025,12,25)   # Navidad
        ]

    def determinar_estacion(self, fecha):
        _mes = fecha.month
        for estacion, meses in self.estaciones.items():
            if _mes in meses:
                return estacion
        return 'baja'

    def es_finde_o_festivo(self, fecha):
        # Verifica si es fin de semana o festivo
        if fecha.weekday() >= 5:  # Sábado=5, Domingo=6
            return True
        return any(fecha.date() == festivo.date() for festivo in self.festivos)

    def calcular_consumo(self, fecha_inicio, dias, consumo_horario_kwh):
        def _dias_en_mes(fecha):
            año = fecha.year
            mes = fecha.month
            _, num_dias = calendar.monthrange(año, mes)
            return num_dias

        consumo = {f'P{i}': 0 for i in range(1,7)}
        for dia in range(dias):
            fecha = fecha_inicio + timedelta(days=dia)
            if self.es_finde_o_festivo(fecha):
                consumo['P6'] += 24 * consumo_horario_kwh
                continue
            
            estacion = self.determinar_estacion(fecha)
            for periodo, tramos in self.horarios[estacion].items():
                for tramo in tramos:
                    horas = min(tramo[1], 24) - max(tramo[0], 0)
                    consumo[periodo] += horas * consumo_horario_kwh
        
        return consumo

    def calcular_coste(self, consumo, dias):
        # Coste energía
        coste_energia = sum(consumo[p] * self.precios_kwh[p] for p in consumo)
        
        # De momento ignorar calculo potencia, nos centramos el calculo del consumo de solo un dispositivo
        # Coste potencia (según factura)
        # coste_potencia = sum(self.potencia_kw * dias * self.precios_potencia[p] 
        #                    for p in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'])
        coste_potencia = 0

        # Impuestos
        impuesto_electrico = (coste_energia + coste_potencia) * porcentaje_impuesto_electrico
        iva = (coste_energia + coste_potencia + impuesto_electrico) * porcentaje_iva
        
        return {
            'consumo_kwh': consumo,
            'coste_energia': coste_energia,
            'coste_potencia': coste_potencia,
            'impuesto_electrico': impuesto_electrico,
            'iva': iva,
            'total': coste_energia + coste_potencia + impuesto_electrico + iva
        }

def dias_en_mes(fecha):
    año = fecha.year
    mes = fecha.month
    _, num_dias = calendar.monthrange(año, mes)
    return num_dias

# Ejemplo con datos de tu factura (febrero 2025 - temporada alta)
config = {
    'potencia_kw': 50,
    'precios_kwh': {'P1': 0.251102, 'P2': 0.227589, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0.185546},
    'precios_potencia': {'P1': 0.062459, 'P2': 0.032716, 'P3': 0.014489, 
                        'P4': 0.012677, 'P5': 0.013355, 'P6': 0.01076}
}



# Definir los argumentos
parser = argparse.ArgumentParser(description="Calcula el coste eléctrico para un consumo y mes dados.")
parser.add_argument('--kwh', type=float, required=True, help='Consumo total en kWh del periodo')
parser.add_argument('--mes', type=int, required=True, help='Mes (1-12)')
parser.add_argument('--anio', type=int, default=datetime.now().year, help='Año (por defecto, el actual)')
args = parser.parse_args()
# Supongamos una máquina de vending de Coca-cola consume un promedio de 105 Watios/hora
consumo_dispositivo = args.kwh # consumo constante 105W = 0.1 kW
#Durante el mes de febrero
mes = datetime(args.anio, args.mes,1)


tarifa = Tarifa30TD(**config)
dias_del_mes = dias_en_mes(mes)
consumo = tarifa.calcular_consumo(mes, dias_del_mes, consumo_dispositivo)
resultado = tarifa.calcular_coste(consumo, dias_del_mes)

# Resultados
print(f"Consumo por periodo (kWh):")
for p, v in resultado['consumo_kwh'].items():
    print(f"{p}: {v:.2f} kWh")

print(f"Coste total: {resultado['total']:.2f}€")
print(f"\nDesglose:")
print(f"- Energía: {resultado['coste_energia']:.2f}€")
# print(f"- Potencia: {resultado['coste_potencia']:.2f}€")
print(f"- Impuesto eléctrico: {resultado['impuesto_electrico']:.2f}€")
print(f"- IVA: {resultado['iva']:.2f}€")
