# freeplane.py
from typing import List, Dict
import random
import time

def generate_id():
    """Gera um ID único para os nós do Freeplane"""
    return f"ID_{random.randint(100000000, 999999999)}"

def generate_timestamp():
    """Gera timestamp para os nós"""
    return str(int(time.time() * 1000))

def build_freeplane(nodes: List[Dict[str, str]]) -> str:
    """
    Constrói o XML no formato Freeplane moderno (.mm) a partir dos nós extraídos.
    
    Args:
        nodes: Lista de dicionários contendo os dados dos nós
        
    Returns:
        String XML formatada para Freeplane (.mm)
    """
    nodes_sorted = sorted(nodes, key=lambda x: x.get("gab", ""))
    
    # Cabeçalho moderno do Freeplane
    xml = '''<map version="freeplane 1.12.1">
<!--To view this file, download free mind mapping software Freeplane from https://www.freeplane.org -->
<node TEXT="QConcursos - Questões" FOLDED="false" ID="''' + generate_id() + '''" CREATED="''' + generate_timestamp() + '''" MODIFIED="''' + generate_timestamp() + '''" STYLE="oval">
<font SIZE="18"/>
<hook NAME="MapStyle">
    <properties edgeColorConfiguration="#808080ff,#ff0000ff,#0000ffff,#00ff00ff,#ff00ffff,#00ffffff,#7c0000ff,#00007cff,#007c00ff,#7c007cff,#007c7cff,#7c7c00ff" fit_to_viewport="false" show_icons="BESIDE_NODES" associatedTemplateLocation="template:/standard-1.6.mm" show_tags="UNDER_NODES" showTagCategories="false" show_icon_for_attributes="true" show_note_icons="true"/>
    <tags category_separator="::"/>

<map_styles>
<stylenode LOCALIZED_TEXT="styles.root_node" STYLE="oval" UNIFORM_SHAPE="true" VGAP_QUANTITY="24 pt">
<font SIZE="24"/>
<stylenode LOCALIZED_TEXT="styles.predefined" POSITION="bottom_or_right" STYLE="bubble">
<stylenode LOCALIZED_TEXT="default" ID="ID_271890427" ICON_SIZE="12 pt" COLOR="#000000" STYLE="fork">
<arrowlink SHAPE="CUBIC_CURVE" COLOR="#000000" WIDTH="2" TRANSPARENCY="200" DASH="" FONT_SIZE="9" FONT_FAMILY="SansSerif" DESTINATION="ID_271890427" STARTARROW="NONE" ENDARROW="DEFAULT"/>
<font NAME="SansSerif" SIZE="10" BOLD="false" ITALIC="false"/>
<richcontent TYPE="DETAILS" CONTENT-TYPE="plain/auto"/>
<richcontent TYPE="NOTE" CONTENT-TYPE="plain/auto"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.details"/>
<stylenode LOCALIZED_TEXT="defaultstyle.tags">
<font SIZE="10"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.attributes">
<font SIZE="9"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.note" COLOR="#000000" BACKGROUND_COLOR="#ffffff" TEXT_ALIGN="LEFT"/>
<stylenode LOCALIZED_TEXT="defaultstyle.floating">
<edge STYLE="hide_edge"/>
<cloud COLOR="#f0f0f0" SHAPE="ROUND_RECT"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.selection" BACKGROUND_COLOR="#afd3f7" BORDER_COLOR_LIKE_EDGE="false" BORDER_COLOR="#afd3f7"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.user-defined" POSITION="bottom_or_right" STYLE="bubble">
<stylenode LOCALIZED_TEXT="styles.topic" COLOR="#18898b" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subtopic" COLOR="#cc3300" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subsubtopic" COLOR="#669900">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.important" ID="ID_67550811">
<icon BUILTIN="yes"/>
<arrowlink COLOR="#003399" TRANSPARENCY="255" DESTINATION="ID_67550811"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.flower" COLOR="#ffffff" BACKGROUND_COLOR="#255aba" STYLE="oval" TEXT_ALIGN="CENTER" BORDER_WIDTH_LIKE_EDGE="false" BORDER_WIDTH="22 pt" BORDER_COLOR_LIKE_EDGE="false" BORDER_COLOR="#f9d71c" BORDER_DASH_LIKE_EDGE="false" BORDER_DASH="CLOSE_DOTS" MAX_WIDTH="6 cm" MIN_WIDTH="3 cm"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.AutomaticLayout" POSITION="bottom_or_right" STYLE="bubble">
<stylenode LOCALIZED_TEXT="AutomaticLayout.level.root" COLOR="#000000" STYLE="oval" SHAPE_HORIZONTAL_MARGIN="10 pt" SHAPE_VERTICAL_MARGIN="10 pt">
<font SIZE="18"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,1" COLOR="#0033ff">
<font SIZE="16"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,2" COLOR="#00b439">
<font SIZE="14"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,3" COLOR="#990000">
<font SIZE="12"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,4" COLOR="#111111">
<font SIZE="10"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,5"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,6"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,7"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,8"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,9"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,10"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,11"/>
</stylenode>
</stylenode>
</map_styles>
</hook>
<hook NAME="AutomaticEdgeColor" COUNTER="6" RULE="ON_BRANCH_CREATION"/>
'''

    # Cores para as bordas dos nós
    colors = ["#ff0000", "#0000ff", "#00ff00", "#ff00ff", "#00ffff", "#7c0000"]
    
    # Adiciona cada questão como um nó filho
    for i, node in enumerate(nodes_sorted):
        if node.get("html"):
            # Extrai o texto principal do HTML para usar como TEXT
            html_content = node["html"]
            
            # Extrai texto entre as tags de richcontent NODE
            start_marker = '<span>'
            end_marker = '</span><br>'
            
            if start_marker in html_content and end_marker in html_content:
                text_start = html_content.find(start_marker) + len(start_marker)
                text_end = html_content.find(end_marker, text_start)
                node_text = html_content[text_start:text_end] if text_end > text_start else f"Questão {i+1}"
            else:
                node_text = f"Questão {i+1}"
            
            # Escapa caracteres especiais para XML
            node_text = node_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            
            # Extrai nota/comentário do HTML
            note_start = '<richcontent TYPE="NOTE"'
            note_end = '</richcontent>'
            note_content = ""
            
            if note_start in html_content and note_end in html_content:
                note_begin = html_content.find(note_start)
                note_finish = html_content.find(note_end, note_begin) + len(note_end)
                note_section = html_content[note_begin:note_finish]
                
                # Extrai o conteúdo da nota
                body_start = note_section.find('<body>') + 6
                body_end = note_section.find('</body>')
                if body_start > 5 and body_end > body_start:
                    note_content = note_section[body_start:body_end].strip()
            
            # Gera o nó moderno do Freeplane
            color = colors[i % len(colors)]
            created_time = generate_timestamp()
            modified_time = generate_timestamp()
            node_id = generate_id()
            
            xml += f'''<node TEXT="{node_text}" POSITION="bottom_or_right" ID="{node_id}" CREATED="{created_time}" MODIFIED="{modified_time}">
<edge COLOR="{color}"/>'''
            
            # Adiciona nota se existir
            if note_content:
                xml += f'''
<richcontent TYPE="NOTE">
<html>
  <head>
    
  </head>
  <body>
    <p>
      {note_content}
    </p>
  </body>
</html>
</richcontent>'''
            
            xml += '</node>\n'
    
    xml += '</node>\n</map>\n'
    return xml 