"""
Punto de entrada principal para la simulación multi-agente
"""
import asyncio
import sys
from environment_agent import EnvironmentAgent
from blob_agent import BlobAgent
from http_server import WebServer
from config import *
from agent_utils import AgentUtils


class SimulationManager:
    """Administrador de la simulación multi-agente"""
    
    def __init__(self):
        self.environment_agent = None
        self.blob_agents = []
        self.web_server = None
        
    async def initialize(self):
        """Inicializa todos los agentes"""
        print("🧬 SIMULACIÓN DE SELECCIÓN NATURAL - MULTI-AGENTE")
        print("=" * 60)
        print(f"📡 Servidor XMPP: {XMPP_DOMAIN}")
        
        # Inicializar agente de entorno
        print(f"\n1️⃣ Inicializando agente de entorno ({ENVIRONMENT_JID})...")
        self.environment_agent = EnvironmentAgent(ENVIRONMENT_JID, ENVIRONMENT_PASSWORD)
        await self.environment_agent.start()
        # await self.environment_agent.setup() <-- ELIMINADO
        
        # Esperar un momento para que el entorno esté listo
        await asyncio.sleep(2)
        
        # Iniciar servidor web
        print("\n2️⃣ Iniciando servidor web...")
        self.web_server = WebServer(self.environment_agent)
        self.web_server.start_in_thread()
        print(f"🌐 Interfaz web disponible en: http://localhost:{WEB_PORT}")
        
        # Crear población inicial de blob agents
        print(f"\n3️⃣ Creando población inicial de {INITIAL_POPULATION} blobs...")
        await self._create_initial_population()
        
        print("\n" + "=" * 60)
        print("✅ SIMULACIÓN INICIADA")
        print(f"🌐 Interfaz web: http://localhost:{WEB_PORT}")
        print(f"🐛 Población inicial: {len(self.blob_agents)} blobs")
        print("\nPresiona Ctrl+C para detener la simulación")
        print("=" * 60 + "\n")
    
    async def _create_initial_population(self):
        """Crea la población inicial de blobs"""
        initial_speed, initial_size, initial_sense = AgentUtils.get_initial_traits()
        
        successful_blobs = 0
        failed_blobs = 0
        
        for i in range(INITIAL_POPULATION):
            blob_id = AgentUtils.get_next_blob_id()
            jid = AgentUtils.generate_blob_jid(blob_id)
            x, y = AgentUtils.generate_random_position()
            
            try:
                # Crear y arrancar blob agent con su propia cuenta XMPP
                blob = BlobAgent(
                    jid, BLOB_PASSWORD, blob_id,
                    x, y, initial_speed, initial_size, initial_sense,
                    generation=0
                )
                
                print(f"  Conectando {jid}...")
                await blob.start()
                # await blob.setup()  <-- ELIMINADO: SPADE llama a setup() automáticamente
                self.blob_agents.append(blob)
                successful_blobs += 1
                print(f"  ✅ {jid} conectado")
                
                # Pequeña pausa para evitar sobrecarga
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed_blobs += 1
                print(f"  ❌ Error conectando {jid}: {str(e)}")
                continue
        
        print(f"\n✅ {successful_blobs} blobs conectados exitosamente")
        if failed_blobs > 0:
            print(f"⚠️  {failed_blobs} blobs fallaron al conectar")
        
        if successful_blobs == 0:
            raise Exception("No se pudo conectar ningún blob. Verifica las credenciales XMPP.")
    
    async def run(self):
        """Ejecuta la simulación"""
        try:
            # Mantener la simulación corriendo
            while True:
                await asyncio.sleep(1)
                
                # Verificar si hay blobs vivos
                alive_count = sum(1 for b in self.blob_agents if b.alive)
                
                # Si todos murieron, podríamos reiniciar (opcional)
                if alive_count == 0 and len(self.blob_agents) > 0:
                    print("\n⚠️ Todos los blobs han muerto")
                    # Aquí podrías implementar lógica de reinicio
                
        except KeyboardInterrupt:
            print("\n\n🛑 Deteniendo simulación...")
            await self.shutdown()
    
    async def shutdown(self):
        """Detiene todos los agentes"""
        print("Deteniendo blobs...")
        for blob in self.blob_agents:
            try:
                await blob.stop()
            except:
                pass
        
        print("Deteniendo agente de entorno...")
        if self.environment_agent:
            try:
                await self.environment_agent.stop()
            except:
                pass
        
        print("✅ Simulación detenida")
        sys.exit(0)


async def main():
    """Función principal"""
    manager = SimulationManager()
    await manager.initialize()
    await manager.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Simulación interrumpida")
        sys.exit(0)
