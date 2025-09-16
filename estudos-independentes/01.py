# especialista_spotify_decada.py
# Sistema especialista → Spotify Web API → recomenda 1 música mais popular por gênero + década

import base64, json, sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os

GENS = [
    "Pop",
    "Funk",
    "Rock",
    "Hip-Hop",
    "Trap",
    "Eletrônica",
    "Lo-fi",
    "MPB",
    "Samba",
    "Pagode",
    "Forró",
    "Sertanejo",
    "Jazz",
    "Blues",
]

GENRE_HINT = {
    "Pop": "pop",
    "Funk": '"funk carioca" OR funk',
    "Rock": "rock",
    "Hip-Hop": '"hip hop" OR rap',
    "Trap": "trap",
    "Eletrônica": "electronic OR edm OR house",
    "Lo-fi": '"lo-fi" OR lofi OR chillhop',
    "MPB": '"musica popular brasileira" OR mpb',
    "Samba": "samba",
    "Pagode": "pagode",
    "Forró": "forro OR forró OR baião",
    "Sertanejo": "sertanejo",
    "Jazz": "jazz",
    "Blues": "blues",
}

DECADAS = {
    "1980s": (1980, 1989),
    "1990s": (1990, 1999),
    "2000s": (2000, 2009),
    "2010s": (2010, 2019),
    "2020s": (2020, 2029),
}

def carregar_env(arquivo):
    with open(arquivo) as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            chave, valor = linha.split("=", 1)
            os.environ[chave.strip()] = valor.strip()

def get_token():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, "config.env")
    carregar_env(env_path)

    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")

    url = "https://accounts.spotify.com/api/token"
    auth_b64 = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = urlencode({"grant_type": "client_credentials"}).encode()
    req = Request(url, data=data, headers=headers)
    with urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())["access_token"]


def spotify_get(url: str, token: str, params: dict):
    qs = urlencode(params)
    req = Request(f"{url}?{qs}", headers={"Authorization": f"Bearer {token}"})
    with urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def buscar_top_decada(token: str, genero: str, decada: tuple, market="BR"):
    inicio, fim = decada
    termo_genero = GENRE_HINT.get(genero, genero)
    q = f"year:{inicio}-{fim} {termo_genero}"
    res = spotify_get(
        "https://api.spotify.com/v1/search",
        token,
        {"q": q, "type": "track", "limit": 50, "market": market},
    )
    items = res.get("tracks", {}).get("items", [])
    if not items:
        return None
    items.sort(key=lambda t: int(t.get("popularity", 0)), reverse=True)
    top = items[0]
    artistas = ", ".join(a["name"] for a in top.get("artists", []))
    return {
        "title": top.get("name"),
        "artists": artistas,
        "album": top.get("album", {}).get("name"),
        "release_date": top.get("album", {}).get("release_date", "?"),
        "popularity": top.get("popularity", 0),
        "link": top.get("external_urls", {}).get("spotify"),
    }

def explicar_recomendacao(genero, decada, rec):
    return (
        f"A música '{rec['title']}' foi escolhida porque é a mais popular "
        f"entre as faixas de {genero} lançadas entre {decada[0]} e {decada[1]} "
        f"segundo o Spotify."
    )

def main():
    print("=== Sistema Especialista Musical (Spotify) ===")
    for i, g in enumerate(GENS, 1):
        print(f"{i}) {g}")
    try:
        op = int(input("Escolha o número do gênero: ").strip())
        genero = GENS[op - 1]
    except:
        genero = "Pop"

    print("\nEscolha a década:")
    decs = list(DECADAS.keys())
    for i, d in enumerate(decs, 1):
        print(f"{i}) {d}")
    try:
        op = int(input("Número da década: ").strip())
        decada = DECADAS[decs[op - 1]]
    except:
        decada = DECADAS["2010s"]

    token = get_token()
    rec = buscar_top_decada(token, genero, decada)
    if not rec:
        print("\nNada encontrado nessa década.")
        return

    print("\n--- Recomendação ---")
    print(f"🎵 Música : {rec['title']}")
    print(f"👤 Artista: {rec['artists']}")
    if rec.get("album"):
        print(f"💿 Álbum  : {rec['album']}")
    print(f"📅 Lanço.: {rec['release_date']}")
    print(f"📈 Popularidade: {rec['popularity']}")
    if rec.get("link"):
        print(f"🔗 Spotify: {rec['link']}")
    print(f"ℹ️ Explicação: {explicar_recomendacao(genero, decada, rec)}")


if __name__ == "__main__":
    main()