# Texniki Tapşırıq: ilkmusic (Mahnı Axtarış Tətbiqi)

> Status: Mərhələ 1 kodlanıb və yoxlanıb · Son yenilənmə: 2026-10-24

## 1. Ümumi təsvir

Öz kompüterində işləyən veb tətbiq. İstifadəçi mahnının adını yazır, YouTube linki yapışdırır və ya mahnını mikrofona səsləndirir. Tətbiq mahnını YouTube-da tapır. Mahnını tətbiqin içində dinləmək və MP3 kimi yükləmək olur.

Mahnıların mənbəyi: **YouTube**.

## 2. Funksional tələblər

### F1. Ad ilə axtarış
- Axtarış sahəsinə mahnının adı yazılır.
- Tətbiq YouTube-da axtarır və **10 nəticə** göstərir: ad, kanal/ifaçı, müddət, şəkil.
- Hər nəticədə "Dinlə" və "MP3 yüklə" düymələri olur.

### F2. YouTube linki ilə axtarış
- İstifadəçi axtarış sahəsinə YouTube linki yapışdırır.
- Tətbiq linki tanıyır və həmin videonun məlumatlarını göstərir.
- Mahnını dinləmək və MP3 kimi yükləmək olur.

### F3. Səslə axtarış (Shazam kimi)
- İstifadəçi "Səslə axtar" düyməsini basır.
- Brauzer mikrofondan təxminən 10 saniyə səs yazır.
- Tətbiq mahnını tanıyır: ad + ifaçı.
- Tanınan ad ilə avtomatik F1 axtarışı başlayır.
- Qeyd: Shazam kimi, orijinal yazını tanıyır (çalan mahnı). Zümzüməni tanımır.

### F4. MP3 yükləmə
- İstifadəçi nəticələrdən bir mahnı seçir.
- Tətbiq YouTube-dan səsi çıxarır, MP3-ə çevirir.
- Fayl brauzer vasitəsilə **"Yükləmələr" (Downloads) qovluğuna** düşür. Tətbiq faylları ayrıca saxlamır.

### F5. Tətbiqin içində dinləmək
- Seçilən mahnı tətbiqin içindəki pleyerdə çalınır (play/pause, irəli-geri çəkmək, səs).

### F7. Ana səhifə (YouTube kimi)
- Tətbiq açılanda, axtarışdan əvvəl ana səhifə görünür: **"Son dinlədiklərin"** və **"Sənə oxşar mahnılar"**.
- Tarixçə hər kompüterdə ayrıca saxlanılır: o kompüterdə dinlənilən və yüklənən mahnılar.
- Oxşar mahnılar son dinlənilən mahnılara əsasən YouTube-un öz tövsiyələrindən (YouTube Mix) götürülür.

### F8. Dizayn: Zaqatala
- Axtarış sahəsinin üstündə böyük "Zaqatala" yazısı.
- Ən arxa fonda Zaqatalanın gözəl şəkli. Mahnılar onun üstündə görünür.

## 3. Texniki tələblər

- Proqramlaşdırma dili: Python
- Platforma: lokal veb tətbiq. Öz kompüterində işləyir, brauzerdə `http://localhost:8000` ilə açılır.
- İşə salma: masaüstündəki ikona iki dəfə basanda tətbiq birbaşa brauzerdə açılır, konsol pəncərəsi görünmür. Səhifə bağlananda server 3 dəqiqə ərzində özü dayanır.

### Texnologiyalar

| Hissə | Alət |
|---|---|
| Backend | FastAPI |
| Frontend | sadə HTML + CSS + JavaScript |
| YouTube axtarış və yükləmə | yt-dlp |
| MP3-ə çevirmə | FFmpeg |
| Səs tanıma (Shazam kimi) | shazamio |
| Brauzerdə səs yazma | MediaRecorder API |

### Kompüterdə lazım olanlar

- Python 3.10 və ya daha yeni
- FFmpeg (yt-dlp MP3-ə çevirmək üçün istifadə edir)

## 4. Mərhələlər

- **Mərhələ 1 (indi):** sadə lokal veb versiya. F1–F5 işləyir.
- **Mərhələ 2 (sonra):** peşəkar versiya (dizayn, sürət, əlavə imkanlar). Detalları sonra müəyyən ediləcək.
  - **F6. Paylaşma:** istifadəçi tətbiqi başqasına link və ya fayl kimi göndərə bilsin, qarşı tərəf açıb istifadə etsin.
    - Variant A, fayl: portativ Windows proqramı. Python + FFmpeg içindədir, quraşdırma tələb etmir. Google Drive/WhatsApp ilə göndərilir.
    - Variant B, link: internetdə server. Pullu, YouTube server IP-lərini tez-tez bloklayır, açıq MP3 servisi hüquqi risklidir.
    - **Seçildi: Variant A (fayl).** Qarşı tərəflər həm kompüter, həm telefon istifadə edir. Telefon üçün həll sonra ayrıca baxılacaq.
    - **Hazırdır:** `dist\ilkmusic.zip` (~130 MB), `packaging\build.py` ilə yığılır. Explorer-dən təmiz qovluqda sınanıb: paketin öz Python-u və FFmpeg-i işləyir, port məşğuldursa 8001–8010 seçilir.
  - **F7, F8:** ana səhifə və Zaqatala dizaynı (bax: bölmə 2).
- **Mərhələ 3: iOS, App Store.** İstifadəçi tətbiqi App Store-a çıxarmaq istəyir.
  - **Məhdudiyyətlər:**
    - App Store qaydası 5.2.3: YouTube kimi mənbələrdən icazəsiz yükləmə, çevirmə və saxlama qadağandır. MP3 yükləmə və YouTube-dan səsin çıxarılması App Store versiyasında ola bilməz.
    - iPhone Python serverini işlədə bilmir, tətbiq Swift (SwiftUI) ilə yenidən yazılmalıdır.
    - Lazımdır: Xcode üçün Mac (və ya bulud Mac xidməti) və Apple Developer Program (ildə 99 $).
  - **Təklif olunan App Store versiyası:**
    - Axtarış: YouTube Data API (rəsmi, API açarı ilə).
    - Dinləmə: YouTube-un rəsmi oynadıcısı tətbiqin içində.
    - Səslə tanıma: Apple-ın rəsmi ShazamKit-i.
    - Ana səhifə (son dinlənilənlər, oxşar mahnılar) və Zaqatala dizaynı.
    - MP3 yükləmə yoxdur.
  - **İstifadəçinin istəyi (2026-11-01):** tətbiqin içində öz "Yükləmələr" bölməsi olsun. Mahnı tətbiqin içinə yüklənsin və internetsiz dinlənsin.
    - Bu, App Store qaydası 5.2.3 ilə ziddiyyət təşkil edir: tətbiqin içində saxlamaq da "save/download" sayılır, App Store qəbul etməz.
    - Mümkün yollar:
      - A) App Store versiyası, yükləmə olmadan.
      - B) Yükləməli versiya yalnız öz iPhone-una Xcode ilə: Mac lazımdır, pulsuz hesabla 7 gündən bir yenilənir.
      - C) Kompüterdəki ilkmusic-i ev Wi-Fi-ı ilə iPhone-un Safari-sindən açmaq: Mac lazım deyil, MP3 iPhone-un "Fayllar" bölməsinə yüklənir. Səslə axtarış HTTPS olmadığı üçün işləməz, kompüter açıq olmalıdır.
  - **Seçildi: C (2026-11-01), hazırdır.**
    - Kompüterdəki ilkmusic-də "📱 Telefonda aç" düyməsi QR kod göstərir.
    - Telefon ev Wi-Fi-ı ilə qoşulur, giriş gizli açarla qorunur.
    - iPhone ana ekran ikonu var.
    - Səslə axtarış telefonda işləmir (HTTPS yoxdur).
  - **Açıq suallar (A/B üçün, sonra):** Mac var? Apple Developer hesabı var?

## 5. İcra planı (Mərhələ 1)

1. Layihənin skeleti: FastAPI server + boş HTML səhifə, `localhost:8000`-da açılır.
2. F1: ad ilə YouTube axtarışı, 10 nəticə.
3. F5: nəticəni tətbiqin içində dinləmək.
4. F4: MP3 yükləmə.
5. F2: YouTube linki ilə axtarış.
6. F3: Shazam kimi səslə axtarış.

## 6. Hüquqi qeyd

YouTube-un istifadə qaydaları videoların yüklənməsini qadağan edir, mahnılar isə müəllif hüququ ilə qorunur. Tətbiq yalnız şəxsi, lokal istifadə üçündür. Mərhələ 2-də internetə çıxarılsa, bu məsələyə yenidən baxılmalıdır.

## 7. Açıq suallar

Yoxdur.

## 8. Dəyişiklik tarixçəsi

- 2026-10-24: İlk qaralama (F1, F2, F3).
- 2026-10-24: F4 (yükləmə) əlavə edildi. Platforma: veb tətbiq. Mərhələlər bölməsi əlavə edildi.
- 2026-10-24: Açıq suallar cavablandı: lokal işləyir, içində dinləmək var (F5), səslə axtarış Shazam kimi, mənbə YouTube, YouTube linkindən MP3 yükləmə. Texnologiyalar təklif edildi, hüquqi qeyd əlavə edildi.
- 2026-10-24: Son qərarlar: FastAPI, shazamio, fayllar "Yükləmələr" qovluğuna, 10 nəticə. İcra planı əlavə edildi. Status: hazır.
- 2026-10-24: Mərhələ 1 kodlandı (F1–F5). Python 3.12, FFmpeg və paketlər quraşdırıldı. Bax: README.md.
- 2026-10-24: Masaüstü ikonu əlavə edildi: tətbiq pəncərəsiz işə düşür, birbaşa brauzerdə açılır, səhifə bağlananda özü dayanır.
- 2026-10-24: Layihə `Documents\MahniAxtarisi` qovluğuna köçürüldü. Tətbiqin adı **ilkmusic** oldu, ikon masaüstü fon şəklindən hazırlandı.
- 2026-10-24: Səslə axtarış düzəldi: brauzerin əks-səda və küy silmə emalı söndürüldü, səs səviyyəsi göstəricisi əlavə edildi, server hər cəhdin səviyyəsini loga yazır.
- 2026-10-24: F6 (paylaşma) üçün portativ Windows paketi hazırlandı: `dist\ilkmusic.zip`.
- 2026-10-24: `ilkmusic.exe` ilk açılışda masaüstü ikonu yaratmağı təklif edir, qovluq köçürüləndə ikonu yeni yerə yönəldir, tək köçürüləndə izah verir.
- 2026-10-25: F7 və F8 hazırdır.
  - Ana səhifə: son dinlənilənlər və YouTube Mix-dən oxşar mahnılar, tarixçə boşdursa populyar mahnılar.
  - Kartlar YouTube kimidir.
  - Arxa fonda Zaqatala şəkli (Wikimedia Commons, CC BY 3.0), axtarışın iki tərəfində "Zaqatala".
  - Paket yenidən yığıldı.
- 2026-10-25: "Zaqatala" yazısı iki tərəfdən götürüldü, axtarışın üstündə bir dənə böyük yazı oldu.
- 2026-11-01: GitHub-a dərc edildi: public repo `ilkin055/ilkmusic` və Release v1.0 (`ilkmusic.zip`).
- 2026-11-01: Tətbiq ayrıca app pəncərəsində açılır (Chrome/Edge `--app`), pəncərə ikonu ilkmusic ikonudur.
- 2026-11-01: Telefondan giriş (Mərhələ 3, yol C).
  - Server ev şəbəkəsində dinləyir, şəbəkədən gələn sorğular gizli açarla (QR kod) yoxlanılır.
  - iPhone üçün dinləmə düzəlişi edildi, ana ekran ikonu əlavə olundu.
