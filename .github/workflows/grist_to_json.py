import requests
import json
import os
import sys
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────
DOC_ID = "ex369ZUNRrA9"
BASE   = "https://grist.numerique.gouv.fr"

# Noms exacts de tes onglets Grist
TABLE_BIB = "Bib"
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

def ms_to_date(val):
    if val is None: return None
    try: return datetime.fromtimestamp(val / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except: return None

def find_table_id(tables_list, name):
    for t in tables_list:
        if t.get("name") == name: return t["id"]
    return None

# ── Récupération ──────────────────────────────────────────────
print("Récupération des tables...")
all_tables = api_get("/tables")["tables"]

table_ids = {}
for name in [TABLE_BIB, TABLE_PER, TABLE_HOR, TABLE_FER, TABLE_PRE]:
    tid = find_table_id(all_tables, name)
    if not tid:
        print(f"Table introuvable : {name}")
        sys.exit(1)
    table_ids[name] = tid

raw = {}
for name, tid in table_ids.items():
    raw[name] = api_get(f"/tables/{tid}/records")["records"]

# ── Transformation ─────────────────────────────────────────────
# --- Bibliothèques ---
bib_by_recid = {}
bibliotheques = []
for r in raw[TABLE_BIB]:
    f = r["fields"]
    bib_by_recid[r["id"]] = f
    bibliotheques.append({
        "id": f.get("id2"),
        "nom": f.get("nom"),
        "icone": f.get("icone"),
        "ordre": f.get("ordre")
    })
bibliotheques.sort(key=lambda x: x.get("ordre") or 99)

# --- Périodes ---
per_by_recid = {}
periodes = []
for r in raw[TABLE_PER]:
    f = r["fields"]
    per_by_recid[r["id"]] = f
    periodes.append({
        "id": f.get("id2"),
        "nom": f.get("nom"),
        "date_debut": ms_to_date(f.get("date_debut")),
        "date_fin": ms_to_date(f.get("date_fin")),
        "priorite": f.get("priorite"),
        "active": bool(f.get("active", False)),
        "alerte": f.get("alerte") or None,
        "type_alerte": f.get("type_alerte") or None
    })

# --- Horaires ---
horaires = {}
for r in raw[TABLE_HOR]:
    f = r["fields"]
    bib_recid = f.get("biblio")
    per_recid = f.get("periode")
    
    bib_id = bib_by_recid.get(bib_recid, {}).get("id2") if bib_recid else None
    per_id = per_by_recid.get(per_recid, {}).get("id2") if per_recid else None

    jour = f.get("jour")
    debut = f.get("heure_debut")
    fin = f.get("heure_fin")

    if not bib_id or not per_id or jour is None or debut is None or fin is None:
        continue

    jour_str = str(int(jour))

    if per_id not in horaires: horaires[per_id] = {}
    if bib_id not in horaires[per_id]: horaires[per_id][bib_id] = {str(j): [] for j in range(7)}

    horaires[per_id][bib_id][jour_str].append({"d": debut, "f": fin})

for per_id in horaires:
    for bib_id in horaires[per_id]:
        for jour_str in horaires[per_id][bib_id]:
            horaires[per_id][bib_id][jour_str].sort(key=lambda x: x["d"])

# --- Fermetures ---
fermetures = []
for r in raw[TABLE_FER]:
    f = r["fields"]
    fermetures.append({
        "biblio": f.get("biblio"),
        "debut": ms_to_date(f.get("date_debut")),
        "fin": ms_to_date(f.get("date_fin")),
        "motif": f.get("motif"),
        "type": f.get("type")
    })

# --- Prêts ---
prets_raw = {}
for r in raw[TABLE_PRE]:
    f = r["fields"]
    cle = f.get("cle")
    if cle: prets_raw[cle] = f

prets = {
    "actif": bool(prets_raw.get("actif", {}).get("valeur_bool", False)),
    "debut": ms_to_date(prets_raw.get("debut", {}).get("valeur_date")),
    "fin": ms_to_date(prets_raw.get("fin", {}).get("valeur_date")),
    "duree_semaines": prets_raw.get("duree_semaines", {}).get("valeur_nombre"),
    "prolongation": bool(prets_raw.get("prolongation", {}).get("valeur_bool", False)),
    "texte": prets_raw.get("texte", {}).get("valeur_texte")
}

# ── Finalisation ──────────────────────────────────────────────
result = {
    "bibliotheques": bibliotheques,
    "periodes": periodes,
    "horaires": horaires,
    "fermetures": fermetures,
    "prets": prets,
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
}

with open("horaires.json", "w", encoding="utf-8") as fp:
    json.dump(result, fp, ensure_ascii=False, indent=2)

print("Fichier horaires.json généré avec succès !")
