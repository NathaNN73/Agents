import asyncio
import sys
from simulation_agent import SimulationAgent
from http_server import WebServer
from config import *


async def main():
    """Función principal que coordina la simulación"""
    print("🧬 SIMULACIÓN DE SELECCIÓN NATURAL")
    
    # Crear agente de simulación
    print("Inicializando agente de simulación...")
    agent = SimulationAgent(AGENT_JID, AGENT_PASSWORD)
    await agent.setup()
    
    # Crear y arrancar servidor web en hilo separado
    web_server = WebServer(agent)
    web_server.start_in_thread()
    
    print("✅ SIMULACIÓN INICIADA")
    print(f"Interfaz web disponible en: http://localhost:{WEB_PORT}/PC3/v5/")
    print()
    print("Ctrl+C para detener simulación")
    print()
    
    # Ejecutar la simulación
    try:
        behaviour = agent.behaviours[0] if agent.behaviours else None
        
        if behaviour:
            while True:
                await behaviour.run()
                await asyncio.sleep(0.01)
        else:
            # Fallback
            while True:
                if not agent.paused:
                    await agent.update_simulation()
                await asyncio.sleep(agent.step_delay)
                
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo simulación...")
        sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Simulación detenida")
        sys.exit(0)
