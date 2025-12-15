import streamlit as st
import pandas as pd
from datetime import datetime

# --- Konfiguracja aplikacji ---
st.set_page_config(page_title="Pełny System Magazynowy", layout="wide")
st.title("Mega Magazyn: Śledzenie, Transakcje i Alarmy")

# 1. Inicjalizacja stanu sesji
if 'magazyn' not in st.session_state:
    # Struktura: {nazwa_towaru: {'ilosc': int, 'min_stan': int, 'transakcje': list}}
    st.session_state.magazyn = {}
if 'transakcje_historia' not in st.session_state:
    # Globalna historia transakcji: [{'typ': 'Przyjęcie/Wydanie', 'towar': nazwa, 'ilosc': int, 'data': datetime}]
    st.session_state.transakcje_historia = []


# --- Funkcje logiki biznesowej ---

def rejestruj_transakcje(typ, nazwa, ilosc):
    """Rejestruje transakcję w historii."""
    st.session_state.transakcje_historia.append({
        'typ': typ,
        'towar': nazwa,
        'ilosc': ilosc,
        'data': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def dodaj_nowy_towar(nazwa, ilosc, min_stan):
    """Dodaje nowy towar z ilością i stanem minimalnym."""
    nazwa = nazwa.strip().capitalize()
    
    if not nazwa or nazwa in st.session_state.magazyn:
        st.error("Nazwa jest pusta lub towar już istnieje.")
        return

    st.session_state.magazyn[nazwa] = {
        'ilosc': int(ilosc),
        'min_stan': int(min_stan),
    }
    rejestruj_transakcje("Przyjęcie (Nowy)", nazwa, ilosc)
    st.success(f"Dodano nowy towar: **{nazwa}** w ilości {ilosc} sztuk. Min. stan: {min_stan}")

def przyjmij_wydaj_towar(nazwa, ilosc_zmiany, operacja):
    """Realizuje operację przyjęcia (dodania) lub wydania (odjęcia)."""
    if nazwa not in st.session_state.magazyn:
        st.error(f"Towar **{nazwa}** nie istnieje.")
        return

    obecna_ilosc = st.session_state.magazyn[nazwa]['ilosc']
    
    if operacja == "Przyjęcie":
        nowa_ilosc = obecna_ilosc + ilosc_zmiany
        rejestruj_transakcje("Przyjęcie", nazwa, ilosc_zmiany)
        st.session_state.magazyn[nazwa]['ilosc'] = nowa_ilosc
        st.success(f"Przyjęto {ilosc_zmiany} szt. **{nazwa}**. Nowy stan: {nowa_ilosc}")
        
    elif operacja == "Wydanie":
        if obecna_ilosc < ilosc_zmiany:
            st.error(f"Błąd! Nie można wydać {ilosc_zmiany} szt. Dostępne: {obecna_ilosc}")
            return
            
        nowa_ilosc = obecna_ilosc - ilosc_zmiany
        rejestruj_transakcje("Wydanie", nazwa, ilosc_zmiany)
        st.session_state.magazyn[nazwa]['ilosc'] = nowa_ilosc
        st.success(f"Wydano {ilosc_zmiany} szt. **{nazwa}**. Nowy stan: {nowa_ilosc}")

        if nowa_ilosc < st.session_state.magazyn[nazwa]['min_stan']:
            st.warning(f"🚨 **UWAGA NISKI STAN!** Towar **{nazwa}** jest poniżej stanu minimalnego ({st.session_state.magazyn[nazwa]['min_stan']}).")


# --- Interfejs użytkownika Streamlit ---

tab_magazyn, tab_transakcje, tab_ustawienia = st.tabs(["📋 Stan Magazynu", "📜 Historia Transakcji", "⚙️ Ustawienia i Narzędzia"])

# --- TABELA STANU MAGAZYNU ---
with tab_magazyn:
    st.header("Stan Magazynu i Transakcje")
    
    # Przetwarzanie danych do wyświetlenia
    data_list = []
    towary_niskostanowe = 0
    
    for nazwa, dane in st.session_state.magazyn.items():
        data_list.append({
            'Nazwa Towaru': nazwa,
            'Ilość w Magazynie': dane['ilosc'],
            'Stan Minimalny': dane['min_stan'],
            'Niski Stan?': 'TAK 🔴' if dane['ilosc'] < dane['min_stan'] else 'NIE 🟢'
        })
        if dane['ilosc'] < dane['min_stan']:
            towary_niskostanowe += 1

    if data_list:
        df = pd.DataFrame(data_list)
        df = df.sort_values(by='Nazwa Towaru')

        # Wyświetlanie alertu o niskim stanie
        if towary_niskostanowe > 0:
            st.error(f"⚠️ **{towary_niskostanowe}** towarów jest poniżej stanu minimalnego! Sprawdź tabelę.")

        # Wyszukiwanie/Filtrowanie
        search_term = st.text_input("Filtruj towary po nazwie:", "", key="search_magazyn").strip()

        if search_term:
            df = df[df['Nazwa Towaru'].str.contains(search_term, case=False)]
            
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("Magazyn jest pusty. Użyj sekcji Transakcje, aby dodać towary.")

    st.markdown("---")
    
    # Panel Dodawania / Transakcji
    st.subheader("Operacje Magazynowe (Przyjęcie/Wydanie)")
    
    col_op_1, col_op_2 = st.columns(2)
    
    with col_op_1:
        st.markdown("##### 🆕 Dodaj NOWY Towar")
        with st.form("form_dodaj_nowy"):
            n_nazwa = st.text_input("Nazwa Towaru:", key="n_nazwa").strip()
            n_ilosc = st.number_input("Ilość Początkowa:", min_value=1, step=1, value=1)
            n_min_stan = st.number_input("Stan Minimalny (alarm):", min_value=1, step=1, value=5)
            if st.form_submit_button("Dodaj Nowy Towar do Magazynu"):
                dodaj_nowy_towar(n_nazwa, n_ilosc, n_min_stan)
                
    with col_op_2:
        st.markdown("##### 🔄 Przyjęcie / Wydanie (Istniejące)")
        if st.session_state.magazyn:
            towary_list = sorted(list(st.session_state.magazyn.keys()))
            op_towar = st.selectbox("Wybierz Towar:", towary_list, key="op_towar")
            op_ilosc = st.number_input("Ilość Zmiany:", min_value=1, step=1, value=1)
            op_typ = st.radio("Typ Operacji:", ["Przyjęcie", "Wydanie"])
            
            if st.button(f"Wykonaj Operację: {op_typ}"):
                przyjmij_wydaj_towar(op_towar, op_ilosc, op_typ)
        else:
            st.info("Brak towarów do operacji. Dodaj towar w panelu obok.")


# --- TABELA HISTORII TRANSAKCJI ---
with tab_transakcje:
    st.header("📜 Rejestr Transakcji")
    
    if st.session_state.transakcje_historia:
        df_transakcje = pd.DataFrame(st.session_state.transakcje_historia)
        
        st.dataframe(
            df_transakcje.sort_values(by='data', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Brak zarejestrowanych transakcji.")

# --- NARZĘDZIA I USTAWIENIA ---
with tab_ustawienia:
    st.header("⚙️ Narzędzia Magazynowe")
    
    st.subheader("Resetowanie Danych")
    st.warning("Ta operacja usunie **wszystkie dane** z magazynu i historię transakcji. Jest nieodwracalna.")
    
    if st.button("Wyczyść Cały Magazyn i Historię", type="primary"):
        st.session_state.magazyn = {}
        st.session_state.transakcje_historia = []
        st.success("Magazyn został pomyślnie zresetowany!")
        st.experimental_rerun() # Odświeżenie aplikacji, aby zmiany były widoczne natychmiast
