DROP TABLE IF EXISTS calisma_oturumlari CASCADE;
DROP TABLE IF EXISTS rezervasyonlar CASCADE;
DROP TABLE IF EXISTS calisma_alanlari CASCADE;
DROP TABLE IF EXISTS alan_turleri CASCADE;
DROP TABLE IF EXISTS kullanicilar CASCADE;
DROP TABLE IF EXISTS log_kayitlari CASCADE;

DROP SEQUENCE IF EXISTS rezervasyon_seq CASCADE;
DROP SEQUENCE IF EXISTS oturum_seq CASCADE;

CREATE SEQUENCE rezervasyon_seq
    START WITH 1000
    INCREMENT BY 1
    NO MAXVALUE
    NO CYCLE;

CREATE SEQUENCE oturum_seq
    START WITH 5000
    INCREMENT BY 1
    NO MAXVALUE
    NO CYCLE;

CREATE TABLE kullanicilar (
    kullanici_id SERIAL PRIMARY KEY,
    ogrenci_no VARCHAR(20) UNIQUE NOT NULL,
    ad VARCHAR(50) NOT NULL,
    soyad VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    sifre VARCHAR(255) NOT NULL,
    telefon VARCHAR(15),
    rol VARCHAR(20) DEFAULT 'ogrenci' CHECK (rol IN ('ogrenci', 'admin')),
    aktif BOOLEAN DEFAULT TRUE,
    kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    toplam_calisma_suresi INTEGER DEFAULT 0
);

CREATE TABLE alan_turleri (
    tur_id SERIAL PRIMARY KEY,
    tur_adi VARCHAR(50) NOT NULL UNIQUE,
    aciklama TEXT,
    max_kapasite INTEGER NOT NULL CHECK (max_kapasite > 0),
    saatlik_limit INTEGER DEFAULT 4 CHECK (saatlik_limit BETWEEN 1 AND 8)
);

CREATE TABLE calisma_alanlari (
    alan_id SERIAL PRIMARY KEY,
    alan_adi VARCHAR(100) NOT NULL,
    tur_id INTEGER NOT NULL REFERENCES alan_turleri(tur_id) ON DELETE RESTRICT,
    konum VARCHAR(100) NOT NULL,
    kapasite INTEGER NOT NULL CHECK (kapasite > 0 AND kapasite <= 50),
    priz_var BOOLEAN DEFAULT FALSE,
    sessiz_alan BOOLEAN DEFAULT FALSE,
    aktif BOOLEAN DEFAULT TRUE,
    UNIQUE(alan_adi, konum)
);

CREATE TABLE rezervasyonlar (
    rezervasyon_id INTEGER PRIMARY KEY DEFAULT nextval('rezervasyon_seq'),
    kullanici_id INTEGER NOT NULL REFERENCES kullanicilar(kullanici_id) ON DELETE CASCADE,
    alan_id INTEGER NOT NULL REFERENCES calisma_alanlari(alan_id) ON DELETE RESTRICT,
    baslangic_zamani TIMESTAMP NOT NULL,
    bitis_zamani TIMESTAMP NOT NULL,
    durum VARCHAR(20) DEFAULT 'aktif' CHECK (durum IN ('aktif', 'iptal', 'tamamlandi')),
    olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notlar TEXT,
    CONSTRAINT sure_kontrolu CHECK (bitis_zamani > baslangic_zamani),
    CONSTRAINT max_sure_kontrolu CHECK (
        EXTRACT(EPOCH FROM (bitis_zamani - baslangic_zamani)) / 3600 <= 4
    )
);

CREATE TABLE calisma_oturumlari (
    oturum_id INTEGER PRIMARY KEY DEFAULT nextval('oturum_seq'),
    rezervasyon_id INTEGER REFERENCES rezervasyonlar(rezervasyon_id) ON DELETE SET NULL,
    kullanici_id INTEGER NOT NULL REFERENCES kullanicilar(kullanici_id) ON DELETE CASCADE,
    alan_id INTEGER NOT NULL REFERENCES calisma_alanlari(alan_id) ON DELETE RESTRICT,
    giris_zamani TIMESTAMP NOT NULL,
    cikis_zamani TIMESTAMP,
    verimlilik_puani INTEGER CHECK (verimlilik_puani BETWEEN 1 AND 10),
    notlar TEXT
);

CREATE TABLE log_kayitlari (
    log_id SERIAL PRIMARY KEY,
    islem_tipi VARCHAR(50) NOT NULL,
    tablo_adi VARCHAR(50) NOT NULL,
    kayit_id INTEGER,
    eski_deger TEXT,
    yeni_deger TEXT,
    kullanici_bilgisi TEXT,
    islem_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rezervasyonlar_tarih ON rezervasyonlar(baslangic_zamani, bitis_zamani);
CREATE INDEX idx_rezervasyonlar_kullanici ON rezervasyonlar(kullanici_id);
CREATE INDEX idx_rezervasyonlar_alan ON rezervasyonlar(alan_id);
CREATE INDEX idx_rezervasyonlar_durum ON rezervasyonlar(durum);
CREATE INDEX idx_kullanicilar_ogrenci_no ON kullanicilar(ogrenci_no);
CREATE INDEX idx_kullanicilar_email ON kullanicilar(email);
CREATE INDEX idx_calisma_alanlari_konum ON calisma_alanlari(konum);
CREATE INDEX idx_calisma_alanlari_tur ON calisma_alanlari(tur_id);

INSERT INTO alan_turleri (tur_adi, aciklama, max_kapasite, saatlik_limit) VALUES
('Bireysel Masa', 'Tek kişilik çalışma masası', 1, 4),
('Grup Masası', '4-6 kişilik grup çalışma masası', 6, 3),
('Sessiz Oda', 'Sessiz çalışma odası', 1, 4),
('Toplantı Odası', 'Grup toplantıları için oda', 10, 2),
('Bilgisayar Masası', 'Bilgisayarlı çalışma masası', 1, 3),
('Proje Odası', 'Proje çalışmaları için geniş oda', 8, 4),
('Seminer Salonu', 'Sunum ve seminerler için', 30, 2),
('Kütüphane Köşesi', 'Kitap okuma köşesi', 2, 4),
('Laboratuvar', 'Deneysel çalışmalar için', 4, 3),
('Çok Amaçlı Alan', 'Esnek kullanımlı alan', 15, 3);

INSERT INTO kullanicilar (ogrenci_no, ad, soyad, email, sifre, telefon, rol, toplam_calisma_suresi) VALUES
('ADMIN001', 'Sistem', 'Yönetici', 'admin@std.yildiz.edu.tr', 'admin123', '5551234567', 'admin', 0),
('ADMIN002', 'Kütüphane', 'Sorumlusu', 'kutuphane@std.yildiz.edu.tr', 'lib123', '5551234568', 'admin', 0),
('20210001', 'Ahmet', 'Yılmaz', 'ahmet.yilmaz@std.yildiz.edu.tr', 'sifre123', '5321112233', 'ogrenci', 1250),
('20210002', 'Ayşe', 'Kaya', 'ayse.kaya@std.yildiz.edu.tr', 'sifre123', '5322223344', 'ogrenci', 890),
('20210003', 'Mehmet', 'Demir', 'mehmet.demir@std.yildiz.edu.tr', 'sifre123', '5323334455', 'ogrenci', 2100),
('20210004', 'Fatma', 'Çelik', 'fatma.celik@std.yildiz.edu.tr', 'sifre123', '5324445566', 'ogrenci', 1560),
('20210005', 'Ali', 'Öztürk', 'ali.ozturk@std.yildiz.edu.tr', 'sifre123', '5325556677', 'ogrenci', 720),
('20210006', 'Zeynep', 'Arslan', 'zeynep.arslan@std.yildiz.edu.tr', 'sifre123', '5326667788', 'ogrenci', 1890),
('20210007', 'Mustafa', 'Şahin', 'mustafa.sahin@std.yildiz.edu.tr', 'sifre123', '5327778899', 'ogrenci', 450),
('20210008', 'Elif', 'Yıldız', 'elif.yildiz@std.yildiz.edu.tr', 'sifre123', '5328889900', 'ogrenci', 2340),
('20210009', 'Emre', 'Aydın', 'emre.aydin@std.yildiz.edu.tr', 'sifre123', '5329990011', 'ogrenci', 1100),
('20210010', 'Selin', 'Koç', 'selin.koc@std.yildiz.edu.tr', 'sifre123', '5320001122', 'ogrenci', 1780);

INSERT INTO calisma_alanlari (alan_adi, tur_id, konum, kapasite, priz_var, sessiz_alan) VALUES
('Masa A1', 1, 'Merkez Kütüphane - Zemin Kat', 1, TRUE, FALSE),
('Masa A2', 1, 'Merkez Kütüphane - Zemin Kat', 1, TRUE, FALSE),
('Masa A3', 1, 'Merkez Kütüphane - Zemin Kat', 1, FALSE, FALSE),
('Grup Masası G1', 2, 'Merkez Kütüphane - 1. Kat', 6, TRUE, FALSE),
('Grup Masası G2', 2, 'Merkez Kütüphane - 1. Kat', 4, TRUE, FALSE),
('Sessiz Oda S1', 3, 'Merkez Kütüphane - 2. Kat', 1, TRUE, TRUE),
('Sessiz Oda S2', 3, 'Merkez Kütüphane - 2. Kat', 1, TRUE, TRUE),
('Toplantı Odası T1', 4, 'Mühendislik Fakültesi - A Blok', 10, TRUE, FALSE),
('Bilgisayar Masası B1', 5, 'Bilgisayar Merkezi', 1, TRUE, FALSE),
('Bilgisayar Masası B2', 5, 'Bilgisayar Merkezi', 1, TRUE, FALSE),
('Proje Odası P1', 6, 'Mühendislik Fakültesi - B Blok', 8, TRUE, FALSE),
('Seminer Salonu SS1', 7, 'Konferans Merkezi', 30, TRUE, FALSE),
('Okuma Köşesi OK1', 8, 'Merkez Kütüphane - 3. Kat', 2, FALSE, TRUE),
('Lab L1', 9, 'Fen Fakültesi - Zemin Kat', 4, TRUE, FALSE),
('Çok Amaçlı CA1', 10, 'Öğrenci Merkezi', 15, TRUE, FALSE);

INSERT INTO rezervasyonlar (kullanici_id, alan_id, baslangic_zamani, bitis_zamani, durum, notlar) VALUES
(3, 1, '2025-01-15 09:00:00', '2025-01-15 11:00:00', 'tamamlandi', 'Matematik çalışması'),
(4, 2, '2025-01-15 10:00:00', '2025-01-15 12:00:00', 'tamamlandi', 'Fizik ödevi'),
(5, 4, '2025-01-15 14:00:00', '2025-01-15 17:00:00', 'tamamlandi', 'Grup projesi toplantısı'),
(6, 6, '2025-01-16 09:00:00', '2025-01-16 13:00:00', 'tamamlandi', 'Tez çalışması'),
(7, 8, '2025-01-16 15:00:00', '2025-01-16 17:00:00', 'iptal', NULL),
(8, 9, '2025-01-17 10:00:00', '2025-01-17 12:00:00', 'tamamlandi', 'Programlama ödevi'),
(3, 3, '2025-01-18 08:00:00', '2025-01-18 11:00:00', 'aktif', 'Final çalışması'),
(4, 5, '2025-01-18 13:00:00', '2025-01-18 16:00:00', 'aktif', 'Grup çalışması'),
(5, 7, '2025-01-19 09:00:00', '2025-01-19 11:00:00', 'aktif', 'Sessiz çalışma'),
(6, 1, '2025-01-20 10:00:00', '2025-01-20 14:00:00', 'aktif', 'Araştırma'),
(9, 11, '2025-01-17 14:00:00', '2025-01-17 18:00:00', 'tamamlandi', 'Proje sunumu hazırlık'),
(10, 13, '2025-01-18 16:00:00', '2025-01-18 18:00:00', 'aktif', 'Kitap okuma'),
(11, 14, '2025-01-19 10:00:00', '2025-01-19 13:00:00', 'aktif', 'Deney hazırlığı'),
(12, 15, '2025-01-19 14:00:00', '2025-01-19 17:00:00', 'aktif', 'Etkinlik organizasyonu'),
(3, 6, '2025-01-21 09:00:00', '2025-01-21 12:00:00', 'aktif', 'Vize çalışması');

INSERT INTO calisma_oturumlari (kullanici_id, alan_id, giris_zamani, cikis_zamani, verimlilik_puani, notlar) VALUES
(3, 1, '2025-01-15 09:05:00', '2025-01-15 10:55:00', 8, 'Verimli çalışma'),
(4, 2, '2025-01-15 10:10:00', '2025-01-15 11:50:00', 7, NULL),
(5, 4, '2025-01-15 14:15:00', '2025-01-15 16:45:00', 9, 'Harika toplantı'),
(6, 6, '2025-01-16 09:00:00', '2025-01-16 12:30:00', 10, 'Çok verimli'),
(8, 9, '2025-01-17 10:05:00', '2025-01-17 11:55:00', 6, 'Biraz dağınık'),
(9, 11, '2025-01-17 14:10:00', '2025-01-17 17:50:00', 8, NULL),
(3, 3, '2025-01-14 08:00:00', '2025-01-14 11:30:00', 9, 'Erken başladım'),
(4, 1, '2025-01-14 14:00:00', '2025-01-14 16:00:00', 7, NULL),
(5, 2, '2025-01-14 09:00:00', '2025-01-14 12:00:00', 8, 'Güzel çalışma'),
(6, 4, '2025-01-13 15:00:00', '2025-01-13 18:00:00', 6, 'Gürültülüydü'),
(7, 6, '2025-01-13 10:00:00', '2025-01-13 13:00:00', 9, NULL),
(8, 8, '2025-01-12 11:00:00', '2025-01-12 14:00:00', 8, 'Toplantı verimli geçti');

CREATE OR REPLACE FUNCTION log_rezervasyon_degisiklik()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO log_kayitlari (islem_tipi, tablo_adi, kayit_id, yeni_deger, kullanici_bilgisi)
        VALUES ('INSERT', 'rezervasyonlar', NEW.rezervasyon_id, 
                'Alan: ' || NEW.alan_id || ', Başlangıç: ' || NEW.baslangic_zamani,
                'Kullanıcı ID: ' || NEW.kullanici_id);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO log_kayitlari (islem_tipi, tablo_adi, kayit_id, eski_deger, yeni_deger, kullanici_bilgisi)
        VALUES ('UPDATE', 'rezervasyonlar', NEW.rezervasyon_id,
                'Eski Durum: ' || OLD.durum,
                'Yeni Durum: ' || NEW.durum,
                'Kullanıcı ID: ' || NEW.kullanici_id);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO log_kayitlari (islem_tipi, tablo_adi, kayit_id, eski_deger, kullanici_bilgisi)
        VALUES ('DELETE', 'rezervasyonlar', OLD.rezervasyon_id,
                'Silinen rezervasyon - Alan: ' || OLD.alan_id,
                'Kullanıcı ID: ' || OLD.kullanici_id);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_rezervasyon_log
AFTER INSERT OR UPDATE OR DELETE ON rezervasyonlar
FOR EACH ROW EXECUTE FUNCTION log_rezervasyon_degisiklik();

CREATE OR REPLACE FUNCTION guncelle_calisma_suresi()
RETURNS TRIGGER AS $$
DECLARE
    sure_dakika INTEGER;
BEGIN
    IF NEW.cikis_zamani IS NOT NULL AND OLD.cikis_zamani IS NULL THEN
        sure_dakika := EXTRACT(EPOCH FROM (NEW.cikis_zamani - NEW.giris_zamani)) / 60;
        
        UPDATE kullanicilar 
        SET toplam_calisma_suresi = toplam_calisma_suresi + sure_dakika
        WHERE kullanici_id = NEW.kullanici_id;
        
        INSERT INTO log_kayitlari (islem_tipi, tablo_adi, kayit_id, yeni_deger, kullanici_bilgisi)
        VALUES ('CALISMA_SURESI', 'calisma_oturumlari', NEW.oturum_id,
                'Eklenen süre: ' || sure_dakika || ' dakika',
                'Kullanıcı ID: ' || NEW.kullanici_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calisma_suresi_guncelle
AFTER UPDATE ON calisma_oturumlari
FOR EACH ROW EXECUTE FUNCTION guncelle_calisma_suresi();

CREATE OR REPLACE VIEW v_aktif_rezervasyonlar AS
SELECT 
    r.rezervasyon_id,
    k.ogrenci_no,
    k.ad || ' ' || k.soyad AS kullanici_adi,
    ca.alan_adi,
    at.tur_adi AS alan_turu,
    ca.konum,
    r.baslangic_zamani,
    r.bitis_zamani,
    r.notlar
FROM rezervasyonlar r
JOIN kullanicilar k ON r.kullanici_id = k.kullanici_id
JOIN calisma_alanlari ca ON r.alan_id = ca.alan_id
JOIN alan_turleri at ON ca.tur_id = at.tur_id
WHERE r.durum = 'aktif'
ORDER BY r.baslangic_zamani;

CREATE OR REPLACE VIEW v_kullanici_istatistikleri AS
SELECT 
    k.kullanici_id,
    k.ogrenci_no,
    k.ad || ' ' || k.soyad AS kullanici_adi,
    COUNT(DISTINCT r.rezervasyon_id) AS toplam_rezervasyon,
    COUNT(DISTINCT CASE WHEN r.durum = 'aktif' THEN r.rezervasyon_id END) AS aktif_rezervasyon,
    COUNT(DISTINCT CASE WHEN r.durum = 'iptal' THEN r.rezervasyon_id END) AS iptal_rezervasyon,
    COUNT(DISTINCT co.oturum_id) AS toplam_oturum,
    COALESCE(ROUND(AVG(co.verimlilik_puani), 2), 0) AS ortalama_verimlilik,
    k.toplam_calisma_suresi AS toplam_calisma_dakika
FROM kullanicilar k
LEFT JOIN rezervasyonlar r ON k.kullanici_id = r.kullanici_id
LEFT JOIN calisma_oturumlari co ON k.kullanici_id = co.kullanici_id
WHERE k.rol = 'ogrenci'
GROUP BY k.kullanici_id, k.ogrenci_no, k.ad, k.soyad, k.toplam_calisma_suresi;

CREATE OR REPLACE VIEW v_alan_doluluk AS
SELECT 
    ca.alan_id,
    ca.alan_adi,
    ca.konum,
    at.tur_adi,
    ca.kapasite,
    COUNT(CASE WHEN r.durum = 'aktif' THEN 1 END) AS aktif_rezervasyon_sayisi,
    ca.aktif AS alan_aktif
FROM calisma_alanlari ca
JOIN alan_turleri at ON ca.tur_id = at.tur_id
LEFT JOIN rezervasyonlar r ON ca.alan_id = r.alan_id
GROUP BY ca.alan_id, ca.alan_adi, ca.konum, at.tur_adi, ca.kapasite, ca.aktif;

CREATE OR REPLACE FUNCTION fn_musait_alanlar(
    p_tarih DATE,
    p_baslangic TIME,
    p_bitis TIME
)
RETURNS TABLE (
    alan_id INTEGER,
    alan_adi VARCHAR(100),
    konum VARCHAR(100),
    tur_adi VARCHAR(50),
    kapasite INTEGER,
    priz_var BOOLEAN,
    sessiz_alan BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ca.alan_id,
        ca.alan_adi,
        ca.konum,
        at.tur_adi,
        ca.kapasite,
        ca.priz_var,
        ca.sessiz_alan
    FROM calisma_alanlari ca
    JOIN alan_turleri at ON ca.tur_id = at.tur_id
    WHERE ca.aktif = TRUE
    AND NOT EXISTS (
        SELECT 1 FROM rezervasyonlar r
        WHERE r.alan_id = ca.alan_id
        AND r.durum = 'aktif'
        AND DATE(r.baslangic_zamani) = p_tarih
        AND (
            (r.baslangic_zamani::TIME <= p_baslangic AND r.bitis_zamani::TIME > p_baslangic)
            OR (r.baslangic_zamani::TIME < p_bitis AND r.bitis_zamani::TIME >= p_bitis)
            OR (r.baslangic_zamani::TIME >= p_baslangic AND r.bitis_zamani::TIME <= p_bitis)
        )
    )
    ORDER BY ca.konum, ca.alan_adi;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_kullanici_detay(p_kullanici_id INTEGER)
RETURNS TABLE (
    kullanici_id INTEGER,
    ogrenci_no VARCHAR(20),
    ad_soyad TEXT,
    email VARCHAR(100),
    rol VARCHAR(20),
    kayit_tarihi TIMESTAMP,
    toplam_rezervasyon BIGINT,
    aktif_rezervasyon BIGINT,
    toplam_oturum BIGINT,
    ortalama_verimlilik NUMERIC,
    toplam_calisma_saat NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        k.kullanici_id,
        k.ogrenci_no,
        k.ad || ' ' || k.soyad,
        k.email,
        k.rol,
        k.kayit_tarihi,
        COUNT(DISTINCT r.rezervasyon_id),
        COUNT(DISTINCT CASE WHEN r.durum = 'aktif' THEN r.rezervasyon_id END),
        COUNT(DISTINCT co.oturum_id),
        ROUND(AVG(co.verimlilik_puani), 2),
        ROUND(k.toplam_calisma_suresi / 60.0, 2)
    FROM kullanicilar k
    LEFT JOIN rezervasyonlar r ON k.kullanici_id = r.kullanici_id
    LEFT JOIN calisma_oturumlari co ON k.kullanici_id = co.kullanici_id
    WHERE k.kullanici_id = p_kullanici_id
    GROUP BY k.kullanici_id, k.ogrenci_no, k.ad, k.soyad, k.email, k.rol, k.kayit_tarihi, k.toplam_calisma_suresi;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_yogunluk_analizi(p_gun_sayisi INTEGER DEFAULT 30)
RETURNS TABLE (
    saat_dilimi TEXT,
    rezervasyon_sayisi BIGINT,
    yogunluk_seviyesi TEXT
) AS $$
DECLARE
    saat_cursor CURSOR FOR
        SELECT 
            TO_CHAR(baslangic_zamani, 'HH24:00') || '-' || TO_CHAR(baslangic_zamani + INTERVAL '1 hour', 'HH24:00') AS dilim,
            COUNT(*) AS sayi
        FROM rezervasyonlar
        WHERE baslangic_zamani >= CURRENT_DATE - (p_gun_sayisi || ' days')::INTERVAL
        GROUP BY TO_CHAR(baslangic_zamani, 'HH24:00'), TO_CHAR(baslangic_zamani + INTERVAL '1 hour', 'HH24:00')
        ORDER BY TO_CHAR(baslangic_zamani, 'HH24:00');
    saat_kayit RECORD;
    max_sayi BIGINT;
BEGIN
    SELECT MAX(cnt) INTO max_sayi
    FROM (
        SELECT COUNT(*) as cnt
        FROM rezervasyonlar
        WHERE baslangic_zamani >= CURRENT_DATE - (p_gun_sayisi || ' days')::INTERVAL
        GROUP BY TO_CHAR(baslangic_zamani, 'HH24:00')
    ) subq;

    IF max_sayi IS NULL THEN
        max_sayi := 1;
    END IF;

    OPEN saat_cursor;
    LOOP
        FETCH saat_cursor INTO saat_kayit;
        EXIT WHEN NOT FOUND;
        
        saat_dilimi := saat_kayit.dilim;
        rezervasyon_sayisi :=	 saat_kayit.sayi;
        
        IF saat_kayit.sayi >= max_sayi * 0.7 THEN
            yogunluk_seviyesi := 'YOĞUN';
        ELSIF saat_kayit.sayi >= max_sayi * 0.4 THEN
            yogunluk_seviyesi := 'ORTA';
        ELSE
            yogunluk_seviyesi := 'DÜŞÜK';
        END IF;
        
        RETURN NEXT;
    END LOOP;
    CLOSE saat_cursor;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE VIEW v_aktif_ogrenciler AS
SELECT DISTINCT k.kullanici_id, k.ogrenci_no, k.ad, k.soyad, 'Rezervasyon' AS aktivite_tipi
FROM kullanicilar k
JOIN rezervasyonlar r ON k.kullanici_id = r.kullanici_id
WHERE k.rol = 'ogrenci'
UNION
SELECT DISTINCT k.kullanici_id, k.ogrenci_no, k.ad, k.soyad, 'Oturum' AS aktivite_tipi
FROM kullanicilar k
JOIN calisma_oturumlari co ON k.kullanici_id = co.kullanici_id
WHERE k.rol = 'ogrenci';

CREATE OR REPLACE VIEW v_sadece_rezervasyon AS
SELECT k.kullanici_id, k.ogrenci_no, k.ad || ' ' || k.soyad AS kullanici_adi
FROM kullanicilar k
WHERE k.kullanici_id IN (
    SELECT DISTINCT kullanici_id FROM rezervasyonlar
    EXCEPT
    SELECT DISTINCT kullanici_id FROM calisma_oturumlari
);

CREATE OR REPLACE VIEW v_tam_katilimci AS
SELECT k.kullanici_id, k.ogrenci_no, k.ad || ' ' || k.soyad AS kullanici_adi
FROM kullanicilar k
WHERE k.kullanici_id IN (
    SELECT DISTINCT kullanici_id FROM rezervasyonlar
    INTERSECT
    SELECT DISTINCT kullanici_id FROM calisma_oturumlari
);

CREATE OR REPLACE VIEW v_basarili_ogrenciler AS
SELECT 
    k.kullanici_id,
    k.ogrenci_no,
    k.ad || ' ' || k.soyad AS kullanici_adi,
    COUNT(DISTINCT r.rezervasyon_id) AS toplam_rezervasyon,
    COUNT(DISTINCT co.oturum_id) AS toplam_oturum,
    ROUND(AVG(co.verimlilik_puani), 2) AS ortalama_verimlilik,
    SUM(EXTRACT(EPOCH FROM (co.cikis_zamani - co.giris_zamani)) / 3600) AS toplam_saat
FROM kullanicilar k
JOIN rezervasyonlar r ON k.kullanici_id = r.kullanici_id
LEFT JOIN calisma_oturumlari co ON k.kullanici_id = co.kullanici_id
WHERE k.rol = 'ogrenci'
GROUP BY k.kullanici_id, k.ogrenci_no, k.ad, k.soyad
HAVING COUNT(DISTINCT r.rezervasyon_id) >= 2 
   AND AVG(co.verimlilik_puani) > 7;

DROP ROLE IF EXISTS studyflow_admin;
DROP ROLE IF EXISTS studyflow_ogrenci;

CREATE ROLE studyflow_admin WITH LOGIN PASSWORD 'admin_sifre_123';
CREATE ROLE studyflow_ogrenci WITH LOGIN PASSWORD 'ogrenci_sifre_123';

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO studyflow_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO studyflow_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO studyflow_admin;

GRANT SELECT ON kullanicilar TO studyflow_ogrenci;
GRANT SELECT ON alan_turleri TO studyflow_ogrenci;
GRANT SELECT ON calisma_alanlari TO studyflow_ogrenci;
GRANT SELECT, INSERT ON rezervasyonlar TO studyflow_ogrenci;
GRANT UPDATE (durum, notlar) ON rezervasyonlar TO studyflow_ogrenci;
GRANT SELECT, INSERT ON calisma_oturumlari TO studyflow_ogrenci;
GRANT UPDATE (cikis_zamani, verimlilik_puani, notlar) ON calisma_oturumlari TO studyflow_ogrenci;
GRANT SELECT ON log_kayitlari TO studyflow_ogrenci;

GRANT SELECT ON v_aktif_rezervasyonlar TO studyflow_ogrenci;
GRANT SELECT ON v_kullanici_istatistikleri TO studyflow_ogrenci;
GRANT SELECT ON v_alan_doluluk TO studyflow_ogrenci;
GRANT SELECT ON v_aktif_ogrenciler TO studyflow_ogrenci;
GRANT SELECT ON v_basarili_ogrenciler TO studyflow_ogrenci;
GRANT SELECT ON v_sadece_rezervasyon TO studyflow_ogrenci;
GRANT SELECT ON v_tam_katilimci TO studyflow_ogrenci;

GRANT USAGE ON SEQUENCE rezervasyon_seq TO studyflow_ogrenci;
GRANT USAGE ON SEQUENCE oturum_seq TO studyflow_ogrenci;

GRANT EXECUTE ON FUNCTION fn_musait_alanlar(DATE, TIME, TIME) TO studyflow_ogrenci;
GRANT EXECUTE ON FUNCTION fn_kullanici_detay(INTEGER) TO studyflow_ogrenci;
GRANT EXECUTE ON FUNCTION fn_yogunluk_analizi(INTEGER) TO studyflow_ogrenci;

CREATE OR REPLACE FUNCTION fn_uygun_zaman_onerisi(
    p_alan_id INTEGER,
    p_tarih DATE,
    p_sure_saat INTEGER DEFAULT 2
)
RETURNS TABLE (
    oneri_baslangic TIME,
    oneri_bitis TIME,
    yogunluk TEXT
) AS $$
DECLARE
    saat_cursor CURSOR FOR
        WITH saatler AS (
            SELECT (generate_series(
                p_tarih + '08:00'::TIME,
                p_tarih + '20:00'::TIME,
                '1 hour'::INTERVAL
            ))::TIME AS saat
        ),
        dolu_saatler AS (
            SELECT DISTINCT baslangic_zamani::TIME AS dolu_saat
            FROM rezervasyonlar
            WHERE alan_id = p_alan_id
            AND DATE(baslangic_zamani) = p_tarih
            AND durum = 'aktif'
            UNION
            SELECT DISTINCT (baslangic_zamani + INTERVAL '1 hour')::TIME
            FROM rezervasyonlar
            WHERE alan_id = p_alan_id
            AND DATE(baslangic_zamani) = p_tarih
            AND durum = 'aktif'
            AND bitis_zamani - baslangic_zamani > INTERVAL '1 hour'
        )
        SELECT s.saat
        FROM saatler s
        WHERE NOT EXISTS (
            SELECT 1 FROM dolu_saatler d WHERE d.dolu_saat = s.saat
        )
        AND s.saat + (p_sure_saat || ' hours')::INTERVAL <= '22:00'::TIME
        ORDER BY s.saat;
    
    saat_kayit RECORD;
    toplam_rez INTEGER;
BEGIN
    SELECT COUNT(*) INTO toplam_rez
    FROM rezervasyonlar
    WHERE DATE(baslangic_zamani) = p_tarih AND durum = 'aktif';
    
    OPEN saat_cursor;
    LOOP
        FETCH saat_cursor INTO saat_kayit;
        EXIT WHEN NOT FOUND;
        
        oneri_baslangic := saat_kayit.saat;
        oneri_bitis := saat_kayit.saat + (p_sure_saat || ' hours')::INTERVAL;
        
        IF EXTRACT(HOUR FROM saat_kayit.saat) BETWEEN 10 AND 14 THEN
            yogunluk := 'YOĞUN SAAT';
        ELSIF EXTRACT(HOUR FROM saat_kayit.saat) BETWEEN 15 AND 18 THEN
            yogunluk := 'ORTA YOĞUNLUK';
        ELSE
            yogunluk := 'SAKİN';
        END IF;
        
        RETURN NEXT;
    END LOOP;
    CLOSE saat_cursor;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION fn_uygun_zaman_onerisi(INTEGER, DATE, INTEGER) TO studyflow_ogrenci;

COMMIT;
