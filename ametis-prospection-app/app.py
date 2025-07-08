# Ajoutez ces modifications à votre code existant

import streamlit as st
import requests
import os
import time
import json
import csv
from datetime import datetime, timezone, timedelta
from fpdf import FPDF

# Import SQLite3 avec vérification renforcée
try:
    import sqlite3
    # Test de fonctionnalité SQLite
    test_conn = sqlite3.connect(':memory:')
    test_conn.execute('CREATE TABLE test (id INTEGER)')
    test_conn.close()
    SQLITE_AVAILABLE = True
    print("✅ SQLite fonctionnel")
except Exception as e:
    SQLITE_AVAILABLE = False
    print(f"❌ SQLite non disponible: {e}")

# Configuration avec chemin absolu pour SQLite
if SQLITE_AVAILABLE:
    # Utiliser le répertoire de travail absolu
    WORK_DIR = os.getcwd()
    DB_FILE = os.path.join(WORK_DIR, "persistent_logs.db")
    print(f"📁 Chemin DB: {DB_FILE}")
else:
    DB_FILE = "persistent_logs.db"

USER_FILE = "users.json"
LOG_FILE = "global_log.json"

# Initialisation renforcée de SQLite
def init_database():
    """Initialise SQLite avec vérifications supplémentaires"""
    if not SQLITE_AVAILABLE:
        st.warning("⚠️ SQLite non disponible, utilisation du mode JSON")
        return False
    
    try:
        # Vérifier les permissions d'écriture
        test_file = os.path.join(os.path.dirname(DB_FILE), "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        # Créer/ouvrir la base avec options optimisées
        conn = sqlite3.connect(DB_FILE, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')  # Mode Write-Ahead Logging
        conn.execute('PRAGMA synchronous=NORMAL')  # Synchronisation normale
        conn.execute('PRAGMA temp_store=MEMORY')  # Stockage temp en mémoire
        
        cursor = conn.cursor()
        
        # Créer la table avec contraintes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                user TEXT NOT NULL,
                entreprise TEXT NOT NULL,
                secteur TEXT NOT NULL,
                mode TEXT NOT NULL,
                tokens INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Créer un index pour optimiser les requêtes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON global_logs(created_at DESC)
        ''')
        
        conn.commit()
        conn.close()
        
        st.success(f"✅ SQLite initialisé: {DB_FILE}")
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur SQLite: {e}")
        return False

# Fonction renforcée pour ajouter des logs
def add_log_entry(datetime_str, user, entreprise, secteur, mode, tokens):
    """Ajoute un log avec retry et vérification"""
    
    # Tentative SQLite avec retry
    if SQLITE_AVAILABLE:
        for attempt in range(3):  # 3 tentatives
            try:
                conn = sqlite3.connect(DB_FILE, timeout=30)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO global_logs (datetime, user, entreprise, secteur, mode, tokens)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (datetime_str, user, entreprise, secteur, mode, tokens))
                
                conn.commit()
                conn.close()
                
                # Vérification immédiate
                if verify_log_saved(datetime_str, user):
                    return True
                else:
                    st.warning(f"Tentative {attempt + 1}: Log non vérifié")
                    
            except Exception as e:
                st.warning(f"Tentative SQLite {attempt + 1} échouée: {e}")
                time.sleep(0.1)  # Petite pause avant retry
    
    # Fallback JSON avec sauvegarde renforcée
    return save_to_json_backup(datetime_str, user, entreprise, secteur, mode, tokens)

def verify_log_saved(datetime_str, user):
    """Vérifie qu'un log a bien été sauvegardé"""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM global_logs WHERE datetime = ? AND user = ?',
            (datetime_str, user)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except:
        return False

def save_to_json_backup(datetime_str, user, entreprise, secteur, mode, tokens):
    """Sauvegarde JSON avec horodatage multiple"""
    try:
        log_entry = {
            "datetime": datetime_str,
            "user": user,
            "entreprise": entreprise,
            "secteur": secteur,
            "mode": mode,
            "tokens": tokens,
            "backup_timestamp": time.time()
        }
        
        # Sauvegarde principale
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        # Sauvegarder avec rotation
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs[-200:], f, indent=2)  # Garder 200 entrées
        
        # Sauvegarde secondaire avec timestamp
        backup_file = f"backup_logs_{datetime.now().strftime('%Y%m')}.json"
        try:
            if os.path.exists(backup_file):
                with open(backup_file, "r", encoding="utf-8") as f:
                    backup_logs = json.load(f)
            else:
                backup_logs = []
            
            backup_logs.append(log_entry)
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_logs[-500:], f, indent=2)  # Garder 500 entrées
        except:
            pass  # Sauvegarde secondaire non critique
        
        return True
        
    except Exception as e:
        st.error(f"Erreur sauvegarde JSON: {e}")
        return False

# Fonction améliorée pour récupérer les logs
def get_logs(limit=100):
    """Récupère les logs avec agrégation SQLite + JSON"""
    all_logs = []
    
    # Récupération SQLite
    if SQLITE_AVAILABLE:
        try:
            conn = sqlite3.connect(DB_FILE, timeout=10)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT datetime, user, entreprise, secteur, mode, tokens
                FROM global_logs
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            sqlite_logs = cursor.fetchall()
            conn.close()
            
            all_logs.extend([
                {
                    "datetime": log[0],
                    "user": log[1],
                    "entreprise": log[2],
                    "secteur": log[3],
                    "mode": log[4],
                    "tokens": log[5],
                    "source": "SQLite"
                }
                for log in sqlite_logs
            ])
            
        except Exception as e:
            st.warning(f"Erreur lecture SQLite: {e}")
    
    # Récupération JSON (complément)
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                json_logs = json.load(f)
            
            # Ajouter les logs JSON qui ne sont pas déjà dans SQLite
            for log in json_logs:
                log["source"] = "JSON"
                # Éviter les doublons basés sur datetime + user
                if not any(l["datetime"] == log["datetime"] and l["user"] == log["user"] for l in all_logs):
                    all_logs.append(log)
    except:
        pass
    
    # Trier par date et limiter
    all_logs.sort(key=lambda x: x["datetime"], reverse=True)
    return all_logs[:limit]

# Test de persistance au démarrage
def test_persistence():
    """Test la persistance des données"""
    if not SQLITE_AVAILABLE:
        return "JSON seulement"
    
    try:
        # Ajouter un log de test
        test_time = datetime.now().isoformat()
        add_log_entry(test_time, "test_user", "test_entreprise", "test_secteur", "test", 0)
        
        # Vérifier immédiatement
        logs = get_logs(1)
        if logs and logs[0]["datetime"] == test_time:
            # Nettoyer le test
            conn = sqlite3.connect(DB_FILE)
            conn.execute("DELETE FROM global_logs WHERE user = 'test_user'")
            conn.commit()
            conn.close()
            return "SQLite persistant ✅"
        else:
            return "SQLite problématique ⚠️"
    except:
        return "SQLite erreur ❌"

# Initialisation avec test
sqlite_initialized = init_database()
persistence_status = test_persistence()

# Affichage du statut dans l'interface
if sqlite_initialized:
    st.sidebar.success(f"🗄️ Base: {persistence_status}")
else:
    st.sidebar.warning("📁 Mode JSON uniquement")

# Dans la section admin, ajoutez ces diagnostics :
def admin_diagnostics():
    """Diagnostics détaillés pour admin"""
    st.markdown("### 🔧 Diagnostics Système")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Statut SQLite:**")
        st.write(f"- Disponible: {SQLITE_AVAILABLE}")
        st.write(f"- Fichier DB: {DB_FILE}")
        st.write(f"- Existe: {os.path.exists(DB_FILE) if SQLITE_AVAILABLE else 'N/A'}")
        
        if SQLITE_AVAILABLE and os.path.exists(DB_FILE):
            try:
                size = os.path.getsize(DB_FILE)
                st.write(f"- Taille: {size} bytes")
            except:
                st.write("- Taille: Erreur lecture")
    
    with col2:
        st.write("**Statut JSON:**")
        st.write(f"- Fichier: {LOG_FILE}")
        st.write(f"- Existe: {os.path.exists(LOG_FILE)}")
        
        if os.path.exists(LOG_FILE):
            try:
                size = os.path.getsize(LOG_FILE)
                st.write(f"- Taille: {size} bytes")
            except:
                st.write("- Taille: Erreur lecture")
    
    # Test de persistance en temps réel
    if st.button("🧪 Tester la persistance"):
        test_result = test_persistence()
        st.info(f"Résultat test: {test_result}")

# Configuration forcée pour Streamlit Cloud
FORCE_SQLITE_MODE = True  # Changez en False si vous voulez désactiver
SQLITE_TIMEOUT = 30

if FORCE_SQLITE_MODE:
    st.sidebar.info("🔧 Mode SQLite forcé pour Streamlit Cloud")
    
# Vérification des secrets Streamlit
try:
    if hasattr(st, 'secrets') and 'FORCE_SQLITE' in st.secrets:
        FORCE_SQLITE_MODE = st.secrets['FORCE_SQLITE'].lower() == 'true'
        st.sidebar.success("✅ Configuration via secrets Streamlit")
except:
    pass
