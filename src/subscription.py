"""
Module de gestion des abonnements (simulation).
Prépare l'intégration des paiements mobiles.
"""
import streamlit as st
from datetime import datetime, timedelta

class SubscriptionManager:
    """Simule un système d'abonnement avec une session utilisateur."""

    # Simulation d'une base de données utilisateurs en session state
    SUBSCRIPTION_KEY = "subscription_active"
    SUBSCRIPTION_EXPIRY_KEY = "subscription_expiry"

    @staticmethod
    def initialize_session():
        """Initialise l'état de l'abonnement dans la session."""
        if SubscriptionManager.SUBSCRIPTION_KEY not in st.session_state:
            st.session_state[SubscriptionManager.SUBSCRIPTION_KEY] = False
        if SubscriptionManager.SUBSCRIPTION_EXPIRY_KEY not in st.session_state:
            st.session_state[SubscriptionManager.SUBSCRIPTION_EXPIRY_KEY] = None

    @staticmethod
    def is_active() -> bool:
        """Vérifie si l'utilisateur a un abonnement actif (non expiré)."""
        SubscriptionManager.initialize_session()
        if not st.session_state[SubscriptionManager.SUBSCRIPTION_KEY]:
            return False

        # Vérifier l'expiration
        expiry = st.session_state[SubscriptionManager.SUBSCRIPTION_EXPIRY_KEY]
        if expiry and datetime.now() > expiry:
            # Expiration automatique
            st.session_state[SubscriptionManager.SUBSCRIPTION_KEY] = False
            st.session_state[SubscriptionManager.SUBSCRIPTION_EXPIRY_KEY] = None
            return False

        return True

    @staticmethod
    def activate_subscription(duration_days: int = 30):
        """Active un abonnement pour une durée donnée (simulation)."""
        SubscriptionManager.initialize_session()
        st.session_state[SubscriptionManager.SUBSCRIPTION_KEY] = True
        st.session_state[SubscriptionManager.SUBSCRIPTION_EXPIRY_KEY] = datetime.now() + timedelta(days=duration_days)
        st.rerun() # Recharger pour mettre à jour l'interface

    @staticmethod
    def show_subscription_ui():
        """Affiche l'interface utilisateur pour la gestion de l'abonnement."""
        with st.sidebar:
            st.divider()
            st.header("💳 Abonnement")

            if SubscriptionManager.is_active():
                expiry = st.session_state[SubscriptionManager.SUBSCRIPTION_EXPIRY_KEY]
                st.success(f"✅ Abonnement actif jusqu'au {expiry.strftime('%d/%m/%Y')}")

                # Simulation d'un bouton de gestion (pourra lier vers un portail de paiement)
                if st.button("Gérer mon abonnement", use_container_width=True):
                    st.info("🔗 Redirection vers la plateforme de paiement (simulée).")
            else:
                st.warning("❌ Abonnement inactif")
                st.markdown("""
                **Profitez de VoxWhisper Pro sans limites !**

                - **Forfait Mensuel:** 2 500 FCFA
                - **Forfait Annuel:** 25 000 FCFA (Économisez 17%)

                **Moyens de paiement acceptés :**
                - 📱 Orange Money
                - 🌊 Wave
                - 💳 Carte bancaire
                """)

                # Interface de simulation de paiement
                payment_method = st.selectbox(
                    "Choisissez votre méthode de paiement",
                    ["Orange Money", "Wave", "Carte bancaire"]
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Mensuel", use_container_width=True):
                        st.session_state['payment_plan'] = 'monthly'
                        st.session_state['show_payment_sim'] = True
                with col2:
                    if st.button("Annuel", use_container_width=True):
                        st.session_state['payment_plan'] = 'yearly'
                        st.session_state['show_payment_sim'] = True

                # Simulation de la fenêtre de paiement
                if st.session_state.get('show_payment_sim', False):
                    with st.form("payment_form"):
                        st.subheader("Simulation de paiement")
                        phone = st.text_input("Numéro de téléphone", placeholder="+223 XX XX XX XX")
                        if st.form_submit_button("Confirmer le paiement"):
                            # Ici, on appellerait une vraie API de paiement (Orange Money API, etc.)
                            st.success("✅ Paiement simulé avec succès !")
                            SubscriptionManager.activate_subscription(duration_days=30 if st.session_state['payment_plan'] == 'monthly' else 365)
                            st.session_state['show_payment_sim'] = False
                            st.rerun()