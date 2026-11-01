// ilkmusic.exe: portativ paketin başladıcısı.
// Yanındakı python\pythonw.exe ilə run.py-ı konsol pəncərəsi olmadan işə salır.
// İlk açılışda masaüstündə ikon yaratmağı təklif edir; qovluq köçürülübsə, ikonu yeni yerə yönəldir.
// packaging\build.py bunu Windows-un öz C# kompilyatoru (csc.exe) ilə yığır.
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text;
using System.Windows.Forms;

static class Launcher
{
    const string ShortcutName = "ilkmusic.lnk";
    const string DeclinedMarker = "masaustu-ikonu-istenmedi.txt";

    [STAThread]
    static void Main()
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string pythonw = Path.Combine(root, @"python\pythonw.exe");
        string script = Path.Combine(root, "run.py");

        // exe qovluqdan ayrı köçürülübsə və ya ZIP-in içindən birbaşa açılıbsa, qalan fayllar yanında olmur.
        if (!File.Exists(pythonw) || !File.Exists(script))
        {
            MessageBox.Show(
                "ilkmusic.exe öz qovluğundan ayrı işləmir.\n\n" +
                "1. ZIP arxivini tam çıxart (sağ klik → \"Hamısını çıxart\").\n" +
                "2. Bütün ilkmusic qovluğunu daimi yerə qoy (məsələn, Sənədlər).\n" +
                "3. Qovluğun içindəki ilkmusic.exe-ni aç: masaüstündə ikon yaratmağı özü təklif edəcək.\n\n" +
                "Bu tək ilkmusic.exe faylını silə bilərsən.",
                "ilkmusic", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        EnsureDesktopShortcut(root, Application.ExecutablePath);

        var startInfo = new ProcessStartInfo(pythonw, "\"" + script + "\"")
        {
            WorkingDirectory = root,
            UseShellExecute = false,
        };
        Process.Start(startInfo);
    }

    static void EnsureDesktopShortcut(string root, string exe)
    {
        try
        {
            string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
            string shortcut = Path.Combine(desktop, ShortcutName);

            if (File.Exists(shortcut))
            {
                // Yalnız ilkmusic.exe-yə baxan qısayola toxunuruq (başqa qısayolların üzərinə yazmırıq).
                string target = ReadShortcutTarget(shortcut);
                bool pointsToLauncher = string.Equals(Path.GetFileName(target), "ilkmusic.exe", StringComparison.OrdinalIgnoreCase);
                if (pointsToLauncher && !string.Equals(target, exe, StringComparison.OrdinalIgnoreCase))
                    SaveShortcut(shortcut, exe, root);  // qovluq köçürülüb: ikonu yeni yerə yönəldirik
                return;
            }

            string declined = Path.Combine(root, DeclinedMarker);
            if (File.Exists(declined))
                return;

            DialogResult answer = MessageBox.Show(
                "Masaüstündə ilkmusic ikonu yaradılsın?\n\nSonra proqramı birbaşa masaüstündən aça bilərsən.",
                "ilkmusic", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (answer == DialogResult.Yes)
                SaveShortcut(shortcut, exe, root);
            else
                File.WriteAllText(declined, "Masaüstü ikonu istənmədi. Fikrini dəyişsən, bu faylı sil və ilkmusic.exe-ni yenidən aç.", Encoding.UTF8);
        }
        catch (Exception)
        {
            // İkon yaradıla bilməsə də, proqram açılmalıdır.
        }
    }

    internal static void SaveShortcut(string shortcut, string exe, string root)
    {
        var link = (IShellLinkW)new ShellLink();
        link.SetPath(exe);
        link.SetWorkingDirectory(root);
        link.SetIconLocation(exe, 0);
        link.SetDescription("ilkmusic: mahnı axtar, dinlə, MP3 yüklə");
        ((IPersistFile)link).Save(shortcut, true);
    }

    internal static string ReadShortcutTarget(string shortcut)
    {
        var link = (IShellLinkW)new ShellLink();
        ((IPersistFile)link).Load(shortcut, 0);
        var target = new StringBuilder(1024);
        link.GetPath(target, target.Capacity, IntPtr.Zero, 0);
        return target.ToString();
    }

    // Windows-un qısayol (.lnk) COM obyekti. WScript.Shell-dən fərqli olaraq Unicode yolları korlamır.
    [ComImport, Guid("00021401-0000-0000-C000-000000000046")]
    class ShellLink { }

    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("000214F9-0000-0000-C000-000000000046")]
    interface IShellLinkW
    {
        void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszFile, int cch, IntPtr pfd, int fFlags);
        void GetIDList(out IntPtr ppidl);
        void SetIDList(IntPtr pidl);
        void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszName, int cch);
        void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string pszName);
        void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszDir, int cch);
        void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string pszDir);
        void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszArgs, int cch);
        void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string pszArgs);
        void GetHotkey(out short pwHotkey);
        void SetHotkey(short wHotkey);
        void GetShowCmd(out int piShowCmd);
        void SetShowCmd(int iShowCmd);
        void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszIconPath, int cch, out int piIcon);
        void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string pszIconPath, int iIcon);
        void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string pszPathRel, int dwReserved);
        void Resolve(IntPtr hwnd, int fFlags);
        void SetPath([MarshalAs(UnmanagedType.LPWStr)] string pszFile);
    }
}
