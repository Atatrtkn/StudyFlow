#Ata Metin Türetken 20011050
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'studyflow_secret_key_2025'

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'studyflow'),
    'user': os.getenv('DB_USER', 'ataturetken'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('login'))
        if session.get('rol') != 'admin':
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ogrenci_no = request.form['ogrenci_no']
        sifre = request.form['sifre']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT kullanici_id, ogrenci_no, ad, soyad, rol 
            FROM kullanicilar 
            WHERE ogrenci_no = %s AND sifre = %s AND aktif = TRUE
        """, (ogrenci_no, sifre))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session['user_id'] = user['kullanici_id']
            session['ogrenci_no'] = user['ogrenci_no']
            session['ad'] = user['ad']
            session['soyad'] = user['soyad']
            session['rol'] = user['rol']
            flash(f'Hoş geldiniz, {user["ad"]} {user["soyad"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Geçersiz öğrenci numarası veya şifre!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    ad = request.form['ad']
    soyad = request.form['soyad']
    ogrenci_no = request.form['ogrenci_no']
    email = request.form['email']
    bolum = request.form['bolum']
    sifre = request.form['sifre']
    
    if not email.endswith('@std.yildiz.edu.tr'):
        flash('Sadece @std.yildiz.edu.tr uzantılı e-posta adresleri kabul edilmektedir!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT 1 FROM kullanicilar WHERE ogrenci_no = %s", (ogrenci_no,))
    if cur.fetchone():
        cur.close()
        conn.close()
        flash('Bu öğrenci numarası zaten kayıtlı!', 'danger')
        return redirect(url_for('login'))
    
    cur.execute("SELECT 1 FROM kullanicilar WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        flash('Bu e-posta adresi zaten kayıtlı!', 'danger')
        return redirect(url_for('login'))
    
    try:
        cur.execute("""
            INSERT INTO kullanicilar (ogrenci_no, ad, soyad, email, sifre, rol)
            VALUES (%s, %s, %s, %s, %s, 'ogrenci')
        """, (ogrenci_no, ad, soyad, email, sifre))
        conn.commit()
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Kayıt sırasında hata oluştu: {str(e)}', 'danger')
    
    cur.close()
    conn.close()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(DISTINCT r.rezervasyon_id) as toplam_rezervasyon,
            COUNT(DISTINCT CASE WHEN r.durum = 'aktif' THEN r.rezervasyon_id END) as aktif_rezervasyon,
            COUNT(DISTINCT co.oturum_id) as toplam_oturum,
            COALESCE(ROUND(AVG(co.verimlilik_puani), 1), 0) as ort_verimlilik
        FROM kullanicilar k
        LEFT JOIN rezervasyonlar r ON k.kullanici_id = r.kullanici_id
        LEFT JOIN calisma_oturumlari co ON k.kullanici_id = co.kullanici_id
        WHERE k.kullanici_id = %s
    """, (session['user_id'],))
    stats = cur.fetchone()
    
    cur.execute("""
        SELECT r.*, ca.alan_adi, ca.konum
        FROM rezervasyonlar r
        JOIN calisma_alanlari ca ON r.alan_id = ca.alan_id
        WHERE r.kullanici_id = %s AND r.durum = 'aktif'
        ORDER BY r.baslangic_zamani
        LIMIT 5
    """, (session['user_id'],))
    aktif_rezervasyonlar = cur.fetchall()
    
    cur.execute("""
        SELECT co.*, ca.alan_adi
        FROM calisma_oturumlari co
        JOIN calisma_alanlari ca ON co.alan_id = ca.alan_id
        WHERE co.kullanici_id = %s
        ORDER BY co.giris_zamani DESC
        LIMIT 5
    """, (session['user_id'],))
    son_oturumlar = cur.fetchall()
    
    cur.execute("""
        SELECT co.*, ca.alan_adi
        FROM calisma_oturumlari co
        JOIN calisma_alanlari ca ON co.alan_id = ca.alan_id
        WHERE co.kullanici_id = %s AND co.cikis_zamani IS NULL
        LIMIT 1
    """, (session['user_id'],))
    aktif_oturum = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', 
                         stats=stats,
                         aktif_rezervasyonlar=aktif_rezervasyonlar,
                         son_oturumlar=son_oturumlar,
                         aktif_oturum=aktif_oturum)

@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        ad = request.form['ad']
        soyad = request.form['soyad']
        email = request.form['email']
        yeni_sifre = request.form.get('yeni_sifre', '')
        
        try:
            if yeni_sifre:
                cur.execute("""
                    UPDATE kullanicilar SET ad = %s, soyad = %s, email = %s, sifre = %s
                    WHERE kullanici_id = %s
                """, (ad, soyad, email, yeni_sifre, session['user_id']))
            else:
                cur.execute("""
                    UPDATE kullanicilar SET ad = %s, soyad = %s, email = %s
                    WHERE kullanici_id = %s
                """, (ad, soyad, email, session['user_id']))
            
            conn.commit()
            session['ad'] = ad
            session['soyad'] = soyad
            flash('Profil güncellendi!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Hata: {str(e)}', 'danger')
    
    cur.execute("SELECT * FROM kullanicilar WHERE kullanici_id = %s", (session['user_id'],))
    kullanici = cur.fetchone()
    
    cur.execute("""
        SELECT 
            COUNT(DISTINCT r.rezervasyon_id) as toplam_rezervasyon,
            COUNT(DISTINCT co.oturum_id) as toplam_oturum,
            COALESCE(SUM(EXTRACT(EPOCH FROM (co.cikis_zamani - co.giris_zamani)) / 3600), 0) as toplam_saat,
            COALESCE(ROUND(AVG(co.verimlilik_puani), 1), 0) as ort_verimlilik
        FROM kullanicilar k
        LEFT JOIN rezervasyonlar r ON k.kullanici_id = r.kullanici_id
        LEFT JOIN calisma_oturumlari co ON k.kullanici_id = co.kullanici_id AND co.cikis_zamani IS NOT NULL
        WHERE k.kullanici_id = %s
    """, (session['user_id'],))
    stats = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return render_template('profil.html', kullanici=kullanici, stats=stats)

@app.route('/takvim')
@login_required
def takvim():
    tarih = request.args.get('tarih', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT ca.alan_id, ca.alan_adi, ca.konum, ca.kapasite, at.tur_adi
        FROM calisma_alanlari ca
        JOIN alan_turleri at ON ca.tur_id = at.tur_id
        WHERE ca.aktif = TRUE
        ORDER BY ca.konum, ca.alan_adi
    """)
    alanlar = cur.fetchall()
    
    cur.execute("""
        SELECT alan_id, 
               EXTRACT(HOUR FROM baslangic_zamani)::INTEGER as baslangic_saat,
               EXTRACT(HOUR FROM bitis_zamani)::INTEGER as bitis_saat,
               COUNT(*) as rez_sayisi
        FROM rezervasyonlar
        WHERE DATE(baslangic_zamani) = %s AND durum = 'aktif'
        GROUP BY alan_id, EXTRACT(HOUR FROM baslangic_zamani), EXTRACT(HOUR FROM bitis_zamani)
    """, (tarih,))
    rezervasyonlar_raw = cur.fetchall()
    
    doluluk = {}
    for r in rezervasyonlar_raw:
        alan_id = r['alan_id']
        if alan_id not in doluluk:
            doluluk[alan_id] = {}
        for saat in range(r['baslangic_saat'], r['bitis_saat']):
            if saat not in doluluk[alan_id]:
                doluluk[alan_id][saat] = 0
            doluluk[alan_id][saat] += r['rez_sayisi']
    
    konumlar = {}
    for alan in alanlar:
        konum = alan['konum']
        if konum not in konumlar:
            konumlar[konum] = []
        konumlar[konum].append(alan)
    
    saatler = list(range(8, 22))
    
    cur.close()
    conn.close()
    
    return render_template('takvim.html', 
                         konumlar=konumlar,
                         doluluk=doluluk,
                         saatler=saatler,
                         secili_tarih=tarih)

@app.route('/api/takvim-verileri')
@login_required
def takvim_verileri():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT r.rezervasyon_id, r.baslangic_zamani, r.bitis_zamani, r.durum,
               ca.alan_adi, ca.konum
        FROM rezervasyonlar r
        JOIN calisma_alanlari ca ON r.alan_id = ca.alan_id
        WHERE r.kullanici_id = %s
        ORDER BY r.baslangic_zamani
    """, (session['user_id'],))
    rezervasyonlar = cur.fetchall()
    
    cur.execute("""
        SELECT co.oturum_id, co.giris_zamani, co.cikis_zamani, co.verimlilik_puani,
               ca.alan_adi
        FROM calisma_oturumlari co
        JOIN calisma_alanlari ca ON co.alan_id = ca.alan_id
        WHERE co.kullanici_id = %s AND co.cikis_zamani IS NOT NULL
        ORDER BY co.giris_zamani
    """, (session['user_id'],))
    oturumlar = cur.fetchall()
    
    cur.close()
    conn.close()
    
    events = []
    
    for r in rezervasyonlar:
        color = '#22c55e' if r['durum'] == 'aktif' else '#ef4444' if r['durum'] == 'iptal' else '#3b82f6'
        events.append({
            'id': f"rez_{r['rezervasyon_id']}",
            'title': f"📅 {r['alan_adi']}",
            'start': r['baslangic_zamani'].isoformat(),
            'end': r['bitis_zamani'].isoformat(),
            'color': color,
            'extendedProps': {
                'type': 'rezervasyon',
                'konum': r['konum'],
                'durum': r['durum']
            }
        })
    
    for o in oturumlar:
        events.append({
            'id': f"oturum_{o['oturum_id']}",
            'title': f"📖 {o['alan_adi']}",
            'start': o['giris_zamani'].isoformat(),
            'end': o['cikis_zamani'].isoformat(),
            'color': '#8b5cf6',
            'extendedProps': {
                'type': 'oturum',
                'verimlilik': o['verimlilik_puani']
            }
        })
    
    return jsonify(events)

@app.route('/rezervasyon/yeni', methods=['GET', 'POST'])
@login_required
def yeni_rezervasyon():
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        alan_id = request.form['alan_id']
        tarih = request.form['tarih']
        baslangic_saat = request.form['baslangic_saat']
        bitis_saat = request.form['bitis_saat']
        notlar = request.form.get('notlar', '')
        
        baslangic = f"{tarih} {baslangic_saat}:00"
        bitis = f"{tarih} {bitis_saat}:00"
        
        cur.execute("""
            SELECT r.rezervasyon_id, ca.alan_adi, r.baslangic_zamani, r.bitis_zamani
            FROM rezervasyonlar r
            JOIN calisma_alanlari ca ON r.alan_id = ca.alan_id
            WHERE r.kullanici_id = %s 
            AND r.durum = 'aktif'
            AND r.baslangic_zamani::DATE = %s::DATE
            AND r.baslangic_zamani < %s::TIMESTAMP
            AND r.bitis_zamani > %s::TIMESTAMP
        """, (session['user_id'], tarih, bitis, baslangic))
        
        cakisan = cur.fetchone()
        if cakisan:
            flash(f'Bu zaman diliminde zaten "{cakisan["alan_adi"]}" alanında rezervasyonunuz var ({cakisan["baslangic_zamani"].strftime("%H:%M")}-{cakisan["bitis_zamani"].strftime("%H:%M")})!', 'danger')
            cur.execute("""
                SELECT ca.*, at.tur_adi 
                FROM calisma_alanlari ca 
                JOIN alan_turleri at ON ca.tur_id = at.tur_id
                WHERE ca.aktif = TRUE
                ORDER BY ca.konum, ca.alan_adi
            """)
            alanlar = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('rezervasyon_yeni.html', alanlar=alanlar)
        
        cur.execute("SELECT kapasite FROM calisma_alanlari WHERE alan_id = %s", (alan_id,))
        alan_bilgi = cur.fetchone()
        kapasite = alan_bilgi['kapasite'] if alan_bilgi else 1
        
        cur.execute("""
            SELECT COUNT(*) as rez_sayisi
            FROM rezervasyonlar
            WHERE alan_id = %s 
            AND durum = 'aktif'
            AND baslangic_zamani < %s::TIMESTAMP
            AND bitis_zamani > %s::TIMESTAMP
        """, (alan_id, bitis, baslangic))
        
        mevcut_rez = cur.fetchone()
        rez_sayisi = mevcut_rez['rez_sayisi'] if mevcut_rez else 0
        
        if rez_sayisi >= kapasite:
            flash(f'Bu alan seçilen saatlerde dolu! (Kapasite: {kapasite}, Mevcut rezervasyon: {rez_sayisi})', 'danger')
            cur.execute("""
                SELECT ca.*, at.tur_adi 
                FROM calisma_alanlari ca 
                JOIN alan_turleri at ON ca.tur_id = at.tur_id
                WHERE ca.aktif = TRUE
                ORDER BY ca.konum, ca.alan_adi
            """)
            alanlar = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('rezervasyon_yeni.html', alanlar=alanlar)
        
        try:
            cur.execute("""
                INSERT INTO rezervasyonlar (kullanici_id, alan_id, baslangic_zamani, bitis_zamani, notlar)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING rezervasyon_id
            """, (session['user_id'], alan_id, baslangic, bitis, notlar))
            
            rez_id = cur.fetchone()['rezervasyon_id']
            conn.commit()
            flash(f'Rezervasyon oluşturuldu! (ID: {rez_id})', 'success')
            return redirect(url_for('rezervasyonlarim'))
            
        except psycopg2.Error as e:
            conn.rollback()
            if 'max_sure_kontrolu' in str(e):
                flash('Maksimum rezervasyon süresi 4 saattir!', 'danger')
            else:
                flash(f'Hata: {str(e)}', 'danger')
    
    cur.execute("""
        SELECT ca.*, at.tur_adi 
        FROM calisma_alanlari ca 
        JOIN alan_turleri at ON ca.tur_id = at.tur_id
        WHERE ca.aktif = TRUE
        ORDER BY ca.konum, ca.alan_adi
    """)
    alanlar = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('rezervasyon_yeni.html', alanlar=alanlar)

@app.route('/rezervasyonlarim')
@login_required
def rezervasyonlarim():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT r.*, ca.alan_adi, ca.konum
        FROM rezervasyonlar r
        JOIN calisma_alanlari ca ON r.alan_id = ca.alan_id
        WHERE r.kullanici_id = %s
        ORDER BY r.baslangic_zamani DESC
    """, (session['user_id'],))
    
    rezervasyonlar = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('rezervasyonlarim.html', rezervasyonlar=rezervasyonlar)

@app.route('/rezervasyon/iptal/<int:rez_id>', methods=['POST'])
@login_required
def rezervasyon_iptal(rez_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE rezervasyonlar SET durum = 'iptal'
            WHERE rezervasyon_id = %s AND kullanici_id = %s
        """, (rez_id, session['user_id']))
        conn.commit()
        flash('Rezervasyon iptal edildi.', 'info')
    except psycopg2.Error as e:
        conn.rollback()
        flash(f'Hata: {str(e)}', 'danger')
    
    cur.close()
    conn.close()
    return redirect(url_for('rezervasyonlarim'))

@app.route('/rezervasyon/guncelle/<int:rez_id>', methods=['GET', 'POST'])
@login_required
def rezervasyon_guncelle(rez_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        tarih = request.form['tarih']
        baslangic_saat = request.form['baslangic_saat']
        bitis_saat = request.form['bitis_saat']
        notlar = request.form.get('notlar', '')
        
        baslangic = f"{tarih} {baslangic_saat}:00"
        bitis = f"{tarih} {bitis_saat}:00"
        
        try:
            cur.execute("""
                UPDATE rezervasyonlar 
                SET baslangic_zamani = %s, bitis_zamani = %s, notlar = %s
                WHERE rezervasyon_id = %s AND kullanici_id = %s
            """, (baslangic, bitis, notlar, rez_id, session['user_id']))
            conn.commit()
            flash('Rezervasyon güncellendi!', 'success')
            return redirect(url_for('rezervasyonlarim'))
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Hata: {str(e)}', 'danger')
    
    cur.execute("""
        SELECT r.*, ca.alan_adi
        FROM rezervasyonlar r
        JOIN calisma_alanlari ca ON r.alan_id = ca.alan_id
        WHERE r.rezervasyon_id = %s AND r.kullanici_id = %s
    """, (rez_id, session['user_id']))
    rezervasyon = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if not rezervasyon:
        flash('Rezervasyon bulunamadı!', 'danger')
        return redirect(url_for('rezervasyonlarim'))
    
    return render_template('rezervasyon_guncelle.html', rezervasyon=rezervasyon)

@app.route('/arama')
@login_required
def arama():
    return render_template('arama.html')

@app.route('/arama/sonuc')
@login_required
def arama_sonuc():
    query = request.args.get('q', '')
    tur = request.args.get('tur', '')
    konum = request.args.get('konum', '')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    sql = """
        SELECT ca.*, at.tur_adi 
        FROM calisma_alanlari ca 
        JOIN alan_turleri at ON ca.tur_id = at.tur_id
        WHERE ca.aktif = TRUE
    """
    params = []
    
    if query:
        sql += " AND (LOWER(ca.alan_adi) LIKE LOWER(%s) OR LOWER(ca.konum) LIKE LOWER(%s))"
        params.extend([f'%{query}%', f'%{query}%'])
    
    if tur:
        sql += " AND at.tur_adi = %s"
        params.append(tur)
    
    if konum:
        sql += " AND ca.konum = %s"
        params.append(konum)
    
    sql += " ORDER BY ca.konum, ca.alan_adi"
    
    cur.execute(sql, params)
    sonuclar = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('arama_sonuc.html', sonuclar=sonuclar, query=query)

@app.route('/istatistikler')
@login_required
def istatistikler():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM fn_yogunluk_analizi(30)")
    yogunluk = cur.fetchall()
    
    cur.execute("SELECT * FROM v_alan_doluluk ORDER BY aktif_rezervasyon_sayisi DESC")
    alan_doluluk = cur.fetchall()
    
    cur.execute("SELECT * FROM v_tam_katilimci")
    tam_katilimci = cur.fetchall()
    
    cur.execute("SELECT * FROM v_sadece_rezervasyon")
    sadece_rezervasyon = cur.fetchall()
    
    cur.execute("""
        SELECT 
            COUNT(DISTINCT r.rezervasyon_id) as toplam_rezervasyon,
            COUNT(DISTINCT co.oturum_id) as toplam_oturum,
            COALESCE(ROUND(SUM(EXTRACT(EPOCH FROM (co.cikis_zamani - co.giris_zamani)) / 3600), 1), 0) as toplam_saat
        FROM kullanicilar k
        LEFT JOIN rezervasyonlar r ON k.kullanici_id = r.kullanici_id
        LEFT JOIN calisma_oturumlari co ON k.kullanici_id = co.kullanici_id AND co.cikis_zamani IS NOT NULL
        WHERE k.kullanici_id = %s
    """, (session['user_id'],))
    kisisel = cur.fetchone()
    
    cur.execute("""
        SELECT ca.alan_adi, COUNT(*) as sayi
        FROM rezervasyonlar r
        JOIN calisma_alanlari ca ON r.alan_id = ca.alan_id
        WHERE r.kullanici_id = %s
        GROUP BY ca.alan_adi
        ORDER BY sayi DESC
        LIMIT 1
    """, (session['user_id'],))
    en_cok = cur.fetchone()
    
    kisisel_stats = {
        'toplam_rezervasyon': kisisel['toplam_rezervasyon'] if kisisel else 0,
        'toplam_oturum': kisisel['toplam_oturum'] if kisisel else 0,
        'toplam_saat': int(kisisel['toplam_saat']) if kisisel and kisisel['toplam_saat'] else 0,
        'en_cok_alan': en_cok['alan_adi'] if en_cok else None
    }
    
    cur.close()
    conn.close()
    
    return render_template('istatistikler.html',
                         yogunluk=yogunluk,
                         alan_doluluk=alan_doluluk,
                         tam_katilimci=tam_katilimci,
                         sadece_rezervasyon=sadece_rezervasyon,
                         kisisel_stats=kisisel_stats)

@app.route('/zaman-onerisi')
@login_required
def zaman_onerisi():
    alan_id = request.args.get('alan_id', type=int)
    tarih = request.args.get('tarih', datetime.now().strftime('%Y-%m-%d'))
    sure = request.args.get('sure', 2, type=int)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT ca.alan_id, ca.alan_adi, ca.konum 
        FROM calisma_alanlari ca 
        WHERE ca.aktif = TRUE
        ORDER BY ca.alan_adi
    """)
    alanlar = cur.fetchall()
    
    oneriler = []
    if alan_id:
        try:
            cur.execute("""
                SELECT * FROM fn_uygun_zaman_onerisi(%s, %s::DATE, %s)
            """, (alan_id, tarih, sure))
            oneriler = cur.fetchall()
        except psycopg2.Error as e:
            flash(f'Öneri alınırken hata oluştu: {str(e)}', 'danger')
    
    cur.close()
    conn.close()
    
    return render_template('zaman_onerisi.html',
                         alanlar=alanlar,
                         oneriler=oneriler,
                         secili_alan=alan_id,
                         secili_tarih=tarih,
                         secili_sure=sure)

@app.route('/oturum/baslat', methods=['GET', 'POST'])
@login_required
def oturum_baslat():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT co.*, ca.alan_adi
        FROM calisma_oturumlari co
        JOIN calisma_alanlari ca ON co.alan_id = ca.alan_id
        WHERE co.kullanici_id = %s AND co.cikis_zamani IS NULL
    """, (session['user_id'],))
    aktif_oturum = cur.fetchone()
    
    if request.method == 'POST':
        if aktif_oturum:
            flash('Zaten devam eden bir oturumunuz var!', 'warning')
            return redirect(url_for('oturumlarim'))
            
        alan_id = request.form['alan_id']
        
        try:
            cur.execute("""
                INSERT INTO calisma_oturumlari 
                (kullanici_id, alan_id, giris_zamani)
                VALUES (%s, %s, NOW())
                RETURNING oturum_id
            """, (session['user_id'], alan_id))
            
            oturum_id = cur.fetchone()['oturum_id']
            conn.commit()
            
            flash(f'Çalışma oturumu başlatıldı! (ID: {oturum_id})', 'success')
            return redirect(url_for('oturumlarim'))
            
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Hata: {str(e)}', 'danger')
    
    cur.execute("""
        SELECT ca.alan_id, ca.alan_adi, ca.konum, ca.kapasite, ca.priz_var, ca.sessiz_alan, at.tur_adi
        FROM calisma_alanlari ca
        JOIN alan_turleri at ON ca.tur_id = at.tur_id
        WHERE ca.aktif = TRUE
        ORDER BY ca.konum, ca.alan_adi
    """)
    alanlar = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('oturum_baslat.html', 
                         alanlar=alanlar,
                         aktif_oturum=aktif_oturum)

@app.route('/oturum/bitir/<int:oturum_id>', methods=['POST'])
@login_required
def oturum_bitir(oturum_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    verimlilik = request.form.get('verimlilik', 5, type=int)
    notlar = request.form.get('notlar', '')
    
    try:
        cur.execute("""
            UPDATE calisma_oturumlari 
            SET cikis_zamani = NOW(), 
                verimlilik_puani = %s,
                notlar = %s
            WHERE oturum_id = %s AND kullanici_id = %s AND cikis_zamani IS NULL
        """, (verimlilik, notlar, oturum_id, session['user_id']))
        
        conn.commit()
        flash('Oturum tamamlandı!', 'success')
        
    except psycopg2.Error as e:
        conn.rollback()
        flash(f'Hata: {str(e)}', 'danger')
    
    cur.close()
    conn.close()
    
    return redirect(url_for('oturumlarim'))

@app.route('/oturumlarim')
@login_required
def oturumlarim():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT co.*, ca.alan_adi, ca.konum
        FROM calisma_oturumlari co
        JOIN calisma_alanlari ca ON co.alan_id = ca.alan_id
        WHERE co.kullanici_id = %s
        ORDER BY co.giris_zamani DESC
    """, (session['user_id'],))
    
    oturumlar = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('oturumlarim.html', oturumlar=oturumlar)

@app.route('/admin')
@admin_required
def admin_panel():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as toplam FROM kullanicilar WHERE rol = 'ogrenci'")
    ogrenci_sayisi = cur.fetchone()['toplam']
    
    cur.execute("SELECT COUNT(*) as toplam FROM rezervasyonlar WHERE durum = 'aktif'")
    aktif_rez = cur.fetchone()['toplam']
    
    cur.execute("SELECT COUNT(*) as toplam FROM calisma_alanlari WHERE aktif = TRUE")
    aktif_alan = cur.fetchone()['toplam']
    
    cur.execute("""
        SELECT * FROM log_kayitlari 
        ORDER BY islem_zamani DESC 
        LIMIT 20
    """)
    loglar = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin_panel.html',
                         ogrenci_sayisi=ogrenci_sayisi,
                         aktif_rez=aktif_rez,
                         aktif_alan=aktif_alan,
                         loglar=loglar)

@app.route('/admin/raporlar')
@admin_required
def admin_raporlar():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DATE(baslangic_zamani) as tarih, COUNT(*) as sayi
        FROM rezervasyonlar
        WHERE baslangic_zamani >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(baslangic_zamani)
        ORDER BY tarih
    """)
    gunluk_rez = cur.fetchall()
    
    cur.execute("""
        SELECT EXTRACT(HOUR FROM baslangic_zamani) as saat, COUNT(*) as sayi
        FROM rezervasyonlar
        WHERE baslangic_zamani >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY saat
        ORDER BY saat
    """)
    saatlik_dagilim = cur.fetchall()
    
    cur.execute("""
        SELECT ca.alan_adi, COUNT(r.rezervasyon_id) as rez_sayisi
        FROM calisma_alanlari ca
        LEFT JOIN rezervasyonlar r ON ca.alan_id = r.alan_id
        GROUP BY ca.alan_id, ca.alan_adi
        ORDER BY rez_sayisi DESC
        LIMIT 10
    """)
    alan_popularite = cur.fetchall()
    
    cur.execute("""
        SELECT 
            COUNT(*) as toplam_kullanici,
            COUNT(CASE WHEN aktif THEN 1 END) as aktif_kullanici,
            COUNT(CASE WHEN rol = 'admin' THEN 1 END) as admin_sayisi
        FROM kullanicilar
    """)
    kullanici_stats = cur.fetchone()
    
    cur.execute("""
        SELECT 
            COUNT(*) as toplam_rezervasyon,
            COUNT(CASE WHEN durum = 'aktif' THEN 1 END) as aktif,
            COUNT(CASE WHEN durum = 'iptal' THEN 1 END) as iptal,
            COUNT(CASE WHEN durum = 'tamamlandi' THEN 1 END) as tamamlandi
        FROM rezervasyonlar
    """)
    rez_stats = cur.fetchone()
    
    cur.execute("""
        SELECT 
            COUNT(*) as toplam_oturum,
            COALESCE(ROUND(AVG(verimlilik_puani), 1), 0) as ort_verimlilik,
            COALESCE(ROUND(AVG(EXTRACT(EPOCH FROM (cikis_zamani - giris_zamani)) / 60), 0), 0) as ort_sure_dk
        FROM calisma_oturumlari
        WHERE cikis_zamani IS NOT NULL
    """)
    oturum_stats = cur.fetchone()
    
    cur.execute("""
        SELECT TO_CHAR(DATE_TRUNC('week', giris_zamani), 'DD.MM') as hafta, 
               COUNT(*) as sayi
        FROM calisma_oturumlari
        WHERE giris_zamani >= CURRENT_DATE - INTERVAL '8 weeks'
        GROUP BY DATE_TRUNC('week', giris_zamani)
        ORDER BY DATE_TRUNC('week', giris_zamani)
    """)
    haftalik_oturum = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin_raporlar.html',
                         gunluk_rez=gunluk_rez,
                         saatlik_dagilim=saatlik_dagilim,
                         alan_popularite=alan_popularite,
                         kullanici_stats=kullanici_stats,
                         rez_stats=rez_stats,
                         oturum_stats=oturum_stats,
                         haftalik_oturum=haftalik_oturum)

@app.route('/admin/kullanicilar')
@admin_required
def admin_kullanicilar():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT k.*, 
               COUNT(DISTINCT r.rezervasyon_id) as rez_sayisi,
               COUNT(DISTINCT co.oturum_id) as oturum_sayisi
        FROM kullanicilar k
        LEFT JOIN rezervasyonlar r ON k.kullanici_id = r.kullanici_id
        LEFT JOIN calisma_oturumlari co ON k.kullanici_id = co.kullanici_id
        GROUP BY k.kullanici_id
        ORDER BY k.kayit_tarihi DESC
    """)
    kullanicilar = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin_kullanicilar.html', kullanicilar=kullanicilar)

@app.route('/admin/alanlar')
@admin_required
def admin_alanlar():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT ca.*, at.tur_adi,
               COUNT(r.rezervasyon_id) as toplam_rez
        FROM calisma_alanlari ca
        JOIN alan_turleri at ON ca.tur_id = at.tur_id
        LEFT JOIN rezervasyonlar r ON ca.alan_id = r.alan_id
        GROUP BY ca.alan_id, at.tur_adi
        ORDER BY ca.konum, ca.alan_adi
    """)
    alanlar = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin_alanlar.html', alanlar=alanlar)

@app.route('/admin/loglar')
@admin_required
def admin_loglar():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM log_kayitlari 
        ORDER BY islem_zamani DESC 
        LIMIT 100
    """)
    loglar = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin_loglar.html', loglar=loglar)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
