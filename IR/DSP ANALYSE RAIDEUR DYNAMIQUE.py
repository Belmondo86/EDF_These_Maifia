# -*- coding: utf-8 -*-
"""
Tracé des prélèvements avec raideur dynamique (géophone bleu)
à partir du fichier ResultatFiltree.xlsx

- Si plusieurs noms dans une cellule (ex: "C35 C36" ou "C1 C2 bis"), ils sont séparés
- "bis" est ignoré
- Si Etat / PM / Emplaçement / Nom manque => ligne ignorée
- Si plusieurs échantillons ont même PM et même emplacement => décalage horizontal léger
- Colorbar horizontale sous la figure
"""
#test github
import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ==========================================================
# FICHIER EXCEL
# ==========================================================
file_path = r"C:\Users\maifia\Documents\expérimental\terrain\raideurdynamique_revin\ResultatFiltree.xlsx"
sheet_name = 0

# ==========================================================
# PARAMÈTRES D'AFFICHAGE
# ==========================================================
dx = 15
figsize = (30, 12)
marker_size = 70
fontsize_label = 8

col_value = "Kd_Bleu_MN/m"
required_cols = ["Etat", "PM", "Emplaçement", "Nom", col_value]

# ==========================================================
# VÉRIFICATIONS
# ==========================================================
if not os.path.exists(file_path):
    raise FileNotFoundError(f"Fichier introuvable : {file_path}")

df = pd.read_excel(file_path, sheet_name=sheet_name)

for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Colonne manquante dans le fichier Excel : {col}")

# ==========================================================
# NETTOYAGE DES DONNÉES
# ==========================================================
df = df.dropna(subset=["Etat", "PM", "Emplaçement", "Nom"]).copy()

df["Etat"] = df["Etat"].astype(str).str.strip()
df["Emplaçement"] = df["Emplaçement"].astype(str).str.strip()
df["Nom"] = df["Nom"].astype(str).str.strip()

df["PM"] = pd.to_numeric(df["PM"], errors="coerce")
df[col_value] = pd.to_numeric(df[col_value], errors="coerce")

df = df.dropna(subset=["PM", col_value]).copy()
df = df[df["Nom"].str.len() > 0].copy()

# ==========================================================
# FONCTION POUR SÉPARER LES NOMS
# ==========================================================
def split_names(name_str):
    s = str(name_str).strip().lower()
    s = s.replace("bis", "")
    tokens = re.findall(r"[a-zA-Z]+\d+", s)
    tokens = [t.upper() for t in tokens]
    if len(tokens) == 0:
        tokens = str(name_str).strip().split()
    return tokens

# ==========================================================
# EXPLOSION DES NOMS MULTIPLES
# ==========================================================
rows = []
for _, row in df.iterrows():
    names = split_names(row["Nom"])
    for nm in names:
        rows.append({
            "Etat": row["Etat"],
            "PM": row["PM"],
            "Emplaçement": row["Emplaçement"],
            "Nom": nm,
            "Raideur": row[col_value]
        })

df_plot = pd.DataFrame(rows)
df_plot = df_plot.dropna(subset=["Etat", "PM", "Emplaçement", "Nom", "Raideur"]).copy()
df_plot["Nom"] = df_plot["Nom"].astype(str).str.strip()
df_plot = df_plot[df_plot["Nom"] != ""].copy()

# ==========================================================
# ORDRE DES EMPLACEMENTS
# ==========================================================
order = [
    "Pied parement",
    "Marnage bas",
    "Marnage milieu",
    "Marnage haut",
    "Haut barrage"
]

df_plot = df_plot[df_plot["Emplaçement"].isin(order)].copy()

if df_plot.empty:
    raise ValueError("Aucune donnée valide après filtrage sur les emplacements.")

y_map = {name: i for i, name in enumerate(order)}
df_plot["y"] = df_plot["Emplaçement"].map(y_map)

df_plot = df_plot.sort_values(["Emplaçement", "PM", "Nom"]).reset_index(drop=True)

# ==========================================================
# DÉCALAGE HORIZONTAL SI PLUSIEURS POINTS AU MÊME PM / EMPLACEMENT
# ==========================================================
x_values = np.full(len(df_plot), np.nan)

for (pm, empl), grp in df_plot.groupby(["PM", "Emplaçement"], sort=False):
    idx = grp.index.to_list()
    n = len(idx)
    if n == 1:
        offsets = [0.0]
    else:
        offsets = np.linspace(-(n - 1) / 2, (n - 1) / 2, n) * dx
    for i, ind in enumerate(idx):
        x_values[ind] = pm + offsets[i]

df_plot["x"] = x_values

# ==========================================================
# PARAMÈTRES VISUELS
# ==========================================================
band_colors = {
    "Pied parement": "#E6E8A6",
    "Marnage bas": "#9A99E2",
    "Marnage milieu": "#C9D8DF",
    "Marnage haut": "#EBCF97",
    "Haut barrage": "#C8C8C8"
}

edgecolor_map = {
    "Saine": "green",
    "Dégradée": "red"
}

marker_map = {
    "Saine": "s",
    "Dégradée": "o"
}

# ==========================================================
# FIGURE
# ==========================================================
fig, ax = plt.subplots(figsize=figsize)

xmin = max(0, df_plot["PM"].min() - 150)
xmax = df_plot["PM"].max() + 150

# bandes horizontales
for i, zone in enumerate(order):
    ax.axhspan(i - 0.5, i + 0.5, facecolor=band_colors[zone], alpha=0.85, zorder=0)

vmin = df_plot["Raideur"].min()
vmax = df_plot["Raideur"].max()

sc_for_cbar = None

# nuages par état
for etat in ["Saine", "Dégradée"]:
    sub = df_plot[df_plot["Etat"] == etat]
    if len(sub) == 0:
        continue

    sc = ax.scatter(
        sub["x"],
        sub["y"],
        c=sub["Raideur"],
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        s=marker_size,
        marker=marker_map.get(etat, "o"),
        edgecolors=edgecolor_map.get(etat, "black"),
        linewidths=0.8,
        zorder=3
    )

    if sc_for_cbar is None:
        sc_for_cbar = sc

# labels des noms
for _, row in df_plot.iterrows():
    ax.text(
        row["x"],
        row["y"] + 0.08,
        row["Nom"],
        rotation=45,
        ha="center",
        va="bottom",
        fontsize=fontsize_label,
        color="black",
        zorder=4
    )

# lignes verticales aux PM
for pm in sorted(df_plot["PM"].dropna().unique()):
    ax.axvline(pm, color="k", linestyle="--", linewidth=0.7, alpha=0.35, zorder=1)

# axes
ax.set_xlim(xmin, xmax)
ax.set_ylim(-0.75, len(order) - 0.25)
ax.set_yticks(range(len(order)))
ax.set_yticklabels(order, fontsize=15)
ax.set_xlabel("Point métrique (PM)", fontsize=16)
ax.set_ylabel("Emplacement", fontsize=16)
ax.tick_params(axis="x", labelsize=15)
ax.tick_params(axis="y", labelsize=15)
ax.grid(False)

# légende état
legend_elements = [
    Line2D(
        [0], [0],
        marker="s",
        color="w",
        label="Saine",
        markerfacecolor="none",
        markeredgecolor="green",
        markersize=9,
        linewidth=0
    ),
    Line2D(
        [0], [0],
        marker="o",
        color="w",
        label="Dégradée",
        markerfacecolor="none",
        markeredgecolor="red",
        markersize=9,
        linewidth=0
    )
]

ax.legend(
    handles=legend_elements,
    title="État de la carotte",
    loc="upper right",
    frameon=True,
    fontsize=11,
    title_fontsize=12
)

# colorbar
plt.subplots_adjust(bottom=0.22)

if sc_for_cbar is None:
    raise ValueError("Impossible de créer la colorbar : aucun point n'a été tracé.")

cbar = fig.colorbar(
    sc_for_cbar,
    ax=ax,
    orientation="horizontal",
    fraction=0.08,
    pad=0.12
)
cbar.set_label("Raideur dynamique (MN/m)", fontsize=13)
cbar.ax.tick_params(labelsize=11)

plt.show()
#%%##
# ZOOM PM 3000 - 3500

pm_min = 3100
pm_max = 3500

df_zoom = df_plot[(df_plot["PM"] >= pm_min) & (df_plot["PM"] <= pm_max)].copy()

fig, ax = plt.subplots(figsize=(22, 6))

# Fond par zone
for i, zone in enumerate(order):
    ax.axhspan(i - 0.5, i + 0.5, facecolor=band_colors[zone], alpha=0.85, zorder=0)

vmin = df_plot["Raideur"].min()  # garder même échelle globale
vmax = df_plot["Raideur"].max()

sc_for_cbar = None

for etat in ["Saine", "Dégradée"]:
    sub = df_zoom[df_zoom["Etat"] == etat]
    if len(sub) == 0:
        continue

    sc = ax.scatter(
        sub["x"],
        sub["y"],
        c=sub["Raideur"],
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        s=80,
        marker=marker_map.get(etat, "o"),
        edgecolors=edgecolor_map.get(etat, "black"),
        linewidths=0.8,
        zorder=3
    )

    if sc_for_cbar is None:
        sc_for_cbar = sc

# Labels
for _, row in df_zoom.iterrows():
    ax.text(
        row["x"],
        row["y"] + 0.08,
        row["Nom"],
        rotation=45,
        ha="center",
        va="bottom",
        fontsize=9,
        zorder=4
    )

# Lignes PM
for pm in sorted(df_zoom["PM"].unique()):
    ax.axvline(pm, color="k", linestyle="--", linewidth=0.7, alpha=0.35)

ax.set_xlim(pm_min - 50, pm_max + 50)
ax.set_ylim(-0.75, len(order) - 0.25)
ax.set_yticks(range(len(order)))
ax.set_yticklabels(order, fontsize=14)

ax.set_xlabel("Point métrique (PM)", fontsize=15)
ax.set_ylabel("Emplacement", fontsize=15)

# Colorbar horizontale
plt.subplots_adjust(bottom=0.25)

cbar = fig.colorbar(
    sc_for_cbar,
    ax=ax,
    orientation="horizontal",
    fraction=0.08,
    pad=0.15
)
cbar.set_label("Raideur dynamique géophone bleu (MN/m)", fontsize=12)

plt.title("Zoom PM 3000 - 3500", fontsize=16)

plt.show()
#%%
# COMPARAISON Kd SAINE vs DÉGRADÉE (BOXPLOTS)

import matplotlib.pyplot as plt
import seaborn as sns

# Vérification des données disponibles
df_box = df_plot.copy()

# Garder uniquement Saine et Dégradée
df_box = df_box[df_box["Etat"].isin(["Saine", "Dégradée"])]

# Figure
plt.figure(figsize=(8, 6))

# Boxplot
sns.boxplot(
    data=df_box,
    x="Etat",
    y="Raideur",
    palette={"Saine": "lightgreen", "Dégradée": "lightcoral"}
)

# Ajout des points (optionnel mais très utile)
sns.stripplot(
    data=df_box,
    x="Etat",
    y="Raideur",
    color="black",
    alpha=0.5,
    jitter=True
)

# Labels
plt.ylabel("Raideur dynamique (MN/m)", fontsize=14)
plt.xlabel("État", fontsize=14)
plt.title("Comparaison de la raideur dynamique : Saine vs Dégradée", fontsize=15)

plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

#%%
# PROFIL TRANSVERSAL EN HISTOGRAMME (C13 → C18)

import matplotlib.pyplot as plt
import numpy as np

# Liste des échantillons du profil
profil_names = ["C27", "C28", "C29", "C30", "C31", "C32"]

# Filtrer
df_profil = df_plot[df_plot["Nom"].isin(profil_names)].copy()

# Mapping zones → ordre vertical
order_profil = {
    "Marnage haut": 0,
    "Marnage milieu": 1,
    "Pied parement": 2
}

df_profil = df_profil[df_profil["Emplaçement"].isin(order_profil.keys())].copy()
df_profil["ordre"] = df_profil["Emplaçement"].map(order_profil)

# Moyenne par zone (C13/C14, etc.)
df_mean = df_profil.groupby("ordre")["Raideur"].mean().reset_index()

# Labels zones
labels = ["Marnage haut", "Marnage milieu", "Pied parement"]

# Figure
plt.figure(figsize=(7, 5))

# Histogramme (barres)
plt.bar(
    df_mean["ordre"],
    df_mean["Raideur"],
    width=0.5
)

# Ajout valeurs
for i, row in df_mean.iterrows():
    plt.text(
        row["ordre"],
        row["Raideur"],
        f"{row['Raideur']:.1f}",
        ha='center',
        va='bottom',
        fontsize=10
    )

# Axes
plt.xticks([0, 1, 2], labels)
plt.ylabel("Raideur dynamique (MN/m)", fontsize=13)
plt.xlabel("Position dans le profil", fontsize=13)
plt.title("Évolution de la raideur dynamique (profil transversal)", fontsize=14)

plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

#%%
# HISTOGRAMME DES PLAQUES - AMPLITUDE DU PIC GEOPHONE BLEU

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

df_hist = df.copy()

# Nettoyage minimal pour éviter les erreurs sur les NaN
df_hist["Nom"] = df_hist["Nom"].fillna("").astype(str).str.strip()
df_hist["Etat"] = df_hist["Etat"].fillna("").astype(str).str.strip()
df_hist["Emplaçement"] = df_hist["Emplaçement"].fillna("").astype(str).str.strip()

# Garder uniquement les plaques (Nom commence par P)
df_hist = df_hist[df_hist["Nom"].str.startswith("P")].copy()

# Garder uniquement les états utiles
df_hist = df_hist[df_hist["Etat"].isin(["Saine", "Dégradée"])].copy()

# S'assurer que PM et A_pic_Bleu sont numériques
df_hist["PM"] = pd.to_numeric(df_hist["PM"], errors="coerce")
df_hist["A_pic_Bleu"] = pd.to_numeric(df_hist["A_pic_Bleu"], errors="coerce")

# Supprimer les lignes incomplètes
df_hist = df_hist.dropna(subset=["PM", "Emplaçement", "Nom", "A_pic_Bleu"]).copy()

# Ordre des emplacements
order_emplacement = {
    "Haut barrage": 0,
    "Marnage haut": 1,
    "Marnage milieu": 2,
    "Marnage bas": 3,
    "Pied parement": 4
}

df_hist["ordre_emplacement"] = df_hist["Emplaçement"].map(order_emplacement)

# Retirer les emplacements non reconnus
df_hist = df_hist.dropna(subset=["ordre_emplacement"]).copy()

# Tri
df_hist = df_hist.sort_values(["PM", "ordre_emplacement", "Nom"]).reset_index(drop=True)

# Couleurs
color_map = {
    "Saine": "green",
    "Dégradée": "red"
}
bar_colors = df_hist["Etat"].map(color_map)

# Positions X
x = np.arange(len(df_hist))

# Labels
x_labels = [
    f"{nom}\n{empl}"
    for nom, empl in zip(df_hist["Nom"], df_hist["Emplaçement"])
]

# Moyenne
mean_amp = df_hist["A_pic_Bleu"].mean()

# Figure
plt.figure(figsize=(18, 5))

plt.bar(
    x,
    df_hist["A_pic_Bleu"],
    color=bar_colors,
    edgecolor="black",
    linewidth=0.8
)

# Valeurs sur les barres
for xi, yi in zip(x, df_hist["A_pic_Bleu"]):
    plt.text(
        xi,
        yi,
        f"{yi:.2e}",
        ha="center",
        va="bottom",
        fontsize=12,
        rotation=90
    )

# Ligne horizontale de moyenne
plt.axhline(
    y=mean_amp,
    color="blue",
    linestyle="--",
    linewidth=2,
    label=f"Moyenne = {mean_amp:.2e}"
)

# Axes
plt.xticks(x, x_labels, rotation=90, fontsize=12)
plt.ylabel("Amplitude du pic géophone bleu", fontsize=14)
plt.xlabel("Plaques / Emplacement", fontsize=14)
plt.title("Amplitude du pic du géophone bleu des plaques", fontsize=16)

plt.grid(axis="y", linestyle="--", alpha=0.5)

# Légende
legend_elements = [
    Patch(facecolor="green", edgecolor="black", label="Saine"),
    Patch(facecolor="red", edgecolor="black", label="Dégradée")
]
plt.legend(handles=legend_elements, title="État")

plt.tight_layout()
plt.show()
# HISTOGRAMME DES PLAQUES UNIQUEMENT (P1, P2, ...) - Raideur Dynamique

import matplotlib.pyplot as plt
import numpy as np

df_hist = df_plot.copy()

# Garder uniquement les plaques (Nom commence par P)
df_hist = df_hist[df_hist["Nom"].str.startswith("P")].copy()

# Garder uniquement les états utiles
df_hist = df_hist[df_hist["Etat"].isin(["Saine", "Dégradée"])].copy()

# Ordre des emplacements
order_emplacement = {
    "Haut barrage": 0,
    "Marnage haut": 1,
    "Marnage milieu": 2,
    "Marnage bas": 3,
    "Pied parement": 4
}

df_hist["ordre_emplacement"] = df_hist["Emplaçement"].map(order_emplacement)

# Tri
df_hist = df_hist.sort_values(["PM", "ordre_emplacement", "Nom"]).reset_index(drop=True)

# Couleurs
color_map = {
    "Saine": "green",
    "Dégradée": "red"
}
bar_colors = df_hist["Etat"].map(color_map)

# Positions X
x = np.arange(len(df_hist))

# Labels
x_labels = [
    f"{nom}\n{empl}"
    for nom, empl in zip(df_hist["Nom"], df_hist["Emplaçement"])
]

# Figure
plt.figure(figsize=(18, 5))

plt.bar(
    x,
    df_hist["Raideur"],
    color=bar_colors,
    edgecolor="black",
    linewidth=0.8
)

# Valeurs
for xi, yi in zip(x, df_hist["Raideur"]):
    plt.text(
        xi,
        yi,
        f"{yi:.1f}",
        ha="center",
        va="bottom",
        fontsize=12,
        rotation=90
    )
# ===== AJOUT : ligne horizontale de moyenne =====
plt.axhline(
    y=mean_kd,
    color="blue",
    linestyle="--",
    linewidth=2,
    label=f"Moyenne = {mean_kd:.1f} MN/m")
# Axes
plt.xticks(x, x_labels, rotation=90, fontsize=12)

plt.ylabel("Raideur dynamique (MN/m)", fontsize=14)
plt.xlabel("Plaques / Emplacement", fontsize=14)
plt.title("Raideur dynamique des plaques", fontsize=16)


plt.grid(axis="y", linestyle="--", alpha=0.5)

# Légende
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="green", edgecolor="black", label="Saine"),
    Patch(facecolor="red", edgecolor="black", label="Dégradée")
]
plt.legend(handles=legend_elements, title="État")

plt.tight_layout()
plt.show()

#%% Boite à moustaches
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Chemin du fichier Excel
excel_path = r'C:\Users\maifia\Documents\Expérimental\Terrain\RaideurDynamique_Revin\ResultatFiltree.xlsx'

# Lecture
df = pd.read_excel(excel_path)

# Garder uniquement les états utiles et les valeurs valides
df_box = df[["Etat", "A_pic_Bleu"]].copy()
df_box = df_box.dropna(subset=["Etat", "A_pic_Bleu"])
df_box["Etat"] = df_box["Etat"].astype(str).str.strip()
df_box["A_pic_Bleu"] = 1/pd.to_numeric(df_box["A_pic_Bleu"], errors="coerce")
df_box = df_box.dropna(subset=["A_pic_Bleu"])
df_box = df_box[df_box["Etat"].isin(["Saine", "Dégradée"])]

# Figure
plt.figure(figsize=(8, 6))

# Boxplot
sns.boxplot(
    data=df_box,
    x="Etat",
    y="A_pic_Bleu",
    palette={"Saine": "lightgreen", "Dégradée": "lightcoral"}
)

# Points individuels
sns.stripplot(
    data=df_box,
    x="Etat",
    y="A_pic_Bleu",
    color="black",
    alpha=0.5,
    jitter=True
)

# Labels
plt.ylabel("Amplitude du pic géophone bleu", fontsize=14)
plt.xlabel("État", fontsize=14)
plt.title("Comparaison de l’amplitude du pic : Saine vs Dégradée", fontsize=15)

plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ==========================================================
# PARAMETRES COMMUNS
# ==========================================================
order_emplacement = {
    "Haut barrage": 0,
    "Marnage haut": 1,
    "Marnage milieu": 2,
    "Marnage bas": 3,
    "Pied parement": 4
}

color_map = {
    "Saine": "green",
    "Dégradée": "red"
}

legend_elements = [
    Patch(facecolor="green", edgecolor="black", label="Saine"),
    Patch(facecolor="red", edgecolor="black", label="Dégradée")
]

# ==========================================================
# FONCTION UNIQUE
# ==========================================================
def plot_hist(ax, df_hist, value_col, title, y_label, value_fmt):

    bar_colors = df_hist["Etat"].map(color_map)
    x = np.arange(len(df_hist))

    x_labels = [
        f"{nom}\n{empl}"
        for nom, empl in zip(df_hist["Nom"], df_hist["Emplaçement"])
    ]

    mean_val = df_hist[value_col].mean()

    ax.bar(
        x,
        df_hist[value_col],
        color=bar_colors,
        edgecolor="black",
        linewidth=0.8
    )

    ax.axhline(
        y=mean_val,
        color="blue",
        linestyle="--",
        linewidth=2
    )

    for xi, yi in zip(x, df_hist[value_col]):
        ax.text(
            xi,
            yi,
            format(yi, value_fmt),
            ha="center",
            va="bottom",
            fontsize=14,
            rotation=90
        )

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=90, fontsize=14)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

# ==========================================================
# PREPARATION DES DONNEES COMMUNES
# ==========================================================
df_hist = df.copy()

df_hist["Nom"] = df_hist["Nom"].fillna("").astype(str).str.strip()
df_hist["Etat"] = df_hist["Etat"].fillna("").astype(str).str.strip()
df_hist["Emplaçement"] = df_hist["Emplaçement"].fillna("").astype(str).str.strip()

df_hist = df_hist[df_hist["Etat"].isin(["Saine", "Dégradée"])].copy()

df_hist["PM"] = pd.to_numeric(df_hist["PM"], errors="coerce")
df_hist["Kd_Bleu_MN/m"] = pd.to_numeric(df_hist["Kd_Bleu_MN/m"], errors="coerce")
df_hist["A_pic_Bleu"] = pd.to_numeric(df_hist["A_pic_Bleu"], errors="coerce")
df_hist["Mobilite_moy_Bleu"] = pd.to_numeric(df_hist["Mobilite_moy_Bleu"], errors="coerce")

df_hist = df_hist.dropna(subset=[
    "PM", "Emplaçement", "Nom",
    "Kd_Bleu_MN/m", "A_pic_Bleu", "Mobilite_moy_Bleu"
]).copy()

df_hist["ordre_emplacement"] = df_hist["Emplaçement"].map(order_emplacement)
df_hist = df_hist.dropna(subset=["ordre_emplacement"]).copy()

df_hist = df_hist.sort_values(["PM", "ordre_emplacement", "Nom"]).reset_index(drop=True)

# Conversion en ×10⁶ pour amplitude et mobilité
df_hist["A_pic_Bleu"] *= 1e6
df_hist["Mobilite_moy_Bleu"] *= 1e6

# ==========================================================
# FIGURE AVEC 3 SUBPLOTS
# ==========================================================
fig, axs = plt.subplots(3, 1, figsize=(28, 15), sharex=True)

# 1) Kd
plot_hist(
    axs[0],
    df_hist,
    "Kd_Bleu_MN/m",
    "Raideur dynamique",
    "Kd (MN/m)",
    ".1f"
)

# 2) Amplitude
plot_hist(
    axs[1],
    df_hist,
    "A_pic_Bleu",
    "Amplitude du pic",
    "Amplitude (×10⁻⁶ m/s/N)",
    ".2f"
)

# 3) Mobilité
plot_hist(
    axs[2],
    df_hist,
    "Mobilite_moy_Bleu",
    "Mobilité moyenne",
    "Mobilité (×10⁻⁶ m/s/N)",
    ".2f"
)

fig.legend(
    handles=legend_elements,
    loc="upper right",
    title="État"
)

plt.tight_layout()
plt.show()
#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ==========================================================
# PARAMETRES COMMUNS
# ==========================================================
order_emplacement = {
    "Haut barrage": 0,
    "Marnage haut": 1,
    "Marnage milieu": 2,
    "Marnage bas": 3,
    "Pied parement": 4
}

color_map = {
    "Saine": "green",
    "Dégradée": "red"
}

legend_elements = [
    Patch(facecolor="green", edgecolor="black", label="Saine"),
    Patch(facecolor="red", edgecolor="black", label="Dégradée")
]

# ==========================================================
# FONCTION UNIQUE
# ==========================================================
def plot_hist(ax, df_hist, value_col, title, y_label, value_fmt):

    bar_colors = df_hist["Etat"].map(color_map)
    x = np.arange(len(df_hist))

    x_labels = [
        f"{nom}\n{empl}"
        for nom, empl in zip(df_hist["Nom"], df_hist["Emplaçement"])
    ]

    # 🔹 MEDIANE
    median_val = df_hist[value_col].median()

    ax.bar(
        x,
        df_hist[value_col],
        color=bar_colors,
        edgecolor="black",
        linewidth=0.8
    )

    # 🔹 LIGNE MEDIANE
    ax.axhline(
        y=median_val,
        color="blue",
        linestyle="--",
        linewidth=2,
        label=f"Médiane = {format(median_val, value_fmt)}"
    )

    # valeurs
    for xi, yi in zip(x, df_hist[value_col]):
        ax.text(
            xi,
            yi,
            format(yi, value_fmt),
            ha="center",
            va="bottom",
            fontsize=14,
            rotation=90
        )

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=90, fontsize=14)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

# ==========================================================
# PREPARATION DES DONNEES COMMUNES
# ==========================================================
df_hist = df.copy()

df_hist["Nom"] = df_hist["Nom"].fillna("").astype(str).str.strip()
df_hist["Etat"] = df_hist["Etat"].fillna("").astype(str).str.strip()
df_hist["Emplaçement"] = df_hist["Emplaçement"].fillna("").astype(str).str.strip()

df_hist = df_hist[df_hist["Etat"].isin(["Saine", "Dégradée"])].copy()

df_hist["PM"] = pd.to_numeric(df_hist["PM"], errors="coerce")
df_hist["Kd_Bleu_MN/m"] = pd.to_numeric(df_hist["Kd_Bleu_MN/m"], errors="coerce")
df_hist["A_pic_Bleu"] = pd.to_numeric(df_hist["A_pic_Bleu"], errors="coerce")
df_hist["Mobilite_moy_Bleu"] = pd.to_numeric(df_hist["Mobilite_moy_Bleu"], errors="coerce")

df_hist = df_hist.dropna(subset=[
    "PM", "Emplaçement", "Nom",
    "Kd_Bleu_MN/m", "A_pic_Bleu", "Mobilite_moy_Bleu"
]).copy()

df_hist["ordre_emplacement"] = df_hist["Emplaçement"].map(order_emplacement)
df_hist = df_hist.dropna(subset=["ordre_emplacement"]).copy()

df_hist = df_hist.sort_values(["PM", "ordre_emplacement", "Nom"]).reset_index(drop=True)

# Conversion en ×10⁶
df_hist["A_pic_Bleu"] *= 1e6
df_hist["Mobilite_moy_Bleu"] *= 1e6

# ==========================================================
# FIGURE
# ==========================================================
fig, axs = plt.subplots(3, 1, figsize=(28, 15), sharex=True)

# 1) Kd
plot_hist(
    axs[0],
    df_hist,
    "Kd_Bleu_MN/m",
    "Raideur dynamique",
    "Kd (MN/m)",
    ".1f"
)

# 2) Amplitude
plot_hist(
    axs[1],
    df_hist,
    "A_pic_Bleu",
    "Amplitude du pic",
    "Amplitude (×10⁻⁶ m/s/N)",
    ".2f"
)

# 3) Mobilité
plot_hist(
    axs[2],
    df_hist,
    "Mobilite_moy_Bleu",
    "Mobilité moyenne",
    "Mobilité (×10⁻⁶ m/s/N)",
    ".2f"
)

# Légende globale
fig.legend(
    handles=legend_elements,
    loc="upper right",
    title="État"
)

plt.tight_layout()
plt.show()
#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ==========================================================
# PARAMETRES COMMUNS
# ==========================================================
order_emplacement = {
    "Haut barrage": 0,
    "Marnage haut": 1,
    "Marnage milieu": 2,
    "Marnage bas": 3,
    "Pied parement": 4
}

color_map = {
    "Saine": "green",
    "Dégradée": "red"
}

legend_elements = [
    Patch(facecolor="green", edgecolor="black", label="Saine"),
    Patch(facecolor="red", edgecolor="black", label="Dégradée")
]

# ==========================================================
# FONCTION UNIQUE
# ==========================================================
def plot_hist(ax, df_hist, value_col, title, y_label, value_fmt):

    bar_colors = df_hist["Etat"].map(color_map)
    x = np.arange(len(df_hist))

    x_labels = [
        f"{nom}\n{empl}"
        for nom, empl in zip(df_hist["Nom"], df_hist["Emplaçement"])
    ]

    # Moyenne et médiane
    mean_val = df_hist[value_col].mean()
    median_val = df_hist[value_col].median()

    # Zone intermédiaire entre moyenne et médiane
    y_min = min(mean_val, median_val)
    y_max = max(mean_val, median_val)

    ax.axhspan(
        y_min,
        y_max,
        color="orange",
        alpha=0.25,
        zorder=0
    )

    # Barres
    ax.bar(
        x,
        df_hist[value_col],
        color=bar_colors,
        edgecolor="black",
        linewidth=0.8,
        zorder=2
    )

    # Ligne moyenne
    ax.axhline(
        y=mean_val,
        color="blue",
        linestyle="--",
        linewidth=2,
        zorder=3
    )

    # Ligne médiane
    ax.axhline(
        y=median_val,
        color="black",
        linestyle="-.",
        linewidth=2,
        zorder=3
    )

    # Valeurs sur les barres
    for xi, yi in zip(x, df_hist[value_col]):
        ax.text(
            xi,
            yi,
            format(yi, value_fmt),
            ha="center",
            va="bottom",
            fontsize=14,
            rotation=90,
            zorder=4
        )

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=90, fontsize=14)
    ax.set_ylabel(y_label, fontsize=14)
    ax.set_title(title, fontsize=16)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

# ==========================================================
# PREPARATION DES DONNEES COMMUNES
# ==========================================================
df_hist = df.copy()

df_hist["Nom"] = df_hist["Nom"].fillna("").astype(str).str.strip()
df_hist["Etat"] = df_hist["Etat"].fillna("").astype(str).str.strip()
df_hist["Emplaçement"] = df_hist["Emplaçement"].fillna("").astype(str).str.strip()

df_hist = df_hist[df_hist["Etat"].isin(["Saine", "Dégradée"])].copy()

df_hist["PM"] = pd.to_numeric(df_hist["PM"], errors="coerce")
df_hist["Kd_Bleu_MN/m"] = pd.to_numeric(df_hist["Kd_Bleu_MN/m"], errors="coerce")
df_hist["A_pic_Bleu"] = pd.to_numeric(df_hist["A_pic_Bleu"], errors="coerce")
df_hist["Mobilite_moy_Bleu"] = pd.to_numeric(df_hist["Mobilite_moy_Bleu"], errors="coerce")

df_hist = df_hist.dropna(subset=[
    "PM", "Emplaçement", "Nom",
    "Kd_Bleu_MN/m", "A_pic_Bleu", "Mobilite_moy_Bleu"
]).copy()

df_hist["ordre_emplacement"] = df_hist["Emplaçement"].map(order_emplacement)
df_hist = df_hist.dropna(subset=["ordre_emplacement"]).copy()

df_hist = df_hist.sort_values(["PM", "ordre_emplacement", "Nom"]).reset_index(drop=True)

# Conversion en ×10⁶ pour amplitude et mobilité
df_hist["A_pic_Bleu"] *= 1e6
df_hist["Mobilite_moy_Bleu"] *= 1e6

# ==========================================================
# FIGURE AVEC 3 SUBPLOTS
# ==========================================================
fig, axs = plt.subplots(3, 1, figsize=(28, 15), sharex=True)

# 1) Kd
plot_hist(
    axs[0],
    df_hist,
    "Kd_Bleu_MN/m",
    "Raideur dynamique",
    "Kd (MN/m)",
    ".1f"
)

# 2) Amplitude
plot_hist(
    axs[1],
    df_hist,
    "A_pic_Bleu",
    "Amplitude du pic",
    "Amplitude (×10⁻⁶ m/s/N)",
    ".2f"
)

# 3) Mobilité
plot_hist(
    axs[2],
    df_hist,
    "Mobilite_moy_Bleu",
    "Mobilité moyenne",
    "Mobilité (×10⁻⁶ m/s/N)",
    ".2f"
)

# ==========================================================
# LEGENDE GLOBALE
# ==========================================================
fig.legend(
    handles=legend_elements + [
        plt.Line2D([0], [0], color='blue', linestyle='--', label='Moyenne'),
        plt.Line2D([0], [0], color='black', linestyle='-.', label='Médiane'),
        plt.Line2D([0], [0], color='orange', linewidth=8, alpha=0.25, label='Zone intermédiaire')
    ],
    loc="upper right",
    title="État / Statistiques"
)

plt.tight_layout()
plt.show()
#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================================================
# PREPARATION DES DONNEES
# ==========================================================
df_box = df.copy()

# Nettoyage
df_box["Etat"] = df_box["Etat"].astype(str).str.strip()
df_box = df_box[df_box["Etat"].isin(["Saine", "Dégradée"])].copy()

# Colonnes numériques
df_box["Kd"] = pd.to_numeric(df_box["Kd_Bleu_MN/m"], errors="coerce")
df_box["A"] = pd.to_numeric(df_box["A_pic_Bleu"], errors="coerce") * 1e6
df_box["Mob"] = pd.to_numeric(df_box["Mobilite_moy_Bleu"], errors="coerce") * 1e6
df_box["f_pic"] = pd.to_numeric(df_box["f_pic_Bleu_Hz"], errors="coerce")

# Suppression valeurs invalides
df_box = df_box.dropna(subset=["Kd", "A", "Mob", "f_pic"])

# ==========================================================
# FIGURE
# ==========================================================
fig, axs = plt.subplots(1, 4, figsize=(24, 6))

# ===== Kd =====
sns.boxplot(
    data=df_box,
    x="Etat",
    y="Kd",
    palette={"Saine": "lightgreen", "Dégradée": "lightcoral"},
    showfliers=False,
    ax=axs[0]
)

sns.stripplot(
    data=df_box,
    x="Etat",
    y="Kd",
    color="black",
    alpha=0.6,
    jitter=True,
    ax=axs[0]
)

axs[0].set_title("Raideur dynamique")
axs[0].set_ylabel("Kd (MN/m)")
axs[0].set_xlabel("Etat")

# ===== Amplitude =====
sns.boxplot(
    data=df_box,
    x="Etat",
    y="A",
    palette={"Saine": "lightgreen", "Dégradée": "lightcoral"},
    showfliers=False,
    ax=axs[1]
)

sns.stripplot(
    data=df_box,
    x="Etat",
    y="A",
    color="black",
    alpha=0.6,
    jitter=True,
    ax=axs[1]
)

axs[1].set_title("Amplitude du pic")
axs[1].set_ylabel("Amplitude (×10⁻⁶ m/s/N)")
axs[1].set_xlabel("Etat")

# ===== Mobilité =====
sns.boxplot(
    data=df_box,
    x="Etat",
    y="Mob",
    palette={"Saine": "lightgreen", "Dégradée": "lightcoral"},
    showfliers=False,
    ax=axs[2]
)

sns.stripplot(
    data=df_box,
    x="Etat",
    y="Mob",
    color="black",
    alpha=0.6,
    jitter=True,
    ax=axs[2]
)

axs[2].set_title("Mobilité moyenne")
axs[2].set_ylabel("Mobilité (×10⁻⁶ m/s/N)")
axs[2].set_xlabel("Etat")

# ===== Fréquence =====
sns.boxplot(
    data=df_box,
    x="Etat",
    y="f_pic",
    palette={"Saine": "lightgreen", "Dégradée": "lightcoral"},
    showfliers=False,
    ax=axs[3]
)

sns.stripplot(
    data=df_box,
    x="Etat",
    y="f_pic",
    color="black",
    alpha=0.6,
    jitter=True,
    ax=axs[3]
)

axs[3].set_title("Fréquence du pic")
axs[3].set_ylabel("Fréquence (Hz)")
axs[3].set_xlabel("Etat")

# ==========================================================
# STYLE GLOBAL
# ==========================================================
for ax in axs:
    ax.grid(axis="y", linestyle="--", alpha=0.5)

plt.tight_layout()
plt.show()
#%%
import numpy as np
import pandas as pd

# ==========================================================
# 1) LECTURE / PREPARATION
# ==========================================================
df_score = df.copy()

df_score["Etat"] = df_score["Etat"].astype(str).str.strip()

# garder uniquement les états utiles
df_score = df_score[df_score["Etat"].isin(["Saine", "Dégradée"])].copy()

# colonnes numériques
df_score["Kd"] = pd.to_numeric(df_score["Kd_Bleu_MN/m"], errors="coerce")
df_score["A"] = pd.to_numeric(df_score["A_pic_Bleu"], errors="coerce")
df_score["Mob"] = pd.to_numeric(df_score["Mobilite_moy_Bleu"], errors="coerce")

# garder lignes valides
df_score = df_score.dropna(subset=["Kd", "A", "Mob"]).copy()

# sécurité amplitude > 0
df_score = df_score[df_score["A"] > 0].copy()

# ==========================================================
# 2) NORMALISATION
# ==========================================================
# ici on garde A directement :
# - A élevé = dégradé
# - Mob élevé = dégradé
# - Kd élevé = sain => on inversera le signe plus tard

mu_Kd = df_score["Kd"].mean()
mu_A   = df_score["A"].mean()
mu_Mob = df_score["Mob"].mean()

std_Kd = df_score["Kd"].std()
std_A   = df_score["A"].std()
std_Mob = df_score["Mob"].std()

df_score["Z_Kd"]  = (df_score["Kd"]  - mu_Kd)  / std_Kd
df_score["Z_A"]   = (df_score["A"]   - mu_A)   / std_A
df_score["Z_Mob"] = (df_score["Mob"] - mu_Mob) / std_Mob

# orientation "dégradation"
# grand = plus dégradé
df_score["Z_Kd_deg"]  = -df_score["Z_Kd"]
df_score["Z_A_deg"]   =  df_score["Z_A"]
df_score["Z_Mob_deg"] =  df_score["Z_Mob"]

# ==========================================================
# 3) SCORE AVEC POIDS EGAUX
# ==========================================================
w_eq = 1/3

df_score["Score_egal"] = (
    w_eq * df_score["Z_Kd_deg"] +
    w_eq * df_score["Z_A_deg"] +
    w_eq * df_score["Z_Mob_deg"]
)

# ==========================================================
# 4) POIDS SELON LA DIFFERENCIATION
# ==========================================================
mask_sain = df_score["Etat"] == "Saine"
mask_deg  = df_score["Etat"] == "Dégradée"

def discrimination_score(series, mask_sain, mask_deg):
    """
    Score simple de différenciation :
    |moyenne_saine - moyenne_degradee| / ecart-type global
    """
    x_sain = series[mask_sain]
    x_deg  = series[mask_deg]
    sigma = series.std()

    if sigma == 0 or np.isnan(sigma):
        return 0.0

    return abs(x_sain.mean() - x_deg.mean()) / sigma

# on évalue la différenciation sur les indicateurs orientés "dégradation"
D_Kd  = discrimination_score(df_score["Z_Kd_deg"],  mask_sain, mask_deg)
D_A   = discrimination_score(df_score["Z_A_deg"],   mask_sain, mask_deg)
D_Mob = discrimination_score(df_score["Z_Mob_deg"], mask_sain, mask_deg)

D_sum = D_Kd + D_A + D_Mob

if D_sum == 0:
    w_Kd = w_A = w_Mob = 1/3
else:
    w_Kd  = D_Kd  / D_sum
    w_A   = D_A   / D_sum
    w_Mob = D_Mob / D_sum

# score pondéré par différenciation
df_score["Score_pondere"] = (
    w_Kd  * df_score["Z_Kd_deg"] +
    w_A   * df_score["Z_A_deg"] +
    w_Mob * df_score["Z_Mob_deg"]
)

# ==========================================================
# 5) SEUILS SIMPLES DE DECISION
# ==========================================================
# avec z-score, seuil 0 est un bon point de départ
seuil_egal = 0
seuil_pond = 0

df_score["Decision_egal"] = np.where(
    df_score["Score_egal"] > seuil_egal,
    "Dégradée",
    "Saine"
)

df_score["Decision_pondere"] = np.where(
    df_score["Score_pondere"] > seuil_pond,
    "Dégradée",
    "Saine"
)

# ==========================================================
# 6) AFFICHAGES
# ==========================================================
print("="*70)
print("STATISTIQUES DE NORMALISATION")
print(f"mu_Kd  = {mu_Kd:.4f}   | std_Kd  = {std_Kd:.4f}")
print(f"mu_A   = {mu_A:.6e} | std_A   = {std_A:.6e}")
print(f"mu_Mob = {mu_Mob:.6e} | std_Mob = {std_Mob:.6e}")

print("\n" + "="*70)
print("POIDS EGAUX")
print(f"w_Kd = {w_eq:.3f} | w_A = {w_eq:.3f} | w_Mob = {w_eq:.3f}")

print("\n" + "="*70)
print("DIFFERENCIATION")
print(f"D_Kd  = {D_Kd:.3f}")
print(f"D_A   = {D_A:.3f}")
print(f"D_Mob = {D_Mob:.3f}")

print("\n" + "="*70)
print("POIDS SELON DIFFERENCIATION")
print(f"w_Kd  = {w_Kd:.3f}")
print(f"w_A   = {w_A:.3f}")
print(f"w_Mob = {w_Mob:.3f}")

print("\n" + "="*70)
print("MATRICE DE COMPARAISON - SCORE EGAL")
print(pd.crosstab(df_score["Etat"], df_score["Decision_egal"]))

print("\n" + "="*70)
print("MATRICE DE COMPARAISON - SCORE PONDERE")
print(pd.crosstab(df_score["Etat"], df_score["Decision_pondere"]))

# ==========================================================
# 7) TABLEAU FINAL
# ==========================================================
cols_out = [
    "Nom", "Etat", "PM", "Emplaçement",
    "Kd", "A", "Mob",
    "Z_Kd_deg", "Z_A_deg", "Z_Mob_deg",
    "Score_egal", "Decision_egal",
    "Score_pondere", "Decision_pondere"
]

# garder seulement les colonnes présentes
cols_out = [c for c in cols_out if c in df_score.columns]

df_resultat_score = df_score[cols_out].copy()

print("\n" + "="*70)
print("APERÇU RESULTATS")
print(df_resultat_score.head())

# export optionnel
excel_out = r"C:\Users\maifia\Documents\expérimental\terrain\raideurdynamique_revin\ResultatScore.xlsx"
df_resultat_score.to_excel(excel_out, index=False)
print("\nFichier exporté :", excel_out)
# ==========================================================
# CALCUL TAUX DE REUSSITE
# ==========================================================

# Fonction pour encoder les états
def encode_etat(series):
    return series.map({
        "Saine": 0,
        "Dégradée": 1
    })

# Encodage
y_true = encode_etat(df_score["Etat"])
y_pred_egal = encode_etat(df_score["Decision_egal"])
y_pred_pond = encode_etat(df_score["Decision_pondere"])

# Suppression valeurs NaN si jamais
mask_valid = y_true.notna() & y_pred_egal.notna() & y_pred_pond.notna()

y_true = y_true[mask_valid]
y_pred_egal = y_pred_egal[mask_valid]
y_pred_pond = y_pred_pond[mask_valid]

# Accuracy
acc_egal = (y_true == y_pred_egal).mean()
acc_pond = (y_true == y_pred_pond).mean()

print("\n" + "="*70)
print("TAUX DE REUSSITE")
print(f"Poids égaux      : {acc_egal*100:.2f} %")
print(f"Poids pondérés   : {acc_pond*100:.2f} %")
# ==========================================================
# MATRICE DE CONFUSION
# ==========================================================
from sklearn.metrics import confusion_matrix

print("\nMatrice - poids égaux")
print(confusion_matrix(y_true, y_pred_egal))

print("\nMatrice - poids pondérés")
print(confusion_matrix(y_true, y_pred_pond))
# ==========================================================
#%% Classification en 5 niveaux c'est moi qui définit les classe + scatter coloré + export Excel
#   Colonne 1 export = Site
#   Légende = seuils T1, T2, T3, T4 avec leurs valeurs

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# ==========================================================
# 1) LECTURE / PREPARATION
# ==========================================================
df_score = df.copy()

df_score["Etat"] = df_score["Etat"].astype(str).str.strip()

# garder uniquement les états utiles
df_score = df_score[df_score["Etat"].isin(["Saine", "Dégradée"])].copy()

# colonnes numériques
df_score["Kd"] = pd.to_numeric(df_score["Kd_Bleu_MN/m"], errors="coerce")
df_score["A"] = pd.to_numeric(df_score["A_pic_Bleu"], errors="coerce")
df_score["Mob"] = pd.to_numeric(df_score["Mobilite_moy_Bleu"], errors="coerce")

# garder lignes valides
df_score = df_score.dropna(subset=["Kd", "A", "Mob"]).copy()

# sécurité amplitude > 0
df_score = df_score[df_score["A"] > 0].copy()

# ==========================================================
# 2) NORMALISATION
# ==========================================================
mu_Kd  = df_score["Kd"].mean()
mu_A   = df_score["A"].mean()
mu_Mob = df_score["Mob"].mean()

std_Kd  = df_score["Kd"].std()
std_A   = df_score["A"].std()
std_Mob = df_score["Mob"].std()

df_score["Z_Kd"]  = (df_score["Kd"]  - mu_Kd)  / std_Kd
df_score["Z_A"]   = (df_score["A"]   - mu_A)   / std_A
df_score["Z_Mob"] = (df_score["Mob"] - mu_Mob) / std_Mob

# orientation "dégradation" : grand = plus dégradé
df_score["Z_Kd_deg"]  = -df_score["Z_Kd"]
df_score["Z_A_deg"]   =  df_score["Z_A"]
df_score["Z_Mob_deg"] =  df_score["Z_Mob"]

# ==========================================================
# 3) POIDS SELON LA DIFFERENCIATION
# ==========================================================
mask_sain = df_score["Etat"] == "Saine"
mask_deg  = df_score["Etat"] == "Dégradée"

def discrimination_score(series, mask_sain, mask_deg):
    x_sain = series[mask_sain]
    x_deg  = series[mask_deg]
    sigma = series.std()

    if sigma == 0 or np.isnan(sigma):
        return 0.0

    return abs(x_sain.mean() - x_deg.mean()) / sigma

D_Kd  = discrimination_score(df_score["Z_Kd_deg"],  mask_sain, mask_deg)
D_A   = discrimination_score(df_score["Z_A_deg"],   mask_sain, mask_deg)
D_Mob = discrimination_score(df_score["Z_Mob_deg"], mask_sain, mask_deg)

D_sum = D_Kd + D_A + D_Mob

if D_sum == 0:
    w_Kd = w_A = w_Mob = 1/3
else:
    w_Kd  = D_Kd  / D_sum
    w_A   = D_A   / D_sum
    w_Mob = D_Mob / D_sum

print("\n" + "="*70)
print("POIDS SELON DIFFERENCIATION")
print(f"w_Kd  = {w_Kd:.4f}")
print(f"w_A   = {w_A:.4f}")
print(f"w_Mob = {w_Mob:.4f}")

# ==========================================================
# 4) SCORE PONDERE
# ==========================================================
df_score["Score_pondere"] = (
    w_Kd  * df_score["Z_Kd_deg"] +
    w_A   * df_score["Z_A_deg"] +
    w_Mob * df_score["Z_Mob_deg"]
)

# ==========================================================
# 5) CALCUL DES SEUILS POUR 5 CLASSES
# ==========================================================
scores_sains = df_score.loc[mask_sain, "Score_pondere"]
scores_degrades = df_score.loc[mask_deg, "Score_pondere"]

mu_sain  = scores_sains.mean()
std_sain = scores_sains.std()

mu_deg   = scores_degrades.mean()
std_deg  = scores_degrades.std()

T1 = mu_sain - 0.5 * std_sain
T2 = mu_sain + 0.5 * std_sain
T3 = mu_deg  - 0.5 * std_deg
T4 = mu_deg  + 0.5 * std_deg

print("\n" + "="*70)
print("STATISTIQUES DES SCORES")
print(f"Saine     : mu = {mu_sain:.4f} | std = {std_sain:.4f}")
print(f"Dégradée  : mu = {mu_deg:.4f} | std = {std_deg:.4f}")

print("\n" + "="*70)
print("SEUILS")
print(f"T1 = {T1:.4f}")
print(f"T2 = {T2:.4f}")
print(f"T3 = {T3:.4f}")
print(f"T4 = {T4:.4f}")

# ==========================================================
# 6) CREATION DES 5 CLASSES
# ==========================================================
def class_5(score):
    if score < T1:
        return "Très saine"
    elif score < T2:
        return "Peu altérée"
    elif score < T3:
        return "Intermédiaire"
    elif score < T4:
        return "Dégradée"
    else:
        return "Très dégradée"

df_score["Classe"] = df_score["Score_pondere"].apply(class_5)

# ==========================================================
# 7) POSITION X DES CLASSES
# ==========================================================
ordre_classes = [
    "Très saine",
    "Peu altérée",
    "Intermédiaire",
    "Dégradée",
    "Très dégradée"
]

x_map = {cat: i for i, cat in enumerate(ordre_classes)}
df_score["x_pos"] = df_score["Classe"].map(x_map)

# ==========================================================
# 8) COULEURS DEGRADEES : VERT -> ROUGE
# ==========================================================
cmap = LinearSegmentedColormap.from_list(
    "vert_rouge",
    ["green", "yellowgreen", "yellow", "darkorange", "red"]
)

color_values = df_score["x_pos"] / (len(ordre_classes) - 1)
point_colors = cmap(color_values)

# ==========================================================
# 9) TRACE
# ==========================================================
plt.figure(figsize=(11, 7))

plt.scatter(
    df_score["x_pos"],
    df_score["Score_pondere"],
    c=point_colors,
    s=70,
    alpha=0.85
)

# seuils avec valeurs dans la légende
plt.axhline(T1, linestyle="--", linewidth=1.8, label=f"T1 = {T1:.3f}")
plt.axhline(T2, linestyle="--", linewidth=1.8, label=f"T2 = {T2:.3f}")
plt.axhline(T3, linestyle="--", linewidth=1.8, label=f"T3 = {T3:.3f}")
plt.axhline(T4, linestyle="--", linewidth=1.8, label=f"T4 = {T4:.3f}")

plt.xticks(range(len(ordre_classes)), ordre_classes, rotation=20, fontsize=16)
plt.yticks(fontsize=14)
plt.xlabel("Classes de dégradation", fontsize=18)
plt.ylabel("Score pondéré", fontsize=18)
plt.title("Classification des scores en 5 niveaux", fontsize=20)

plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(fontsize=12)
plt.tight_layout()
plt.show()

# ==========================================================
# 10) TABLEAU RESULTAT POUR EXPORT EXCEL
#     colonne 1 : Site
#     colonne 2 : Etat
#     colonne 3 : Score
#     colonne 4 : Classe
# ==========================================================
if "Site" in df_score.columns:
    col_site = "Site"
elif "Nom" in df_score.columns:
    col_site = "Nom"
else:
    df_score["Site_export"] = np.arange(len(df_score)) + 1
    col_site = "Site_export"

df_export = pd.DataFrame({
    "Site": df_score[col_site],
    "Etat": df_score["Etat"],
    "Score": df_score["Score_pondere"],
    "Classe": df_score["Classe"]
})

print("\n" + "="*70)
print("APERÇU EXPORT")
print(df_export.head())

# ==========================================================
# 11) EXPORT EXCEL
# ==========================================================
excel_out = r"C:\Users\maifia\Documents\expérimental\terrain\raideurdynamique_revin\Classification_5_classes.xlsx"
df_export.to_excel(excel_out, index=False)

print("\nFichier exporté :", excel_out)
#%% TABLEAU COLORE DES SITES SELON LA CLASSE

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# ==========================================================
# 1) CHOIX DE LA COLONNE NOM DE SITE
# ==========================================================
if "Nom" in df_score.columns:
    col_site = "Nom"
elif "Site" in df_score.columns:
    col_site = "Site"
else:
    raise ValueError("Aucune colonne 'Nom' ou 'Site' trouvée dans df_score.")

# garder seulement les colonnes utiles
df_visu = df_score[[col_site, "Etat", "Score_pondere", "Classe"]].copy()
df_visu = df_visu.rename(columns={col_site: "Site"})

# si un même nom apparaît plusieurs fois, on garde la première ligne
# tu peux remplacer par moyenne si besoin
df_visu = df_visu.drop_duplicates(subset="Site").copy()

# trier selon le score pour une meilleure lecture
df_visu = df_visu.sort_values("Score_pondere").reset_index(drop=True)

# ==========================================================
# 2) ENCODAGE DES CLASSES
# ==========================================================
ordre_classes = [
    "Très saine",
    "Peu altérée",
    "Intermédiaire",
    "Dégradée",
    "Très dégradée"
]

class_to_num = {c: i for i, c in enumerate(ordre_classes)}
df_visu["Classe_num"] = df_visu["Classe"].map(class_to_num)

# matrice 1 x N pour affichage en tableau coloré
mat = np.array([df_visu["Classe_num"].values])

# ==========================================================
# 3) COULEURS
# ==========================================================
cmap = ListedColormap([
    "green",        # Très saine
    "yellowgreen",  # Peu altérée
    "yellow",       # Intermédiaire
    "darkorange",   # Dégradée
    "red"           # Très dégradée
])

# ==========================================================
# 4) TRACE
# ==========================================================
fig, ax = plt.subplots(figsize=(max(12, len(df_visu)*0.45), 2.8))

im = ax.imshow(mat, aspect="auto", cmap=cmap, vmin=-0.5, vmax=4.5)

# noms des sites sur x
ax.set_xticks(np.arange(len(df_visu)))
ax.set_xticklabels(df_visu["Site"], rotation=90, fontsize=11)

# une seule ligne en y
ax.set_yticks([0])
ax.set_yticklabels(["Classe"], fontsize=12)

#ax.set_title("Classification finale par site", fontsize=16)
ax.set_xlabel("Site", fontsize=13)

# ajouter une grille visuelle
ax.set_xticks(np.arange(-0.5, len(df_visu), 1), minor=True)
ax.set_yticks(np.arange(-0.5, 1.5, 1), minor=True)
ax.grid(which="minor", color="black", linestyle="-", linewidth=0.8)
ax.tick_params(which="minor", bottom=False, left=False)

# ==========================================================
# 5) LEGENDE
# ==========================================================
from matplotlib.patches import Patch

legend_elements = [
    Patch(facecolor="green", label="Très saine"),
    Patch(facecolor="yellowgreen", label="Peu altérée"),
    Patch(facecolor="yellow", label="Intermédiaire"),
    Patch(facecolor="darkorange", label="Dégradée"),
    Patch(facecolor="red", label="Très dégradée"),
]

ax.legend(
    handles=legend_elements,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.35),
    ncol=5,
    fontsize=11,
    frameon=True
)

plt.tight_layout()
plt.show()

# ==========================================================
# 6) EXPORT EXCEL DU TABLEAU FINAL
# ==========================================================
excel_out = r"C:\Users\maifia\Documents\expérimental\terrain\raideurdynamique_revin\Tableau_colore_sites.xlsx"

df_export = df_visu[["Site", "Etat", "Score_pondere", "Classe"]].copy()
df_export.columns = ["Site", "Etat", "Score", "Classe"]

df_export.to_excel(excel_out, index=False)
print("Fichier exporté :", excel_out)

#%% Classification en 5 niveaux par K-means + scatter coloré + export Excel
#   Colonne 1 export = Site
#   Légende = centres des clusters + frontières

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from sklearn.cluster import KMeans

# ==========================================================
# 1) LECTURE / PREPARATION
# ==========================================================
df_score = df.copy()

df_score["Etat"] = df_score["Etat"].astype(str).str.strip()

# garder uniquement les états utiles
df_score = df_score[df_score["Etat"].isin(["Saine", "Dégradée"])].copy()

# colonnes numériques
df_score["Kd"] = pd.to_numeric(df_score["Kd_Bleu_MN/m"], errors="coerce")
df_score["A"] = pd.to_numeric(df_score["A_pic_Bleu"], errors="coerce")
df_score["Mob"] = pd.to_numeric(df_score["Mobilite_moy_Bleu"], errors="coerce")

# garder lignes valides
df_score = df_score.dropna(subset=["Kd", "A", "Mob"]).copy()

# sécurité amplitude > 0
df_score = df_score[df_score["A"] > 0].copy()

# ==========================================================
# 2) NORMALISATION
# ==========================================================
mu_Kd  = df_score["Kd"].mean()
mu_A   = df_score["A"].mean()
mu_Mob = df_score["Mob"].mean()

std_Kd  = df_score["Kd"].std()
std_A   = df_score["A"].std()
std_Mob = df_score["Mob"].std()

df_score["Z_Kd"]  = (df_score["Kd"]  - mu_Kd)  / std_Kd
df_score["Z_A"]   = (df_score["A"]   - mu_A)   / std_A
df_score["Z_Mob"] = (df_score["Mob"] - mu_Mob) / std_Mob

# orientation "dégradation" : grand = plus dégradé
df_score["Z_Kd_deg"]  = -df_score["Z_Kd"]
df_score["Z_A_deg"]   =  df_score["Z_A"]
df_score["Z_Mob_deg"] =  df_score["Z_Mob"]

# ==========================================================
# 3) POIDS SELON LA DIFFERENCIATION
# ==========================================================
mask_sain = df_score["Etat"] == "Saine"
mask_deg  = df_score["Etat"] == "Dégradée"

def discrimination_score(series, mask_sain, mask_deg):
    x_sain = series[mask_sain]
    x_deg  = series[mask_deg]
    sigma = series.std()

    if sigma == 0 or np.isnan(sigma):
        return 0.0

    return abs(x_sain.mean() - x_deg.mean()) / sigma

D_Kd  = discrimination_score(df_score["Z_Kd_deg"],  mask_sain, mask_deg)
D_A   = discrimination_score(df_score["Z_A_deg"],   mask_sain, mask_deg)
D_Mob = discrimination_score(df_score["Z_Mob_deg"], mask_sain, mask_deg)

D_sum = D_Kd + D_A + D_Mob

if D_sum == 0:
    w_Kd = w_A = w_Mob = 1/3
else:
    w_Kd  = D_Kd  / D_sum
    w_A   = D_A   / D_sum
    w_Mob = D_Mob / D_sum

print("\n" + "="*70)
print("POIDS SELON DIFFERENCIATION")
print(f"w_Kd  = {w_Kd:.4f}")
print(f"w_A   = {w_A:.4f}")
print(f"w_Mob = {w_Mob:.4f}")

# ==========================================================
# 4) SCORE PONDERE
# ==========================================================
df_score["Score_pondere"] = (
    w_Kd  * df_score["Z_Kd_deg"] +
    w_A   * df_score["Z_A_deg"] +
    w_Mob * df_score["Z_Mob_deg"]
)

# ==========================================================
# 5) K-MEANS CLUSTERING SUR LE SCORE
# ==========================================================
X = df_score["Score_pondere"].values.reshape(-1, 1)

kmeans = KMeans(n_clusters=5, random_state=0, n_init=10)
df_score["Cluster_brut"] = kmeans.fit_predict(X)

centres = kmeans.cluster_centers_.flatten()

print("\n" + "="*70)
print("CENTRES DES CLUSTERS (BRUTS)")
for i, c in enumerate(centres):
    print(f"Cluster {i} : {c:.4f}")

# ==========================================================
# 6) TRI DES CLUSTERS DU PLUS SAIN AU PLUS DEGRADE
# ==========================================================
ordre_centres = np.argsort(centres)
mapping_clusters = {old: new for new, old in enumerate(ordre_centres)}

df_score["Cluster_ord"] = df_score["Cluster_brut"].map(mapping_clusters)

centres_ordonnes = np.sort(centres)

print("\n" + "="*70)
print("CENTRES DES CLUSTERS (ORDONNES)")
for i, c in enumerate(centres_ordonnes):
    print(f"C{i+1} = {c:.4f}")

# ==========================================================
# 7) CALCUL DES FRONTIERES
# ==========================================================
frontieres = [
    (centres_ordonnes[i] + centres_ordonnes[i+1]) / 2
    for i in range(len(centres_ordonnes) - 1)
]

print("\n" + "="*70)
print("FRONTIERES ENTRE CLUSTERS")
for i, s in enumerate(frontieres):
    print(f"S{i+1} = {s:.4f}")

# ==========================================================
# 8) CREATION DES 5 CLASSES
# ==========================================================
ordre_classes = [
    "Très saine",
    "Peu altérée",
    "Intermédiaire",
    "Dégradée",
    "Très dégradée"
]

cluster_to_class = {i: classe for i, classe in enumerate(ordre_classes)}
df_score["Classe_KMeans"] = df_score["Cluster_ord"].map(cluster_to_class)

# position x
x_map = {cat: i for i, cat in enumerate(ordre_classes)}
df_score["x_pos"] = df_score["Classe_KMeans"].map(x_map)

# ==========================================================
# 9) COULEURS DEGRADEES : VERT -> ROUGE
# ==========================================================
cmap = LinearSegmentedColormap.from_list(
    "vert_rouge",
    ["green", "yellowgreen", "yellow", "darkorange", "red"]
)

color_values = df_score["x_pos"] / (len(ordre_classes) - 1)
point_colors = cmap(color_values)

# ==========================================================
# 10) TRACE
# ==========================================================
plt.figure(figsize=(11, 7))

plt.scatter(
    df_score["x_pos"],
    df_score["Score_pondere"],
    c=point_colors,
    s=70,
    alpha=0.85
)

# lignes horizontales aux centres ordonnés
for i, c in enumerate(centres_ordonnes):
    plt.axhline(
        c,
        linestyle=":",
        linewidth=1.8,
        label=f"Centre C{i+1} = {c:.3f}"
    )

# lignes horizontales aux frontières
for i, s in enumerate(frontieres):
    plt.axhline(
        s,
        linestyle="--",
        linewidth=2.0,
        label=f"Frontière S{i+1} = {s:.3f}"
    )

plt.xticks(range(len(ordre_classes)), ordre_classes, rotation=20, fontsize=16)
plt.yticks(fontsize=14)
plt.xlabel("Classes de dégradation (K-means)", fontsize=18)
plt.ylabel("Score pondéré", fontsize=18)
plt.title("Classification des scores en 5 niveaux par K-means", fontsize=20)

plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(fontsize=11, loc="best")
plt.tight_layout()
plt.show()

# ==========================================================
# 11) TABLEAU RESULTAT POUR EXPORT EXCEL
#     colonne 1 : Site
#     colonne 2 : Etat
#     colonne 3 : Score
#     colonne 4 : Classe_KMeans
# ==========================================================
if "Site" in df_score.columns:
    col_site = "Site"
elif "Nom" in df_score.columns:
    col_site = "Nom"
else:
    df_score["Site_export"] = np.arange(len(df_score)) + 1
    col_site = "Site_export"

df_export = pd.DataFrame({
    "Site": df_score[col_site],
    "Etat": df_score["Etat"],
    "Score": df_score["Score_pondere"],
    "Classe_KMeans": df_score["Classe_KMeans"]
})

print("\n" + "="*70)
print("APERÇU EXPORT")
print(df_export.head())

# ==========================================================
# 12) EXPORT EXCEL
# ==========================================================
excel_out = r"C:\Users\maifia\Documents\expérimental\terrain\raideurdynamique_revin\Classification_5_classes_KMeans.xlsx"
df_export.to_excel(excel_out, index=False)

print("\nFichier exporté :", excel_out)
#%% TABLEAU COLORE DES SITES SELON LA CLASSE K-MEANS

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# ==========================================================
# 1) CHOIX DE LA COLONNE NOM DE SITE
# ==========================================================
if "Nom" in df_score.columns:
    col_site = "Nom"
elif "Site" in df_score.columns:
    col_site = "Site"
else:
    raise ValueError("Aucune colonne 'Nom' ou 'Site' trouvée dans df_score.")

# vérifier que la colonne KMeans existe
if "Classe_KMeans" not in df_score.columns:
    raise ValueError("La colonne 'Classe_KMeans' n'existe pas. Exécute d'abord le code K-means.")

# garder seulement les colonnes utiles
df_visu = df_score[[col_site, "Etat", "Score_pondere", "Classe_KMeans"]].copy()
df_visu = df_visu.rename(columns={col_site: "Site"})

# si un même nom apparaît plusieurs fois, on garde la première ligne
df_visu = df_visu.drop_duplicates(subset="Site").copy()

# trier selon le score pour une meilleure lecture
df_visu = df_visu.sort_values("Score_pondere").reset_index(drop=True)

# ==========================================================
# 2) ENCODAGE DES CLASSES
# ==========================================================
ordre_classes = [
    "Très saine",
    "Peu altérée",
    "Intermédiaire",
    "Dégradée",
    "Très dégradée"
]

class_to_num = {c: i for i, c in enumerate(ordre_classes)}
df_visu["Classe_num"] = df_visu["Classe_KMeans"].map(class_to_num)

# matrice 1 x N pour affichage en tableau coloré
mat = np.array([df_visu["Classe_num"].values])

# ==========================================================
# 3) COULEURS
# ==========================================================
cmap = ListedColormap([
    "green",        # Très saine
    "yellowgreen",  # Peu altérée
    "yellow",       # Intermédiaire
    "darkorange",   # Dégradée
    "red"           # Très dégradée
])

# ==========================================================
# 4) TRACE
# ==========================================================
fig, ax = plt.subplots(figsize=(max(12, len(df_visu)*0.45), 2.8))

im = ax.imshow(mat, aspect="auto", cmap=cmap, vmin=-0.5, vmax=4.5)

# noms des sites sur x
ax.set_xticks(np.arange(len(df_visu)))
ax.set_xticklabels(df_visu["Site"], rotation=90, fontsize=11)

# une seule ligne en y
ax.set_yticks([0])
ax.set_yticklabels(["Classe K-means"], fontsize=12)

ax.set_xlabel("Site", fontsize=13)

# grille visuelle
ax.set_xticks(np.arange(-0.5, len(df_visu), 1), minor=True)
ax.set_yticks(np.arange(-0.5, 1.5, 1), minor=True)
ax.grid(which="minor", color="black", linestyle="-", linewidth=0.8)
ax.tick_params(which="minor", bottom=False, left=False)

# ==========================================================
# 5) LEGENDE
# ==========================================================
legend_elements = [
    Patch(facecolor="green", label="Très saine"),
    Patch(facecolor="yellowgreen", label="Peu altérée"),
    Patch(facecolor="yellow", label="Intermédiaire"),
    Patch(facecolor="darkorange", label="Dégradée"),
    Patch(facecolor="red", label="Très dégradée"),
]

ax.legend(
    handles=legend_elements,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.35),
    ncol=5,
    fontsize=11,
    frameon=True
)

plt.tight_layout()
plt.show()

# ==========================================================
# 6) EXPORT EXCEL DU TABLEAU FINAL
# ==========================================================
excel_out = r"C:\Users\maifia\Documents\expérimental\terrain\raideurdynamique_revin\Tableau_colore_sites_KMeans.xlsx"

df_export = df_visu[["Site", "Etat", "Score_pondere", "Classe_KMeans"]].copy()
df_export.columns = ["Site", "Etat", "Score", "Classe_KMeans"]

df_export.to_excel(excel_out, index=False)
print("Fichier exporté :", excel_out)

