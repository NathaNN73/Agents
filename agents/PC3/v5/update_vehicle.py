"""
Script para actualizar vehicle.py con atributo entry_lane
"""

# Leer el archivo
with open('vehicle.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Agregar entry_lane después de stuck_counter
if 'self.entry_lane' not in content:
    content = content.replace(
        '# Sistema de detección de bloqueos\n        self.stuck_counter = 0\n        self.last_position = (x, y)\n        self.path_recalc_timer = 0.0',
        '# Sistema de detección de bloqueos\n        self.stuck_counter = 0\n        self.last_position = (x, y)\n        self.path_recalc_timer = 0.0\n        \n        # Pista de entrada (para saber por dónde salir si es rechazado)\n        self.entry_lane = "middle"  # Default'
    )

# Guardar
with open('vehicle.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ vehicle.py actualizado con atributo entry_lane")
