"""
Prepara os dados do painel a partir de dados.json (gerado por extrair.py)
e dos relatórios HTML do site (de onde vêm os mapas).

Uso:
    python preparar_painel.py <dados.json> <pasta_raiz_do_site> <pasta_saida>

Gera em <pasta_saida>:
    json/<id>.json   um arquivo por conjunto de dados (para o painel online)
    js/<id>.js       o mesmo conteúdo como script (para o painel offline)
    manifesto.json   lista dos conjuntos, com título e descrição

Conjuntos:
    municipios          um por município, com as contagens de localidades e propostas
    loc_<UF>            localidades rurais distantes do estado
    prop_<UF>           rotas propostas no estado
    mapas_<UF>[_<n>]    mapas (SVG) dos relatórios do estado, em partes de até ~6 MB
"""
import json
import os
import re
import sys
from collections import defaultdict

dados_json, raiz, saida = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(dados_json, encoding="utf-8"))
UFS = ["CE", "RN", "PB", "PE", "AL", "SE", "BA", "PI", "MA"]
ESTADO = {"CE": "Ceará", "RN": "Rio Grande do Norte", "PB": "Paraíba", "PE": "Pernambuco", "AL": "Alagoas",
          "SE": "Sergipe", "BA": "Bahia", "PI": "Piauí", "MA": "Maranhão"}
LIMITE_MAPAS = 6_000_000


def categoria(s):
    if s.startswith("Atendida"):
        return "Atendida"
    if s.startswith("Rota passa perto"):
        return "Ônibus a 1–2 km"
    return "Sem rota"


chave = lambda uf, nome: f"{uf}|{nome}"

# ---- propostas, por estado, e índice localidade -> propostas ----
por_localidade = defaultdict(list)
prop = defaultdict(list)
cont = defaultdict(lambda: {"rotas_novas": 0, "paradas_extras": 0, "extensoes": 0, "km_rotas_novas": 0.0})
for p in sorted(d["propostas"], key=lambda p: (p["uf"], p["municipio"], p["tipo_proposta"] != "Rota nova")):
    uf = p["uf"]
    prop[uf].append({
        "id": f"P{uf}{len(prop[uf]) + 1:05d}", "uf": uf, "municipio": p["municipio"], "tipo": p["tipo_proposta"],
        "proposta": p["proposta"], "percurso": p["percurso"], "localidades_atendidas": p["localidades_atendidas"],
        "n_localidades": p["n_localidades_atendidas"], "extensao_km": p["extensao_km"], "tempo": p["tempo"],
    })
    c = cont[chave(uf, p["municipio"])]
    if p["tipo_proposta"] == "Rota nova":
        c["rotas_novas"] += 1
        c["km_rotas_novas"] += p["extensao_km"] or 0
    elif p["tipo_proposta"] == "Parada extra":
        c["paradas_extras"] += 1
    else:
        c["extensoes"] += 1
    for nome in [x.strip() for x in p["localidades_atendidas"].split(",") if x.strip()]:
        por_localidade[(uf, p["municipio"], nome)].append(p["proposta"])

# ---- localidades, por estado ----
loc = defaultdict(list)
cl = defaultdict(lambda: {"analisadas": 0, "atendidas": 0, "perto": 0, "sem_rota": 0})
for l in sorted(d["localidades"], key=lambda l: (l["uf"], l["municipio"])):
    uf, cat = l["uf"], categoria(l["situacao"])
    sol = ""
    if cat != "Atendida":
        sol = "; ".join(dict.fromkeys(por_localidade.get((uf, l["municipio"], l["localidade"]), [])))
    loc[uf].append({
        "id": f"L{uf}{len(loc[uf]) + 1:06d}", "uf": uf, "municipio": l["municipio"], "localidade": l["localidade"],
        "situacao": cat, "situacao_detalhe": l["situacao"], "km_local_votacao": l["km_ate_local_votacao"],
        "rota_mais_proxima": l["rota_mais_proxima"], "km_ate_rota": l["km_ate_percurso_rota"],
        "solucao_proposta": sol,
    })
    c = cl[chave(uf, l["municipio"])]
    c["analisadas"] += 1
    c[{"Atendida": "atendidas", "Ônibus a 1–2 km": "perto", "Sem rota": "sem_rota"}[cat]] += 1

# ---- mapas, por estado, em partes ----
mapas = {}
mapa_de = {}
for uf in UFS:
    partes, atual, tam = [], [], 0
    for m in sorted([m for m in d["municipios"] if m["uf"] == uf and not m["fora_do_levantamento"]], key=lambda m: m["nome"]):
        cam = os.path.join(raiz, uf.lower(), m["slug"], "relatorio.html")
        if not os.path.exists(cam):
            continue
        achado = re.search(r"<svg.*?</svg>", open(cam, encoding="utf-8").read(), re.S)
        if not achado:
            continue
        svg = re.sub(r"\s+", " ", achado.group(0))
        if atual and tam + len(svg.encode()) > LIMITE_MAPAS:
            partes.append(atual)
            atual, tam = [], 0
        atual.append({"municipio": m["nome"], "svg": svg})
        tam += len(svg.encode())
    if atual:
        partes.append(atual)
    for i, parte in enumerate(partes, 1):
        ds = f"mapas_{uf}" if len(partes) == 1 else f"mapas_{uf}_{i}"
        mapas[ds] = parte
        for r in parte:
            mapa_de[chave(uf, r["municipio"])] = ds

# ---- municípios ----
municipios = []
for m in d["municipios"]:
    k = chave(m["uf"], m["nome"])
    fora = m["fora_do_levantamento"]
    r = {
        "chave": k, "uf": m["uf"], "estado": ESTADO[m["uf"]], "nome": m["nome"],
        "situacao_rotas": m["situacao_rotas"], "versao": None if fora else m.get("versao"),
        "fora_do_levantamento": fora, "zona": m.get("zona"), "sede_zona": m.get("sede_zona") or None,
        "juiz_eleitoral": m.get("juiz_eleitoral") or None, "edital": m.get("edital") or None,
        "eleitores": m.get("eleitores"), "eleitores_rurais": m.get("eleitores_rurais"),
        "abstencoes_1t": m.get("abstencoes_1t"),
        "abstencao_pct_1t": None if m.get("abstencao_pct_1t") is None else m["abstencao_pct_1t"] / 100,
        "rotas_edital": m.get("rotas_edital"), "url": m.get("url"), "url_pdf": m.get("url_pdf"),
        "mapa": mapa_de.get(k),
    }
    r.update(cl[k] if k in cl else {"analisadas": 0, "atendidas": 0, "perto": 0, "sem_rota": 0})
    c = cont[k] if k in cont else {"rotas_novas": 0, "paradas_extras": 0, "extensoes": 0, "km_rotas_novas": 0.0}
    r.update(c)
    r["km_rotas_novas"] = round(r["km_rotas_novas"], 1)
    municipios.append(r)

# ---- gravação ----
conjuntos = {"municipios": (municipios, "Municípios do Nordeste",
             "Um por município (9 estados), extraído dos relatórios do levantamento (19/10/2026): eleitorado, "
             "situação das rotas, edital e abstenção, mais as localidades por situação e as propostas contadas "
             "nas tabelas de cada relatório.")}
for uf in UFS:
    conjuntos[f"loc_{uf}"] = (loc[uf], f"Localidades – {uf}",
        f"Localidades rurais de {ESTADO[uf]} a 3 km ou mais do local de votação, com distância por estrada à urna "
        "e ao percurso do ônibus, situação e a proposta que as atende. Distâncias que o relatório não mede ficam vazias.")
    conjuntos[f"prop_{uf}"] = (prop[uf], f"Rotas propostas – {uf}",
        f"Rotas novas, paradas extras e extensões propostas nos relatórios de {ESTADO[uf]}, com percurso, extensão e tempo.")
for ds, linhas in mapas.items():
    uf = ds.split("_")[1]
    parte = f" (parte {ds.split('_')[2]})" if ds.count("_") == 2 else ""
    conjuntos[ds] = (linhas, f"Mapas – {uf}{parte}",
        f"Mapas (SVG) dos relatórios de {ESTADO[uf]}{parte}, com rotas do edital, propostas e localidades.")

os.makedirs(os.path.join(saida, "json"), exist_ok=True)
os.makedirs(os.path.join(saida, "js"), exist_ok=True)
manifesto = []
for ds, (linhas, titulo, desc) in conjuntos.items():
    texto = json.dumps(linhas, ensure_ascii=False, separators=(",", ":"))
    open(os.path.join(saida, "json", ds + ".json"), "w", encoding="utf-8").write(texto)
    open(os.path.join(saida, "js", ds + ".js"), "w", encoding="utf-8").write(
        f"window.DADOS = window.DADOS || {{}};\nwindow.DADOS[{json.dumps(ds)}] = {texto};\n"
        f"if (window.__dadosCarregados) window.__dadosCarregados({json.dumps(ds)});\n")
    manifesto.append({"id": ds, "titulo": titulo, "descricao": desc, "linhas": len(linhas), "bytes": len(texto.encode())})
json.dump(manifesto, open(os.path.join(saida, "manifesto.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for x in manifesto:
    print(f'{x["id"]:14s} {x["linhas"]:6d} linhas {x["bytes"] / 1e6:6.2f} MB')
