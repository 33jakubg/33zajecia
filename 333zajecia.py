import streamlit as st

# --- Konfiguracja aplikacji ---
st.set_page_config(page_title="Prosty Magazyn", layout="centered")
st.title("📦 Prosty Magazyn Towarów")
st.markdown("---")

# 1. Inicjalizacja stanu sesji (listy towarów)
# Jeśli lista 'towary' nie istnieje w stanie sesji, utwórz ją jako pustą listę.
if 'towary' not in st.session_state:
    st.session_state.towary = []

# --- Funkcje logiki biznesowej ---

def dodaj_towar(nazwa):
    """Dodaje nowy towar do listy."""
    if nazwa and nazwa not in st.session_state.towary:
        st.session_state.towary.append(nazwa)
        st.success(f"Dodano: **{nazwa}**")
    elif nazwa in st.session_state.towary:
        st.warning(f"Towar **{nazwa}** już jest w magazynie!")
    else:
        st.warning("Nazwa towaru nie może być pusta.")

def usun_towar(nazwa):
    """Usuwa towar z listy, jeśli istnieje."""
    try:
        st.session_state.towary.remove(nazwa)
        st.success(f"Usunięto: **{nazwa}**")
    except ValueError:
        st.error(f"Błąd: Towar **{nazwa}** nie znaleziono w magazynie.")

# --- Interfejs użytkownika Streamlit ---

# 2. Sekcja Dodawania Towaru
st.header("➕ Dodaj Nowy Towar")
with st.form("dodaj_formularz"):
    nowy_towar = st.text_input("Nazwa Towaru:", key="input_dodaj").strip()
    dodaj_przycisk = st.form_submit_button("Dodaj do Magazynu")

    if dodaj_przycisk:
        dodaj_towar(nowy_towar)

st.markdown("---")

# 3. Sekcja Usuwania Towaru
st.header("➖ Usuń Towar")
if st.session_state.towary:
    towar_do_usuniecia = st.selectbox(
        "Wybierz Towar do Usunięcia:",
        st.session_state.towary,
        key="select_usun"
    )
    usun_przycisk = st.button("Usuń Wybrany Towar")

    if usun_przycisk:
        usun_towar(towar_do_usuniecia)
else:
    st.info("Magazyn jest pusty. Nie ma towarów do usunięcia.")

st.markdown("---")

# 4. Sekcja Stanu Magazynu
st.header("📋 Aktualny Stan Magazynu")

if st.session_state.towary:
    st.dataframe(
        {'Towar': st.session_state.towary},
        use_container_width=True,
        hide_index=True
    )
    st.markdown(f"**Liczba unikalnych towarów:** `{len(st.session_state.towary)}`")
else:
    st.info("Magazyn jest pusty.")
