import re
from typing import Optional
from bs4 import BeautifulSoup


class ContentProcessor:
    """Handles HTML to Markdown conversion and content processing"""
    
    def __init__(self):
        self.ui_selectors = [
            '.md-code-block-banner',
            '.code-info-button-text', 
            '.ds-button',
            '.d813de27',
            '.efa13877',
            '.d2a24f03',
            '[role="button"]',
            '.ds-button__icon',
            '.ds-icon'
        ]
    
    def process_html_to_markdown(self, html_content: str) -> str:
        """Convert HTML content to clean markdown"""
        if not html_content:
            return ""
        
        try:
            # Clean up HTML structure first
            cleaned_html = self._remove_em_inside_strong(html_content)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(cleaned_html, 'html.parser')
            
            # Process in order of importance
            self._process_html_entities(soup)
            self._convert_code_blocks(soup)
            self._remove_ui_elements(soup)
            self._convert_html_to_markdown(soup)
            
            # Get final text and clean up
            result = soup.get_text()
            return self._final_cleanup(result)
            
        except Exception as e:
            print(f"Error processing HTML to markdown: {e}")
            return html_content
    
    def _remove_em_inside_strong(self, html: str) -> str:
        """Remove <em> tags inside <strong> tags"""
        try:
            result = []
            inside_strong = False
            i = 0
            
            while i < len(html):
                if html[i:i+8] == "<strong>":
                    inside_strong = True
                    result.append("<strong>")
                    i += 8
                elif html[i:i+9] == "</strong>":
                    inside_strong = False
                    result.append("</strong>")
                    i += 9
                elif html[i:i+4] == "<em>" and inside_strong:
                    i += 4  # Skip <em>
                elif html[i:i+5] == "</em>" and inside_strong:
                    i += 5  # Skip </em>
                else:
                    result.append(html[i])
                    i += 1
            
            return "".join(result)
        except Exception:
            return html
    
    def _process_html_entities(self, soup: BeautifulSoup) -> None:
        """Process HTML entities in ds-markdown-html spans"""
        for span in soup.find_all('span', class_='ds-markdown-html'):
            content = span.get_text()
            # Convert HTML entities to actual characters
            content = content.replace('&lt;', '<')
            content = content.replace('&gt;', '>')
            content = content.replace('&amp;', '&')
            content = content.replace('&nbsp;', ' ')
            content = content.replace('&quot;', '"')
            span.replace_with(content)
    
    def _convert_code_blocks(self, soup: BeautifulSoup) -> None:
        """Convert DeepSeek code blocks to Markdown"""
        code_blocks = soup.find_all('div', class_='md-code-block')
        
        for code_block in code_blocks:
            try:
                # Extract language
                language_elem = code_block.find('span', class_='d813de27')
                language = language_elem.get_text().strip() if language_elem else ''
                
                # Extract code content
                pre_tag = code_block.find('pre')
                if pre_tag:
                    code_content = pre_tag.get_text().strip()
                    
                    # Create Markdown code block
                    if language and language.lower() not in ['text', '']:
                        markdown_code = f"\n```{language}\n{code_content}\n```\n"
                    else:
                        markdown_code = f"\n```\n{code_content}\n```\n"
                    
                    code_block.replace_with(markdown_code)
                    
            except Exception as e:
                # Fallback: just extract pre content
                pre_tag = code_block.find('pre')
                if pre_tag:
                    code_block.replace_with(f"\n```\n{pre_tag.get_text()}\n```\n")
    
    def _remove_ui_elements(self, soup: BeautifulSoup) -> None:
        """Remove unwanted UI elements"""
        # Remove unwanted tags completely
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        
        # Remove UI selectors
        for selector in self.ui_selectors:
            for element in soup.select(selector):
                element.decompose()
    
    def _convert_html_to_markdown(self, soup: BeautifulSoup) -> None:
        """Convert remaining HTML elements to Markdown"""
        # Convert headers
        for i in range(1, 7):
            for header in soup.find_all(f'h{i}'):
                header_text = header.get_text()
                markdown_header = f"\n{'#' * i} {header_text}\n"
                header.replace_with(markdown_header)
        
        # Convert links
        for link in soup.find_all('a', href=True):
            link_text = link.get_text()
            link_url = link.get('href')
            if link_text and link_url:
                link.replace_with(f"[{link_text}]({link_url})")
        
        # Convert images
        for img in soup.find_all('img', src=True):
            alt_text = img.get('alt', '')
            img_url = img.get('src')
            img.replace_with(f"![{alt_text}]({img_url})")
        
        # Convert blockquotes
        for quote in soup.find_all('blockquote'):
            quote_text = quote.get_text().strip()
            quote_lines = quote_text.split('\n')
            markdown_quote = '\n'.join(f"> {line}" for line in quote_lines)
            quote.replace_with(f"\n{markdown_quote}\n")
        
        # Convert horizontal rules
        for hr in soup.find_all('hr'):
            hr.replace_with("\n---\n")
        
        # Handle line breaks
        for br in soup.find_all('br'):
            br.replace_with('\n')
        
        # Convert lists
        self._convert_lists(soup)
        
        # Handle paragraphs
        for p in soup.find_all('p'):
            p.insert_after('\n\n')
        
        # Convert formatting
        self._convert_formatting(soup)
        
        # Convert tables
        self._convert_tables(soup)
        
        # Clean up remaining elements
        for span in soup.find_all('span'):
            if 'ds-markdown-html' not in span.get('class', []):
                span.unwrap()
        
        for div in soup.find_all('div'):
            div.unwrap()
    
    def _convert_lists(self, soup: BeautifulSoup) -> None:
        """Convert HTML lists to Markdown with proper nesting support"""
        # Find all top-level lists (not nested inside other lists)
        top_level_lists = []
        for list_elem in soup.find_all(['ul', 'ol']):
            # Check if this list is nested inside another list
            is_nested = False
            parent = list_elem.parent
            while parent:
                if parent.name in ['ul', 'ol']:
                    is_nested = True
                    break
                parent = parent.parent
            
            if not is_nested:
                top_level_lists.append(list_elem)
        
        # Process each top-level list recursively
        for list_elem in top_level_lists:
            self._convert_list_recursive(list_elem, 0)
        
        # Clean up any remaining orphaned list items
        for li in soup.find_all('li'):
            li.replace_with(f"- {li.get_text().strip()}")
    
    def _convert_list_recursive(self, list_element, indent_level):
        """Recursively convert a list and all its nested lists"""
        indent = "  " * indent_level  # 2 spaces per level
        markdown_lines = []
        
        # Get only direct children <li> elements
        list_items = []
        for child in list_element.children:
            if hasattr(child, 'name') and child.name == 'li':
                list_items.append(child)
        
        for i, li in enumerate(list_items):
            # Extract text from direct children only (no nested lists)
            li_text = self._extract_li_text_only(li)
            
            # Create the list item
            if list_element.name == 'ol':
                marker = f"{i + 1}."
            else:
                marker = "-"
            
            if li_text:
                markdown_lines.append(f"{indent}{marker} {li_text}")
            
            # Process any nested lists within this <li>
            nested_lists = []
            for child in li.children:
                if hasattr(child, 'name') and child.name in ['ul', 'ol']:
                    nested_lists.append(child)
            
            for nested_list in nested_lists:
                nested_markdown = self._convert_list_recursive(nested_list, indent_level + 1)
                if nested_markdown:
                    # Add nested content directly to markdown_lines
                    nested_lines = nested_markdown.split('\n')
                    for line in nested_lines:
                        if line.strip():
                            markdown_lines.append(line)
        
        # Convert list to markdown and return the result
        result = '\n'.join(markdown_lines)
        
        # Replace the original list element only if we're at the top level
        if indent_level == 0:
            if result:
                list_element.replace_with('\n' + result + '\n')
            else:
                list_element.extract()
        
        return result
    
    def _extract_li_text_only(self, li_element):
        """Extract text from li element, excluding any nested lists"""
        text_parts = []
        
        for child in li_element.children:
            if hasattr(child, 'name'):
                if child.name in ['ul', 'ol']:
                    # Skip nested lists completely
                    continue
                elif child.name == 'p':
                    # Get text from paragraph
                    p_text = child.get_text().strip()
                    if p_text:
                        text_parts.append(p_text)
                elif child.name in ['span', 'em', 'strong', 'b', 'i', 'code']:
                    # Get text from inline elements
                    inline_text = child.get_text().strip()
                    if inline_text:
                        text_parts.append(inline_text)
                else:
                    # Other elements - try to get text but exclude lists
                    if child.name not in ['ul', 'ol']:
                        other_text = child.get_text().strip()
                        if other_text:
                            text_parts.append(other_text)
            else:
                # Text node
                text = str(child).strip()
                if text:
                    text_parts.append(text)
        
        return ' '.join(text_parts).strip()
    
    def _convert_formatting(self, soup: BeautifulSoup) -> None:
        """Convert formatting tags to Markdown"""
        # Handle inline code first
        for code in soup.find_all('code'):
            parent_code_block = code.find_parent('div', class_='md-code-block')
            if not parent_code_block:
                text_content = code.get_text()
                if text_content.strip():
                    if '\n' in text_content and len(text_content.strip().split('\n')) > 1:
                        code.replace_with(f"\n```\n{text_content.strip()}\n```\n")
                    else:
                        code.replace_with(f"`{text_content}`")
        
        # Convert bold
        for strong in soup.find_all(['strong', 'b']):
            text_content = strong.get_text()
            if text_content.strip():
                strong.replace_with(f"**{text_content}**")
        
        # Convert italic
        for em in soup.find_all(['em', 'i']):
            text_content = em.get_text()
            if text_content.strip():
                em.replace_with(f"*{text_content}*")
    
    def _convert_tables(self, soup: BeautifulSoup) -> None:
        """Convert tables to Markdown format"""
        for table in soup.find_all('table'):
            try:
                rows = table.find_all('tr')
                if rows:
                    markdown_table = []
                    
                    # Header row
                    header_row = rows[0]
                    headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                    if headers:
                        markdown_table.append('| ' + ' | '.join(headers) + ' |')
                        markdown_table.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
                    
                    # Data rows
                    for row in rows[1:]:
                        cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                        if cells:
                            markdown_table.append('| ' + ' | '.join(cells) + ' |')
                    
                    table.replace_with('\n' + '\n'.join(markdown_table) + '\n')
            except Exception:
                table.unwrap()
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup of the converted text"""
        # Convert any remaining entities
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&quot;', '"')
        
        # Clean up spacing and formatting
        text = re.sub(r'\n{3,}', '\n\n', text)      # Limit consecutive newlines
        text = re.sub(r'\*{3,}', '**', text)         # Fix multiple asterisks
        text = re.sub(r'`{4,}', '```', text)         # Fix 4+ backticks to triple
        text = re.sub(r'(?<!`)`{2}(?!`)', '`', text) # Fix double backticks to single
        text = re.sub(r'^[\s]*\n', '', text)         # Remove leading empty lines
        text = re.sub(r'\n[\s]*$', '', text)         # Remove trailing empty lines
        
        # Clean up Markdown formatting issues
        text = re.sub(r'\n\s*\n\s*```', '\n\n```', text)  # Fix code block spacing
        text = re.sub(r'```\s*\n\s*\n', '```\n', text)    # Fix code block spacing
        text = re.sub(r'\n\s*\n\s*#', '\n\n#', text)      # Fix header spacing
        text = re.sub(r'\n\s*\n\s*-', '\n\n-', text)      # Fix list spacing
        
        return text.strip()
    
    def get_closing_symbol(self, text: str) -> str:
        """Determine if text needs a closing quote or asterisk"""
        try:
            if not text:
                return ""
            
            text = text.strip()
            analysis_text = text.split("\n")[-1].strip()
            
            if re.search(r'(?:"\.?$|\*\.?$)', analysis_text):
                return ""
            
            current_symbol = None
            opposite_chars = {
                '"': ['*'],
                '*': ['"']
            }
            
            for char in analysis_text:
                if char in ['"', '*']:
                    if current_symbol is None:
                        current_symbol = char
                    elif char == current_symbol:
                        current_symbol = None
                    elif char in opposite_chars.get(current_symbol, []):
                        current_symbol = char
            
            return current_symbol if current_symbol else ""
            
        except Exception:
            return ""