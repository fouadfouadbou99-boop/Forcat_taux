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
        df["Poids"] *
        df["Total Return"]
    ).sum()


# =====================================================
# TITRE
# =====================================================

st.title("📈 Prévision de Rentabilité Obligataire")

uploaded = st.file_uploader(
    "Importer le fichier Excel",
    type=["xlsx"]
)

# =====================================================
# LECTURE EXCEL
# =====================================================

if uploaded is not None:

    try:

        df = pd.read_excel(
            uploaded,
            sheet_name="02_PORTEFEUILLE"
        )

    except Exception:

        df = pd.read_excel(uploaded)

    # Nettoyage colonnes

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # Suppression colonnes parasites

    df = df.loc[
        :,
        ~df.columns.str.contains("^Unnamed")
    ]

    # Compatibilité anciens fichiers

    if "YTM" not in df.columns:

        if "Taux actuel %" in df.columns:

            df["YTM"] = df["Taux actuel %"]

    if "Convexity" not in df.columns:

        if "Convexite" in df.columns:

            df["Convexity"] = df["Convexite"]

    # Vérification

    required_columns = [
        "YTM",
        "Duration",
        "Convexity",
        "RollDown",
        "Encours"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:

        st.error(
            f"Colonnes manquantes : {missing}"
        )

        st.write(
            "Colonnes trouvées :",
            df.columns.tolist()
        )

        st.stop()

    # =================================================
    # PARAMETRES
    # =================================================

    st.sidebar.header("Paramètres")

    horizon = st.sidebar.slider(
        "Horizon (années)",
        0.25,
        1.00,
        1.00,
        0.25
    )

    delta_bps = st.sidebar.number_input(
        "Variation taux (bps)",
        -200,
        200,
        -20
    )

    delta_rate = delta_bps / 10000

    # =================================================
    # MODIFICATION DES DONNEES
    # =================================================

    st.subheader("📋 Portefeuille")

    df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic"
    )

    # =================================================
    # CALCUL AUTOMATIQUE DES POIDS
    # =================================================

    df["Poids"] = (
        df["Encours"]
        / df["Encours"].sum()
    )

    # =================================================
    # CALCUL TOTAL RETURN
    # =================================================

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

    # =================================================
    # PERFORMANCE PORTEFEUILLE
    # =================================================

    performance = portfolio_return(df)

    col1, col2 = st.columns(2)

    col1.metric(
        "Performance Prévisionnelle",
        f"{performance:.2%}"
    )

    col2.metric(
        "Duration Portefeuille",
        f"{(df['Duration']*df['Poids']).sum():.2f}"
    )

    # =================================================
    # SCENARIOS
    # =================================================

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

            *

            df.apply(

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

        *

        scenarios["Performance"]

    ).sum()

    st.subheader("🎯 Analyse par Scénario")

    st.dataframe(
        scenarios,
        use_container_width=True
    )

    st.metric(
        "Espérance de Rentabilité",
        f"{esperance:.2%}"
    )

    # =================================================
    # EXPORT CSV
    # =================================================

    csv = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📄 Télécharger CSV",
        csv,
        "Resultats_Portefeuille.csv",
        "text/csv"
    )

    # =================================================
    # EXPORT EXCEL
    # =================================================

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
        label="📊 Télécharger Excel",
        data=excel_file,
        file_name="Prevision_Obligataire.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
