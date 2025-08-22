"""
Gestor de versiones de prompts para experimentación y optimización
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class PromptVersionManager:
    """Gestiona múltiples versiones de prompts para testing A/B/C/D"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.agentes_dir = self.base_dir / "agentes"
        self.backups_dir = self.agentes_dir / "backups"
        self.variants_dir = self.base_dir / "config" / "prompt_variants"
        
        # Crear directorios si no existen
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.variants_dir.mkdir(parents=True, exist_ok=True)
        
        # Registro de variantes activas
        self.variants_registry_file = self.variants_dir / "registry.json"
        self.variants_registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Carga el registro de variantes"""
        if self.variants_registry_file.exists():
            with open(self.variants_registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_registry(self):
        """Guarda el registro de variantes"""
        with open(self.variants_registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.variants_registry, f, ensure_ascii=False, indent=2)
    
    def backup_prompt(self, agent_name: str, backup_name: Optional[str] = None) -> str:
        """
        Crea backup del prompt actual de un agente
        
        Args:
            agent_name: Nombre del agente
            backup_name: Nombre opcional para el backup
            
        Returns:
            Path al archivo de backup
        """
        source_file = self.agentes_dir / f"{agent_name}.json"
        
        if not source_file.exists():
            raise FileNotFoundError(f"No existe el agente: {agent_name}")
        
        # Generar nombre de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if backup_name:
            backup_filename = f"{agent_name}_{backup_name}_{timestamp}.json"
        else:
            backup_filename = f"{agent_name}_backup_{timestamp}.json"
        
        backup_path = self.backups_dir / backup_filename
        
        # Copiar archivo
        shutil.copy2(source_file, backup_path)
        logger.info(f"Backup creado: {backup_path}")
        
        return str(backup_path)
    
    def create_variant(self, agent_name: str, variant_name: str, 
                      modifications: Dict[str, Any]) -> str:
        """
        Crea una variante del prompt sin modificar el original
        
        Args:
            agent_name: Nombre del agente
            variant_name: Nombre de la variante (ej: "with_examples", "structured")
            modifications: Diccionario con las modificaciones a aplicar
                - append: Texto a agregar al final
                - prepend: Texto a agregar al inicio
                - replace: Dict de {buscar: reemplazar}
                - full_content: Reemplazo completo del contenido
        
        Returns:
            Path al archivo de la variante
        """
        # Cargar prompt original
        original_file = self.agentes_dir / f"{agent_name}.json"
        if not original_file.exists():
            raise FileNotFoundError(f"No existe el agente: {agent_name}")
        
        with open(original_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # Crear copia para modificar
        variant_data = original_data.copy()
        
        # Aplicar modificaciones
        if "full_content" in modifications:
            # Reemplazo completo
            variant_data["content"] = modifications["full_content"]
        else:
            content = variant_data["content"]
            
            # Prepend
            if "prepend" in modifications:
                content = modifications["prepend"] + "\n\n" + content
            
            # Replace
            if "replace" in modifications:
                for search, replace in modifications["replace"].items():
                    content = content.replace(search, replace)
            
            # Append
            if "append" in modifications:
                content = content + "\n\n" + modifications["append"]
            
            variant_data["content"] = content
        
        # Agregar metadata
        variant_data["_variant_metadata"] = {
            "variant_name": variant_name,
            "based_on": agent_name,
            "created_at": datetime.now().isoformat(),
            "modifications": list(modifications.keys())
        }
        
        # Guardar variante
        variant_file = self.variants_dir / f"{agent_name}_{variant_name}.json"
        with open(variant_file, 'w', encoding='utf-8') as f:
            json.dump(variant_data, f, ensure_ascii=False, indent=2)
        
        # Actualizar registro
        if agent_name not in self.variants_registry:
            self.variants_registry[agent_name] = {}
        
        self.variants_registry[agent_name][variant_name] = {
            "file": str(variant_file),
            "created_at": datetime.now().isoformat(),
            "modifications": modifications
        }
        self._save_registry()
        
        logger.info(f"Variante creada: {variant_file}")
        return str(variant_file)
    
    def load_variant(self, agent_name: str, variant_name: str) -> Dict:
        """
        Carga una variante específica
        
        Args:
            agent_name: Nombre del agente
            variant_name: Nombre de la variante
            
        Returns:
            Contenido de la variante
        """
        if variant_name == "original":
            # Cargar el original
            original_file = self.agentes_dir / f"{agent_name}.json"
            with open(original_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Buscar en registro
        if agent_name in self.variants_registry and variant_name in self.variants_registry[agent_name]:
            variant_file = self.variants_registry[agent_name][variant_name]["file"]
            with open(variant_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Buscar archivo directamente
        variant_file = self.variants_dir / f"{agent_name}_{variant_name}.json"
        if variant_file.exists():
            with open(variant_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        raise FileNotFoundError(f"No existe la variante {variant_name} para {agent_name}")
    
    def apply_variant(self, agent_name: str, variant_name: str) -> str:
        """
        Aplica una variante como el prompt activo (modifica el archivo original)
        ADVERTENCIA: Hacer backup antes!
        
        Args:
            agent_name: Nombre del agente
            variant_name: Nombre de la variante a aplicar
            
        Returns:
            Path al backup del original
        """
        # Crear backup automático
        backup_path = self.backup_prompt(agent_name, "before_variant")
        
        # Cargar variante
        variant_data = self.load_variant(agent_name, variant_name)
        
        # Remover metadata de variante si existe
        if "_variant_metadata" in variant_data:
            del variant_data["_variant_metadata"]
        
        # Aplicar al archivo original
        original_file = self.agentes_dir / f"{agent_name}.json"
        with open(original_file, 'w', encoding='utf-8') as f:
            json.dump(variant_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Variante {variant_name} aplicada a {agent_name}. Backup en: {backup_path}")
        return backup_path
    
    def restore_original(self, agent_name: str, backup_path: Optional[str] = None) -> bool:
        """
        Restaura el prompt original desde un backup
        
        Args:
            agent_name: Nombre del agente
            backup_path: Path específico del backup (si no, usa el más reciente)
            
        Returns:
            True si se restauró exitosamente
        """
        if backup_path:
            backup_file = Path(backup_path)
        else:
            # Buscar el backup más reciente
            backups = list(self.backups_dir.glob(f"{agent_name}_*.json"))
            if not backups:
                logger.error(f"No hay backups disponibles para {agent_name}")
                return False
            backup_file = max(backups, key=lambda p: p.stat().st_mtime)
        
        if not backup_file.exists():
            logger.error(f"No existe el backup: {backup_file}")
            return False
        
        # Restaurar
        original_file = self.agentes_dir / f"{agent_name}.json"
        shutil.copy2(backup_file, original_file)
        
        logger.info(f"Restaurado {agent_name} desde {backup_file}")
        return True
    
    def list_variants(self, agent_name: str) -> List[Dict]:
        """
        Lista todas las variantes disponibles para un agente
        
        Args:
            agent_name: Nombre del agente
            
        Returns:
            Lista de variantes con metadata
        """
        variants = []
        
        # Original
        original_file = self.agentes_dir / f"{agent_name}.json"
        if original_file.exists():
            variants.append({
                "name": "original",
                "file": str(original_file),
                "type": "original"
            })
        
        # Variantes del registro
        if agent_name in self.variants_registry:
            for variant_name, variant_info in self.variants_registry[agent_name].items():
                variants.append({
                    "name": variant_name,
                    "file": variant_info["file"],
                    "created_at": variant_info.get("created_at"),
                    "type": "variant"
                })
        
        return variants
    
    def compare_variants(self, agent_name: str, variant1: str, variant2: str) -> Dict:
        """
        Compara dos variantes de un agente
        
        Args:
            agent_name: Nombre del agente
            variant1: Primera variante
            variant2: Segunda variante
            
        Returns:
            Diccionario con las diferencias
        """
        v1_data = self.load_variant(agent_name, variant1)
        v2_data = self.load_variant(agent_name, variant2)
        
        v1_content = v1_data.get("content", "")
        v2_content = v2_data.get("content", "")
        
        # Análisis básico
        comparison = {
            "variant1": variant1,
            "variant2": variant2,
            "length_diff": len(v2_content) - len(v1_content),
            "v1_length": len(v1_content),
            "v2_length": len(v2_content),
            "identical": v1_content == v2_content
        }
        
        # Encontrar diferencias línea por línea
        if not comparison["identical"]:
            v1_lines = v1_content.split('\n')
            v2_lines = v2_content.split('\n')
            
            comparison["line_changes"] = {
                "added": len(v2_lines) - len(v1_lines),
                "v1_lines": len(v1_lines),
                "v2_lines": len(v2_lines)
            }
        
        return comparison


def get_prompt_manager() -> PromptVersionManager:
    """Obtiene una instancia del gestor de prompts"""
    return PromptVersionManager()