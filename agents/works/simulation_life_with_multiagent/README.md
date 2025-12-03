# Simulación de Selección Natural - Multi-Agente (v6)

## 🧬 Descripción

Simulación de selección natural donde cada criatura (blob) es un **agente SPADE autónomo** capaz de comunicarse con otros agentes y con el entorno. Los blobs compiten por recursos, evolucionan y se adaptan a través de generaciones.

### Diferencias con v5

| Característica | v5 | v6 |
|----------------|----|----|
| **Arquitectura** | Objetos simples | Agentes SPADE |
| **Comunicación** | N/A | Mensajes XMPP entre agentes |
| **Autonomía** | Controlados por simulación central | Comportamientos autónomos |
| **Población** | 25 inicial, 200 máx | 10 inicial, 50 máx (optimizado) |

## 🏗️ Arquitectura

### Agentes

1. **EnvironmentAgent** (`environment_agent.py`)
   - Agente central que coordina la simulación
   - Gestiona comida, ciclos de día, y estadísticas
   - Broadcast de información a todos los blobs

2. **BlobAgent** (`blob_agent.py`)
   - Agente autónomo que representa una criatura
   - Comportamientos: búsqueda de comida, supervivencia, huida, caza
   - Comunicación con entorno y otros blobs

### Comunicación

Los agentes se comunican mediante mensajes XMPP definidos en `messages.py`:

- `REGISTER_BLOB`: Blob se registra con el entorno
- `FOOD_SPAWNED`: Entorno informa ubicaciones de comida
- `FOOD_CONSUMED`: Blob reporta consumo de comida
- `BLOB_DIED`: Blob notifica su muerte
- `DAY_END`: Entorno señala fin de día
- `NEARBY_BLOBS`: Entorno informa blobs cercanos

## 📁 Estructura del Proyecto

```
v6/
├── config.py              # Configuración (población, energía, XMPP)
├── messages.py            # Protocolos de mensajes
├── agent_utils.py         # Utilidades (JID generation, distancias, mutaciones)
├── blob_agent.py          # Agente Blob con comportamientos autónomos
├── environment_agent.py   # Agente coordinador del entorno
├── main.py               # Punto de entrada principal
├── http_server.py        # Servidor web para interfaz
├── index.html            # Interfaz web
├── style.css             # Estilos
└── simulation.js         # Lógica frontend
```

## 🚀 Instalación y Ejecución

### Requisitos

```bash
pip install spade
```

### Configuración XMPP

Edita `config.py` para configurar las credenciales XMPP:

```python
ENVIRONMENT_JID = "environment@xmpp.jp"
ENVIRONMENT_PASSWORD = "env12345"
BLOB_PASSWORD = "blob12345"
```

Los JIDs de los blobs se generan dinámicamente: `blob_1@xmpp.jp`, `blob_2@xmpp.jp`, etc.

### Ejecutar Simulación

```bash
cd "d:\Ciclo VIII\Tópicos en Ciencias de la Computación\agents\PC3\v6"
python main.py
```

Abre tu navegador en: `http://localhost:10000`

## 🎮 Controles

- **⏸️ Pausar**: Pausa/reanuda la simulación
- **Velocidad**: Ajusta la velocidad de simulación (0.1x - 3.0x)
- **Presets**: Lento (0.2x), Normal (1.0x), Rápido (2.0x)

## 🧬 Mecánicas de Simulación

### Rasgos de los Blobs

Cada blob tiene tres rasgos heredables:

- **Velocidad** (2.0 - 5.0): Qué tan rápido se mueve
- **Tamaño** (0.5 - 2.0): Tamaño físico (afecta depredación)
- **Sentido** (80.0 - 180.0): Rango de detección

### Comportamientos Autónomos

Los blobs ejecutan comportamientos en orden de prioridad:

1. **Volver a casa**: Si tiene 2+ comida o energía baja (<40%)
2. **Huir**: Si detecta un blob más grande (amenaza)
3. **Cazar**: Si detecta un blob más pequeño (presa)
4. **Buscar comida**: Si detecta comida en su rango
5. **Explorar**: Movimiento aleatorio

### Ciclo de Día

1. Los blobs buscan comida durante el día
2. Al final del día, deben regresar a casa
3. **Supervivencia**:
   - 0 comida → Muere
   - 1 comida → Sobrevive
   - 2+ comida → Sobrevive y se replica

### Evolución

Los descendientes heredan rasgos con posible mutación:
- 10% probabilidad de mutación por rasgo
- ±15% cambio en el valor del rasgo

## 📊 Estadísticas

La interfaz muestra:

- **Día actual**
- **Población**: Blobs vivos
- **Total nacidos/muertos**: Histórico
- **Rasgos promedio**: Velocidad, tamaño, sentido

## ⚙️ Configuración Avanzada

### Ajustar Población

En `config.py`:

```python
INITIAL_POPULATION = 10  # Población inicial
MAX_POPULATION = 50      # Población máxima
FOOD_PER_DAY = 20        # Comida por día
```

### Ajustar Comunicación

```python
MESSAGE_TIMEOUT = 5.0                    # Timeout de mensajes
STATE_UPDATE_INTERVAL = 0.1              # Actualización de estado
POSITION_BROADCAST_INTERVAL = 1.0        # Broadcast de posiciones
```

### Ajustar Energía

```python
BASE_ENERGY = 1000.0    # Energía inicial
FOOD_ENERGY = 200.0     # Energía por comida
BLOB_ENERGY = 500.0     # Energía por comer blob
```

## 🐛 Troubleshooting

### Error de conexión XMPP

Verifica que las credenciales en `config.py` sean correctas y que el servidor XMPP esté accesible.

### Blobs no se mueven

Revisa la consola para mensajes de error. Asegúrate de que el `EnvironmentAgent` esté enviando broadcasts de comida.

### Población se extingue rápidamente

Ajusta los parámetros de energía o aumenta `FOOD_PER_DAY` en `config.py`.

## 📝 Notas Técnicas

- Cada blob es un agente SPADE independiente con su propio ciclo de vida
- La comunicación es asíncrona mediante mensajes XMPP
- El `EnvironmentAgent` coordina sin controlar directamente los blobs
- Los blobs toman decisiones autónomas basadas en su percepción local

## 🎯 Próximas Mejoras

- [ ] Implementar depredación entre blobs
- [ ] Agregar más tipos de comportamientos
- [ ] Visualización de mensajes entre agentes
- [ ] Gráficos de evolución de rasgos
- [ ] Exportar datos de simulación

---

**Desarrollado con SPADE (Smart Python Agent Development Environment)**
