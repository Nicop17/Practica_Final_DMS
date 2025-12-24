import io
import tokenize
from .base import MetricStrategy

class TodosStrategy(MetricStrategy):
    """
    Estrategia para contar comentarios TODO y FIXME.
    """
    def compute(self, source: str) -> int:
        if not isinstance(source, str): 
            raise TypeError("Debe ser string")
        
        count = 0
        try:
            # Convertimos el string a un flujo de bytes/texto que el tokenizer pueda leer
            # tokenize.generate_tokens espera una función readline
            token_stream = io.StringIO(source).readline
            tokens = tokenize.generate_tokens(token_stream)
            
            for toknum, tokval, _, _, _ in tokens:
                # toknum es el tipo de token. Buscamos específicamente COMMENT
                if toknum == tokenize.COMMENT:
                    # tokval es el contenido del comentario (ej: "# TODO: arreglar")
                    comment_upper = tokval.upper()
                    if 'TODO' in comment_upper or 'FIXME' in comment_upper:
                        count += 1
                        
        except (tokenize.TokenError, IndentationError):
            # En caso de código mal formado (ej: comillas sin cerrar), 
            # devolvemos 0 o el conteo parcial para evitar que la app explote.
            pass
            
        return count