import re
import json
from typing import Dict, List, Tuple, Any, Union
from collections import OrderedDict

class Report:
    def __init__(self, report_outline: str):
        """
        Initialize the report object.

        Args:
            report_outline (str): Markdown outline string such as
                                  "# Title\n\n## Introduction\n### Background\n..."
        """
        self.report_outline = report_outline
        
        self.report_structure = {}
        self.sections = []
        self.title = ''
        self._content = ''
        self.abstract = ''
        # self._final_content = ''
        all_structure = self._parse_outline(self.report_outline)
        self._build_sections(all_structure)
    
    # def set_content(self, content: str):
    #     self._final_content = content
    

    @property
    def content(self):
        # if self._final_content != '':
        #     return self._final_content
        if self.sections == []:
            content = self._content
        else:
            content = self._content
            content += self.abstract + '\n\n'
            for section in self.sections:
                content += section.content.strip() + '\n\n'
        return content
    
    def _build_sections(self, all_structure: dict):
        if '__content__' in all_structure:
            del all_structure['__content__']
        if len(all_structure) > 1:
            self.logger.error(f"all_structure: {all_structure}")
            raise ValueError("Report outline must contain exactly one top-level heading.")
        self.title = list(all_structure.keys())[0]
        self.report_structure = all_structure[self.title]
        self._content = f'# {self.title}\n'
        for section_title, section_outline in self.report_structure.items():
            if section_title == '__content__':
                self._content += section_outline
                self._content += '\n'
            else:
                self.sections.append(Section(section_title, section_outline))

    def _parse_outline(self, markdown_text: str) -> dict:
        """
        Parse Markdown outline text into a nested dictionary keyed by headings.

        Args:
            markdown_text: Markdown-formatted string.

        Returns:
            Dict describing the outline hierarchy. '__content__' holds any
            free text preceding the first heading.
        """
        # 1. Preprocess and segment by heading markers
        lines = markdown_text.strip().split('\n')
        sections = []
        current_content = []

        for line in lines:
            if line.strip().startswith('#'):
                if current_content:
                    if not sections:
                        sections.append({'level': 0, 'title': '__root__', 'content': '\n'.join(current_content)})
                    else:
                        sections[-1]['content'] = '\n'.join(current_content).strip()
                
                match = re.match(r'^(#+)\s+(.*)', line.strip())
                if match:
                    level = len(match.group(1))
                    title = match.group(2).strip()
                    sections.append({'level': level, 'title': title, 'content': ''})
                
                current_content = []
            else:
                current_content.append(line)
        
        if sections:
            if current_content:
                sections[-1]['content'] = '\n'.join(current_content).strip()
        elif current_content:
            return {'__content__': '\n'.join(current_content).strip()}

        # 2. Recursively build nested dictionaries
        def build_nested_dict(sections: list) -> dict:
            if not sections:
                return {}

            nested_dict = {}
            
            if sections and sections[0]['level'] == 0:
                root_content = sections.pop(0)
                if root_content['content']:
                    nested_dict['__content__'] = root_content['content']

            i = 0
            while i < len(sections):
                current_section = sections[i]
                current_level = current_section['level']
                current_title = current_section['title']
                
                sub_sections = []
                j = i + 1
                while j < len(sections) and sections[j]['level'] > current_level:
                    sub_sections.append(sections[j])
                    j += 1

                children = build_nested_dict(sub_sections)
                
                result_value = {}
                if current_section['content']:
                    result_value['__content__'] = current_section['content']
                
                if children:
                    result_value.update(children)

                if len(result_value) == 1 and '__content__' in result_value:
                    nested_dict[current_title] = result_value['__content__']
                else:
                    nested_dict[current_title] = result_value
                
                i = j
            
            return nested_dict

        report_structure = build_nested_dict(sections)
        return report_structure

class Section:
    def __init__(
        self,
        section_title: str,
        section_outline: Union[Dict, str],
        level = '##'
    ):
        self.title = section_title
        self.outline_items = section_outline
        self.level = level
        
        self._outline = None
        self._content = None # When absent, fall back to the outline
        self.children = []
    
    def set_content(self, content: str):
        paragraphs = content.split('\n\n')
        self._content = paragraphs
    
    @property
    def content(self):
        if self._content is not None and len(self._content) > 0:
            return "\n\n".join(self._content)
        else:
            return self.outline

    @property
    def outline(self):
        if self._outline is not None:
            return self._outline
    
        outline = ''
        outline += f'{self.level} {self.title}\n'
        if isinstance(self.outline_items, str):
            outline += self.outline_items
            outline += '\n'
        else:
            # Recursively build the outline string
            for child_title, child_outline in self.outline_items.items():
                if child_title == '__content__':
                    outline += child_outline
                    outline += '\n'
                else:
                    child_node = Section(
                        section_title=child_title,
                        section_outline=child_outline,
                        level=self.level+'#'
                    )
                    self.children.append(child_node)
                    outline += child_node.outline
        self._outline = outline
        return outline
    
    def __str__(self):
        return self.outline
    
    def __repr__(self):
        return self.outline
            

