# Transporte de eleitores rurais – Nordeste

Projeto de estudo de análise de dados e indicação de rotas feito com o apoio de
inteligência artificial, para fins educacionais.

O projeto reúne, em um painel interativo e em planilhas, dados sobre
localidades rurais dos 9 estados do Nordeste (CE, RN, PB, PE, AL, SE, BA, PI e
MA): a distância de cada uma até o local de votação e até o percurso dos
ônibus publicados pela Justiça Eleitoral, e as rotas sugeridas para as que
ficam sem ônibus.

**Painel publicado:** <https://arturfelipeveloso.github.io/transporte-eleitores-nordeste/>

## Origem dos dados

Os dados foram extraídos dos relatórios municipais publicados em
<https://fabio1974.github.io/eleicoes/> (atualizados em 19/10/2026). Segundo
esses relatórios, as fontes originais são o TRE e o TSE (locais de votação), os
editais de rotas no Diário da Justiça Eletrônico, o IBGE (Localidades do Brasil
2022), o OpenStreetMap e o OSRM (distâncias por estrada).

Por se tratar de um estudo, os números não substituem as informações oficiais
e devem ser confirmados com o Cartório Eleitoral de cada zona.

## Conteúdo

- **Painel:** `painel/index.html`. Funciona no navegador, inclusive sem
  internet. Tem duas abas:
  - **Diagnóstico:** cobertura das localidades por estado e município,
    distância até a urna e até o ônibus, tabela de localidades e mapa do
    relatório de cada município.
  - **Plano de rotas:** rotas sugeridas organizadas por prioridade, gráfico de
    custo × alcance e o trajeto de cada rota desenhado parada a parada. O link
    `painel/#plano` abre direto nesta aba.
- **Planilha de diagnóstico:** `planilha/transporte_eleitores_rurais_NE.xlsx`,
  com resumo por estado e as abas Municípios, Localidades, Rotas propostas e
  Rotas do edital.
- **Planilha de indicações:** `planilha/plano_de_rotas_NE.xlsx`, com resumo por
  estado, indicações por município, cada rota sugerida e cada localidade sem
  ônibus com a rota que a atende.
- **Dados:** `dados/` traz os conjuntos em JSON, e `dados/dados_extraidos.json`
  tudo o que foi extraído dos relatórios.
- **Scripts:** `scripts/` traz a extração, a montagem das planilhas e a
  preparação dos dados do painel.

## Números principais

| | Nordeste |
|---|---|
| Municípios com relatório | 1.780 |
| Localidades distantes (3 km ou mais do local de votação) | 59.414 |
| Atendidas (ônibus a até 1 km) | 26.350 |
| Ônibus a 1–2 km | 5.833 |
| Sem rota | 27.231 |
| Rotas sugeridas | 13.203 |
| Localidades sem ônibus cobertas por uma sugestão | 33.056 de 33.064 |

As 8 capitais não fazem parte do levantamento original (área essencialmente
urbana) e 6 municípios estavam com o relatório em preparação.

## Prioridades das rotas sugeridas

| Prioridade | Critério | Sugestões |
|---|---|---|
| 1 – Ação rápida | Parada extra ou extensão de uma rota do edital | 3.724 |
| 2 – Rota nova eficiente | Rota nova com até 10 km de percurso por localidade atendida | 4.426 |
| 3 – Rota nova cara | Rota nova com mais de 10 km por localidade atendida | 5.053 |

O limite de 10 km por localidade é um critério do estudo, próximo da mediana
das rotas novas.

## Definições

- **Localidade distante:** comunidade rural a 3 km ou mais, por estrada, do
  local de votação mais próximo.
- **Atendida:** um ônibus do edital passa a até 1 km.
- **Ônibus a 1–2 km:** basta uma parada extra ou um pequeno desvio.
- **Sem rota:** ônibus a mais de 2 km, município sem rotas publicadas no DJE ou
  transporte dispensado pela Justiça Eleitoral.
- Quando o relatório marca a distância até o ônibus como 1.000.000.000 km
  (rota que não pôde ser traçada), o valor foi tratado como vazio.

## Como atualizar os dados

Requer Python 3 com `beautifulsoup4` e `openpyxl`.

```bash
git clone https://github.com/fabio1974/eleicoes.git site
python scripts/extrair.py site dados/dados_extraidos.json
python scripts/planilha.py dados/dados_extraidos.json planilha/transporte_eleitores_rurais_NE.xlsx
python scripts/preparar_painel.py dados/dados_extraidos.json site saida
cp saida/js/*.js painel/dados/
python scripts/planilha_plano.py saida/json planilha/plano_de_rotas_NE.xlsx
```

As planilhas são geradas com fórmulas sem valores calculados; o Excel ou o
LibreOffice calculam ao abrir.

## Estrutura

```
index.html     redireciona para o painel
painel/        painel interativo (HTML, d3 e dados em JS)
planilha/      planilhas Excel
dados/         dados em JSON
scripts/       extração, planilhas e preparação do painel
```
