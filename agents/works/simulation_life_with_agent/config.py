# Dimensiones del mapa
MAP_WIDTH = 800
MAP_HEIGHT = 600

# Parámetros de población
INITIAL_POPULATION = 25 
MAX_POPULATION = 200
FOOD_PER_DAY = 40

# Parámetros de mutación
MUTATION_RATE = 0.1  # 10% de probabilidad de mutación
MUTATION_STRENGTH = 0.15  # ±15% de cambio en el rasgo

# Rangos iniciales de rasgos
SPEED_RANGE = (2.0, 5.0)
SIZE_RANGE = (0.5, 2.0)
SENSE_RANGE = (80.0, 180.0)

# Parámetros de energía
BASE_ENERGY = 1000.0
FOOD_ENERGY = 200.0
BLOB_ENERGY = 500.0 

# Parámetros de comportamiento
SIZE_EAT_THRESHOLD = 1.2
FLEE_DISTANCE_MULTIPLIER = 1.5

# Servidor web
WEB_PORT = 10000


# XMPP (SPADE)
XMPP_SERVER = "localhost"
AGENT_JID = "z3r007@xmpp.jp"
AGENT_PASSWORD = "12356890"