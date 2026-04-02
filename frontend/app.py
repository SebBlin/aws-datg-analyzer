        report += "---\n*Généré par AWS DATG Analyzer*\n"
        return report
    
    def render_history_tab(self):
        """Onglet d'historique des analyses."""
        st.markdown('<h1 class="main-header">📜 Historique des Analyses</h1>', unsafe_allow_html=True)
        
        # Charger l'historique depuis le backend
        try:
            response = requests.get(f"{BACKEND_URL}/analyses", timeout=10)
            if response.status_code == 200:
                history = response.json()
            else:
                history = self.session_state.analysis_history
        except:
            history = self.session_state.analysis_history
        
        if not history:
            st.info("📭 Aucune analyse dans l'historique.")
            return
        
        # Tableau d'historique
        df = pd.DataFrame(history)
        if not df.empty:
            # Formater les dates
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['Date'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
            
            # Afficher le tableau
            columns_to_show = ['Date', 'filename', 'llm_provider']
            if 'overall_score' in df.columns:
                columns_to_show.append('overall_score')
            
            st.dataframe(
                df[columns_to_show].rename(columns={
                    'filename': 'Fichier',
                    'llm_provider': 'LLM',
                    'overall_score': 'Score'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Graphique des scores historiques
            if 'overall_score' in df.columns and 'created_at' in df.columns:
                st.subheader("Évolution des Scores")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['created_at'],
                    y=df['overall_score'],
                    mode='lines+markers',
                    name='Score',
                    line=dict(color='#FF9900', width=2),
                    marker=dict(size=8)
                ))
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Score",
                    yaxis_range=[0, 100],
                    height=300,
                    margin=dict(l=50, r=50, t=30, b=50)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Bouton pour vider l'historique
        if st.button("🗑️ Vider l'historique local", type="secondary"):
            self.session_state.analysis_history = []
            st.rerun()
    
    def render_config_tab(self):
        """Onglet de configuration."""
        st.markdown('<h1 class="main-header">⚙️ Configuration</h1>', unsafe_allow_html=True)
        
        with st.form("config_form"):
            st.subheader("Configuration Backend")
            backend_url = st.text_input(
                "URL du Backend",
                value=BACKEND_URL,
                help="URL de l'API FastAPI (ex: http://localhost:8000)"
            )
            
            st.subheader("Configuration LLM")
            llm_config_col1, llm_config_col2 = st.columns(2)
            
            with llm_config_col1:
                openai_key = st.text_input(
                    "Clé API OpenAI",
                    type="password",
                    help="sk-..."
                )
            
            with llm_config_col2:
                anthropic_key = st.text_input(
                    "Clé API Anthropic",
                    type="password",
                    help="sk-ant-..."
                )
            
            st.subheader("Configuration AWS (optionnel)")
            aws_access_key = st.text_input("AWS Access Key ID", type="password")
            aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
            aws_region = st.selectbox(
                "Région AWS",
                ["eu-west-1", "eu-west-3", "us-east-1", "us-west-2"],
                index=0
            )
            
            submitted = st.form_submit_button("💾 Sauvegarder la configuration", use_container_width=True)
            
            if submitted:
                # Ici, normalement on sauvegarderait dans un fichier .env
                st.success("✅ Configuration sauvegardée (démonstration)")
                st.info("Note: En production, stockez les secrets dans des variables d'environnement sécurisées.")
    
    def render_about_tab(self):
        """Onglet À propos."""
        st.markdown('<h1 class="main-header">ℹ️ À propos</h1>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image("https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg", width=200)
        
        with col2:
            st.markdown("""
            ### AWS DATG Analyzer
            Version 1.0.0
            
            Une application IA pour analyser les Documents d'Architecture Technique Général (DATG) AWS
            et évaluer leur conformité aux bonnes pratiques du Well-Architected Framework.
            
            **Fonctionnalités:**
            - 📄 Analyse de documents PDF, DOCX, TXT, Markdown
            - 🤖 Évaluation par IA (OpenAI, Anthropic, Ollama)
            - 📊 Scores détaillés sur les 5 piliers AWS
            - ⚠️ Identification des risques et recommandations
            - 📈 Historique et rapports exportables
            
            **Technologies utilisées:**
            - Backend: FastAPI (Python)
            - Frontend: Streamlit
            - LLM: OpenAI GPT-4, Anthropic Claude, Ollama
            - Base de données: PostgreSQL/SQLite
            
            **Développé par:** [SebBlin](https://github.com/SebBlin)
            """)
        
        st.markdown("---")
        
        # Documentation
        with st.expander("📚 Documentation"):
            st.markdown("""
            ### Guide d'utilisation
            
            1. **Uploader un document**
               - Allez dans l'onglet "Analyse"
               - Sélectionnez un fichier (PDF, DOCX, TXT, MD)
               - Choisissez le fournisseur LLM
               - Cliquez sur "Analyser"
            
            2. **Interpréter les résultats**
               - **Score global:** 0-100 (plus haut = meilleur)
               - **Scores par pilier:** Détails sur chaque aspect
               - **Risques:** Problèmes identifiés (critique → faible)
               - **Recommandations:** Actions d'amélioration
            
            3. **Exporter les résultats**
               - JSON: Données brutes
               - PDF: Rapport formaté (en développement)
               - Markdown: Rapport texte
            
            ### Bonnes pratiques AWS évaluées
            
            L'application évalue l'architecture sur les 5 piliers du Well-Architected Framework:
            
            1. **Excellence opérationnelle**
               - Monitoring et logging
               - CI/CD automatisé
               - Gestion des changements
            
            2. **Sécurité**
               - IAM (least privilege)
               - Chiffrement des données
               - Sécurité réseau
            
            3. **Fiabilité**
               - Haute disponibilité (multi-AZ)
               - Backup et recovery
               - Auto-scaling
            
            4. **Performance**
               - Optimisation des ressources
               - Mise en cache
               - Scaling horizontal
            
            5. **Optimisation des coûts**
               - Réservations d'instances
               - Monitoring des coûts
               - Cleanup des ressources
            """)
        
        # Statut
        with st.expander("🔧 Statut du système"):
            try:
                health = requests.get(f"{BACKEND_URL}/health", timeout=5)
                if health.status_code == 200:
                    st.success("✅ Backend: Connecté")
                    st.json(health.json())
                else:
                    st.error(f"❌ Backend: Erreur {health.status_code}")
            except Exception as e:
                st.error(f"❌ Backend: {str(e)}")

def main():
    """Fonction principale."""
    app = DATGAnalyzerApp()
    app.run()

if __name__ == "__main__":
    main()