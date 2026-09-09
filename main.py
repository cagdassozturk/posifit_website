# main.py - Güncellenmiş versiyon
from flask import Flask, send_from_directory, redirect, url_for
import os

# Flask server oluştur
server = Flask(__name__)

def read_html_file(filename):
    try:
        with open(f'static/{filename}', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # HTML linklerini Flask route'larına çevir
        content = content.replace('href="about.html"', 'href="/about"')
        content = content.replace('href="contact.html"', 'href="/contact"')
        content = content.replace('href="contributors.html"', 'href="/contributors"')
        content = content.replace('href="index.html"', 'href="/"')
        
        # Pilot linklerini düzelt
        content = content.replace('href="pilot_lux.html"', 'href="/pilot_lux"')
        content = content.replace('href="pilot_tur.html"', 'href="/pilot_tur"')
        content = content.replace('href="pilot_hun.html"', 'href="/pilot_hun"')
        content = content.replace('href="pilot_spa.html"', 'href="/pilot_spa"')
        content = content.replace('href="pilot_net.html"', 'href="/pilot_net"')
        content = content.replace('href="pilot_results_tur.html"', 'href="/pilot_results_tur"')
        
        # DASH SAYFALARINI DÜZELT - Bu çok önemli!
        content = content.replace('href="/pilot_lux_explorer"', 'href="/pilot_lux_explorer"')
        content = content.replace('href="/pilot_lux_optimized"', 'href="/pilot_lux_optimized"')
        
        # CSS ve JS yollarını düzelt
        content = content.replace('href="style.css"', 'href="/style.css"')
        content = content.replace('src="script.js"', 'src="/script.js"')
        
        return content
    except FileNotFoundError:
        return f"<h1>File {filename} not found</h1>"

# HTML sayfaları
@server.route('/')
def index():
    return read_html_file('index.html')

@server.route('/about')
def about():
    return read_html_file('about.html')

@server.route('/contact')
def contact():
    return read_html_file('contact.html')

@server.route('/contributors')
def contributors():
    return read_html_file('contributors.html')

# Pilot sayfaları
@server.route('/pilot_tur')
def pilot_tur():
    return read_html_file('pilot_tur.html')

@server.route('/pilot_hun') 
def pilot_hun():
    return read_html_file('pilot_hun.html')

@server.route('/pilot_spa')
def pilot_spa():
    return read_html_file('pilot_spa.html')

@server.route('/pilot_net')
def pilot_net():
    return read_html_file('pilot_net.html')

@server.route('/pilot_lux')
def pilot_lux():
    return read_html_file('pilot_lux.html')

@server.route('/pilot_results_tur')
def pilot_results_tur():
    return read_html_file('pilot_results_tur.html')

# DASH PAGES - Nginx will proxy these to Dash app (port 8051)
# No redirects needed here - nginx handles routing directly

# CSS ve JS dosyları
@server.route('/style.css')
def style_css():
    return send_from_directory('static', 'style.css')

@server.route('/script.js')
def script_js():
    return send_from_directory('static', 'script.js')

# Statik dosyalar
@server.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@server.route('/logo/<path:filename>')
def logo_files(filename):
    return send_from_directory('static/logo', filename)

@server.route('/cards/<path:filename>')
def card_files(filename):
    return send_from_directory('static/cards', filename)

@server.route('/pilots/<path:filename>')
def pilot_files(filename):
    return send_from_directory('static/pilots', filename)

@server.route('/header/<path:filename>')
def header_files(filename):
    return send_from_directory('static/header', filename)

@server.route('/About/<path:filename>')
def about_files(filename):
    return send_from_directory('static/About', filename)

@server.route('/profilepicture/<path:filename>')
def profile_files(filename):
    return send_from_directory('static/profilepicture', filename)

@server.route('/assets/<path:filename>')
def assets_files(filename):
    return send_from_directory('assets', filename)

if __name__ == '__main__':
    # Sadece Flask server'ı başlat - Dash ayrı çalışacak
    server.run(debug=True, host='0.0.0.0', port=8050)