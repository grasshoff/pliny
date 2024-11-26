import os
from jinja2 import Template
import google.generativeai as genai
import re

class Tempus:
    def __init__(self, template_path='tempus.j2'):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, template_path)
        
        with open(template_path) as f:
            self.template = Template(f.read())
            
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.generation_config = {
            "temperature": 0.1,
            "top_p": 0.01,
            "top_k": 20,
            "max_output_tokens": 8192,
        }
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=self.generation_config,
        )
        
    def _get_prompt(self, latin_text: str) -> str:
        return f"""Erstelle aus diesem Lateinischen Satz eine Analyse:

{latin_text}

Gib die Analyse in folgender Form aus:
<satz>{latin_text}</satz>

<wortanalyse>
  <wort>
    <nr>ZAHL</nr>
    <form>WORTFORM</form>
    <stamm>STAMMFORM</stamm>
    <wortart>POS</wortart>
    <flexion>GRAMMATISCHE_MERKMALE</flexion>
    <uebersetzung>DEUTSCHE_BEDEUTUNG</uebersetzung>
  </wort>
</wortanalyse>

<literale_uebersetzung>ÜBERSETZUNG</literale_uebersetzung>

<tempus_analyse>
Informative Analyse des Wortes "tempus" im vorliegenden Kontext:

- Bedeutungsrelevante grammatikalische Merkmale
- Kontextspezifische Bedeutungsnuancen
- Fachspezifische Verwendung
- Naturwissenschaftliche Bezüge
- Thematische Einbindung

Gib ausschließlich fundierte Erkenntnisse wieder.
</tempus_analyse>

<spezifisch>ERLÄUTERUNG_SPEZIFISCHER_AUSDRÜCKE_UND_WENDUNGEN</spezifisch>"""

    def _xml2md(self, xml_text: str) -> str:
        """Convert XML analysis to Markdown format"""
        # Clean up the text
        text = xml_text.replace('```xml', '').replace('```', '').strip()
        
        # Extract sections using regex
        satz = re.search(r'<satz>(.*?)</satz>', text, re.DOTALL)
        wortanalyse = re.search(r'<wortanalyse>(.*?)</wortanalyse>', text, re.DOTALL)
        uebersetzung = re.search(r'<literale_uebersetzung>(.*?)</literale_uebersetzung>', text, re.DOTALL)
        tempus = re.search(r'<tempus_analyse>(.*?)</tempus_analyse>', text, re.DOTALL)
        spezifisch = re.search(r'<spezifisch>(.*?)</spezifisch>', text, re.DOTALL)
        
        # Build markdown
        md = []
        md.append("## Lateinischer Satz")
        md.append(f"*{satz.group(1).strip() if satz else 'Nicht verfügbar'}*")
        md.append("")
        
        if wortanalyse:
            md.append("## Wortanalyse")
            words = re.finditer(r'<wort>(.*?)</wort>', wortanalyse.group(1), re.DOTALL)
            for word in words:
                word_text = word.group(1)
                nr = re.search(r'<nr>(.*?)</nr>', word_text)
                form = re.search(r'<form>(.*?)</form>', word_text)
                stamm = re.search(r'<stamm>(.*?)</stamm>', word_text)
                wortart = re.search(r'<wortart>(.*?)</wortart>', word_text)
                flexion = re.search(r'<flexion>(.*?)</flexion>', word_text)
                ueb = re.search(r'<uebersetzung>(.*?)</uebersetzung>', word_text)
                
                md.append(f"**{nr.group(1) if nr else '?'}.** {form.group(1) if form else ''}")
                md.append(f"- Stamm: *{stamm.group(1) if stamm else ''}*")
                md.append(f"- Wortart: {wortart.group(1) if wortart else ''}")
                md.append(f"- Flexion: {flexion.group(1) if flexion else ''}")
                md.append(f"- Bedeutung: {ueb.group(1) if ueb else ''}")
                md.append("")
        
        if uebersetzung:
            md.append("## Wörtliche Übersetzung")
            md.append(f"*{uebersetzung.group(1).strip()}*")
            md.append("")
        
        if tempus:
            md.append("## Tempus-Analyse")
            # Clean up tempus analysis text and convert to pure markdown
            tempus_text = tempus.group(1).strip()
            # Remove XML-like tags if present
            tempus_text = re.sub(r'<[^>]+>', '', tempus_text)
            # Clean up numbered lists to proper markdown
            tempus_text = re.sub(r'^\d+\.\s*', '- ', tempus_text, flags=re.MULTILINE)
            md.append(tempus_text)
            md.append("")
        
        if spezifisch:
            md.append("## Spezifische Erläuterungen")
            md.append(spezifisch.group(1).strip())
        
        return '\n'.join(md)

    def analyze(self, latin_text: str) -> str:
        """Analyze a Latin text and return formatted markdown"""
        prompt = self._get_prompt(latin_text)
        response = self.model.generate_content(prompt)
        return self._xml2md(response.text)

    def render_template(self, context: dict) -> str:
        """Render the template with given context"""
        return self.template.render(context) 