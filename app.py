import streamlit as st
import pandas as pd
from tempus import Tempus
import os
import re

st.set_page_config(page_title="Pliny Browser", layout="wide")
st.title("Plinius Historia Naturalis - Tempus phrases")

# Get script directory and construct data path
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, 'pliny_data.json')

# Load DataFrame from JSON
df = pd.read_json(data_path)

# Function to split sentence into words
def get_words(sentence):
    return [w for w in re.findall(r'\b\w+\b', sentence)]

# Function to extract word analysis into a list of dictionaries
def extract_word_analyses(analysis_text):
    word_entries = []
    parts = analysis_text.split('##')
    for part in parts:
        if 'Wortanalyse' in part:
            entries = re.findall(r'\*\*(\d+)\.\*\* (.*?)(?=\*\*\d+\.\*\*|\Z)', part, re.DOTALL)
            for nr, content in entries:
                # Extract individual fields
                form = re.search(r'- Stammform: \*(.*?)\*', content)
                wortart = re.search(r'- Wortart: (.*?)[\n\r]', content)
                flexion = re.search(r'- Flexion: (.*?)[\n\r]', content)
                bedeutung = re.search(r'- Bedeutung: (.*?)[\n\r]', content)
                
                word_entries.append({
                    'Nr': int(nr),
                    'Stammform': form.group(1) if form else '',
                    'Wortart': wortart.group(1) if wortart else '',
                    'Flexion': flexion.group(1) if flexion else '',
                    'Bedeutung': bedeutung.group(1) if bedeutung else ''
                })
    return word_entries

# Sidebar
with st.sidebar:
    st.header("Navigation")
    # Index selection
    index = st.number_input('Select Index', 0, len(df)-1, 0)
    st.write(f"Book: {df.iloc[index]['book']} | Chapter: {df.iloc[index]['chapter']}")
    
    # Get current sentence
    latin_text = df.iloc[index]['sentence']
    words = get_words(latin_text)
    word_options = [f"{i+1}: {word}" for i, word in enumerate(words)]
    
    # Word selection
    selected_word_index = st.selectbox('Select Word', range(len(word_options)), 
                                     format_func=lambda x: word_options[x])
    
    # Blue button matching Streamlit's theme
    analyze_button = st.button('Analyze with Lettre.AI', type='primary')

# Main content
# Highlight selected word in text area with red color
highlighted_text = latin_text
if words:
    word_to_highlight = words[selected_word_index]
    pattern = r'\b' + re.escape(word_to_highlight) + r'\b'
    highlighted_text = re.sub(pattern, f':red[{word_to_highlight}]', latin_text)

# Store analysis in session state
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None
if 'word_analyses' not in st.session_state:
    st.session_state.word_analyses = None

# Analysis display in columns
if analyze_button or st.session_state.current_analysis is None:
    with st.spinner('Analyzing Latin text...'):
        tempus = Tempus()
        analysis = tempus.analyze(latin_text)
        st.session_state.current_analysis = analysis
        st.session_state.word_analyses = extract_word_analyses(analysis)

if st.session_state.current_analysis:
    # Split analysis into parts
    parts = st.session_state.current_analysis.split('##')
    
    # Create columns
    col1, col2 = st.columns(2)
    
    # Left column: Latin, Translation, Word Analysis
    with col1:
        st.markdown('## Lateinischer Satz')
        st.markdown(f"*{highlighted_text}*")
        
        # Extract and display translation
        uebersetzung = next((p for p in parts if 'Wörtliche Übersetzung' in p), '')
        if uebersetzung:
            st.markdown('## Übersetzung')
            # Remove header and clean up text
            clean_translation = re.sub(r'^.*?Übersetzung\s*', '', uebersetzung, flags=re.DOTALL).strip()
            st.markdown(f"*{clean_translation}*")
        
        # Word Analysis
        st.markdown('## Wortanalyse')
        if st.session_state.word_analyses:
            selected_word = next(
                (word for word in st.session_state.word_analyses 
                 if word['Nr'] == selected_word_index + 1), None
            )
            if selected_word:
                df_word = pd.DataFrame([selected_word])
                st.table(df_word[['Stammform', 'Wortart', 'Flexion', 'Bedeutung']].set_index('Stammform'))
    
    # Right column: Tempus Analysis and Specific Notes
    with col2:
        # Extract and display tempus analysis
        tempus_analyse = next((p for p in parts if 'Tempus-Analyse' in p), '')
        if tempus_analyse:
            st.markdown('## Tempus-Analyse')
            clean_analysis = re.sub(r'^.*?Tempus-Analyse\s*', '', tempus_analyse, flags=re.DOTALL).strip()
            if clean_analysis:  # Only display if there's actual content
                st.markdown(clean_analysis)
        
        # Extract and display specific notes
        erlaeuterungen = next((p for p in parts if 'Spezifische Erläuterungen' in p), '')
        if erlaeuterungen:
            st.markdown('## Erläuterungen')
            clean_notes = re.sub(r'^.*?Erläuterungen\s*', '', erlaeuterungen, flags=re.DOTALL).strip()
            if clean_notes:  # Only display if there's actual content
                st.markdown(clean_notes)
    