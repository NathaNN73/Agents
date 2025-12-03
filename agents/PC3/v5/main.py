import asyncio
import sys
from parking_agent import ParkingAgent
from http_server import WebServer
from config import *

async def main():
    print("🅿️ SISTEMA DE ESTACIONAMIENTO INTELIGENTE")
    
    # Crea agente
    print("Inicializando agente de parking...")
    agent = ParkingAgent(AGENT_JID, AGENT_PASSWORD)
    await agent.setup()
    
    # Crear y arrancar servidor web en hilo separado
    web_server = WebServer(agent)
    web_server.start_in_thread()
    
    print("✅ SISTEMA INICIADO")
    print(f"Interfaz web disponible en: http://localhost:{WEB_PORT}")
    print()
    print("Ctrl+C para detener sistema")
    print()
    
    # Ejecuta el sistema
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
                    await agent.update_parking_system()
                await asyncio.sleep(agent.step_delay)
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo sistema...")
        sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Sistema detenido")
        sys.exit(0)
