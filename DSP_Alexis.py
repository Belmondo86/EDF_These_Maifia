# -*- coding: utf-8 -*-
"""
Created on Thu Dec  4 14:32:45 2025

@author: maifia
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as patches
import matplotlib.cm as cm
import matplotlib.colors as colors

# --- Lecture du fichier Excel ---
fichier_excel = r"C:\Users\maifia\Documents\Expérimental\US\Programme_US_ACSYS(Récupération automatique).xlsx"
feuille = "BBE"
df = pd.read_excel(fichier_excel, sheet_name=feuille)

# Nettoyage colonnes
df.columns = df.columns.str.strip()

# Nettoyage Emplacement
df['Emplacement'] = df['Emplacement'].astype(str).str.strip().str.title()

# Liste des emplacements attendus
emplacements = ["Pied Barrage", "Marnage Bas", "Marnage Milieu", "Marnage Haut", "Haut Barrage"]
df = df[df['Emplacement'].isin(emplacements)]

# PM en numérique
df['PM_num'] = df['PM'].astype(str).str.extract(r'(\d+)').astype(float)

# Axe Y
y_pos = np.arange(len(emplacements))

# Couleurs de fond
emplacement_colors = {
    "Pied Barrage": "yellow",
    "Marnage Bas": "blue",
    "Marnage Milieu": "lightblue",
    "Marnage Haut": "orange",
    "Haut Barrage": "grey"
}

# Coloration continue selon Edyn
norm = colors.Normalize(vmin=df['Edyn (GPa)'].min(), vmax=df['Edyn (GPa)'].max())
cmap = cm.get_cmap("RdYlGn")

# Formes selon état
state_marker = {"saine": "s", "dégradée": "o"}
state_edge = {"saine": "green", "dégradée": "red"}

# Tracé
fig, ax = plt.subplots(figsize=(24, 8))

# Bandes colorées
for i, emplacement in enumerate(emplacements):
    ax.barh(
        y=i,
        width=df['PM_num'].max() * 1.1,
        height=1,
        color=emplacement_colors[emplacement],
        alpha=0.3,
        edgecolor=None
    )

# Décalage pour PM dupliqués
pm_counts = df.groupby(['PM_num', 'Emplacement']).cumcount()
df['PM_adj'] = df['PM_num'] + pm_counts * 35

# Limites X utiles
x_min = df['PM_num'].min()
x_max = df['PM_num'].max() * 1.1

# ==========================================================
# ZONES TRANSPARENTES : PARTIES SUR-CREUSÉES
# ==========================================================

# Zone 0 → 545 PM
ax.axvspan(
    0, 545,
    color="#2ecc71" ,
    alpha=0.2,
    zorder=1
)

# Zone 3500 PM → fin
ax.axvspan(
    3500, x_max,
    color="#2ecc71" ,
    alpha=0.2,
    zorder=1
)

# Carottes à encadrer
carottes_cible = ["C42", "CP7", "C30", "C04", "C27", "C56", "C20", "C48", "C06", "C54"]

# ----------------------------
# TRACE LES POINTS
# ----------------------------
for i, row in df.iterrows():
    y = y_pos[emplacements.index(row['Emplacement'])]
    x = row['PM_adj']

    etat = row['Etat'].lower()
    marker = state_marker.get(etat, 'o')
    edge = state_edge.get(etat, 'black')

    color_value = cmap(norm(row['Edyn (GPa)']))

    ax.scatter(
        x, y,
        marker=marker,
        s=200,
        facecolor=color_value,
        edgecolor=edge,
        linewidth=1.3,
        zorder=4
    )

    ax.text(
        x, y + 0.1,
        str(row['Carotte']),
        fontsize=14,
        ha='center',
        va='bottom',
        rotation=45,
        zorder=5
    )

    if row['Carotte'] in carottes_cible:
        rect = patches.Rectangle(
            (x - 25, y - 0.2),
            50,
            0.4,
            linewidth=1.5,
            edgecolor="purple",
            facecolor="none",
            alpha=0.6,
            zorder=3
        )
        ax.add_patch(rect)

# Lignes verticales PM
pm_intervals = [(3000, 3600), (0, 700), (700, 2800)]
for start, end in pm_intervals:
    ax.axvline(start, color='black', linestyle='--', linewidth=1)
    ax.axvline(end, color='black', linestyle='--', linewidth=1)

# ==========================================================
# SCHÉMATISATION DES DRAINS LONGITUDINAUX
# ==========================================================

epaisseur = 0.08



# --- Drain inférieur : sur toute la longueur ---
x2_start, x2_end = x_min, x_max
y2 = 0.75

ax.hlines(y2 - epaisseur/2, x2_start, x2_end,
          colors="black", linestyles="dashed", linewidth=2.5, zorder=2)
ax.hlines(y2 + epaisseur/2, x2_start, x2_end,
          colors="black", linestyles="dashed", linewidth=2.5, zorder=2)

# Axes
ax.set_yticks(y_pos)
ax.set_yticklabels(emplacements, fontsize=20)

ax.set_xlabel("Point métrique (PM)", fontsize=20)
ax.set_ylabel("Emplacement", fontsize=20)
ax.tick_params(axis='x', labelsize=20)
ax.tick_params(axis='y', labelsize=20)

# Barre de couleur horizontale en haut
sm = cm.ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])

cbar = fig.colorbar(
    sm,
    ax=ax,
    orientation="horizontal",
    location="top",
    pad=0.08,
    fraction=0.04,
    aspect=40
)

cbar.ax.tick_params(labelsize=16)
cbar.set_label("Edyn (GPa)", fontsize=16)

# Légende
legend_shapes = [
    Line2D([0], [0], marker='s', color='w', label='Saine (carré)',
           markerfacecolor='white', markeredgecolor='green', markersize=16),
    Line2D([0], [0], marker='o', color='w', label='Dégradée (cercle)',
           markerfacecolor='white', markeredgecolor='red', markersize=16),
    Line2D([0], [0], color='black', linestyle='--',
           linewidth=2.5, label='Drain longitudinal'),
    patches.Patch(facecolor='#2ecc71', edgecolor='none',
                  alpha=0.35, label='Partie sur-creusée')
]

ax.legend(handles=legend_shapes, title="État de la carotte", fontsize=12, title_fontsize=12, loc="upper right")

plt.tight_layout()
plt.savefig(r"C:\Users\maifia\Documents\Expérimental\US\figure_US_ACSYS.png", dpi=300, bbox_inches='tight')
plt.show()