from flask import Flask, request, send_file, jsonify
from markdown import markdown
from weasyprint import HTML
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import unicodedata
from flask_cors import CORS
import re
from gerarpdf import *


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from dotenv import load_dotenv
import os
import chromedriver_autoinstaller

# Inicialização do app Flask
app = Flask(__name__)
CORS(app)
# Carregar variáveis de ambiente
load_dotenv(dotenv_path="./.env")

# Configuração de diretórios e Supabase
PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")  # só usa se precisar, mas pode remover

supabase: Client = create_client(
    "https://daszicjqshnxpdaxqbip.supabase.co", SUPABASE_KEY
)


def listar_pdfs_usuarios():
    # Listar todos os arquivos no bucket "pdfs"
    response = supabase.storage.from_("pdfs").list(
        path="pdfs",
        options={
            "limit": 100,  # Limitar a 100 resultados
            "offset": 0,  # Começar do primeiro arquivo
            "sortBy": {
                "column": "name",
                "order": "desc",
            },  # Ordenar por nome, de forma decrescente
        },
    )
    print(response)
    if response:
        return response  # Retorna a lista de arquivos encontrados
    else:
        return []  # Caso não haja arquivos, retorna uma lista vazia


# Função de upload com tratamento de erro
def upload_pdf_to_supabase(pdf_path, filename):
    try:
        with open(pdf_path, "rb") as f:
            response = supabase.storage.from_("pdfs").upload(
                file=f,
                path=f"pdfs/{filename}",
                file_options={
                    "content-type": "application/pdf",
                    "cache-control": "3600",
                    "upsert": "true",
                },
            )

        print("Upload concluído:", response.path)

        return {
            "success": True,
            "path": response.path,
            "full_path": response.full_path,
        }

    except Exception as e:
        print("Erro ao fazer upload:", str(e))
        return {
            "success": False,
            "error": str(e),
        }


def sanitize_filename(title):
    # Remove acentos
    nfkd_form = unicodedata.normalize("NFKD", title)
    only_ascii = nfkd_form.encode("ASCII", "ignore").decode("utf-8")

    # Remove caracteres inválidos e substitui espaços por underscores
    safe_title = re.sub(r'[\\/*?:"<>|]', "", only_ascii)
    safe_title = re.sub(r"\s+", "_", safe_title)

    return safe_title


# Rotas simples
@app.route("/", methods=["GET"])
def index():
    dados = listar_pdfs_usuarios()
    return dados


@app.route("/teste", methods=["GET"])
def index2():
    return "Hello, World!"


@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    if "file" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400

    audio_file = request.files["file"]
    filename = sanitize_filename(audio_file.filename)

    # Salvar temporariamente
    temp_path = os.path.join("audios", filename)
    os.makedirs("audios", exist_ok=True)
    audio_file.save(temp_path)

    # Fazer upload para o Supabase
    try:
        with open(temp_path, "rb") as f:
            response = supabase.storage.from_("audios").upload(
                path=f"audios/{filename}",
                file=f,
                file_options={
                    "content-type": "audio/mpeg",
                    "cache-control": "3600",
                    "upsert": "true",
                },
            )

        # Deletar arquivo local depois do upload
        os.remove(temp_path)

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/audios/audios/{filename}"

        return jsonify(
            {
                "mensagem": "Áudio enviado com sucesso!",
                "nome_arquivo": filename,
                "url_audio": public_url,
            }
        )

    except Exception as e:
        return jsonify({"erro": "Erro ao fazer upload", "detalhe": str(e)}), 500


# Rota principal para gerar PDF
@app.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    data = request.get_json()

    required_fields = ["markdown", "title"]
    missing_fields = [field for field in required_fields if field not in data]
    title_text = re.sub(r'[\\/*?:"<>|]', "_", data["title"].strip())
    if missing_fields:
        return (
            jsonify({"erro": f"Campo(s) obrigatório(s): {', '.join(missing_fields)}"}),
            400,
        )

    safe_title = sanitize_filename(title_text)

    markdown_text = data["markdown"]
    html_content = markdown(markdown_text, extensions=["fenced_code"])

    # Template HTML do PDF
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

    # Define nome e caminho do PDF
    filename = f"{safe_title}.pdf"
    pdf_path = os.path.join(PDF_DIR, filename)

    # Gera o PDF localmente
    HTML(string=full_html).write_pdf(pdf_path)

    # Faz upload no Supabase
    upload_response = upload_pdf_to_supabase(pdf_path, filename)

    if not upload_response["success"]:
        return (
            jsonify(
                {
                    "erro": "Falha ao enviar para o Supabase",
                    "detalhe": upload_response["error"],
                }
            ),
            500,
        )

    # Monta URL pública do PDF no Supabase
    public_url = (
        f"{SUPABASE_URL}/storage/v1/object/public/pdfs/{upload_response['path']}"
    )

    return jsonify(
        {
            "mensagem": "PDF gerado e enviado com sucesso!",
            "nome_arquivo": filename,
            "url_pdf": public_url,
        }
    )


@app.route("/gerar-caca-palavras", methods=["POST"])
def gerar_caca_palavras_pdf():
    data = request.get_json()

    required_fields = ["palavras", "title"]
    missing_fields = [field for field in required_fields if field not in data]
    title_text = re.sub(r'[\\/*?:"<>|]', "_", data["title"].strip())

    if missing_fields:
        return (
            jsonify({"erro": f"Campo(s) obrigatório(s): {', '.join(missing_fields)}"}),
            400,
        )

    palavras = data["palavras"]
    if not isinstance(palavras, list) or not all(isinstance(p, str) for p in palavras):
        return (
            jsonify({"erro": "O campo 'palavras' deve ser uma lista de strings."}),
            400,
        )

    safe_title = sanitize_filename(title_text)
    filename = f"{safe_title}.pdf"
    pdf_path = os.path.join(PDF_DIR, filename)

    try:
        grade = gerar_grade_caca_palavras(palavras, tamanho=30)
        exportar_caca_palavras_para_pdf(grade, palavras, pdf_path)
    except Exception as e:
        return jsonify({"erro": "Erro ao gerar PDF", "detalhe": str(e)}), 500

    upload_response = upload_pdf_to_supabase(pdf_path, filename)

    if not upload_response["success"]:
        return (
            jsonify(
                {
                    "erro": "Falha ao enviar para o Supabase",
                    "detalhe": upload_response["error"],
                }
            ),
            500,
        )

    return jsonify({"sucesso": True, "arquivo": filename}), 200


##ROTA PARA CRIAR SITE LOVABLE


email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
chromedriver_path = os.getenv("CHROMEDRIVER_PATH")


@app.route("/gerar_link", methods=["POST"])
def gerar_link():

    data = request.get_json()  # Captura o JSON do corpo
    prompt = data.get("prompt")
    # chromedriver_autoinstaller.install()
    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"

    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 360)

    try:
        driver.get("https://lovable.dev/login")
        time.sleep(15)
        print("Acessando o login do Lovable")
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.send_keys(email)
        print("Preenchendo o email")
        password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
        password_input.send_keys(password)
        print("Preenchendo a senha")
        login_button = driver.find_element(
            By.CSS_SELECTOR,
            "body > div > div > div.flex.justify-center.px-4.py-20 > div > div > div > div.grid.gap-4 > form > div > div.flex.flex-col.gap-3 > div.relative.flex.items-center > div.flex-grow > button",
        )
        login_button.click()

        time.sleep(20)
        print("Acessando o painel do Lovable")
        chat_input = wait.until(EC.presence_of_element_located((By.ID, "chatinput")))
        chat_input.send_keys(prompt)
        chat_input.send_keys(Keys.ENTER)
        print("Enviando o prompt")
        time.sleep(10)
        wait.until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "#preview-url-bar > button > svg")
            )
        )
        time.sleep(10)

        share_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#share-menu"))
        )
        share_button.click()

        text_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".mr-2.inline-block.text-sm.font-medium")
            )
        )
        nome_texto = text_element.text.strip()

        url_final = f"https://preview--{nome_texto}"

        return jsonify({"url_gerada": url_final})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

    finally:
        driver.quit()


# Executa a aplicação
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
