# ilkmusic

Öz kompüterində işləyən veb tətbiq: mahnını adı, YouTube linki və ya səsi ilə tapır, tətbiqin içində dinlədir və MP3 kimi yükləyir. Tələblər: [TEXNIKI_TAPSIRIQ.md](TEXNIKI_TAPSIRIQ.md).

## Yüklə və istifadə et (Windows 10/11)

1. **[ilkmusic.zip-i yüklə](https://github.com/ilkin055/ilkmusic/releases/latest/download/ilkmusic.zip)** (təxminən 130 MB). Bütün versiyalar: [Releases](https://github.com/ilkin055/ilkmusic/releases).
2. ZIP-ə sağ klik → **"Hamısını çıxart"** (Extract All). ZIP-in içində birbaşa açma.
3. Çıxardılan `ilkmusic` qovluğunu daimi yerə qoy, məsələn **Sənədlər**.
4. Qovluğun içindəki **`ilkmusic.exe`**-ni aç. İlk dəfə masaüstündə ikon yaratmağı soruşacaq, "Bəli" de.
5. Windows "Windows protected your PC" yazsa: **"More info" → "Run anyway"**. Proqram imzalanmadığı üçün belə yazır.

Heç nə quraşdırmaq lazım deyil: Python və FFmpeg paketin içindədir. Ətraflı təlimat ZIP-in içindəki `OXU.txt` faylındadır.

## Telefonda istifadə (iPhone və Android, ev Wi-Fi-ı ilə)

1. Kompüterdə ilkmusic-i aç və yuxarı sağdakı **"📱 Telefonda aç"** düyməsinə bas.
2. Telefonun kamerası ilə QR kodu skan et, link Safari-də (və ya Chrome-da) açılacaq.
3. iPhone-da **Paylaş → "Ana ekrana əlavə et"**: telefonda ilkmusic ikonu yaranır.

Mahnı axtarmaq, dinləmək və MP3 yükləmək olur, yüklənən mahnılar iPhone-un "Fayllar" bölməsinə düşür.

- Telefon kompüterlə **eyni Wi-Fi**-da olmalıdır, kompüterdə ilkmusic açıq qalmalıdır.
- İlk dəfə Windows Firewall Python-un şəbəkəyə çıxışı üçün icazə soruşacaq: **"Özəl şəbəkələr"** seçili olsun və **"Girişə icazə ver"** bas. Windows-da ev Wi-Fi-ı "Özəl" (Private) şəbəkə kimi qeyd olunmalıdır.
- Səslə axtarış telefonda işləmir: brauzer mikrofonu yalnız təhlükəsiz (HTTPS) bağlantıda verir.
- QR koddakı link gizli açar daşıyır, onsuz Wi-Fi-dakı başqası tətbiqə girə bilmir. Açarı dəyişmək üçün `%LOCALAPPDATA%\ilkmusic\access-key.txt` faylını sil və ilkmusic-i yenidən başlat: köhnə linklər işləməyəcək.

## İnkişaf: işə salmaq

Masaüstündəki **ilkmusic** ikonuna iki dəfə bas. Tətbiq ayrıca pəncərədə, adi proqram kimi açılır (Chrome və ya Edge-in "app" rejimi: ünvan sətri və tablar olmadan). Chrome da, Edge də yoxdursa, adi brauzer tabında açılır.

- **Bağlamaq:** ilkmusic pəncərəsini bağla. Server 3 dəqiqə ərzində özü dayanır.
- Tətbiq artıq işləyirkən ikona yenidən bassan, yeni pəncərə açılır, ikinci server başlamır.
- `start.bat` da eyni işi görür, amma serverin loglarını qara pəncərədə göstərir. Problem axtaranda faydalıdır.
- İkonla işə salananda loglar `%TEMP%\ilkmusic.log` faylına yazılır.
- 8000 portu başqa proqramla məşğuldursa, tətbiq özü 8001–8010 arasında boş port seçir.

## Başqasına göndərmək

1. Portativ paketi yığ. Tətbiqi dəyişəndən sonra bunu hər dəfə təkrarla:

   ```bat
   "%USERPROFILE%\.venvs\mahni-app\Scripts\python.exe" packaging\build.py
   ```

2. `dist\ilkmusic.zip` faylını GitHub-da yeni versiya kimi dərc et. Dostların onu yuxarıdakı linkdən yükləyir:

   ```bat
   "%LOCALAPPDATA%\Programs\gh\bin\gh.exe" release create v1.1 dist\ilkmusic.zip --title "ilkmusic v1.1" --notes "Nə dəyişdi"
   ```

   Və ya faylı (təxminən 130 MB) WhatsApp, Telegram, Google Drive ilə birbaşa göndər.
3. Qarşı tərəf ZIP-i çıxarır, qovluğu daimi yerə qoyur (məsələn, Sənədlər) və `ilkmusic.exe`-ni açır. Heç nə quraşdırmaq lazım deyil. Təlimat ZIP-in içindədir: `OXU.txt`.
   - İlk açılışda `ilkmusic.exe` masaüstündə ikon yaratmağı təklif edir. Qovluq sonra köçürülsə, ikonu yeni yerə özü yönəldir.
   - `ilkmusic.exe` qovluqdan ayrı köçürülsə, nə etmək lazım olduğunu izah edən pəncərə çıxır.

Qeydlər:
- Yalnız Windows 10/11-də işləyir, telefonda yox.
- `ilkmusic.exe` imzalanmayıb. İlk açılışda Windows "Windows protected your PC" yazacaq: "More info" → "Run anyway".
- YouTube dəyişəndə paketdəki yt-dlp köhnələ bilər. Onda yt-dlp-ni yenilə (aşağıya bax), paketi yenidən yığ və yenidən göndər.

## Nə edə bilir

- **Ad ilə axtarış:** mahnının adını yaz, YouTube-dan 10 nəticə çıxır.
- **Link ilə axtarış:** YouTube linkini yapışdır (`youtube.com`, `youtu.be`, `music.youtube.com`, Shorts).
- **Səslə axtarış:** "🎤 Səslə axtar" düyməsini bas və mahnını 10 saniyə mikrofona tut. Tətbiq onu Shazam ilə tanıyıb avtomatik axtarır.
- **Dinlə:** mahnı aşağıdakı pleyerdə çalınır.
- **MP3 yüklə:** fayl brauzerin "Yükləmələr" qovluğuna düşür.
- **Ana səhifə:** "Son dinlədiklərin" və "Sənə oxşar mahnılar" (son 3 mahnının YouTube Mix-indən, təkrarlar olmadan). Tarixçə boşdursa, "Populyar mahnılar" göstərilir.
  - Tarixçə hər kompüterdə ayrıca saxlanılır: `%LOCALAPPDATA%\ilkmusic\history.json`. Saytdakı "Tarixçəni təmizlə" düyməsi onu silir.
- **Dizayn:** arxa fonda Zaqatalanın mənzərəsi, axtarışın üstündə böyük "Zaqatala" yazısı. Fon şəkli: [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Zaqatala_Umumi_Gorunus_-_panoramio.jpg), müəllif NorthernCaucasusStud…, CC BY 3.0.

İlk "Dinlə" və ya "MP3 yüklə" bir neçə saniyə çəkir, çünki mahnı YouTube-dan götürülüb MP3-ə çevrilir. Sonrakı kliklər dərhal işləyir. Müvəqqəti MP3-lər `%TEMP%\ilkmusic-cache` qovluğunda saxlanır və tətbiq bağlananda silinir.

## Kompüterdə nə quraşdırılıb

| Nə | Harada |
|---|---|
| Python 3.12.10 (rəsmi NuGet paketi) | `%LOCALAPPDATA%\Programs\Python\Python312` |
| FFmpeg 9.0.2 (gyan.dev) | `%LOCALAPPDATA%\Programs\ffmpeg` |
| Layihənin virtual mühiti | `%USERPROFILE%\.venvs\mahni-app` |
| Qısayol | Masaüstü: `ilkmusic.lnk` |

PATH, reyestr və sistem ayarlarına toxunulmayıb. Hamısını silmək istəsən, bu üç qovluğu və qısayolu silmək kifayətdir.

Python PATH-də olmadığı üçün onu tam yolu ilə çağırmaq lazımdır və ya virtual mühiti aktivləşdirmək olar:

```bat
%USERPROFILE%\.venvs\mahni-app\Scripts\activate
```

## YouTube işləməyi dayandırsa

YouTube tez-tez dəyişir. Axtarış və ya yükləmə xəta versə, yt-dlp-ni yenilə:

```bat
"%USERPROFILE%\.venvs\mahni-app\Scripts\python.exe" -m pip install -U yt-dlp
```

## Struktur

| Fayl | Nə üçündür |
|---|---|
| `app/main.py` | FastAPI backend: axtarış, MP3, tanıma |
| `app/static/` | İnterfeys (HTML, CSS, JS) |
| `run.py` | Serveri işə salır, brauzeri açır, səhifə bağlananda serveri dayandırır |
| `start.bat` | `run.py`-ı virtual mühitlə, loglar görünən pəncərədə işə salır |
| `ilkmusic.ico` | Qısayolun ikonu (masaüstü fon şəklindən kəsilib) |
| `packaging/build.py` | Portativ paketi (`dist\ilkmusic.zip`) yığır |
| `packaging/launcher.cs` | `ilkmusic.exe` başladıcısının kodu |
| `packaging/OXU.txt` | Paketin içindəki təlimat |
| `dist/` | Yığılmış paket (yenidən yaradılır) |
| `requirements.txt` | Python paketləri (versiyaları sabitlənib) |

## Hüquqi qeyd

YouTube-un istifadə qaydaları yükləməni qadağan edir, mahnılar isə müəllif hüququ ilə qorunur. Tətbiq yalnız şəxsi, lokal istifadə üçündür və yalnız `127.0.0.1`-də işləyir, yəni şəbəkədəki digər cihazlar ona qoşula bilmir.
