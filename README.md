# Transporte de eleitores rurais – Nordeste

Painel e planilha com as localidades rurais que ficam longe do local de votação
e do percurso dos ônibus da Justiça Eleitoral, nos 9 estados do Nordeste
(CE, RN, PB, PE, AL, SE, BA, PI, MA), para apoiar pedidos de inclusão de rotas
de transporte gratuito (Lei nº 6.091/1974).

Os dados foram extraídos dos relatórios municipais publicados em
<https://fabio1974.github.io/eleicoes/> (atualizados em 19/10/2026). As fontes
originais, segundo o levantamento, são TRE e TSE (locais de votação), editais
de rotas no Diário da Justiça Eletrônico, IBGE – Localidades do Brasil 2022,
OpenStreetMap e OSRM (distâncias por estrada). Confirme os números com o
Cartório Eleitoral de cada zona.

## Como usar

- **Painel:** abra `painel/index.html` no navegador. Funciona sem internet.
  Escolha um estado para ver as localidades, a dispersão de distâncias e as
  rotas propostas; escolha um município para ver o mapa do relatório.
- **Planilha:** `planilha/transporte_eleitores_rurais_NE.xlsx`, com resumo por
  estado (fórmulas) e as abas Municípios, Localidades, Rotas propostas e Rotas
  do edital.
- **Dados brutos:** `dados/` traz os mesmos conjuntos em JSON, e
  `dados/dados_extraidos.json` tudo o que foi extraído dos relatórios.

## Números principais

| | Nordeste |
|---|---|
| Municípios com relatório | 1.780 |
| Localidades distantes (3 km+ do local de votação) | 59.414 |
| Atendidas (ônibus a até 1 km) | 26.350 |
| Ônibus a 1–2 km (parada extra resolve) | 5.833 |
| Sem rota | 27.231 |
| Rotas novas propostas | 9.479 |
| Paradas extras propostas | 3.721 |

As 8 capitais ficam fora do levantamento (área essencialmente urbana) e 6
municípios estavam com relatório em preparação.

## Definições

- **Atendida:** um ônibus do edital passa a até 1 km.
- **Ônibus a 1–2 km:** basta uma parada extra ou um pequeno desvio.
- **Sem rota:** ônibus a mais de 2 km, município sem rotas publicadas no DJE ou
  transporte dispensado pela Justiça Eleitoral.
- Quando o relatório marca a distância até o ônibus como 1.000.000.000 km
  (rota que não pôde ser traçada), o valor foi tratado como vazio.

## Atualizar os dados

Requer Python 3 com `beautifulsoup4` e `openpyxl`.

```bash
git clone https://github.com/fabio1974/eleicoes.git site
python scripts/extrair.py site dados/dados_extraidos.json
python scripts/planilha.py dados/dados_extraidos.json planilha/transporte_eleitores_rurais_NE.xlsx
python scripts/preparar_painel.py dados/dados_extraidos.json site saida
cp saida/js/*.js painel/dados/
```

A planilha é gerada sem valores calculados nas fórmulas; o Excel ou o
LibreOffice calculam ao abrir.

## Estrutura

```
index.html            redireciona para o painel
painel/               painel interativo (HTML, d3 e dados em JS)
planilha/             planilha Excel
dados/                dados em JSON
scripts/              extração, planilha e preparação do painel
```
