import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# st_charts.py
# Contient toutes les figures Plotly de l'application.
# Aucun code Streamlit ici — uniquement des fonctions qui retournent des fig.
# =============================================================================


# --- 1. DONUTS ---

def apply_style(fig):
    """
    Applique le style commun à tous les donuts (texte, position, hover).
    Modifie la figure en place — pas de return nécessaire.

    Args:
        fig (go.Figure): figure Plotly à styler
    """
    fig.update_traces(
        textinfo='percent',
        texttemplate='<b>%{percent:.0%}</b>',
        textposition='inside',
        insidetextorientation='horizontal',
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} €<extra></extra>"
    )


def make_donuts(df, names, values, color_discrete_map, rotation, labels, poids=None, taille=200):
    """
    Crée un donut chart générique pour afficher la répartition d'une enveloppe.
    Utilisé dans Home.py (poids global) et Dashboards.py (répartition interne).

    Args:
        df (DataFrame): données filtrées pour ce donut (ex: df.query("ptf_id in [1, 2]"))
        names (str): nom de la colonne utilisée pour les labels (ex: 'nom_pour_legende')
        values (str): nom de la colonne utilisée pour les valeurs (ex: 'capital_actuel')
        color_discrete_map (dict): mapping label → couleur hex (ex: {"S&P 500": "#822A2A"})
        rotation (int): angle de départ du premier secteur (en degrés)
        labels (str): texte affiché au centre du donut (ex: "Poids ETF")
        poids (float, optional): poids en % affiché en grand au centre. 
                                 Si None, le label est centré sans valeur. Default: None
        taille (int, optional): hauteur du graphique en pixels. Default: 200

    Returns:
        go.Figure: figure Plotly prête à être affichée avec st.plotly_chart()
    """
    # Layout commun : taille dynamique, fond transparent, pas de légende
    common_layout = dict(
        height=taille,
        showlegend=False,
        margin=dict(t=0, b=10, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        separators=", "
    )

    # Création du pie chart avec trou (hole) pour l'effet donut
    fig = px.pie(
        df,
        names=names,
        values=values,
        hole=0.68,
        color=names,
        color_discrete_map=color_discrete_map
    )

    # Application du style commun + rotation spécifique à cette enveloppe
    apply_style(fig)
    fig.update_traces(rotation=rotation)

    # Layout + annotations : label en haut, poids en grand en bas
    annotations = []
    if poids is not None:
        annotations.append(dict(text=labels, x=0.5, y=0.6, showarrow=False, font=dict(size=18)))
        annotations.append(dict(text=f"<b>{poids:.0f}%</b>", x=0.51, y=0.4, showarrow=False, font=dict(size=35)))
    else:
        annotations.append(dict(text=labels, x=0.5, y=0.5, showarrow=False, font=dict(size=18)))
    
    fig.update_layout(common_layout, hoverlabel=dict(font_size=15), annotations=annotations)

    return fig


# --- 2. GRAPH GLOBAL ---

def make_graph_global(df_apports_graph, df_capital_graph):
    """
    Crée le graphique principal de la Home : évolution du capital vs apports + perf marchés.
    Combine 2 axes Y : barres (perf %) à gauche, lignes (capital €) à droite.

    Args:
        df_apports_graph (DataFrame): apports cumulés filtrés sur la période
                                      doit contenir : index datetime, colonne 'cumsum'
        df_capital_graph (DataFrame): capital mensuel filtré sur la période
                                      doit contenir : index datetime, colonnes 'Total', 'delta', 'perf_graph'

    Returns:
        go.Figure: figure Plotly prête à être affichée avec st.plotly_chart()
    """
    graph_global = go.Figure()

    # Coloration dynamique des barres : rouge si perf négative, vert si positive
    coloration = df_capital_graph['perf_graph'].apply(
        lambda x: '#ff4b4b' if x < 0 else '#09ab3b'
    )

    # Ligne 1 : Capital total (axe Y droit)
    graph_global.add_trace(go.Scatter(
        x=df_capital_graph.index,
        y=df_capital_graph['Total'],
        name="Capital",
        mode='lines+markers',
        marker=dict(size=4),
        yaxis="y2",
        line=dict(color='#FFD700'),
        customdata=df_capital_graph['delta'],  # écart capital - apports cumulés
        hovertemplate="%{y:,.0f} €<br>Delta: %{customdata:,.0f} €"
    ))

    # Ligne 2 : Apports cumulés (axe Y droit) — sert de référence vs le capital réel
    graph_global.add_trace(go.Scatter(
        x=df_apports_graph.index,
        y=df_apports_graph['cumsum'],
        name="Injecté",
        mode='lines+markers',
        marker=dict(size=4),
        yaxis="y2",
        line=dict(color='#4DA6FF'),
        hovertemplate="%{y:,.0f} €",
    ))

    # Barres : performance mensuelle des marchés en % (axe Y gauche)
    graph_global.add_trace(go.Bar(
        x=df_capital_graph.index,
        y=df_capital_graph['perf_graph'],
        name="Perf Marchés",
        marker=dict(color=coloration, opacity=0.8),
        width=1000 * 3600 * 24 * 3,  # largeur des barres en millisecondes
        hovertemplate="%{y:,.2f} %"
    ))

    # Calcul des bornes de l'axe Y droit pour éviter que les lignes soient écrasées
    y_min = min(df_capital_graph['Total'].min(), df_apports_graph['cumsum'].min()) * 0.95
    y_max = max(df_capital_graph['Total'].max(), df_apports_graph['cumsum'].max()) * 1.05

    # Habillage général : double axe Y, légende horizontale en haut, hover unifié
    graph_global.update_layout(
        yaxis=dict(title="Perf %", showgrid=False),
        xaxis=dict(tickformat="%B %Y"),
        yaxis2=dict(
            side='right',
            overlaying='y',
            range=[y_min, y_max],
            title="Capital (€)"
        ),
        legend=dict(orientation='h', y=1.1, x=0.5, xanchor='center'),
        height=600,
        hovermode='x unified',
        hoverlabel=dict(font_size=15),
        separators=". "
    )

    return graph_global