import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path

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


def clean_dataframe(df):

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    df = df.loc[
        :,
        ~df.columns.str.contains("^Unnamed")
    ]

    if "YTM" not in df.columns:
        if "Taux actuel %" in df.columns:
            df["YTM"] = df["Taux actuel %"]

    if "Convexity" not in df.columns:
        if "Convexite" in df.columns:
            df["Convexity"] = df["Convexite"]

    return df


# =====================================================
# CHARGEMENT DONNEES
# =====================================================

@st.cache_data
def load_portfolio_from_github():

    return pd.read_excel(
        EXCEL_SOURCE,
        sheet_name="02_PORTEFEUILLE"
    )


# =====================================================
# TITRE
# =====================================================

st.title("📈 Prévision de Rentabilité Obligataire")

st.success(
    "Le fichier Excel du dépôt GitHub est chargé automatiquement."
)

# =====================================================
# BOUTON ACTUALISER
# =====================================================

if st.button("🔄 Actualiser les données GitHub"):

    st.cache_data.clear()

# =====================================================
# CHARGEMENT PAR DEFAUT
# =====================================================

try:

    df = load_portfolio_from_github()

    source = "Fichier GitHub"

except Exception as e:

    st.error(
        f"Impossible de charger le fichier GitHub : {e}"
    )

    st.stop()

# =====================================================
# UPLOAD OPTIONNEL
# =====================================================

uploaded_file = st.file_uploader(
    "Charger un autre fichier Excel (optionnel)",
    type=["xlsx"]
)

if uploaded_file is not None:

    df = pd.read_excel(
        uploaded_file,
        sheet_name="02_PORTEFEUILLE"
    )

    source = "Fichier téléversé"

# =====================================================
# NETTOYAGE
# =====================================================

df = clean_dataframe(df)

st.info(f"Source utilisée : {source}")

# =====================================================
# VERIFICATION
# =====================================================

required_columns = [
    "YTM",
    "Duration",
    "Convexity",
    "RollDown",
    "Encours"
]

missing = [
    c
    for c in required_columns
    if c not in df.columns
]

if missing:

    st.error(
        f"Colonnes manquantes : {missing}"
    )

    st.write(df.columns.tolist())

    st.stop()

# =====================================================
# PARAMETRES
# =====================================================

st.sidebar.header("Paramètres")

horizon = st.sidebar.slider(
    "Horizon (années)",
    0.25,
    1.00,
    1.00,
    0.25
)

delta_bps = st.sidebar.number_input(
    "Variation des taux (bps)",
    -200,
    200,
    -20
)

delta_rate = delta_bps / 10000

# =====================================================
# PORTFOLIO
# =====================================================

st.subheader("📋 Portefeuille")

df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic"
)

# =====================================================
# POIDS AUTOMATIQUES
# =====================================================

df["Poids"] = (
    df["Encours"]
    / df["Encours"].sum()
)

# =====================================================
# TOTAL RETURN
# =====================================================

df["Total Return"] = df.apply(
    lambda row:
    total_return(
        float(row["YTM"]) / 100,
        float(row["Duration"]),
        float(row["Convexity"]),
        horizon,
        delta_rate,
        float(row["RollDown"])
    ),
    axis=1
)

# =====================================================
# PERFORMANCE
# =====================================================

performance = portfolio_return(df)

duration_pf = (
    df["Duration"]
    * df["Poids"]
).sum()

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
# AFFICHAGE
# =====================================================

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
        0.20,
        0.60,
        0.20
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

        * df.apply(

            lambda row:
            total_return(
                float(row["YTM"]) / 100,
                float(row["Duration"]),
                float(row["Convexity"]),
                horizon,
                delta / 10000,
                float(row["RollDown"])
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

st.subheader("🎯 Analyse par scénario")

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
    "📄 Télécharger CSV",
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

excel_file = output.getvalue()

st.download_button(
    "📊 Télécharger Excel",
    excel_file,
    "Prevision_Obligataire.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
