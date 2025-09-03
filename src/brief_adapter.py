"""
Adaptador para convertir diferentes formatos de brief al formato esperado por el pipeline
"""

def adapt_brief(input_brief):
    """
    Convierte un brief con formato extendido al formato simple esperado por el pipeline.
    
    Args:
        input_brief: Brief en cualquier formato soportado
        
    Returns:
        Brief en formato estándar del pipeline
    """
    
    # Si ya tiene el formato correcto, devolverlo tal cual
    if all(key in input_brief for key in ['personajes', 'historia', 'mensaje_a_transmitir', 'edad_objetivo']):
        # Verificar tipos correctos
        if isinstance(input_brief['personajes'], list) and \
           isinstance(input_brief['historia'], str) and \
           isinstance(input_brief['mensaje_a_transmitir'], str) and \
           isinstance(input_brief['edad_objetivo'], (int, float)):
            # Si personajes es lista de strings, está OK
            if all(isinstance(p, str) for p in input_brief['personajes']):
                return input_brief
    
    # Adaptar formato extendido
    adapted = {}
    
    # Edad objetivo
    if 'edad_objetivo' in input_brief:
        edad = input_brief['edad_objetivo']
        if isinstance(edad, str):
            # Extraer el primer número del rango "2-6 años" -> 4 (promedio)
            import re
            numeros = re.findall(r'\d+', edad)
            if numeros:
                if len(numeros) >= 2:
                    adapted['edad_objetivo'] = (int(numeros[0]) + int(numeros[1])) // 2
                else:
                    adapted['edad_objetivo'] = int(numeros[0])
            else:
                adapted['edad_objetivo'] = 4  # Default
        else:
            adapted['edad_objetivo'] = edad
    else:
        adapted['edad_objetivo'] = 4  # Default
    
    # Personajes
    if 'personajes' in input_brief:
        personajes = input_brief['personajes']
        if isinstance(personajes, list):
            # Si es lista de objetos, extraer nombres
            if personajes and isinstance(personajes[0], dict):
                adapted['personajes'] = [p.get('nombre', f'Personaje{i+1}') 
                                        for i, p in enumerate(personajes)]
            else:
                # Si ya es lista de strings
                adapted['personajes'] = personajes
        else:
            adapted['personajes'] = ['Protagonista']
    else:
        adapted['personajes'] = ['Protagonista']
    
    # Historia
    adapted['historia'] = input_brief.get('historia', 'Una aventura mágica')
    
    # Mensaje a transmitir
    if 'mensaje_a_transmitir' in input_brief:
        mensaje = input_brief['mensaje_a_transmitir']
        if isinstance(mensaje, dict):
            # Combinar valores y comportamientos
            partes = []
            
            if 'valores_y_desarrollo_emocional' in mensaje:
                valores = mensaje['valores_y_desarrollo_emocional']
                if isinstance(valores, list):
                    partes.extend(valores)
                else:
                    partes.append(str(valores))
            
            if 'comportamientos_a_reforzar' in mensaje:
                comportamientos = mensaje['comportamientos_a_reforzar']
                if isinstance(comportamientos, list):
                    partes.extend(comportamientos)
                else:
                    partes.append(str(comportamientos))
            
            if 'gestion_emocional' in mensaje:
                gestion = mensaje['gestion_emocional']
                if isinstance(gestion, list):
                    partes.extend(gestion)
                else:
                    partes.append(str(gestion))
            
            # Unir todas las partes
            adapted['mensaje_a_transmitir'] = '. '.join(partes) if partes else 'Fomentar valores positivos'
        else:
            adapted['mensaje_a_transmitir'] = str(mensaje)
    else:
        adapted['mensaje_a_transmitir'] = 'Fomentar valores positivos'
    
    return adapted


def validate_adapted_brief(brief):
    """
    Valida que el brief adaptado tenga el formato correcto.
    
    Args:
        brief: Brief a validar
        
    Returns:
        tuple (bool, str): (es_valido, mensaje_error)
    """
    required_fields = ['personajes', 'historia', 'mensaje_a_transmitir', 'edad_objetivo']
    
    # Verificar campos requeridos
    for field in required_fields:
        if field not in brief:
            return False, f"Campo requerido faltante: {field}"
    
    # Verificar tipos
    if not isinstance(brief['personajes'], list):
        return False, "personajes debe ser una lista"
    
    if not all(isinstance(p, str) for p in brief['personajes']):
        return False, "personajes debe ser lista de strings"
    
    if not isinstance(brief['historia'], str):
        return False, "historia debe ser string"
    
    if not isinstance(brief['mensaje_a_transmitir'], str):
        return False, "mensaje_a_transmitir debe ser string"
    
    if not isinstance(brief['edad_objetivo'], (int, float)):
        return False, "edad_objetivo debe ser número"
    
    return True, "Brief válido"