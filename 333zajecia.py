import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Konfiguracja Supabase ---
SUPABASE_URL = "https://egrgpcpgjvyeabotbars.supabase.co"
SUPABASE_KEY = "sb_publishable_8GmVc2u3elgCKQLX-glA1w_YBGJJvMO"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- Funkcje bazy danych ---

def pobierz_stan_magazynu():
    try:
        response = supabase.table("magazyn").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Błąd tabeli 'magazyn': {e}")
        return []

def pobierz_historie():
    try:
        # Próba 1: Pobranie z sortowaniem po 'created_at' (standard Supabase)
        response = supabase.table("transakcje").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception:
        try:
            # Próba 2: Pobranie bez sortowania (jeśli kolumna czasu nie istnieje)
            response = supabase.table("transakcje").select("*").execute()
            return response.data
        except Exception as e:
            # Próba 3: Wyświetlenie konkretnego błędu, jeśli tabela w ogóle nie działa
            st.error(f"Nie udało się pobrać historii. Sprawdź czy tabela 'transakcje' istnieje w Supabase. Szczegóły: {e}")
            return []

def rejestruj_transakcje(typ, nazwa, ilosc):
    data = {
        "typ": str(typ),
        "towar": str(nazwa),
        "ilosc": int(ilosc)
    }
    try:
        supabase.table("transakcje").insert(data).execute()
    except Exception as e:
        st.error(f"Błąd podczas zapisywania transakcji: {e}")

def dodaj_nowy_towar(nazwa, ilosc, min_stan):
    nazwa = nazwa.strip().capitalize()
    if not nazwa:
        st.error("Nazwa nie może być pusta.")
        return
    try:
        data = {"nazwa": nazwa, "ilosc": int(ilosc), "min_stan": int(min_stan)}
        supabase.table("magazyn").insert(data).execute()
        rejestruj_transakcje("Przyjęcie (Nowy)", nazwa, ilosc)
        st.success(f"Dodano nowy towar: **{nazwa}**")
    except Exception as e:
        st.error(f"Błąd: Towar prawdopodobnie już istnieje lub brak uprawnień. ({e})")

def aktualizuj_stan(nazwa, ilosc_zmiany, operacja):
    try:
        res = supabase.table("magazyn").select("ilosc, min_stan").eq("nazwa", nazwa).single().execute()
        if not res.data:
            st.error("Nie znaleziono towaru.")
            return

        obecna_ilosc = res.data['ilosc']
        min_stan = res.data['min_stan']
        nowa_ilosc = obecna_ilosc + ilosc_zmiany if operacja == "Przyjęcie" else obecna_ilosc - ilosc_zmiany

        if operacja == "Wydanie" and obecna_ilosc < ilosc_zmiany:
            st.error("Zbyt mała ilość w magazynie!")
            return

        supabase.table("magazyn").update({"ilosc": nowa_ilosc}).eq("nazwa", nazwa).execute()
        rejestruj_transakcje(operacja, nazwa, ilosc_zmiany)
        st.success(f"Zaktualizowano {nazwa}. Nowy stan: {nowa_ilosc}")
    except Exception as e:
        st.error(f"Błąd aktualizacji: {e}")

# --- Interfejs Streamlit ---
st.set_page_config(page_title="Magazyn Supabase", layout="wide")
st.title("Mega Magazyn: Integracja z Supabase")

tab_magazyn, tab_transakcje, tab_ustawienia = st.tabs(["📋 Stan Magazynu", "📜 Historia Transakcji", "⚙️ Ustawienia"])

with tab_magazyn:
    dane = pobierz_stan_magazynu()
    if dane:
        df = pd.DataFrame(dane)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        with col1:
            with st.form("nowy_produkt"):
                n_nazwa = st.text_input("Nazwa")
                n_ilosc = st.number_input("Ilość", min_value=0)
                n_min = st.number_input("Minimum", min_value=0, value=5)
                if st.form_submit_button("Dodaj"):
                    dodaj_nowy_towar(n_nazwa, n_ilosc, n_min)
                    st.rerun()
        with col2:
            lista = [item['nazwa'] for item in dane]
            o_towar = st.selectbox("Wybierz produkt", lista)
            o_ilosc = st.number_input("Ilość zmiany", min_value=1)
            o_typ = st.radio("Typ", ["Przyjęcie", "Wydanie"])
            if st.button("Wykonaj operację"):
                aktualizuj_stan(o_towar, o_ilosc, o_typ)
                st.rerun()
    else:
        st.warning("Baza danych jest pusta lub niedostępna.")
        if st.button("Spróbuj dodać pierwszy towar"):
            dodaj_nowy_towar("Testowy Produkt", 10, 5)
            st.rerun()

with tab_transakcje:
    historia = pobierz_historie()
    if historia:
        st.dataframe(pd.DataFrame(historia), use_container_width=True)
    else:
        st.info("Brak zarejestrowanych transakcji.")

with tab_ustawienia:
    if st.button("Wyczyść wszystko", type="primary"):
        supabase.table("magazyn").delete().neq("nazwa", "").execute()
        supabase.table("transakcje").delete().neq("typ", "").execute()
        st.rerun()
