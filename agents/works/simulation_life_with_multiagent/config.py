# Dimensiones del mapa
MAP_WIDTH = 800
MAP_HEIGHT = 600

# Parámetros de población (REDUCIDOS para rendimiento con agentes)
INITIAL_POPULATION = 5  # Reducido de 25 a 10
MAX_POPULATION = 25      # Reducido de 200 a 50
FOOD_PER_DAY = 20        # Reducido proporcionalmente

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

# XMPP (SPADE) - Configuración para multi-agente con cuentas individuales
XMPP_DOMAIN = "@xmpp.jp"

# Agente de entorno
ENVIRONMENT_JID = "z3r007@xmpp.jp"
ENVIRONMENT_PASSWORD = "12356890"

# Configuración de blobs (cuentas individuales blob_001 a blob_025)
BLOB_JID_PREFIX = "blob_"  # Prefijo para generar JIDs
BLOB_PASSWORD = "123456"   # Contraseña común para todos los blobs

# Parámetros de comunicación entre agentes
MESSAGE_TIMEOUT = 5.0  # Timeout para mensajes en segundos
STATE_UPDATE_INTERVAL = 0.1  # Intervalo de actualización de estado (segundos)
POSITION_BROADCAST_INTERVAL = 1.0  # Intervalo para broadcast de posiciones (reducido para rendimiento)
