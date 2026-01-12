import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Konfiguracja Supabase ---
# Wprowadź swoje dane z ustawień projektu Supabase (Settings -> API)
SUPABASE_URL = "https://egrgpcpgjvyeabotbars.supabase.co"
SUPABASE_KEY = "sb_publishable_8GmVc2u3elgCKQLX-glA1w_YBGJJvMO"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- Konfiguracja aplikacji ---
st.set_page_config(page_title="Magazyn Supabase", layout="wide")
st.title("Mega Magazyn: Integracja z Supabase")

# --- Funkcje bazy danych (Logic) ---

def pobierz_stan_magazynu():
    response = supabase.table("magazyn").select("*").execute()
    return response.data

def pobierz_historie():
    response = supabase.table("transakcje").select("*").order("data", desc=True).execute()
    return response.data

def rejestruj_transakcje(typ, nazwa, ilosc):
    data = {
        "typ": typ,
        "towar": nazwa,
        "ilosc": ilosc
    }
    supabase.table("transakcje").insert(data).execute()

def dodaj_nowy_towar(nazwa, ilosc, min_stan):
    nazwa = nazwa.strip().capitalize()
    if not nazwa:
        st.error("Nazwa nie może być pusta.")
        return

    # Próba dodania do tabeli magazyn
    try:
        data = {"nazwa": nazwa, "ilosc": int(ilosc), "min_stan": int(min_stan)}
        supabase.table("magazyn").insert(data).execute()
        rejestruj_transakcje("Przyjęcie (Nowy)", nazwa, ilosc)
        st.success(f"Dodano nowy towar: **{nazwa}**")
    except Exception as e:
        st.error(f"Błąd: Prawdopodobnie towar już istnieje. ({e})")

def aktualizuj_stan(nazwa, ilosc_zmiany, operacja):
    # Pobierz aktualny stan z bazy
    res = supabase.table("magazyn").select("ilosc, min_stan").eq("nazwa", nazwa).single().execute()
    obecna_ilosc = res.data['ilosc']
    min_stan = res.data['min_stan']

    if operacja == "Przyjęcie":
        nowa_ilosc = obecna_ilosc + ilosc_zmiany
    else: # Wydanie
        if obecna_ilosc < ilosc_zmiany:
            st.error(f"Błąd! Zbyt mała ilość w magazynie ({obecna_ilosc}).")
            return
        nowa_ilosc = obecna_ilosc - ilosc_zmiany

    # Update w Supabase
    supabase.table("magazyn").update({"ilosc": nowa_ilosc}).eq("nazwa", nazwa).execute()
    rejestruj_transakcje(operacja, nazwa, ilosc_zmiany)
    
    st.success(f"Zaktualizowano {nazwa}. Nowy stan: {nowa_ilosc}")
    if nowa_ilosc < min_stan:
        st.warning(f"🚨 Niski stan towaru {nazwa}!")

# --- Interfejs użytkownika ---

tab_magazyn, tab_transakcje, tab_ustawienia = st.tabs(["📋 Stan Magazynu", "📜 Historia Transakcji", "⚙️ Ustawienia"])

with tab_magazyn:
    st.header("Aktualny stan z bazy danych")
    dane_magazynu = pobierz_stan_magazynu()
    
    if dane_magazynu:
        df = pd.DataFrame(dane_magazynu)
        # Logika alertów
        niskie_stany = df[df['ilosc'] < df['min_stan']]
        if not niskie_stany.empty:
            st.error(f"⚠️ Uwaga! {len(niskie_stany)} produktów wymaga uzupełnienia.")
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Magazyn jest pusty.")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🆕 Nowy produkt")
        with st.form("dodaj_form", clear_on_submit=True):
            n_nazwa = st.text_input("Nazwa")
            n_ilosc = st.number_input("Ilość", min_value=0, value=0)
            n_min = st.number_input("Minimum", min_value=0, value=5)
            if st.form_submit_button("Zapisz w Supabase"):
                dodaj_nowy_towar(n_nazwa, n_ilosc, n_min)
                st.rerun()

    with col2:
        st.subheader("🔄 Operacja")
        if dane_magazynu:
            lista_towarow = [item['nazwa'] for item in dane_magazynu]
            o_towar = st.selectbox("Produkt", lista_towarow)
            o_ilosc = st.number_input("Ilość zmiany", min_value=1, value=1)
            o_typ = st.radio("Typ", ["Przyjęcie", "Wydanie"])
            if st.button("Wykonaj"):
                aktualizuj_stan(o_towar, o_ilosc, o_typ)
                st.rerun()

with tab_transakcje:
    st.header("Historia operacji (Live z Supabase)")
    historia = pobierz_historie()
    if historia:
        st.dataframe(pd.DataFrame(historia), use_container_width=True)

with tab_ustawienia:
    if st.button("Usuń całą zawartość magazynu (Danger Zone)", type="primary"):
        # Supabase wymaga filtru przy delete, .neq("nazwa", "") zazwyczaj usuwa wszystko
        supabase.table("magazyn").delete().neq("nazwa", "").execute()
        supabase.table("transakcje").delete().neq("typ", "").execute()
        st.success("Wyczyszczono bazę danych.")
        st.rerun()
