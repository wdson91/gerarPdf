from flask import Flask, request, send_file, jsonify
from markdown import markdown
from weasyprint import HTML
import os
from datetime import datetime

app = Flask(__name__)

# Cria a pasta se ela não existir
PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    return "Hello, World!"


@app.route("/teste", methods=["GET"])
def index2():
    return "Hello, World!"


@app.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    data = request.get_json()

    if not data or "markdown" not in data:
        return jsonify({"erro": "Campo 'markdown' é obrigatório"}), 400

    markdown_text = data["markdown"]
    html_content = markdown(markdown_text, extensions=["fenced_code"])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                padding: 40px;
            }}
            code, pre {{
                background: #f4f4f4;
                padding: 10px;
                display: block;
                border-radius: 5px;
                font-family: monospace;
                white-space: pre-wrap;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Define o caminho do arquivo PDF com timestamp
    filename = f"rewlatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(PDF_DIR, filename)

    # Gera o PDF e salva no disco
    HTML(string=full_html).write_pdf(pdf_path)

    # Retorna o arquivo como download
    return send_file(pdf_path, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
