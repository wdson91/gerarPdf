import re
import random
import string
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle


def gerar_grade_caca_palavras(palavras, tamanho=15):
    grade = [[" " for _ in range(tamanho)] for _ in range(tamanho)]
    direcoes = [(0, 1), (1, 0), (1, 1), (-1, 1)]

    for palavra in palavras:
        palavra = palavra.upper()
        colocada = False
        tentativas = 0

        while not colocada and tentativas < 100:
            dx, dy = random.choice(direcoes)
            linha = random.randint(0, tamanho - 1)
            coluna = random.randint(0, tamanho - 1)
            if pode_colocar(palavra, grade, linha, coluna, (dx, dy)):
                for i in range(len(palavra)):
                    x = linha + i * dx
                    y = coluna + i * dy
                    grade[x][y] = palavra[i]
                colocada = True
            tentativas += 1

    for i in range(tamanho):
        for j in range(tamanho):
            if grade[i][j] == " ":
                grade[i][j] = random.choice(string.ascii_uppercase)

    return grade


def pode_colocar(palavra, grade, linha, coluna, direcao):
    dx, dy = direcao
    for i in range(len(palavra)):
        x = linha + i * dx
        y = coluna + i * dy
        if not (0 <= x < len(grade) and 0 <= y < len(grade)):
            return False
        if grade[x][y] != " " and grade[x][y] != palavra[i]:
            return False
    return True


def exportar_caca_palavras_para_pdf(grade, palavras, pdf_path):
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 50, "Caça-palavras")

    # Tamanho da fonte e espaçamento
    font_size = 12
    spacing = 17

    c.setFont("Helvetica", font_size)

    start_x = 40
    start_y = height - 100

    # Desenhar grade
    for row_index, row in enumerate(grade):
        for col_index, letter in enumerate(row):
            x = start_x + col_index * spacing
            y = start_y - row_index * spacing
            c.drawString(x, y, letter)

    # Preparar palavras em colunas
    colunas = 5
    palavras_por_coluna = -(-len(palavras) // colunas)  # ceil division
    palavras_organizadas = []

    for i in range(palavras_por_coluna):
        linha = []
        for j in range(colunas):
            index = i + j * palavras_por_coluna
            if index < len(palavras):
                linha.append(palavras[index])
            else:
                linha.append("")
        palavras_organizadas.append(linha)

    # Desenhar tabela de palavras
    tabela = Table(palavras_organizadas)
    tabela.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 14),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    tabela.wrapOn(c, width, height)
    tabela.drawOn(c, 40, 60)  # posição da tabela

    c.save()
