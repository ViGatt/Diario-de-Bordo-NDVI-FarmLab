# 🛰️ Diário de Bordo — NDVI FarmLab
# Acesso - https://vigatt.github.io/Diario-de-Bordo-NDVI-FarmLab/
### Monitoramento de Milho por Satélite · Safra 2025–2026

> Projeto acadêmico de análise temporal de NDVI desenvolvido com dados fornecidos pela **Jacto / FarmLab**, utilizando imagens do satélite **Sentinel-2 (ESA)** processadas pela plataforma **One Soil**.

---

## 📌 Sobre o Projeto

Este repositório documenta a análise de índices de vegetação (NDVI) aplicada ao monitoramento de quatro talhões de milho durante a safra safrinha 2025–2026, localizada na região de Marília – SP.

O objetivo é acompanhar a evolução fenológica da cultura por meio de imagens de satélite, comparar sistemas de manejo (Convencional vs. Agricultura 4.0) e correlacionar os dados espectrais com os eventos da safra — plantio, adubação, aplicação de defensivos e colheita.

---

## 🌽 Contexto Agrícola

| Talhão | Season ID | Tipo de Colheita | Sistema de Manejo |
|---|---|---|---|
| Silagem Convencional | `0bf86c8b` | Silagem (~Mar/Abr 2026) | Convencional |
| Grão 4.0 | `258e47e0` | Grão (Mai 2026) | Agricultura de Precisão 4.0 |
| Grão Convencional | `b7292cb8` | Grão (Mai 2026) | Convencional |
| Silagem 4.0 | `f791bf13` | Silagem (~Mar/Abr 2026) | Agricultura de Precisão 4.0 |

**Estágio atual (Fev 2026):** Florescimento — NDVI ~0.2–0.4 (vegetação baixa/inicial).

---

## 🗓️ Timeline da Safra

```
Out 2025  →  Plantio do milho (safrinha)
Nov 2025  →  Adubação de base
Dez 2025  →  1ª Aplicação de defensivos
Jan 2026  →  2ª Aplicação + Imagens NDVI #1
Fev 2026  →  Florescimento + Imagens NDVI #2  ← AGORA
Mar 2026  →  Enchimento de grãos
Mai 2026  →  Colheita + Mapas de Produtividade (Yield)
```

---

## 🛰️ Dados

### Fonte
- **Satélite:** Sentinel-2 (ESA) — resolução espacial de 10 m/pixel
- **Plataforma:** One Soil (análise de satélite e zonas de manejo)
- **Projeção original:** SIRGAS 2000 / UTM fuso 22S (`EPSG:31982`)
- **Projeção dos arquivos:** Web Mercator (`EPSG:3857`)

### Arquivos do Dataset

| Arquivo | Formato | Descrição |
|---|---|---|
| `ndvi/` | GeoTIFF | 196 imagens NDVI · 4 talhões × 49 datas · 3 bandas · 54×40 px |
| `images/` | JPEG | 196 previews RGB para visualização rápida |
| `ndvi_metadata.csv` | CSV | 196 registros · 75 colunas · estatísticas raster por imagem |
| `ndvi_metadata.parquet` | Parquet | Mesma estrutura do CSV em formato binário otimizado |

### Estrutura das Bandas (GeoTIFF)

| Banda | Conteúdo | Colunas-chave |
|---|---|---|
| B1 — NDVI | Índice de vegetação por pixel (−1 a 1) | `b1_mean`, `b1_std`, `b1_valid_pixels`, `b1_pct_*` |
| B2 — Qualidade | Máscara de confiança do pixel (0 = válido) | `b2_mean`, `b2_valid_pixels` |
| B3 — Máscara Talhão | Delimitação do polígono agrícola (0/1) | `b3_count_veg_densa`, `b3_mean` |

---

## 📊 Escala NDVI — Interpretação Agronômica

| Faixa | Classe | Significado |
|---|---|---|
| `< 0.0` | Água | Superfícies aquáticas / sombra |
| `0.0 – 0.2` | Solo exposto | Esperado no plantio (Out 2025) |
| `0.2 – 0.4` | Veg. baixa ← **atual** | Desenvolvimento inicial / florescimento |
| `0.4 – 0.6` | Veg. moderada | Crescimento ativo |
| `0.6 – 0.8` | Veg. alta | Dossel bem desenvolvido |
| `> 0.8` | Veg. densa | Cobertura máxima |

---

## 🌐 Diário de Bordo (Site)

O arquivo `diario_ndvi.html` é o site de documentação do projeto — um diário de bordo interativo com abas que são atualizadas a cada nova descoberta da análise.

**Abas disponíveis:**
- `01 · Contexto` — visão geral, escala NDVI, notas metodológicas
- `02 · Timeline` — eventos da safra com marcação temporal
- `03 · Dataset` — arquivos, schema das bandas, alertas de qualidade
- `04 · Talhões` — identificação dos talhões, comparativo de sistemas

> Novas abas de pesquisa são adicionadas conforme o projeto avança.

Para visualizar localmente, basta abrir o arquivo `diario_ndvi.html` no navegador — sem dependências ou servidor necessário.

---

## 🔬 Análises Planejadas

- [ ] Série temporal de NDVI por talhão (curva fenológica)
- [ ] Filtragem de imagens nubladas (`b1_valid_pixels = 0`)
- [ ] Comparativo Convencional vs. Agricultura 4.0
- [ ] Mapa de heterogeneidade espacial (`b1_std`)
- [ ] Detecção de eventos via quedas abruptas de NDVI
- [ ] Correlação NDVI × Timeline da safra
- [ ] Correlação NDVI × Mapas de produtividade (Yield)

---

## 🏛️ Parceiros e Fontes

| | |
|---|---|
| **Dados** | Jacto / FarmLab |
| **Plataforma** | One Soil |
| **Imagens** | Sentinel-2, ESA (European Space Agency) |
| **Instituição** | Projeto Acadêmico — Tratativa de NDVI |

---

## 📁 Estrutura do Repositório

```
📦 ndvi-farmlab/
├── 📄 diario_ndvi.html       # Diário de bordo interativo
├── 📄 README.md              # Este arquivo
├── 📂 ndvi/                  # GeoTIFFs (196 imagens)
│   └── ndvi_raw_{season_id}_{data}.tiff
├── 📂 images/                # Previews JPEG (196 imagens)
│   └── ndvi_raw_{season_id}_{data}.jpg
├── 📄 ndvi_metadata.csv      # Metadados raster (196 × 75)
└── 📄 ndvi_metadata.parquet  # Idem em formato Parquet
```

---

*Safra 2025–2026 · Sentinel-2 (ESA) · EPSG:31982 · Jacto / One Soil*
