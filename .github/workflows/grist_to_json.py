import requests
import json
import os
import sys
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────
DOC_ID = "ex369ZUNRrA9"
BASE   = "https://grist.numerique.gouv.fr"

# Noms exacts de tes onglets Grist
TABLE_BIB = "Bibliotheques"
TABLE_PER = "Periodes"
TABLE_HOR = "Horaires"
TABLE_FER = "Fermetures"
TABLE_PRE = "Prets"

API_KEY = os.environ.get("GRIST_API_KEY", "")
if not API_KEY:
    print("ERREUR : variable GRIST_API_KEY vide")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def api_get(path):
    url = f"{BASE}/api/docs/{DOC_ID}{path}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"ERREUR API {r.status_code} sur {url}")
        sys.exit(1)
    return r.json()

# ── DEBUG : Voir exactement ce que l'API renvoie ──────────────
print("Récupération des tables...")
all_tables = api_get("/tables")["tables"]

print("=== TABLES TROUVÉES DANS GRIST ===")
for t in all_tables:
    # On affiche le nom avec des guillemets pour voir les espaces cachés
    nom = t.get("name", "")
    print(f"ID: {t.get('id')} | Nom: '{nom}' | Longueur: {len(nom)}")
print("==================================")

# On compare avec ce qu'on cherche
noms_cherches = [TABLE_BIB, TABLE_PER, TABLE_HOR, TABLE_FER, TABLE_PRE]
print(f"Noms qu'on cherche : {noms_cherches}")
sys.exit(0) # On arrête le script ici juste pour voir le résultat
