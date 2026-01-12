import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Konfiguracja Supabase ---
# Pobierz te dane z: Settings -> API w panelu Supabase
SUPABASE_URL = "https://egrgpcpgjvyeabotbars.supabase.co"
SUPABASE_KEY = "b_publishable_8GmVc2u3elgCKQLX-glA1w_YBGJJvMO"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- Konfiguracja aplikacji ---
st.set_page_config(page_title="Mega Magazyn Supabase", layout="wide")
st.title("Mega Magazyn: Cloud Edition ☁️")

# --- Funkcje bazy danych ---

def get_magazyn():
    response = supabase.table("magazyn").select("*").execute()
    return response.data

def get_transakcje():
    response = supabase.table("transakcje_historia").select("*").order("data", desc=True).execute()
    return response.data

def rejestruj_transakcje(typ, nazwa, ilosc):
    supabase.table("transakcje_historia").insert({
        "typ": typ,
        "towar": nazwa,
        "ilosc": ilosc
    }).execute()

def dodaj_nowy_towar(nazwa, ilosc, min_stan):
    nazwa = nazwa.strip().capitalize()
    if not nazwa:
        st.error("Nazwa nie może być pusta.")
        return

    # Próba dodania towaru
    try:
        supabase.table("magazyn").insert({
            "nazwa": nazwa,
            "ilosc": ilosc,
            "min_stan": min_stan
        }).execute()
        
        rejestruj_transakcje("Przyjęcie (Nowy)", nazwa, ilosc)
        st.success(f"Dodano nowy towar: **{nazwa}**")
        st.rerun()
    except Exception:
        st.error("Błąd: Towar o tej nazwie prawdopodobnie już istnieje.")

def przyjmij_wydaj_towar(nazwa, ilosc_zmiany, operacja, obecna_ilosc):
    if operacja == "Przyjęcie":
        nowa_ilosc = obecna_ilosc + ilosc_zmiany
    else:
        if obecna_ilosc < ilosc_zmiany:
            st.error("Brak wystarczającej ilości w magazynie!")
            return
        nowa_ilosc = obecna_ilosc - ilosc_zmiany

    # Aktualizacja bazy
    supabase.table("magazyn").update({"ilosc": nowa_ilosc}).eq("nazwa", nazwa).execute()
    rejestruj_transakcje(operacja, nazwa, ilosc_zmiany)
    st.success(f"Zaktualizowano {nazwa}. Nowy stan: {nowa_ilosc}")
    st.rerun()

# --- Interfejs użytkownika ---

tab_magazyn, tab_transakcje, tab_ustawienia = st.tabs(["📋 Stan Magazynu", "📜 Historia", "⚙️ Zarządzanie"])

# Pobieranie aktualnych danych
magazyn_data = get_magazyn()

with tab_magazyn:
    if magazyn_data:
        df = pd.DataFrame(magazyn_data)
        # Logika alertów
        niskie_stany = df[df['ilosc'] < df['min_stan']]
        if not niskie_stany.empty:
            st.error(f"⚠️ Uwaga! {len(niskie_stany)} towarów wymaga uzupełnienia.")
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Magazyn jest pusty.")

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Dodaj nowy towar")
        with st.form("nowy_towar"):
            n_nazwa = st.text_input("Nazwa")
            n_ilosc = st.number_input("Ilość", min_value=0, value=0)
            n_min = st.number_input("Minimum", min_value=0, value=5)
            if st.form_submit_button("Zatwierdź"):
                dodaj_nowy_towar(n_nazwa, n_ilosc, n_min)

    with col2:
        st.subheader("Ruch towaru")
        if magazyn_data:
            with st.form("ruch_towaru"):
                op_towar = st.selectbox("Wybierz towar", [x['nazwa'] for x in magazyn_data])
                op_ilosc = st.number_input("Ilość zmiany", min_value=1, value=1)
                op_typ = st.radio("Typ", ["Przyjęcie", "Wydanie"])
                
                # Pobranie aktualnej ilości dla wybranego towaru
                aktualna = next(item['ilosc'] for item in magazyn_data if item['nazwa'] == op_towar)
                
                if st.form_submit_button("Wykonaj"):
                    przyjmij_wydaj_towar(op_towar, op_ilosc, op_typ, aktualna)

with tab_transakcje:
    transakcje_data = get_transakcje()
    if transakcje_data:
        st.dataframe(pd.DataFrame(transakcje_data), use_container_width=True)
    else:
        st.info("Brak historii.")

with tab_ustawienia:
    if st.button("USUŃ WSZYSTKIE DANE", type="primary"):
        # Supabase CASCADE usunie też historię jeśli tak ustawiono w SQL
        supabase.table("magazyn").delete().neq("nazwa", "dummy_value_to_trigger_all").execute()
        st.success("Wyczyszczono bazę danych.")
        st.rerun()
