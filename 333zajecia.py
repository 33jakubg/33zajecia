import streamlit as st
import pandas as pd
from supabase import create_client, Client
from postgrest.exceptions import APIError

# --- Konfiguracja Supabase ---
# Upewnij się, że te dane są poprawne!
SUPABASE_URL = "https://egrgpcpgjvyeabotbars.supabase.co"
SUPABASE_KEY = "sb_publishable_8GmVc2u3elgCKQLX-glA1w_YBGJJvMO"

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Nie udało się połączyć z Supabase: {e}")
        return None

supabase = init_connection()

# --- Funkcje bazy danych z obsługą błędów ---

def get_magazyn():
    try:
        response = supabase.table("magazyn").select("*").execute()
        return response.data
    except Exception as e:
        # Zamiast błędu krytycznego, zwracamy pustą listę i komunikat
        st.sidebar.warning("Błąd bazy danych: Czy tabele zostały utworzone?")
        return []

def get_transakcje():
    try:
        response = supabase.table("transakcje_historia").select("*").order("data", desc=True).execute()
        return response.data
    except:
        return []

# --- Interfejs użytkownika ---
st.set_page_config(page_title="Mega Magazyn Supabase", layout="wide")
st.title("Mega Magazyn: System Chmurowy ☁️")

# Pobieranie danych
magazyn_data = get_magazyn()

# SPRAWDZENIE CZY TABELA ISTNIEJE
if not magazyn_data and not any(d.get('nazwa') for d in magazyn_data):
    st.info("💡 **Pierwsza konfiguracja?** Jeśli widzisz błędy, upewnij się, że wykonałeś poniższy kod w SQL Editorze na Supabase:")
    st.code("""
    CREATE TABLE IF NOT EXISTS magazyn (
        nazwa TEXT PRIMARY KEY,
        ilosc INTEGER DEFAULT 0,
        min_stan INTEGER DEFAULT 5
    );

    CREATE TABLE IF NOT EXISTS transakcje_historia (
        id SERIAL PRIMARY KEY,
        typ TEXT,
        towar TEXT REFERENCES magazyn(nazwa) ON DELETE CASCADE,
        ilosc INTEGER,
        data TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """, language="sql")

# --- Reszta logiki interfejsu (Tabs) ---
tab_magazyn, tab_transakcje = st.tabs(["📋 Stan Magazynu", "📜 Historia"])

with tab_magazyn:
    if magazyn_data:
        df = pd.DataFrame(magazyn_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Szybka operacja zmiany stanu (przykład)
        with st.expander("Dodaj nowy towar"):
            with st.form("nowy_towar"):
                n_nazwa = st.text_input("Nazwa")
                n_ilosc = st.number_input("Ilość", min_value=0)
                n_min = st.number_input("Minimum", min_value=0, value=5)
                if st.form_submit_button("Dodaj"):
                    try:
                        supabase.table("magazyn").insert({"nazwa": n_nazwa, "ilosc": n_ilosc, "min_stan": n_min}).execute()
                        st.success("Dodano!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd dodawania: {e}")
    else:
        st.warning("Brak danych w tabeli 'magazyn'.")

with tab_transakcje:
    trans_data = get_transakcje()
    if trans_data:
        st.dataframe(pd.DataFrame(trans_data), use_container_width=True)
    else:
        st.write("Brak historii transakcji.")
