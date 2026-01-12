import streamlit as st
import pandas as pd
from datetime import datetime

# --- Konfiguracja aplikacji ---
st.set_page_config(page_title="Pełny System Magazynowy", layout="wide")
st.title("Mega Magazyn: Śledzenie, Transakcje i Alarmy")

# --- KONFIGURACJA BAZY DANYCH ---
# Używamy wbudowanego mechanizmu st.connection dla SQL
conn = st.connection('magazyn_db', type='sql')

# Inicjalizacja tabel, jeśli nie istnieją
with conn.session as s:
    s.execute('CREATE TABLE IF NOT EXISTS magazyn (nazwa TEXT PRIMARY KEY, ilosc INTEGER, min_stan INTEGER);')
    s.execute('CREATE TABLE IF NOT EXISTS transakcje_historia (typ TEXT, towar TEXT, ilosc INTEGER, data TEXT);')
    s.commit()

# --- Funkcje logiki biznesowej ---

def rejestruj_transakcje(typ, nazwa, ilosc):
    """Rejestruje transakcję w historii bazy danych."""
    data_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn.session as s:
        s.execute(
            'INSERT INTO transakcje_historia (typ, towar, ilosc, data) VALUES (:typ, :towar, :ilosc, :data)',
            params={"typ": typ, "towar": nazwa, "ilosc": ilosc, "data": data_str}
        )
        s.commit()

def dodaj_nowy_towar(nazwa, ilosc, min_stan):
    """Dodaje nowy towar do bazy danych."""
    nazwa = nazwa.strip().capitalize()
    
    # Sprawdzenie czy istnieje
    istnieje = conn.query(f"SELECT nazwa FROM magazyn WHERE nazwa = '{nazwa}'")
    
    if not nazwa or not istnieje.empty:
        st.error("Nazwa jest pusta lub towar już istnieje.")
        return

    with conn.session as s:
        s.execute(
            'INSERT INTO magazyn (nazwa, ilosc, min_stan) VALUES (:nazwa, :ilosc, :min_stan)',
            params={"nazwa": nazwa, "ilosc": int(ilosc), "min_stan": int(min_stan)}
        )
        s.commit()
    
    rejestruj_transakcje("Przyjęcie (Nowy)", nazwa, ilosc)
    st.success(f"Dodano nowy towar: **{nazwa}** w ilości {ilosc} sztuk. Min. stan: {min_stan}")

def przyjmij_wydaj_towar(nazwa, ilosc_zmiany, operacja):
    """Realizuje operację przyjęcia lub wydania w bazie danych."""
    res = conn.query(f"SELECT ilosc, min_stan FROM magazyn WHERE nazwa = '{nazwa}'", ttl=0)
    if res.empty:
        st.error(f"Towar **{nazwa}** nie istnieje.")
        return

    obecna_ilosc = res.iloc[0]['ilosc']
    min_stan = res.iloc[0]['min_stan']
    
    if operacja == "Przyjęcie":
        nowa_ilosc = obecna_ilosc + ilosc_zmiany
    elif operacja == "Wydanie":
        if obecna_ilosc < ilosc_zmiany:
            st.error(f"Błąd! Nie można wydać {ilosc_zmiany} szt. Dostępne: {obecna_ilosc}")
            return
        nowa_ilosc = obecna_ilosc - ilosc_zmiany

    with conn.session as s:
        s.execute(
            'UPDATE magazyn SET ilosc = :nowa WHERE nazwa = :nazwa',
            params={"nowa": int(nowa_ilosc), "nazwa": nazwa}
        )
        s.commit()

    rejestruj_transakcje(operacja, nazwa, ilosc_zmiany)
    st.success(f"Operacja {operacja} zakończona dla **{nazwa}**. Nowy stan: {nowa_ilosc}")

    if nowa_ilosc < min_stan:
        st.warning(f"🚨 **UWAGA NISKI STAN!** Towar **{nazwa}** jest poniżej stanu minimalnego ({min_stan}).")


# --- Interfejs użytkownika Streamlit ---

tab_magazyn, tab_transakcje, tab_ustawienia = st.tabs(["📋 Stan Magazynu", "📜 Historia Transakcji", "⚙️ Ustawienia i Narzędzia"])

# --- TABELA STANU MAGAZYNU ---
with tab_magazyn:
    st.header("Stan Magazynu i Transakcje")
    
    # Pobieranie danych z bazy
    df_magazyn = conn.query("SELECT * FROM magazyn", ttl=0)
    
    if not df_magazyn.empty:
        df_display = df_magazyn.copy()
        df_display['Niski Stan?'] = df_display.apply(lambda x: 'TAK 🔴' if x['ilosc'] < x['min_stan'] else 'NIE 🟢', axis=1)
        
        towary_niskostanowe = (df_magazyn['ilosc'] < df_magazyn['min_stan']).sum()

        if towary_niskostanowe > 0:
            st.error(f"⚠️ **{towary_niskostanowe}** towarów jest poniżej stanu minimalnego! Sprawdź tabelę.")

        search_term = st.text_input("Filtruj towary po nazwie:", "", key="search_magazyn").strip()
        if search_term:
            df_display = df_display[df_display['nazwa'].str.contains(search_term, case=False)]
            
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Magazyn jest pusty. Użyj sekcji Transakcje, aby dodać towary.")

    st.markdown("---")
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
                st.rerun()
                
    with col_op_2:
        st.markdown("##### 🔄 Przyjęcie / Wydanie (Istniejące)")
        if not df_magazyn.empty:
            towary_list = sorted(df_magazyn['nazwa'].tolist())
            op_towar = st.selectbox("Wybierz Towar:", towary_list, key="op_towar")
            op_ilosc = st.number_input("Ilość Zmiany:", min_value=1, step=1, value=1)
            op_typ = st.radio("Typ Operacji:", ["Przyjęcie", "Wydanie"])
            
            if st.button(f"Wykonaj Operację: {op_typ}"):
                przyjmij_wydaj_towar(op_towar, op_ilosc, op_typ)
                st.rerun()
        else:
            st.info("Brak towarów do operacji. Dodaj towar w panelu obok.")


# --- TABELA HISTORII TRANSAKCJI ---
with tab_transakcje:
    st.header("📜 Rejestr Transakcji")
    df_historia = conn.query("SELECT * FROM transakcje_historia ORDER BY data DESC", ttl=0)
    
    if not df_historia.empty:
        st.dataframe(df_historia, use_container_width=True, hide_index=True)
    else:
        st.info("Brak zarejestrowanych transakcji.")

# --- NARZĘDZIA I USTAWIENIA ---
with tab_ustawienia:
    st.header("⚙️ Narzędzia Magazynowe")
    st.subheader("Resetowanie Danych")
    st.warning("Ta operacja usunie **wszystkie dane** z bazy danych. Jest nieodwracalna.")
    
    if st.button("Wyczyść Cały Magazyn i Historię", type="primary"):
        with conn.session as s:
            s.execute('DELETE FROM magazyn;')
            s.execute('DELETE FROM transakcje_historia;')
            s.commit()
        st.success("Magazyn został pomyślnie zresetowany!")
        st.rerun()
