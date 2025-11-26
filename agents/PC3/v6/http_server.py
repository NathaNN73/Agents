"""
Servidor HTTP para la interfaz web de la simulación
"""
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from urllib.parse import urlparse, parse_qs
from config import WEB_PORT


class SimulationHTTPHandler(SimpleHTTPRequestHandler):
    """Manejador HTTP para la simulación multi-agente"""
    
    environment_agent = None
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/state':
            self.send_json_response(self.get_simulation_state())
        elif parsed_path.path == '/api/stats':
            self.send_json_response(self.get_stats())
        else:
            super().do_GET()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/toggle_pause':
            if self.environment_agent:
                paused = self.environment_agent.toggle_pause()
                self.send_json_response({'paused': paused, 'success': True})
            else:
                self.send_json_response({'error': 'Simulation not running'}, status=500)
        
        elif parsed_path.path.startswith('/api/set_speed/'):
            try:
                speed = float(parsed_path.path.split('/')[-1])
                if self.environment_agent:
                    self.environment_agent.set_speed(speed)
                    self.send_json_response({'speed': speed, 'success': True})
                else:
                    self.send_json_response({'error': 'Simulation not running'}, status=500)
            except ValueError:
                self.send_json_response({'error': 'Invalid speed value'}, status=400)
        else:
            self.send_json_response({'error': 'Endpoint not found'}, status=404)
    
    def get_simulation_state(self):
        """Obtiene el estado de la simulación del agente de entorno"""
        if self.environment_agent:
            return self.environment_agent.get_state()
        return {'error': 'Simulation not running'}
    
    def get_stats(self):
        """Obtiene las estadísticas de la simulación"""
        if self.environment_agent:
            return self.environment_agent.stats
        return {'error': 'Simulation not running'}
    
    def send_json_response(self, data, status=200):
        """Envía una respuesta JSON"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        """Suprime logs de HTTP"""
        pass


class WebServer:
    """Servidor web para la interfaz de la simulación"""
    
    def __init__(self, environment_agent):
        self.environment_agent = environment_agent
        SimulationHTTPHandler.environment_agent = environment_agent
        self.server = None
        
    def run(self):
        """Inicia el servidor HTTP"""
        server_address = ('', WEB_PORT)
        self.server = HTTPServer(server_address, SimulationHTTPHandler)
        
        print(f"🌐 Servidor web iniciado en puerto {WEB_PORT}")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
    
    def start_in_thread(self):
        """Inicia el servidor en un hilo separado"""
        thread = Thread(target=self.run, daemon=True)
        thread.start()
        return thread
