import sys, os, re, json
from bs4 import BeautifulSoup

# Uso: python extrair.py <pasta_raiz_do_site> <saida.json>
RAIZ = sys.argv[1]
OUT = sys.argv[2]
BASE_URL = "https://fabio1974.github.io/eleicoes"
UFS = {"ce": "Ceará", "rn": "Rio Grande do Norte", "pb": "Paraíba", "pe": "Pernambuco", "al": "Alagoas",
       "se": "Sergipe", "ba": "Bahia", "pi": "Piauí", "ma": "Maranhão"}

STATUS = {
    "conf": "Rotas do edital, 2º turno confirmado",
    "naodiz": "Rotas do edital, sem dizer o turno",
    "t1": "Rotas só do 1º turno",
    "semdje": "Sem rotas no DJE (rotas sugeridas)",
    "disp": "Transporte dispensado",
    "capital": "Capital, fora do levantamento",
}


def num(s):
    """'5.559' -> 5559 ; '10,1' -> 10.1"""
    if s is None:
        return None
    s = s.strip().replace(".", "").replace(",", ".")
    try:
        return int(s) if re.fullmatch(r"-?\d+", s) else float(s)
    except ValueError:
        return None


def rx(pat, text, g=1, conv=num):
    m = re.search(pat, text, re.S)
    if not m:
        return None
    v = m.group(g)
    return conv(v) if conv else v.strip()


def txt(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)) if el else ""


lista = []
for uf, estado in UFS.items():
  main = BeautifulSoup(open(os.path.join(RAIZ, uf, "index.html"), encoding="utf-8").read(), "html.parser")
  for a in main.select(".mun"):
    slug = a.get("data-n")
    if not slug:
        continue
    flags = (a.get("data-s") or "").split()
    abst = txt(a.find(class_="abst"))
    lista.append({
        "uf": uf.upper(), "estado": estado,
        "slug": slug,
        "nome": txt(a.find("strong")),
        "capital": "capital" in flags,
        "abst_card": rx(r"^([\d.]+) abstenções", abst),
        "abst_pct_card": rx(r"\(([\d,]+)%", abst),
        "situacao_rotas": next((STATUS[f] for f in flags if f in STATUS), "Relatório em preparação" if "prep" in (a.get("class") or []) else ""),
        "versao": "Preliminar" if "prelim" in flags else "Relatório pronto",
        "sem_proposta": "semprop" in flags,
        "rotulo_site": txt(a.find(class_="st")),
    })

municipios, localidades, edital, propostas = [], [], [], []

for item in lista:
    slug = item["slug"]
    uf = item["uf"].lower()
    PI = os.path.join(RAIZ, uf)
    d = dict(item)
    if d.pop("capital") or not os.path.exists(os.path.join(PI, slug, "relatorio.html")):
        d.update({"abstencoes_1t": d.pop("abst_card"), "abstencao_pct_1t": d.pop("abst_pct_card"),
                  "url": f"{BASE_URL}/{uf}/", "url_pdf": None, "fora_do_levantamento": True})
        municipios.append(d)
        continue
    d.pop("abst_card"); d.pop("abst_pct_card")
    d["fora_do_levantamento"] = False
    d["url"] = f"{BASE_URL}/{uf}/{slug}/"

    # --- página do município ---
    s = BeautifulSoup(open(os.path.join(PI, slug, "index.html"), encoding="utf-8").read(), "html.parser")
    pdf = s.find("a", attrs={"download": True})
    d["url_pdf"] = (f"{BASE_URL}/{uf}/{slug}/" + pdf["href"].split("?")[0]) if pdf else None
    if d["url_pdf"]:
        d["url_pdf"] = re.sub(r"/[^/]+/\.\./", "/", d["url_pdf"])
    h1 = s.find("h1")
    sub = txt(h1.find_next("p")) if h1 else ""
    d["zona"] = rx(r"(\d+)ª Zona", sub)
    for div in s.select("dl > div"):
        k, v = txt(div.find("dt")), txt(div.find("dd"))
        if k == "Eleitores":
            d["eleitores"] = num(v)
        elif k == "Locais de votação":
            d["locais_votacao"] = num(v)
        elif k == "Seções":
            d["secoes"] = num(v)
        elif k.startswith("Localidades que precisam"):
            d["localidades_precisam"] = num(v)
        elif k == "Abstenções":
            d["abstencoes_1t"] = rx(r"^([\d.]+)", v)
            d["abstencao_pct_1t"] = rx(r"\(([\d,]+)%", v)
        else:  # candidatos
            d[f"votos_{k}"] = rx(r"^([\d.]+)", v)
            d[f"pct_{k}"] = rx(r"\(([\d,]+)%", v)
    prop = s.find("strong", string=re.compile("Proposta"))
    d["proposta_resumo"] = txt(prop.parent).replace("Proposta:", "").strip() if prop else ""
    d["atualizado_em"] = rx(r"Atualizado em ([\d/]+)", s.get_text(), conv=None)

    # --- relatório ---
    r = BeautifulSoup(open(os.path.join(PI, slug, "relatorio.html"), encoding="utf-8").read(), "html.parser")
    full = re.sub(r"\s+", " ", r.get_text(" ", strip=True))
    d["eleitores_rurais"] = rx(r"São [\d.]+ locais rurais, com ([\d.]+) eleitores", full)
    d["locais_rurais"] = rx(r"São ([\d.]+) locais rurais", full)
    d["pct_eleitores_rurais"] = rx(r"locais rurais, com [\d.]+ eleitores \((\d+)% do total\)", full)
    d["locais_rurais_10km_mais"] = rx(r"([\d.]+) locais rurais ficam a 10 km ou mais da sede", full)
    d["eleitores_locais_10km_mais"] = rx(r"10 km ou mais da sede, com ([\d.]+) eleitores", full)
    d["localidades_rurais_no_mapa"] = rx(r"O mapa mostra ([\d.]+) localidades rurais", full)
    d["loc_mais_5km"] = rx(r"Mais de 5 km \((\d+)\)", full)
    d["loc_3a5km"] = rx(r"De 3 a 5 km \((\d+)\)", full)
    d["loc_ate_3km"] = rx(r"Até 3 km ou com local de votação na própria localidade \((\d+)\)", full)
    d["loc_sem_rota_mais_2km"] = rx(r"([\d.]+) localidades rurais distantes ficam a mais de 2 km", full)
    d["loc_onibus_1a2km"] = rx(r"e outras ([\d.]+) ficam a 1–2 km", full)
    d["rotas_edital"] = rx(r"O edital tem ([\d.]+) rotas", full)
    if d["rotas_edital"] is None and "Não há rotas de transporte de eleitores publicadas" in full:
        d["rotas_edital"] = 0
    d["edital"] = rx(r"Transporte de Eleitores – .*?\) *: proposta.*?Propomos", full, g=0, conv=None) and None
    h2s = r.find_all("h2")
    ed_h = next((h for h in h2s if txt(h).startswith("Rotas d") and "propostas" not in txt(h)), None)
    d["edital"] = re.sub(r"^Rotas do ", "", txt(ed_h)) if ed_h and txt(ed_h).startswith("Rotas do ") else ("Sem rotas publicadas no DJE" if ed_h else "")
    d["horarios_edital"] = rx(r"Horários: (.*?)\. Veículos:", full, conv=None)
    d["veiculos_edital"] = rx(r"Veículos: (.*?)(?:\.\s+Rota Percurso|\. Rota Percurso| Rota Percurso)", full, conv=None)
    att = r.find(string=re.compile(r"^\s*Atenção:?\s*$"))
    d["observacao_turno"] = txt(att.find_parent("p")).replace("Atenção:", "").strip() if att and att.find_parent("p") else ""
    d["propostas_texto"] = rx(r"Propomos ao Juiz Eleitoral da \d+ª Zona Eleitoral (.*?) no transporte gratuito", full, conv=None)
    d["rotas_novas"] = rx(r"(\d+) rotas? novas?", d["propostas_texto"] or "") or 0
    d["paradas_extras"] = rx(r"(\d+) paradas? extras?", d["propostas_texto"] or "") or 0
    d["extensoes"] = rx(r"(\d+) extens(?:ão|ões)", d["propostas_texto"] or "") or 0
    d["juiz_eleitoral"] = rx(r"Excelentíssim\w*(?:\(a\))? Senhor\w*(?:\(a\))? (.*?) Juiz\(?a?\)? Eleitoral da", full, conv=None)
    if d["juiz_eleitoral"] and d["juiz_eleitoral"].startswith("["):
        d["juiz_eleitoral"] = ""
    sede = rx(r"Juiz\(?a?\)? Eleitoral da \d+ª Zona Eleitoral – (.*?)/PI", full, conv=None)
    d["sede_zona"] = "" if (sede or "").startswith("[") else sede

    # --- tabelas ---
    for t in r.find_all("table"):
        heads = [txt(th) for th in t.find_all("th")]
        rows = [[txt(td) for td in tr.find_all("td")] for tr in t.find_all("tr")]
        rows = [x for x in rows if x]
        if heads and heads[0] == "Localidade":
            for x in rows:
                localidades.append({
                    "uf": d["uf"], "municipio": d["nome"], "zona": d["zona"], "localidade": x[0],
                    "km_ate_local_votacao": num(x[1]), "rota_mais_proxima": x[2],
                    # o relatório usa 1.000.000.000 km quando não conseguiu medir: vira vazio
                    "km_ate_percurso_rota": (lambda v: None if v is not None and v >= 1e6 else v)(num(x[3]) if len(x) > 3 else None),
                    "situacao": x[4] if len(x) > 4 else "",
                })
        elif heads and heads[0] == "Rota":
            for x in rows:
                edital.append({"uf": d["uf"], "municipio": d["nome"], "zona": d["zona"], "edital": d["edital"],
                               "rota": x[0], "percurso": x[1] if len(x) > 1 else ""})
        elif heads and heads[0] == "Proposta":
            for x in rows:
                tipo = x[0].split("–")[0].strip()
                tipo_proposta = ("Rota nova" if tipo.startswith("Rota nova") or "(nova)" in x[0] else
                                 "Parada extra" if tipo.startswith("Parada") else
                                 "Extensão de rota" if tipo.startswith("Extensão") else
                                 "Ajuste em rota do edital")
                propostas.append({
                    "uf": d["uf"], "municipio": d["nome"], "zona": d["zona"], "proposta": x[0], "tipo": tipo, "tipo_proposta": tipo_proposta,
                    "percurso": x[1], "localidades_atendidas": x[2],
                    "n_localidades_atendidas": len([p for p in re.split(r",\s*", x[2]) if p]),
                    "extensao_km": rx(r"([\d.,]+) km", x[3]), "extensao_texto": x[3],
                    "tempo": x[4] if len(x) > 4 else "",
                })
    meus = [p for p in propostas if p["municipio"] == d["nome"] and p["uf"] == d["uf"]]
    d["rotas_novas"] = sum(1 for p in meus if p["tipo_proposta"] == "Rota nova")
    d["paradas_extras"] = sum(1 for p in meus if p["tipo_proposta"] == "Parada extra")
    d["extensoes"] = sum(1 for p in meus if p["tipo_proposta"] != "Rota nova" and p["tipo_proposta"] != "Parada extra")
    d["n_localidades_tabela"] = sum(1 for l in localidades if l["municipio"] == d["nome"] and l["uf"] == d["uf"])
    municipios.append(d)

json.dump({"municipios": municipios, "localidades": localidades, "edital": edital, "propostas": propostas},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(municipios), len(localidades), len(edital), len(propostas))
