import re
import mistune
from bs4 import BeautifulSoup 

def remove_markdown(md: str) -> str:
    '''
    Rimuove il Markdown da una stringa, restituendo solo il testo pulito.
    Usa la libreria mistune per convertire il Markdown in HTML, poi BeautifulSoup per estrarre solo il testo.
    '''
    html = mistune.html(md)
    soup = BeautifulSoup(html, "html.parser")
    # rimuove i tag lasciando il testo esattamente in-place (nessun separatore aggiunto, mantiene punteggiatura)
    for tag in soup.find_all(True):
        tag.unwrap()
    
    text = re.sub(r'[ \t]+', ' ', str(soup))  # collassa spazi orizzontali (non \n)
    text = re.sub(r'\n+', '\n', text)  # collassa nuove linee multiple in una sola
    return text.strip()