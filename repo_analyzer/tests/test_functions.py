import pytest
import sys
import os

# Configuración del path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.functions import FunctionsStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.functions'.")

class TestFunctionsStrategyAudit:
    """
    Auditoría de Métricas de Funciones.
    
    Vectores de Ataque:
    1. El "Bug del Padre Fantasma" (Detección de Métodos vs Funciones).
    2. Colisión de Nombres (Scope Global vs Clase).
    3. Complejidad Ciclomática Moderna (Match/Case).
    4. Precisión de LOC y Anidamiento.
    """

    @pytest.fixture
    def strategy(self):
        return FunctionsStrategy()

    # --------------------------------------------------------------------------
    # 1. PRUEBA DE CONTEXTO (Method Detection / Ghost Parent Bug)
    # --------------------------------------------------------------------------
    def test_method_parameter_counting(self, strategy):
        """
        ATACAMOS: La lógica que intenta descontar 'self'.
        FALLO ACTUAL: El AST nativo no tiene atributo .parent.
        RESULTADO: 'is_method' siempre es False. 'self' se cuenta como parámetro.
        """
        code = """
class User:
    def update(self, data, force=False):
        pass
"""
        # Esperamos: 2 parámetros reales ('data', 'force'). 'self' es implícito.
        # El código actual dirá: 3 parámetros.
        results = strategy.compute(code)
        
        # Obtenemos las métricas de 'update'
        # Nota: Si falla por colisión de nombres (ver siguiente test), esto podría fallar antes.
        metrics = results.get("update")
        
        assert metrics is not None, "No se encontró la función 'update'."
        
        # Esta aserción fallará si el código cuenta 'self'
        assert metrics["params"] == 2, \
            f"FALLO DE LÓGICA: Se contó 'self' como parámetro. Detectados: {metrics['params']}. " \
            "Causa probable: Uso de 'node.parent' que no existe en AST estándar."

    # --------------------------------------------------------------------------
    # 2. PRUEBA DE COLISIÓN DE NOMBRES (Data Loss)
    # --------------------------------------------------------------------------
    def test_name_collision_global_vs_class(self, strategy):
        """
        ATACAMOS: Funciones con el mismo nombre en diferentes scopes.
        FALLO ACTUAL: El diccionario usa 'node.name' (ej: 'run') como clave única.
        IMPACTO: Sobrescritura de datos.
        """
        code = """
def run():
    # Función global compleja (CC alta)
    if True:
        if True:
            pass
    pass

class Runner:
    def run(self):
        # Método simple (CC baja)
        pass
"""
        results = strategy.compute(code)
        
        # Deberíamos tener DOS entradas para 'run', o nombres cualificados.
        # Ej: 'run' y 'Runner.run'.
        # El código actual solo tendrá una clave 'run'.
        
        # Verificamos si hemos perdido datos.
        # Si len es 1, una machacó a la otra.
        assert len(results) > 1, \
            "PÉRDIDA DE DATOS: La función global 'run' y el método 'Runner.run' colisionaron."

    # --------------------------------------------------------------------------
    # 3. PRUEBA DE COMPLEJIDAD CICLOMÁTICA (Match/Case)
    # --------------------------------------------------------------------------
    def test_cyclomatic_complexity_modern_python(self, strategy):
        """
        ATACAMOS: Soporte para Python 3.10+ (Match/Case).
        FALLO ACTUAL: Probablemente ignora nodos ast.Match.
        """
        code = """
def router(status):
    match status:      # +1 Decision Point
        case 200:      # +1
            return "OK"
        case 400:      # +1
            return "Bad"
        case 500:      # +1
            return "Error"
    return "Unknown"
"""
        results = strategy.compute(code)
        cc = results["router"]["cc"]
        
        # Base (1) + Match (1) + 3 Cases (3) = 5 (aproximadamente, depende de la métrica exacta)
        # Si ignora el match, dará 1 (flujo lineal).
        assert cc >= 4, f"OBSOLESCENCIA: Complejidad Ciclomática ignoró match/case. CC calculada: {cc}"

    # --------------------------------------------------------------------------
    # 4. PRUEBA DE ANIDAMIENTO (Nesting Depth)
    # --------------------------------------------------------------------------
    def test_max_nesting_calculation(self, strategy):
        """
        Verifica el cálculo de profundidad máxima.
        """
        code = """
def deep_function():
    if True:                # Nivel 1
        for x in range(10): # Nivel 2
            try:            # Nivel 3
                pass
            except:
                pass
"""
        results = strategy.compute(code)
        nesting = results["deep_function"]["max_nesting"]
        
        assert nesting == 3, f"Cálculo de anidamiento incorrecto. Esperado: 3, Obtenido: {nesting}"

    # --------------------------------------------------------------------------
    # 5. PRUEBA DE LOC (Lineas de Código)
    # --------------------------------------------------------------------------
    def test_loc_calculation(self, strategy):
        """
        Verifica que LOC cuente correctamente el rango de líneas.
        """
        code = """
def my_func():
    # linea 1
    # linea 2
    return True
"""
        # La función ocupa desde 'def' hasta 'return'.
        # def (lineno 2) ... return (lineno 5). Total: 5-2+1 = 4 líneas.
        # (Depende de si hay líneas en blanco antes/después dentro del archivo simulado,
        # pero ast.parse ajusta los números de línea relativos al string).
        
        results = strategy.compute(code)
        loc = results["my_func"]["loc"]
        
        # El string empieza con un newline vacío, así que 'def' está en línea 2.
        # Cuerpo tiene 3 líneas + cabecera = 4.
        assert loc == 4, f"Error en cálculo de LOC. Obtenido: {loc}"
