import streamlit as st
import requests
import json
import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="SIM-PA MDUK",
    page_icon="📚",
    layout="wide"
)

# --- KONFIGURASI SUPABASE REST API ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://URL-PROYEK-ANDA.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "KEY-ANON-PUBLIC-ANDA")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# --- HELPER FUNCTIONS ---
def get_user(username, password):
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&password=eq.{password}&select=*"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200 and len(res.json()) > 0:
            return res.json()[0]
    except Exception as e:
        st.error(f"Gagal terhubung ke database: {e}")
    return None

def register_user(username, password, nama_lengkap, mapel):
    check_url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=*"
    res_check = requests.get(check_url, headers=HEADERS)
    if res_check.status_code == 200 and len(res_check.json()) > 0:
        return "EXISTS"
    
    url = f"{SUPABASE_URL}/rest/v1/users"
    post_headers = HEADERS.copy()
    post_headers["Prefer"] = "return=representation"
    payload = {
        "username": username,
        "password": password,
        "nama_lengkap": nama_lengkap,
        "role": "guru",
        "mapel": mapel
    }
    res = requests.post(url, headers=post_headers, data=json.dumps(payload))
    if res.status_code in [200, 201]:
        return "SUCCESS"
    return "FAILED"

def upload_file_storage(file_bytes, file_name, username):
    timestamp = int(datetime.datetime.now().timestamp())
    file_path = f"{username}/{timestamp}_{file_name}"
    url = f"{SUPABASE_URL}/storage/v1/object/perangkat-ajar/{file_path}"
    
    storage_headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "x-upsert": "true"
    }
    
    res = requests.post(url, headers=storage_headers, data=file_bytes)
    if res.status_code in [200, 201]:
        return f"{SUPABASE_URL}/storage/v1/object/public/perangkat-ajar/{file_path}"
    return None

def insert_document(doc_data):
    url = f"{SUPABASE_URL}/rest/v1/documents"
    post_headers = HEADERS.copy()
    post_headers["Prefer"] = "return=representation"
    res = requests.post(url, headers=post_headers, data=json.dumps(doc_data))
    return res.status_code in [200, 201]

def get_documents(username=None):
    if username:
        url = f"{SUPABASE_URL}/rest/v1/documents?username=eq.{username}&order=created_at.desc"
    else:
        url = f"{SUPABASE_URL}/rest/v1/documents?order=created_at.desc"
    
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return []

def update_document_status(doc_id, status, catatan):
    url = f"{SUPABASE_URL}/rest/v1/documents?id=eq.{doc_id}"
    patch_headers = HEADERS.copy()
    patch_headers["Prefer"] = "return=minimal"
    payload = {
        "status_verifikasi": status,
        "catatan_revisi": catatan
    }
    res = requests.patch(url, headers=patch_headers, data=json.dumps(payload))
    return res.status_code in [200, 204]

# --- INISIALISASI SESI ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

# ==========================================
# 1. HALAMAN LOGIN & REGISTRASI
# ==========================================
if not st.session_state.authenticated:
    st.title("🔒 SIM-PA MTsS Darul Ulum Kotabaru")
    st.caption("Sistem Informasi Manajemen Perangkat Ajar Guru")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Buat Akun Guru Baru"])
        
        with tab_login:
            with st.form("login_form"):
                st.subheader("Login Pengguna")
                username_input = st.text_input("Username")
                password_input = st.text_input("Password", type="password")
                submit_btn = st.form_submit_button("Masuk (Login)", use_container_width=True)
                
                if submit_btn:
                    if username_input and password_input:
                        user_data = get_user(username_input.lower().strip(), password_input)
                        if user_data:
                            st.session_state.authenticated = True
                            st.session_state.user = user_data
                            st.success("Login berhasil!")
                            st.rerun()
                        else:
                            st.error("Username atau password salah!")
                    else:
                        st.warning("Mohon isi username dan password.")

        with tab_register:
            with st.form("register_form"):
                st.subheader("Pendaftaran Akun Guru")
                reg_nama = st.text_input("Nama Lengkap & Gelar (contoh: Ahmad Fauzi, S.Pd.)")
                reg_mapel = st.selectbox("Mata Pelajaran Utama", [
                    "Matematika", "Bahasa Indonesia", "Bahasa Inggris", "IPA", "IPS",
                    "Pendidikan Agama Islam", "Al-Qur'an Hadits", "Fiqih", "SKI", 
                    "Bahasa Arab", "PJOK", "Seni Budaya", "Informatika", "Lainnya"
                ])
                reg_username = st.text_input("Buat Username (huruf kecil & tanpa spasi)")
                reg_password = st.text_input("Buat Password", type="password")
                reg_submit = st.form_submit_button("Daftar Akun Baru", type="primary", use_container_width=True)
                
                if reg_submit:
                    if reg_nama and reg_username and reg_password:
                        result = register_user(reg_username.lower().strip(), reg_password, reg_nama, reg_mapel)
                        if result == "SUCCESS":
                            st.success("✓ Akun berhasil dibuat! Silakan pindah ke tab 'Login' untuk masuk.")
                        elif result == "EXISTS":
                            st.error("Username tersebut sudah digunakan! Gunakan username lain.")
                        else:
                            st.error("Gagal mendaftarkan akun. Silakan periksa koneksi.")
                    else:
                        st.warning("Harap lengkapi semua kolom pendaftaran.")

# ==========================================
# 2. APLIKASI UTAMA (SETELAH LOGIN)
# ==========================================
else:
    user = st.session_state.user
    
    st.sidebar.title("📚 SIM-PA MDUK")
    st.sidebar.write(f"👤 **{user['nama_lengkap']}**")
    st.sidebar.write(f"🔰 Role: **{user['role'].capitalize()}**")
    if user['mapel'] != '-':
        st.sidebar.write(f"📖 Mapel: **{user['mapel']}**")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Log Keluar", type="secondary", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

    # DASBOR GURU
    if user["role"] == "guru":
        st.header("📌 Dasbor Pengelolaan Berkas Guru")
        tab1, tab2 = st.tabs(["📤 Unggah Perangkat Ajar", "📂 Riwayat Berkas Saya"])
        
        with tab1:
            st.subheader("Formulir Pengumpulan Dokumen")
            with st.form("upload_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    mapel = st.text_input("Mata Pelajaran", value=user['mapel'])
                    kelas = st.selectbox("Kelas Target", ["Kelas 7", "Kelas 8", "Kelas 9"])
                with col_b:
                    jenis = st.selectbox("Jenis Dokumen", ["RPP / Modul Ajar", "Prota", "Promes", "ATP", "KKTP", "Lainnya"])
                    ta = st.text_input("Tahun Ajaran", value="2026/2027")
                
                file_up = st.file_uploader("Upload Berkas (PDF, DOCX, XLSX)", type=["pdf", "docx", "xlsx"])
                submit_upload = st.form_submit_button("Kirim Berkas ke Kurikulum", type="primary")
                
                if submit_upload:
                    if file_up is not None:
                        with st.spinner("Mengunggah berkas ke database..."):
                            file_bytes = file_up.read()
                            public_file_url = upload_file_storage(file_bytes, file_up.name, user["username"])
                            
                            if public_file_url:
                                doc_payload = {
                                    "username": user["username"],
                                    "nama_guru": user["nama_lengkap"],
                                    "mapel": mapel,
                                    "kelas": kelas,
                                    "jenis_doc": jenis,
                                    "tahun_ajaran": ta,
                                    "file_name": file_up.name,
                                    "file_url": public_file_url,
                                    "status_verifikasi": "Belum Diperiksa",
                                    "catatan_revisi": ""
                                }
                                success = insert_document(doc_payload)
                                if success:
                                    st.success(f"✓ Berkas '{file_up.name}' berhasil diunggah!")
                                else:
                                    st.error("Gagal menyimpan data ke database.")
                            else:
                                st.error("Gagal mengunggah file ke cloud storage.")
                    else:
                        st.warning("Pilih berkas terlebih dahulu!")

        with tab2:
            st.subheader("Daftar Dokumen yang Telah Diunggah")
            my_docs = get_documents(user["username"])
            
            if my_docs:
                for d in my_docs:
                    status = d.get('status_verifikasi', 'Belum Diperiksa')
                    if status == "Disetujui":
                        badge = "🟢 Disetujui"
                    elif status == "Perlu Revisi":
                        badge = "🔴 Perlu Revisi"
                    else:
                        badge = "🟡 Belum Diperiksa"
                        
                    with st.expander(f"{d['jenis_doc']} - {d['kelas']} ({badge})"):
                        st.write(f"**Nama File:** {d['file_name']}")
                        st.write(f"**Mata Pelajaran:** {d['mapel']}")
                        st.write(f"**Catatan Revisi:** {d['catatan_revisi'] if d['catatan_revisi'] else 'Tidak ada.'}")
                        st.markdown(f"📥 [Unduh / Buka Dokumen]({d['file_url']})")
            else:
                st.info("Belum ada berkas yang Anda unggah.")

    # DASBOR KURIKULUM
    elif user["role"] == "kurikulum":
        st.header("📊 Panel Monitoring Kurikulum MDUK")
        all_docs = get_documents()
        
        total_berkas = len(all_docs)
        disetujui = len([d for d in all_docs if d.get('status_verifikasi') == 'Disetujui'])
        revisi = len([d for d in all_docs if d.get('status_verifikasi') == 'Perlu Revisi'])
        pending = len([d for d in all_docs if d.get('status_verifikasi') == 'Belum Diperiksa'])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Berkas Masuk", f"{total_berkas}")
        c2.metric("Belum Diperiksa", f"{pending}")
        c3.metric("Disetujui", f"{disetujui}")
        c4.metric("Perlu Revisi", f"{revisi}")
        
        st.markdown("---")
        st.subheader("Daftar Pengumpulan Perangkat Ajar Guru")
        
        if all_docs:
            for d in all_docs:
                status_curr = d.get('status_verifikasi', 'Belum Diperiksa')
                with st.expander(f"👨‍🏫 {d['nama_guru']} | {d['jenis_doc']} - {d['kelas']} ({d['mapel']})"):
                    st.write(f"**Nama Berkas:** {d['file_name']}")
                    st.write(f"**Status Saat Ini:** {status_curr}")
                    st.markdown(f"📄 [Lihat / Download File Dokumen]({d['file_url']})")
                    
                    with st.form(f"verif_form_{d['id']}"):
                        new_status = st.selectbox(
                            "Ubah Status Verifikasi",
                            ["Belum Diperiksa", "Disetujui", "Perlu Revisi"],
                            index=["Belum Diperiksa", "Disetujui", "Perlu Revisi"].index(status_curr)
                        )
                        catatan = st.text_area("Catatan Revisi / Masukan", value=d.get('catatan_revisi', ''))
                        btn_simpan = st.form_submit_button("Simpan Perubahan Status")
                        
                        if btn_simpan:
                            updated = update_document_status(d['id'], new_status, catatan)
                            if updated:
                                st.success("✓ Verifikasi berhasil disimpan!")
                                st.rerun()
                            else:
                                st.error("Gagal memperbarui status verifikasi.")
        else:
            st.info("Belum ada dokumen yang diunggah oleh para guru.")
