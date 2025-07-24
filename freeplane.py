# freeplane.py
from typing import List, Dict

def build_freeplane(nodes: List[Dict[str, str]]) -> str:
    """
    Constrói o XML no formato Freeplane a partir dos nós extraídos.
    
    Args:
        nodes: Lista de dicionários contendo os dados dos nós
        
    Returns:
        String XML formatada para Freeplane
    """
    nodes_sorted = sorted(nodes, key=lambda x: x.get("gab", ""))
    xml = '<map version="freeplane 1.9.8"><node LOCALIZED_TEXT="new_mindmap">'
    xml += "".join(n["html"] for n in nodes_sorted)
    xml += "</node></map>"
    return xml 