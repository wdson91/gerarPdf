import requests
import json
import time
import threading
from geopy.geocoders import Nominatim
from geopy.distance import geodesic, distance as geopy_distance
from concurrent.futures import ThreadPoolExecutor, as_completed

# === CONFIGURAÇÕES DA API GOOGLE PLACES ===
API_KEY = "AIzaSyB0zhi598LKqqmFuYtD8cr9BzNoaVaXLA0"
URL = "https://places.googleapis.com/v1/places:searchText"
HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": (
        "nextPageToken,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.location,"
        "places.id,"
        "places.types,"
        "places.primaryType,"
        "places.nationalPhoneNumber,"
        "places.internationalPhoneNumber,"
        "places.rating,"
        "places.userRatingCount,"
        "places.businessStatus,"
        "places.priceLevel,"
        "places.googleMapsUri,"
        "places.websiteUri,"
        "places.regularOpeningHours,"
        "places.currentOpeningHours,"
        "places.editorialSummary,"
        "places.takeout,"
        "places.delivery,"
        "places.dineIn,"
        "places.curbsidePickup,"
        "places.reservable,"
        "places.servesBreakfast,"
        "places.servesLunch,"
        "places.priceRange,"
        "places.servesDinner,"
        "places.servesBeer,"
        "places.servesWine,"
        "places.servesVegetarianFood,"
        "places.servesCoffee,"
        "places.servesDessert,"
    ),
}


# === BUSCA COORDENADAS DA CIDADE USANDO GEOPY ===
def obter_coordenadas(cidade):
    geolocator = Nominatim(user_agent="busca_pizzarias_app")
    local = geolocator.geocode(cidade)
    if local:
        return (local.latitude, local.longitude)
    else:
        raise ValueError(f"❌ Não foi possível localizar a cidade: {cidade}")


# === GERA MALHA DE COORDENADAS AO REDOR DO CENTRO ===
def gerar_malha_circular(centro, raio_total_km=20, espacamento_km=2):
    lat_centro, lng_centro = centro
    coordenadas = []

    passos = int((raio_total_km * 2) / espacamento_km) + 1
    for dx in range(-passos, passos + 1):
        for dy in range(-passos, passos + 1):
            desloc_lat = (
                geopy_distance(kilometers=dy * espacamento_km)
                .destination((lat_centro, lng_centro), bearing=0)
                .latitude
            )
            desloc_lng = (
                geopy_distance(kilometers=dx * espacamento_km)
                .destination((lat_centro, lng_centro), bearing=90)
                .longitude
            )
            nova_coord = (desloc_lat, desloc_lng)
            if geodesic(centro, nova_coord).km <= raio_total_km:
                coordenadas.append(nova_coord)

    print(f"📍 Malha gerada com {len(coordenadas)} pontos.")
    return coordenadas


# === CONSULTA A API GOOGLE PLACES ===
def buscar_leads(lat, lng, query, radius=2000):
    body = {
        "textQuery": query,
        "pageSize": 60,
        "locationBias": {
            "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius}
        },
    }

    try:
        response = requests.post(URL, headers=HEADERS, json=body, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro ao buscar em ({lat}, {lng}): {e}")
        return []

    resultados = []
    for place in data.get("places", []):
        local = place.get("location", {})

        resultado = {
            # "nextPageToken": data.get("nextPageToken", ""),
            "nome": place.get("displayName", {}).get("text", "Sem nome"),
            "endereco": place.get("formattedAddress", "Sem endereço"),
            "coordenadas": f"{local.get('latitude')},{local.get('longitude')}",
            "id": place.get("id", ""),
            "tipoPrincipal": place.get("primaryType", ""),
            "telefoneNacional": place.get("nationalPhoneNumber", ""),
            "telefoneInternacional": place.get("internationalPhoneNumber", ""),
            "avaliacao": place.get("rating", None),
            "numeroAvaliacoes": place.get("userRatingCount", 0),
            "statusEmpresa": place.get("businessStatus", ""),
            "nivelPreco": place.get("priceLevel", ""),
            "urlGoogleMaps": place.get("googleMapsUri", ""),
            "urlWebsite": place.get("websiteUri", ""),
            "resumoEditorial": place.get("editorialSummary", {}).get("text", ""),
            "price_range": formatar_price_range(place.get("priceRange", {})),
            "servicos": {
                "takeout": "Sim" if place.get("takeout", False) else "Não",
                "delivery": "Sim" if place.get("delivery", False) else "Não",
                "dineIn": "Sim" if place.get("dineIn", False) else "Não",
                "curbsidePickup": (
                    "Sim" if place.get("curbsidePickup", False) else "Não"
                ),
                "reservable": "Sim" if place.get("reservable", False) else "Não",
            },
        }
        resultados.append(resultado)

    return resultados


# === FILTRA ÁREAS JÁ COBERTAS ===
def esta_perto_suficiente(
    nova_coord, pontos_cobertos, raio_m=1000, limite_resultados=40
):
    for lat, lng, count in pontos_cobertos:
        distancia = geodesic(nova_coord, (lat, lng)).meters
        if distancia < raio_m and count >= limite_resultados:
            return True
    return False


# === THREAD-SAFE: CONSULTA COM CONTROLE ===
API_SEMAPHORE = threading.Semaphore(10)  # Máximo de 10 requisições simultâneas


def buscar_com_controle(lat, lng, query):
    with API_SEMAPHORE:
        print(f"🔍 Buscando em ({lat:.5f}, {lng:.5f})")
        resultados = buscar_leads(lat, lng, query)
        return (lat, lng, resultados)


# === MULTITHREAD: BUSCAR EM TODA ÁREA ===
def buscar_em_toda_area_multithread(coordenadas, query):
    todos_resultados = []
    pontos_cobertos = []
    tarefas = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        for lat, lng in coordenadas:
            if esta_perto_suficiente((lat, lng), pontos_cobertos):
                print(f"⏭️ Pulando busca em ({lat:.5f}, {lng:.5f}) — área já coberta.")
                continue
            tarefas.append(executor.submit(buscar_com_controle, lat, lng, query))

        for future in as_completed(tarefas):
            try:
                lat, lng, resultados = future.result()
                pontos_cobertos.append((lat, lng, len(resultados)))
                todos_resultados.extend(resultados)
            except Exception as e:
                print(f"❌ Erro na thread: {e}")

    # Remoção de duplicatas
    vistos = set()
    unicos = []
    for r in todos_resultados:
        chave = (r["nome"], r["coordenadas"])
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(r)

    print(f"🔍 {len(todos_resultados)} resultados totais.")
    print(f"✅ {len(unicos)} resultados únicos após filtragem.")
    return unicos


# === SALVAR COMO JSON ===
def salvar_json(dados, query, caminho=None):
    if not caminho:
        nome_base = query[:40].replace(",", "").replace(" ", "_")
        caminho = f"{nome_base}_resultado.json"
    with open(caminho, mode="w", encoding="utf-8") as file:
        json.dump(dados, file, indent=2, ensure_ascii=False)
    print(f"✅ JSON salvo em {caminho}")


import csv
import re


def limpar_nome_arquivo(texto):
    texto = re.sub(r"[^\w\s-]", "", texto)
    return texto.replace(" ", "_")[:40]


def salvar_csv(dados, query, caminho=None):
    if not caminho:
        nome_base = limpar_nome_arquivo(query)
        caminho = f"{nome_base}_resultado.csv"

    if not dados:
        print("⚠️ Nenhum dado para salvar no CSV.")
        return

    campos = list(dados[0].keys())

    # Remove campos indesejados
    for campo in ["servicos", "coordenadas", "id", "resumoEditorial"]:
        if campo in campos:
            campos.remove(campo)

    # Adiciona subcampos de 'servicos' como colunas
    if "servicos" in dados[0]:
        campos.extend(dados[0]["servicos"].keys())

    with open(caminho, mode="w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()
        for item in dados:
            linha = {}

            # Inclui apenas os campos permitidos
            for campo in campos:
                if campo in item:
                    linha[campo] = item[campo]
                elif "servicos" in item and campo in item["servicos"]:
                    linha[campo] = item["servicos"][campo]
                else:
                    linha[campo] = ""

            writer.writerow(linha)

    print(f"✅ CSV salvo em: {caminho}")


def formatar_price_range(price_range):
    if not isinstance(price_range, dict):
        return ""

    currency = price_range.get("startPrice", {}).get("currencyCode", "")
    start = price_range.get("startPrice", {}).get("units")
    end = price_range.get("endPrice", {}).get("units")

    if currency and start and end:
        return f"{currency} {start} - {end}"
    elif currency and start:
        return f"{currency} {start}"
    else:
        return ""


def search_leads(cidade, query):

    centro = obter_coordenadas(cidade)
    coordenadas = gerar_malha_circular(centro, raio_total_km=10, espacamento_km=1.5)
    resultados = buscar_em_toda_area_multithread(coordenadas, query)
    # salvar_json(resultados, query)
    salvar_csv(resultados, query)
    return {len(resultados), resultados}


# === EXECUÇÃO PRINCIPAL ===
if __name__ == "__main__":
    cidade = "Porto, Portugal"
    query = "barbearias, cabeleireiros, salões de beleza, manicures, pedicures, estéticas, depilação, barbearias, cabeleireiros, salões de beleza, manicures, pedicures, estéticas, depilação"
    try:
        centro = obter_coordenadas(cidade)
        coordenadas = gerar_malha_circular(centro, raio_total_km=10, espacamento_km=1.5)
        resultados = buscar_em_toda_area_multithread(coordenadas, query)
        salvar_json(resultados, query, caminho="pizzarias.json")
    except ValueError as e:
        print(str(e))
