import sys
import os
from flask import Flask, request

# ==============================================================================
# 1. AJUSTE DE PATH
# ==============================================================================
# Añadimos la carpeta actual al path para que Python encuentre los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports con manejo de errores para darte pistas si algo falla
try:
    from config import ConfigSingleton
    from proxy.proxy_subject import ProxySubject
    from ui.mediator import UIMediator
except ImportError as e:
    print(f"\n[ERROR CRÍTICO DE IMPORTACIÓN]: {e}")
    print("Consejo: Verifica que en 'proxy/proxy_subject.py' la línea del import sea:")
    print("    from .subject_interface import SubjectInterface\n")
    sys.exit(1)

# ==============================================================================
# 2. CONFIGURACIÓN FLASK
# ==============================================================================
# 'template_folder' apunta a donde pusiste los HTMLs
app = Flask(__name__, template_folder="ui/templates")

# ==============================================================================
# 3. COMPOSITION ROOT (Arranque del sistema)
# ==============================================================================

def init_system():
    print("--- 🚀 Arrancando RepoAnalyzer ---")
    
    # 1. Cargar Configuración
    ConfigSingleton.get_instance()

    # 2. Instanciar Proxy (Negocio + BD + Repo)
    # Este objeto ya crea internamente DBManager y RepoManager
    subject = ProxySubject()

    # 3. Instanciar Mediador (UI)
    # Conectamos la interfaz con el Proxy
    mediator = UIMediator(subject)
    
    print("--- ✅ Sistema Listo en http://127.0.0.1:5000 ---")
    return mediator

# Instancia global del mediador
mediator_instance = init_system()

# ==============================================================================
# 4. RUTAS
# ==============================================================================

@app.route("/", methods=["GET"])
def index():
    return mediator_instance.show_index()

@app.route("/analyze", methods=["POST"])
def analyze():
    return mediator_instance.handle_analyze(request.form)

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
