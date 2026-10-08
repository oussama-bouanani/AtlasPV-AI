"""AtlasPV AI - prototype web dashboard. Start with: streamlit run app.py"""
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pv_core import PVConfig, create_alerts, make_demo_data, prepare_data, summarize

st.set_page_config(page_title="AtlasPV AI | Solar Intelligence", page_icon="☀️", layout="wide")
st.markdown('''
<style>
.block-container { padding-top: 1.7rem; max-width: 1320px; }
[data-testid="stMetric"] { border:1px solid rgba(120,140,160,.26); border-radius:13px; padding:16px; background:rgba(75,100,130,.05); }
.hero {background: linear-gradient(110deg,#15352d,#12344a);border:1px solid #31635d;border-radius:18px;padding:25px 28px;color:#ecfffc;margin-bottom:19px;}
.hero h1 {margin:0 0 4px 0;font-size:2.5rem;color:white;}
.hero p {margin:0;color:#cee4e4;font-size:1rem;}
.pill {display:inline-block;background:#276a58;color:#ebffef;border-radius:99px;padding:3px 11px;font-size:.78rem;margin-bottom:12px;}
</style>
''', unsafe_allow_html=True)

st.markdown('''<div class="hero"><span class="pill">PROTOTYPE · DONNÉES DE DÉMONSTRATION</span>
<h1>☀️ AtlasPV AI</h1><p>Surveillance photovoltaïque • détection d'anomalies • aide à la maintenance • rapports Claude (optionnel)</p>
</div>''', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    capacity = st.number_input("Puissance installée (kWc)", min_value=0.5, max_value=100000.0, value=10.0, step=0.5)
    factor = st.slider("Facteur global de performance", min_value=0.60, max_value=1.00, value=0.90, step=0.01)
    threshold = st.slider("Seuil de déficit (%)", min_value=10, max_value=70, value=22, step=1)
    irradiation = st.slider("Irradiance minimale (W/m²)", min_value=100, max_value=600, value=250, step=25)
    st.divider()
    st.header("📂 Sources de données")
    source = st.radio("Données", ["Démonstration simulée", "Charger un CSV"], label_visibility="collapsed")
    uploaded = None
    if source == "Charger un CSV":
        uploaded = st.file_uploader("Fichier de mesures", type=["csv"])
        st.caption("Colonnes : timestamp, irradiance_wm2, module_temp_c, power_kw")
    st.divider()
    st.caption("Ce prototype n'envoie pas de données à un service externe, sauf si vous demandez explicitement une synthèse Claude API.")

config = PVConfig(capacity_kwp=capacity, performance_factor=factor,
                  min_irradiance_wm2=irradiation, deficit_threshold=threshold / 100)
if source == "Charger un CSV" and uploaded is None:
    st.info("Chargez votre CSV pour afficher les mesures, ou choisissez la démonstration simulée.")
    st.stop()
try:
    if uploaded is not None:
        raw = pd.read_csv(uploaded, sep=None, engine="python", encoding="utf-8-sig")
        raw.columns = raw.columns.str.strip()
    else:
        raw = make_demo_data(capacity_kwp=capacity)
    data = prepare_data(raw, config)
except Exception as exc:
    st.error(f"Impossible d'analyser ces mesures : {exc}")
    st.stop()

is_demo = uploaded is None
if is_demo:
    st.warning("Données **100 % simulées** : les incidents, températures et productions ne viennent d'aucune centrale réelle.", icon="🧪")
else:
    st.info("Données CSV fournies par l'utilisateur. Vérifiez les unités, la qualité des capteurs et les paramètres avant toute décision technique.")

summary = summarize(data)
alerts = create_alerts(data)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Production mesurée", f"{summary['measured_kwh']:.1f} kWh")
m2.metric("Production attendue (modèle)", f"{summary['expected_kwh']:.1f} kWh")
m3.metric("Production / référence", f"{summary['ratio_pct']:.1f} %")
m4.metric("Écart pendant les alertes", f"{summary['estimated_gap_kwh']:.1f} kWh")
m5.metric("Épisodes suspects", str(len(alerts)))

tab1, tab2, tab3, tab4 = st.tabs(["📊 Tableau de bord", "📈 Historique", "🛠️ Alertes", "🤖 Rapport et Claude"])

with tab1:
    st.subheader("Puissance AC : mesurée et estimée")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["timestamp"], y=data["expected_kw"], name="Référence physique (kW)", mode="lines", line=dict(color="#2a9d8f", width=2)))
    fig.add_trace(go.Scatter(x=data["timestamp"], y=data["power_kw"], name="Puissance mesurée (kW)", mode="lines", line=dict(color="#e7a32b", width=2)))
    flagged = data[data["is_anomaly"]]
    if not flagged.empty:
        fig.add_trace(go.Scatter(x=flagged["timestamp"], y=flagged["power_kw"], mode="markers", name="Alerte", marker=dict(color="#ef5350", size=6)))
    fig.update_layout(height=420, margin=dict(l=15, r=15, t=25, b=0), xaxis_title="Date et heure", yaxis_title="Puissance (kW)", hovermode="x unified", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Production journalière (kWh)")
    daily = data.assign(jour=data["timestamp"].dt.date).groupby("jour", as_index=False)[["measured_kwh", "expected_kwh"]].sum()
    fig_daily = go.Figure()
    fig_daily.add_trace(go.Bar(x=daily['jour'], y=daily['expected_kwh'], name='Référence (kWh)', marker_color='#2a9d8f'))
    fig_daily.add_trace(go.Bar(x=daily['jour'], y=daily['measured_kwh'], name='Mesurée (kWh)', marker_color='#e7a32b'))
    fig_daily.update_layout(barmode="group", height=330, margin=dict(l=15, r=15, t=30, b=0), xaxis_title='Jour', yaxis_title='Énergie (kWh)')
    st.plotly_chart(fig_daily, use_container_width=True)

with tab2:
    st.subheader("Conditions environnementales")
    col1, col2 = st.columns(2)
    with col1:
        irr_fig = go.Figure(go.Scatter(x=data['timestamp'], y=data['irradiance_wm2'], line=dict(color='#e7a32b')))
        irr_fig.update_layout(title='Irradiance (W/m²)', height=320, margin=dict(l=10, r=10, t=38, b=0))
        st.plotly_chart(irr_fig, use_container_width=True)
    with col2:
        temp_fig = go.Figure(go.Scatter(x=data['timestamp'], y=data['module_temp_c'], line=dict(color='#e96848')))
        temp_fig.update_layout(title='Température modules (°C)', height=320, margin=dict(l=10, r=10, t=38, b=0))
        st.plotly_chart(temp_fig, use_container_width=True)
    st.subheader("Mesures et résultats calculés")
    st.dataframe(data, use_container_width=True, hide_index=True, height=360)
    st.download_button("⬇️ Télécharger les mesures enrichies (CSV)", data=data.to_csv(index=False).encode('utf-8-sig'), file_name='atlaspv_analyse.csv', mime='text/csv')

with tab3:
    st.subheader("Détection de pertes persistantes")
    st.write(f"Une alerte est proposée si la production descend d'au moins **{threshold} %** sous le modèle pendant **3 relevés consécutifs**, avec irradiance ≥ **{irradiation} W/m²**.")
    if alerts.empty:
        st.success("Aucun épisode prolongé détecté avec les seuils sélectionnés.")
    else:
        st.dataframe(alerts, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Exporter les alertes (CSV)", data=alerts.to_csv(index=False).encode('utf-8-sig'), file_name='atlaspv_alertes.csv', mime='text/csv')
    st.warning("Important : une baisse détectée n'identifie pas à elle seule un composant défaillant. Vérifier d'abord capteurs, ombrages et conditions réelles ; toute intervention électrique exige un professionnel qualifié.")


def local_report() -> str:
    if len(alerts):
        incidents = "\n".join(
            f"- {r['Début']} → {r['Fin']} : {r['Priorité']}, déficit {r['Baisse moyenne (%)']:.1f} %, "
            f"écart {r['Énergie non produite estimée (kWh)']:.2f} kWh ; {r['Piste de vérification']}."
            for _, r in alerts.iterrows()
        )
    else:
        incidents = "- Aucun incident persistant détecté par la règle actuelle."
    return ("# Rapport technique — AtlasPV AI\n\n"
            f"**Source :** {'simulation / démonstration' if is_demo else 'fichier CSV utilisateur'}\n\n"
            f"**Installation :** {capacity:g} kWc (paramètre déclaré)\n\n"
            f"**Période :** {data['timestamp'].min()} — {data['timestamp'].max()}\n\n"
            f"**Énergie mesurée :** {summary['measured_kwh']:.2f} kWh\n\n"
            f"**Énergie de référence calculée :** {summary['expected_kwh']:.2f} kWh\n\n"
            f"**Ratio production/référence :** {summary['ratio_pct']:.1f} %\n\n"
            f"**Écart estimé pendant alertes :** {summary['estimated_gap_kwh']:.2f} kWh\n\n"
            f"## Alertes ({len(alerts)})\n{incidents}\n\n"
            "## Limites\nRéférence calculée par une formule simple (irradiance × correction thermique × facteur global). "
            "Les données de démonstration sont synthétiques. Les causes proposées ne constituent pas un diagnostic. "
            "Aucune connexion capteur, aucun modèle ML entraîné, ni validation sur site ne sont inclus dans ce MVP.\n")

with tab4:
    st.subheader("Rapport de maintenance — sans frais API")
    report = local_report()
    st.markdown(report)
    st.download_button("⬇️ Télécharger le rapport (.md)", data=report.encode('utf-8'), file_name='rapport_atlaspv.md', mime='text/markdown')
    st.divider()
    st.subheader("✨ Générer un compte rendu avec Claude (optionnel)")
    st.caption("Cette option nécessite une clé API Anthropic et des crédits API. Elle n'est PAS incluse dans la démo gratuite. Seul un résumé des statistiques et des alertes est envoyé.")
    language = st.selectbox('Langue du rapport', ['Français', 'Arabe'])
    api_key = st.text_input("Clé ANTHROPIC_API_KEY (conservée uniquement pendant cette session)", type='password', value=os.environ.get('ANTHROPIC_API_KEY', ''))
    model = st.text_input("Identifiant de modèle disponible sur votre compte", value=os.environ.get('ANTHROPIC_MODEL', ''), placeholder='Exemple : votre modèle Claude actif')
    if st.button("Générer le rapport Claude", type='primary'):
        if not api_key or not model:
            st.error('Renseignez une clé API valide et un identifiant de modèle disponible dans votre compte.')
        else:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key, timeout=45.0)
                request_text = ("Rédige un rapport technique concis de maintenance photovoltaïque. "
                                "N'invente aucune mesure, ne promets pas de diagnostic et recommande de vérifier sur site. "
                                f"Langue : {language}. Voici uniquement les résultats agrégés :\n{report[:12000]}")
                message = client.messages.create(model=model, max_tokens=1200,
                    system="Tu es un assistant d'aide à la maintenance PV. Différencie simulations, hypothèses et mesures réelles. Évite toute instruction d'intervention dangereuse.",
                    messages=[{"role": "user", "content": request_text}])
                response = "\n".join(part.text for part in message.content if getattr(part, "type", "") == "text")
                st.markdown(response or "Aucun texte renvoyé.")
                if response:
                    st.download_button("⬇️ Télécharger le compte rendu Claude", response.encode('utf-8'), 'rapport_atlaspv_claude.md')
            except ImportError:
                st.error("Module Anthropic absent : pip install -r requirements.txt")
            except Exception as exc:
                st.error("La demande API n'a pas abouti. Vérifiez votre clé, votre modèle, vos crédits et la connexion réseau.")
                st.caption(f"Type d'erreur : {type(exc).__name__}")

st.divider()
st.caption("AtlasPV AI • Prototype éducatif / startup early-stage • Modèle de référence simplifié, alertes explicables, Claude API facultatif • Aucune qualification de sécurité électrique ou de performance contractuelle")
