import streamlit as st
import pandas as pd

# =====================================================
# Fonctions de calcul
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
# Interface Streamlit
# =====================================================

st.set_page_config(
    page_title="Prévision de Rentabilité Obligataire",
    layout="wide"
)

st.title("📈 Prévision de Rentabilité Obligataire")

uploaded = st.file_uploader(
    "Importer le fichier Excel",
    type=["xlsx"]
)

if uploaded is not None:

    try:

        df = pd.read_excel(
            uploaded,
            sheet_name="02_PORTEFEUILLE"
        )

    except Exception:

        df = pd.read_excel(uploaded)

    # =================================================
    # Nettoyage des colonnes
    # =================================================

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

    # =================================================
    # Compatibilité anciens formats Excel
    # =================================================

    if "YTM" not in df.columns:

        if "Taux actuel %" in df.columns:

            df["YTM"] = df["Taux actuel %"]

    if "Convexity" not in df.columns:

        if "Convexite" in df.columns:

            df["Convexity"] = df["Convexite"]

    # =================================================
    # Vérification des colonnes obligatoires
    # =================================================

    required_columns = [
        "YTM",
        "Duration",
        "Convexity",
        "RollDown",
        "Poids"
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
            "Colonnes détectées :",
            df.columns.tolist()
        )

        st.stop()

    # =================================================
    # Paramètres utilisateur
    # =================================================

    st.sidebar.header("Paramètres")

    horizon = st.sidebar.slider(
        "Horizon (années)",
        min_value=0.25,
        max_value=1.00,
        value=1.00,
        step=0.25
    )

    delta_bps = st.sidebar.number_input(
        "Variation des taux (bps)",
        min_value=-200,
        max_value=200,
        value=-20
    )

    delta_rate = delta_bps / 10000

    # =================================================
    # Calcul Total Return
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

    performance = portfolio_return(df)

    # =================================================
    # Affichage Portefeuille
    # =================================================

    st.subheader("Portefeuille")

    st.dataframe(
        df,
        use_container_width=True
    )

    st.metric(
        "Performance prévisionnelle",
        f"{performance:.2%}"
    )

    # =================================================
    # Analyse par scénarios
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

    # =================================================
    # Affichage scénarios
    # =================================================

    st.subheader("Analyse par scénario")

    st.dataframe(
        scenarios,
        use_container_width=True
    )

    st.metric(
        "Espérance de rentabilité",
        f"{esperance:.2%}"
    )

    # =================================================
    # Télécharger résultats
    # =================================================

    csv = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Télécharger les résultats CSV",
        csv,
        "resultats_portefeuille.csv",
        "text/csv"
    )
