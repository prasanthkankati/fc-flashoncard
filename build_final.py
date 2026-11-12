import json

with open('C:/Users/Prasa/.gemini/antigravity-cli/brain/0265613d-2cca-4554-a02a-96753dff0147/scratch/logo_b64.json') as f:
    logos = json.load(f)

logo_white = logos['white']
logo_black = logos['black']

with open('C:/Users/Prasa/fc-posters/template.html', 'r', encoding='utf-8') as f:
    template = f.read()

final_html = template.replace('__LOGO_WHITE__', logo_white).replace('__LOGO_BLACK__', logo_black)

with open('C:/Users/Prasa/.gemini/antigravity-cli/brain/0265613d-2cca-4554-a02a-96753dff0147/scratch/compiled_index.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print('Compiled scratch index successfully!')
