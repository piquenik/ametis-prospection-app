with st.expander("🧪 Test direct de l’API DeepSeek"):
    test_prompt = st.text_area("Prompt de test", "Donne-moi un résumé de l'entreprise ACTIBIO 53 dans le secteur agroalimentaire.")
    endpoint_to_test = st.selectbox("Endpoint à tester", API_ENDPOINTS)
    
    if st.button("Lancer le test réel"):
        headers = {
            "Authorization": f"Bearer {sk-844f7121c69e471da4933807b23a1b01}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": test_prompt}],
            "temperature": 0.7,
            "max_tokens": 500
        }

        try:
            start = time.time()
            response = requests.post(endpoint_to_test, headers=headers, json=payload, timeout=15)
            duration = time.time() - start

            st.write(f"⏱ Temps de réponse : {duration:.2f} secondes")
            st.write(f"📡 Code HTTP : {response.status_code}")

            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                st.success("Réponse reçue :")
                st.markdown(f"```markdown\n{content}\n```")
            else:
                st.error(f"Erreur HTTP : {response.status_code}")
                st.code(response.text[:1000])

        except Exception as e:
            st.error(f"Exception levée : {str(e)}")
