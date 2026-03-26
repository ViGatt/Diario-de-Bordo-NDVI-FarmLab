"""
╔══════════════════════════════════════════════════════════════════╗
║        GAP-FILLING TEMPORAL — NDVI FarmLab / Safra 2025-2026    ║
║  Substitui imagens nubladas pela estimativa de NDVI via:         ║
║    Método 1 → Forward Fill (última imagem válida)                ║
║    Método 2 → Média das N imagens válidas anteriores             ║
║    Método 3 → Interpolação Linear (recomendado)                  ║
╚══════════════════════════════════════════════════════════════════╝

Dependências:  pip install pandas numpy matplotlib
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ─────────────────────────────────────────────
#  CONFIGURAÇÕES
# ─────────────────────────────────────────────
CSV_PATH    = "ndvi_metadata.csv"   # caminho do arquivo CSV
OUTPUT_DIR  = Path("output_gap_filling")
OUTPUT_DIR.mkdir(exist_ok=True)

N_MEDIA     = 3    # número de imagens anteriores para o Método 2
TALHOES = {
    "0bf86c8b": "Silagem Conv.",
    "258e47e0": "Grão 4.0",
    "b7292cb8": "Grão Conv.",
    "f791bf13": "Silagem 4.0",
}

# ─────────────────────────────────────────────
#  CARREGAMENTO
# ─────────────────────────────────────────────
def carregar_dados(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(
        df["filename"].str.extract(r"(\d{4}-\d{2}-\d{2})")[0]
    )
    df["season_short"] = df["season_id"].str[:8]
    df["talhao"] = df["season_short"].map(TALHOES)
    df = df.sort_values(["talhao", "date"]).reset_index(drop=True)
    return df


# ─────────────────────────────────────────────
#  MÉTODOS DE GAP-FILLING
# ─────────────────────────────────────────────
def metodo_forward_fill(serie: pd.Series) -> pd.Series:
    """
    Método 1 — Forward Fill
    Substitui cada valor ausente pelo último valor válido anterior.
    Simples, mas pode congelar o NDVI por longos períodos nublados.
    """
    return serie.ffill()


def metodo_media_n_anteriores(serie: pd.Series, n: int = 3) -> pd.Series:
    """
    Método 2 — Média das N imagens válidas anteriores
    Para cada gap, calcula a média das N observações válidas mais recentes.
    Suaviza variações abruptas. É o método sugerido pelo professor.
    """
    result = serie.copy()
    for i, idx in enumerate(serie.index):
        if pd.isna(serie[idx]):
            anteriores = serie.iloc[:i].dropna()
            if len(anteriores) >= 1:
                result[idx] = anteriores.tail(n).mean()
    return result


def metodo_interpolacao_linear(serie: pd.Series) -> pd.Series:
    """
    Método 3 — Interpolação Linear (recomendado para fenologia)
    Calcula o valor esperado entre o último ponto válido antes
    e o primeiro depois do gap. Captura a tendência de crescimento.
    Limitação: requer ao menos um ponto válido depois do gap.
    """
    return serie.interpolate(method="linear", limit_direction="forward")


# ─────────────────────────────────────────────
#  APLICAR GAP-FILLING A UM TALHÃO
# ─────────────────────────────────────────────
def aplicar_gap_filling(df: pd.DataFrame, talhao: str, n_media: int = 3) -> pd.DataFrame:
    """
    Retorna DataFrame com as três séries preenchidas para um talhão.
    """
    sub = df[df["talhao"] == talhao].sort_values("date").copy()

    # Marca imagens nubladas (sem pixels válidos)
    sub["nublada"] = sub["b1_valid_pixels"] == 0

    # Série original — NaN onde nublado
    sub["ndvi_original"] = np.where(sub["nublada"], np.nan, sub["b1_mean"])

    # Aplica os três métodos
    sub["ndvi_ffill"]  = metodo_forward_fill(sub["ndvi_original"])
    sub["ndvi_mean_n"] = metodo_media_n_anteriores(sub["ndvi_original"], n=n_media)
    sub["ndvi_interp"] = metodo_interpolacao_linear(sub["ndvi_original"])

    return sub.reset_index(drop=True)


# ─────────────────────────────────────────────
#  MÉTRICAS DE AVALIAÇÃO
# ─────────────────────────────────────────────
def calcular_metricas(resultado: pd.DataFrame) -> dict:
    """
    Compara os métodos nas posições onde temos valor real
    (simulação de validação cruzada: remove 20% dos pontos válidos
     e compara a estimativa com o valor real removido).
    """
    validas = resultado[~resultado["nublada"]].copy()

    # Separa 20% como "pseudo-gaps" para teste
    np.random.seed(42)
    mask = np.random.rand(len(validas)) < 0.2
    teste = validas[mask].copy()

    if len(teste) == 0:
        return {}

    metricas = {}
    for metodo, col in [
        ("Forward Fill", "ndvi_ffill"),
        (f"Média {N_MEDIA} ant.", "ndvi_mean_n"),
        ("Interpolação", "ndvi_interp"),
    ]:
        real = teste["ndvi_original"].values
        est  = teste[col].values
        mae  = np.mean(np.abs(real - est))
        rmse = np.sqrt(np.mean((real - est) ** 2))
        metricas[metodo] = {"MAE": round(mae, 4), "RMSE": round(rmse, 4)}

    return metricas


# ─────────────────────────────────────────────
#  VISUALIZAÇÃO
# ─────────────────────────────────────────────
def plotar_gap_filling(resultado: pd.DataFrame, talhao: str, metricas: dict):
    """
    Gera gráfico comparativo com os 3 métodos de gap-filling.
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    fig.suptitle(
        f"Gap-Filling Temporal — NDVI · {talhao}",
        fontsize=14, fontweight="bold", y=0.98
    )

    metodos = [
        ("ndvi_ffill",  "Método 1 — Forward Fill",          "#5ca8e0"),
        ("ndvi_mean_n", f"Método 2 — Média {N_MEDIA} anteriores", "#f5c842"),
        ("ndvi_interp", "Método 3 — Interpolação Linear",   "#3ddc84"),
    ]

    datas = resultado["date"]

    for ax, (col, titulo, cor) in zip(axes, metodos):
        # Região de fundo onde havia nuvem
        for _, row in resultado[resultado["nublada"]].iterrows():
            ax.axvspan(row["date"] - pd.Timedelta(days=1),
                       row["date"] + pd.Timedelta(days=1),
                       color="gray", alpha=0.15, lw=0)

        # Linha preenchida
        ax.plot(datas, resultado[col], color=cor, lw=1.8,
                linestyle="--", alpha=0.7, label="Gap preenchido")

        # Pontos originais válidos
        validos = resultado[~resultado["nublada"]]
        ax.scatter(validos["date"], validos["ndvi_original"],
                   color=cor, s=40, zorder=5, label="NDVI válido")

        # Pontos preenchidos
        nubladas = resultado[resultado["nublada"]]
        ax.scatter(nubladas["date"], resultado.loc[resultado["nublada"], col],
                   color="white", s=30, zorder=6, edgecolors=cor,
                   linewidths=1.5, label="Gap preenchido")

        mae  = metricas.get(titulo, {}).get("MAE",  "–")
        rmse = metricas.get(titulo, {}).get("RMSE", "–")
        info = f"  MAE={mae}  RMSE={rmse}" if mae != "–" else ""

        ax.set_title(f"{titulo}{info}", fontsize=10, loc="left", pad=6)
        ax.set_ylabel("NDVI", fontsize=9)
        ax.set_ylim(0, 1)
        ax.axhline(0.4, color="gray", lw=0.6, ls=":", alpha=0.5)
        ax.axhline(0.6, color="gray", lw=0.6, ls=":", alpha=0.5)
        ax.grid(axis="y", alpha=0.2)
        ax.legend(fontsize=8, loc="upper left")

        # Anotações de fase
        fases = [
            ("2025-10-01", "Plantio"),
            ("2025-11-15", "Estabelec."),
            ("2026-01-01", "Crescimento"),
            ("2026-02-01", "Pós-pico"),
        ]
        for data_fase, label in fases:
            d = pd.Timestamp(data_fase)
            if datas.min() <= d <= datas.max():
                ax.axvline(d, color="white", lw=0.8, ls=":", alpha=0.3)
                ax.text(d, 0.02, label, fontsize=7, color="gray",
                        rotation=90, va="bottom")

    axes[-1].set_xlabel("Data", fontsize=9)
    plt.xticks(rotation=45, ha="right", fontsize=8)

    # Legenda de fundo cinza
    patch = mpatches.Patch(color="gray", alpha=0.3, label="Imagem nublada (gap)")
    fig.legend(handles=[patch], loc="lower center", ncol=1, fontsize=9,
               bbox_to_anchor=(0.5, 0.01))

    plt.tight_layout(rect=[0, 0.04, 1, 0.97])
    output_path = OUTPUT_DIR / f"gap_filling_{talhao.replace(' ', '_').replace('.', '')}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="#0a0f0d", edgecolor="none")
    plt.close()
    print(f"  ✅ Gráfico salvo: {output_path}")


# ─────────────────────────────────────────────
#  EXPORTAR CSV COM SÉRIES PREENCHIDAS
# ─────────────────────────────────────────────
def exportar_csv(todos_resultados: list):
    """
    Salva um CSV consolidado com todas as séries preenchidas.
    """
    completo = pd.concat(todos_resultados, ignore_index=True)
    cols = [
        "talhao", "date", "nublada",
        "ndvi_original", "ndvi_ffill", "ndvi_mean_n", "ndvi_interp",
        "b1_std", "b1_valid_pixels", "b1_total_pixels"
    ]
    completo = completo[[c for c in cols if c in completo.columns]]
    out = OUTPUT_DIR / "ndvi_gap_filled.csv"
    completo.to_csv(out, index=False)
    print(f"\n  📄 CSV consolidado salvo: {out}")
    return completo


# ─────────────────────────────────────────────
#  RESUMO ESTATÍSTICO
# ─────────────────────────────────────────────
def imprimir_resumo(resultado: pd.DataFrame, talhao: str, metricas: dict):
    n_total   = len(resultado)
    n_nublada = resultado["nublada"].sum()
    n_valida  = n_total - n_nublada
    n_gaps_restantes = resultado["ndvi_interp"].isna().sum()

    print(f"\n{'─'*55}")
    print(f"  Talhão: {talhao}")
    print(f"  Total de datas:      {n_total}")
    print(f"  Imagens válidas:     {n_valida}  ({n_valida/n_total*100:.1f}%)")
    print(f"  Imagens nubladas:    {n_nublada} ({n_nublada/n_total*100:.1f}%)")
    print(f"  Gaps após interp.:   {n_gaps_restantes}  (só início sem histórico)")
    if metricas:
        print(f"\n  Métricas (cross-val 20%):")
        for metodo, vals in metricas.items():
            print(f"    {metodo:<22}  MAE={vals['MAE']:.4f}  RMSE={vals['RMSE']:.4f}")


# ─────────────────────────────────────────────
#  EXECUÇÃO PRINCIPAL
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  GAP-FILLING TEMPORAL — NDVI FarmLab")
    print("=" * 55)

    # Carrega dados
    df = carregar_dados(CSV_PATH)
    print(f"\n  Dataset carregado: {len(df)} registros · {df['talhao'].nunique()} talhões")

    todos_resultados = []

    for talhao in TALHOES.values():
        resultado = aplicar_gap_filling(df, talhao, n_media=N_MEDIA)
        metricas  = calcular_metricas(resultado)
        imprimir_resumo(resultado, talhao, metricas)
        plotar_gap_filling(resultado, talhao, metricas)
        todos_resultados.append(resultado)

    # Exporta CSV consolidado
    completo = exportar_csv(todos_resultados)

    # Resumo final
    print(f"\n{'='*55}")
    print("  RESUMO FINAL")
    print(f"{'='*55}")
    for talhao in TALHOES.values():
        t = completo[completo["talhao"] == talhao]
        nubladas = t["nublada"].sum()
        nan_restantes = t["ndvi_interp"].isna().sum()
        print(f"  {talhao:<20}  {nubladas} gaps → {nan_restantes} não preenchidos")

    print(f"\n  Arquivos salvos em: ./{OUTPUT_DIR}/")
    print("  ✅ Gap-filling concluído com sucesso!\n")


if __name__ == "__main__":
    main()
