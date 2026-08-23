import streamlit as st
import pandas as pd
from io import BytesIO

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Prévision de Rentabilité Obligataire",
    layout="wide"
)

EXCEL_SOURCE = "Modele_Prevision_Obligataire_Complet_Streamlit.xlsx"

# =====================================================
# FONCTIONS
# =====================================================

def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


def total_return(
    yield_rate,
    duration,
    convexity,
    horizon,
    delta_rate,
    roll_down
):

    carry = yield_rate * horizon

    price_effect = -duration * delta_rate

    convexity_effect = (
        0.5 * convexity * (delta_rate ** 2)
    )

    return (
        carry
        + roll_down
        + price_effect
        + convexity_effect
    )


def portfolio_return(df):

    return (
        df["Poids"]
        * df["Total Return"]
    ).sum()


# =====================================================
# TITRE
# =====================================================

st.title("📈 Prévision de Rentabilité Obligataire")

# =====================================================
# TELECHARGEMENT FICHIER SOURCE
# =====================================================

try:

    with open(EXCEL_SOURCE, "rb") as f:

        st.download_button(
            "📥 Télécharger le fichier Excel source",
            data=f.read(),
            file_name=EXCEL_SOURCE,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

except:
    pass

# =====================================================
# CHARGEMENT OPTIONNEL D'UN FICHIER
# =====================================================

uploaded_file = st.file_uploader(
    "📤 Charger un fichier Excel (optionnel)",
    type=["xlsx"]
)

# =====================================================
# LECTURE DU FICHIER
# =====================================================

try:

    if uploaded_file is not None:

        excel_file = uploaded_file
        source = "Fichier téléversé"

    else:

        excel_file = EXCEL_SOURCE
        source = "Fichier GitHub"

    # PARAMETRES

    params = pd.read_excel(
        excel_file,
        sheet_name="01_PARAMETRES"
    )

    params_dict = dict(
        zip(
            params["Parametre"],
            params["Valeur"]
        )
    )

    # PORTEFEUILLE

    df = pd.read_excel(
        excel_file,
        sheet_name="02_PORTEFEUILLE"
    )

except Exception as e:

    st.error(
        f"Erreur de lecture : {e}"
    )

    st.stop()

# =====================================================
# PARAMETRES ISSUS D'EXCEL
# =====================================================

horizon_excel = safe_float(
    params_dict.get("Horizon", 1)
)

delta_excel = safe_float(
    params_dict.get("Delta_bps", -20)
)

prob_favorable = safe_float(
    params_dict.get("Prob_Favorable", 0.20)
)

prob_central = safe_float(
    params_dict.get("Prob_Central", 0.60)
)

prob_defavorable = safe_float(
    params_dict.get("Prob_Defavorable", 0.20)
)

# =====================================================
# INFO
# =====================================================

st.success(
    f"Source utilisée : {source}"
)

# =====================================================
# NETTOYAGE
# =====================================================

df.columns = (
    df.columns
      .astype(str)
      .str.strip()
)

df = df.loc[
    :,
    ~df.columns.str.contains("^Unnamed")
]

# =====================================================
# COMPATIBILITE
# =====================================================

if "YTM" not in df.columns:

    if "Taux actuel %" in df.columns:
        df["YTM"] = df["Taux actuel %"]

if "Convexity" not in df.columns:

    if "Convexite" in df.columns:
        df["Convexity"] = df["Convexite"]

# =====================================================
# CONTROLE
# =====================================================

required = [
    "Encours",
    "YTM",
    "Duration",
    "Convexity",
    "RollDown"
]

missing = [
    c for c in required
    if c not in df.columns
]

if missing:

    st.error(
        f"Colonnes manquantes : {missing}"
    )

    st.stop()

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Paramètres")

horizon = st.sidebar.slider(
    "Horizon (années)",
    0.25,
    1.00,
    float(horizon_excel),
    0.25
)

delta_bps = st.sidebar.number_input(
    "Taux de variation (bps)",
    value=int(delta_excel)
)

delta_rate = delta_bps / 10000

# =====================================================
# POIDS
# =====================================================

df["Encours"] = pd.to_numeric(
    df["Encours"],
    errors="coerce"
).fillna(0)

df["Poids"] = (
    df["Encours"]
    / df["Encours"].sum()
)

# =====================================================
# CALCUL
# =====================================================

df["Total Return"] = df.apply(

    lambda row:

    total_return(

        safe_float(row["YTM"]) / 100,

        safe_float(row["Duration"]),

        safe_float(row["Convexity"]),

        horizon,

        delta_rate,

        safe_float(row["RollDown"])

    ),

    axis=1

)

performance = portfolio_return(df)

duration_pf = (
    df["Duration"]
    * df["Poids"]
).sum()

# =====================================================
# KPI
# =====================================================

col1, col2 = st.columns(2)

col1.metric(
    "Performance Prévisionnelle",
    f"{performance:.2%}"
)

col2.metric(
    "Duration Portefeuille",
    f"{duration_pf:.2f}"
)

# =====================================================
# TABLEAU
# =====================================================

st.subheader("Portefeuille")

st.dataframe(
    df,
    use_container_width=True
)

# =====================================================
# SCENARIOS
# =====================================================

scenarios = pd.DataFrame({

    "Scénario": [
        "Favorable",
        "Central",
        "Défavorable"
    ],

    "Probabilité": [
        prob_favorable,
        prob_central,
        prob_defavorable
    ],

    "Delta_bps": [
        -25,
        0,
        25
    ]

})

scenario_perf = []

for delta in scenarios["Delta_bps"]:

    perf = (

        df["Poids"]

        *

        df.apply(

            lambda row:

            total_return(

                safe_float(row["YTM"]) / 100,

                safe_float(row["Duration"]),

                safe_float(row["Convexity"]),

                horizon,

                delta / 10000,

                safe_float(row["RollDown"])

            ),

            axis=1

        )

    ).sum()

    scenario_perf.append(perf)

scenarios["Performance"] = scenario_perf

esperance = (
    scenarios["Probabilité"]
    * scenarios["Performance"]
).sum()

# =====================================================
# RESULTATS
# =====================================================

st.subheader("Analyse par scénario")

st.dataframe(
    scenarios,
    use_container_width=True
)

st.metric(
    "Espérance de rentabilité",
    f"{esperance:.2%}"
)

# =====================================================
# EXPORT CSV
# =====================================================

csv = df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "📄 Télécharger les résultats CSV",
    csv,
    "Resultats_Portefeuille.csv",
    "text/csv"
)

# =====================================================
# EXPORT EXCEL
# =====================================================

output = BytesIO()

with pd.ExcelWriter(
    output,
    engine="openpyxl"
) as writer:

    df.to_excel(
        writer,
        sheet_name="Portefeuille",
        index=False
    )

    scenarios.to_excel(
        writer,
        sheet_name="Scenarios",
        index=False
    )

excel_file_export = output.getvalue()

st.download_button(
    "📊 Télécharger les résultats Excel",
    excel_file_export,
    "Prevision_Obligataire.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
