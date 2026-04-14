from pydantic import BaseModel
import re

class ParseCleaner(BaseModel):
    @staticmethod
    def parsed_clean(src_file: str, dest_file: str, enc: str) -> None:
        '''
            Scrive in dest_file il testo markdown preso in input pulito
            Argomenti:
                src_file: path del file markdown da pulire
                dest_file: path del file markdown pulito
                enc: encoding del file, UTF-8 è raccomandato
        '''

        md_file = open(src_file, 'r', encoding=enc)
        cleaned_md = open(dest_file, 'w', encoding=enc)
        for line in md_file:
            line = re.sub(r'\(\s*https?://[^)]*\)', ' ', line)
            line = re.sub(r'\[\d+\]', ' ', line)
            line = re.sub(r'[^a-zA-Z0-9]', ' ', line)
            line = re.split(" ", line)
            for w in line:
                if w:
                    cleaned_md.write(w+',')
        md_file.close()
        cleaned_md.close()