import streamlit as st
import pandas as pd # Dodajemy Pandas dla lepszego wyświetlania tabel

# --- Konfiguracja aplikacji ---
st.set_page_config(page_title="Zaawansowany Magazyn", layout="wide")
st.title("🏭 Zaawansowany System Magazynowy")
st.caption("Przechowuje nazwy i ilości, z możliwością modyfikacji i filtrowania.")

# 1. Inicjalizacja stanu sesji (słownik towarów: {nazwa: ilosc})
if 'magazyn' not in st.session_state:
    # Słownik jest lepszy niż lista, gdy potrzebujemy par klucz-wartość (nazwa: ilość)
    st.session_state.magazyn = {}

# --- Funkcje logiki biznesowej ---

def dodaj_lub_zaktualizuj_towar(nazwa, ilosc):
    """Dodaje nowy towar lub zwiększa/aktualizuje jego ilość."""
    nazwa = nazwa.strip().capitalize()
    
    if not nazwa:
        st.error("Nazwa towaru nie może być pusta.")
        return

    try:
        ilosc = int(ilosc)
        if ilosc <= 0:
            st.warning("Ilość musi być liczbą całkowitą większą niż 0.")
            return
            
        if nazwa in st.session_state.magazyn:
            st.session_state.magazyn[nazwa] += ilosc
            st.success(f"Zwiększono stan towaru **{nazwa}** o {ilosc} sztuk.")
        else:
            st.session_state.magazyn[nazwa] = ilosc
            st.success(f"Dodano nowy towar: **{nazwa}** w ilości {ilosc} sztuk.")
            
    except ValueError:
        st.error("Ilość musi być poprawną liczbą całkowitą.")

def usun_towar_calkowicie(nazwa):
    """Usuwa towar całkowicie z magazynu."""
    if nazwa in st.session_state.magazyn:
        del st.session_state.magazyn[nazwa]
        st.success(f"Towar **{nazwa}** został usunięty z magazynu.")
    else:
        st.warning(f"Towar **{nazwa}** nie znaleziono.")

def modyfikuj_ilosc(nazwa, zmiana):
    """Zwiększa lub zmniejsza ilość istniejącego towaru."""
    if nazwa not in st.session_state.magazyn:
        st.error(f"Towar **{nazwa}** nie istnieje w magazynie.")
        return

    nowa_ilosc = st.session_state.magazyn[nazwa] + zmiana

    if nowa_ilosc < 0:
        st.warning(f"Nie można zmniejszyć ilości poniżej 0. Aktualny stan: {st.session_state.magazyn[nazwa]}")
        return
    elif nowa_ilosc == 0:
        # Pytanie, czy usunąć, jeśli zejdzie do zera. Na razie usuwamy.
        usun_towar_calkowicie(nazwa)
        st.info(f"Towar **{nazwa}** zszedł do zera i został usunięty z listy.")
    else:
        st.session_state.magazyn[nazwa] = nowa_ilosc
        st.success(f"Zmieniono stan towaru **{nazwa}**. Nowa ilość: {nowa_ilosc}")

# --- Interfejs użytkownika Streamlit (użycie kolumn dla lepszego layoutu) ---

col1, col2 = st.columns(2)

# --- PANEL 1: DODAWANIE / AKTUALIZACJA ---
with col1:
    st.header("➕ Dodaj / Zaktualizuj Towar")
    with st.form("form_dodaj"):
        towar_do_dodania = st.text_input("Nazwa Towaru (unikalna):").strip()
        ilosc_startowa = st.number_input("Początkowa Ilość:", min_value=1, step=1, value=1)
        dodaj_przycisk = st.form_submit_button("Dodaj/Zwiększ Stan")

        if dodaj_przycisk:
            dodaj_lub_zaktualizuj_towar(towar_do_dodania, ilosc_startowa)

# --- PANEL 2: MODYFIKACJA STANU ---
with col2:
    st.header("🔄 Modifikacja Stanu")
    if st.session_state.magazyn:
        towary_list = list(st.session_state.magazyn.keys())
        towar_do_zmiany = st.selectbox(
            "Wybierz Towar do Zmiany:",
            towary_list,
            key="select_mod"
        )
        
        zmiana = st.number_input("Zmień Ilość o (ujemna = odejmij):", value=0, step=1)
        
        col_mod_1, col_mod_2 = st.columns(2)

        if col_mod_1.button("Zapisz Zmianę Ilości", use_container_width=True):
            if zmiana != 0:
                modyfikuj_ilosc(towar_do_zmiany, zmiana)
            else:
                st.warning("Wprowadź wartość inną niż 0.")
                
        if col_mod_2.button("Usuń Towar Całkowicie", type="primary", use_container_width=True):
            usun_towar_calkowicie(towar_do_zmiany)

    else:
        st.info("Brak towarów do modyfikacji. Dodaj coś najpierw!")

st.markdown("---")

# --- PANEL 3: WIDOK MAGAZYNU I WYSZUKIWANIE ---

st.header("📋 Stan Magazynu")

if st.session_state.magazyn:
    # Konwersja słownika na DataFrame Pandas dla łatwego wyświetlania
    df = pd.DataFrame(
        list(st.session_state.magazyn.items()), 
        columns=['Nazwa Towaru', 'Ilość']
    )
    df['Nazwa Towaru'] = df['Nazwa Towaru'].str.capitalize()
    df = df.sort_values(by='Nazwa Towaru')

    # Funkcja Wyszukiwania/Filtrowania
    search_term = st.text_input("Filtruj towary po nazwie:", "").strip()

    if search_term:
        df_filtered = df[
            df['Nazwa Towaru'].str.contains(search_term, case=False)
        ]
        st.dataframe(
            df_filtered, 
            use_container_width=True, 
            hide_index=True
        )
        st.info(f"Znaleziono {len(df_filtered)} towarów pasujących do frazy '{search_term}'.")
    else:
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True
        )
        
    st.markdown(f"**Całkowita liczba unikalnych towarów w magazynie:** `{len(st.session_state.magazyn)}`")

else:
    st.info("Magazyn jest pusty. Użyj panelu 'Dodaj' powyżej.")
