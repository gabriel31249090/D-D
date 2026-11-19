// ARCANUM per-user installer. Built with the Windows .NET Framework compiler.
// The uninstall manifest names only managed application files; user data is never removed.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Win32;

public class InstallManifest {
    public string Product = "ARCANUM.Desktop";
    public string Version = "0.2.0";
    public string[] Files;
    public bool Registered;
    public bool Shortcuts;
}

public static class Setup {
    const string RegistryPath = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\ARCANUM.Desktop";
    const string ManifestName = ".arcanum-install.json";
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = 16 * 1024 * 1024 };
    static string logPath;

    [STAThread]
    public static int Main(string[] args) {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        string root = Option(args, "--install-dir") ?? DefaultRoot();
        logPath = Option(args, "--log");
        bool silent = args.Contains("--silent");
        try {
            if (args.Contains("--remove-root")) {
                Uninstall(Option(args, "--remove-root"));
                return 0;
            }
#if UNINSTALLER
            string installedRoot = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            if (!silent && MessageBox.Show("Remover o ARCANUM? Seus dados, campanhas e livros serão preservados.", "ARCANUM", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return 0;
            string helper = Path.Combine(Path.GetTempPath(), "Arcanum-Uninstall-" + Guid.NewGuid().ToString("N") + ".exe");
            File.Copy(Assembly.GetExecutingAssembly().Location, helper);
            var start = new ProcessStartInfo(helper, "--remove-root " + Quote(installedRoot) + (logPath == null ? "" : " --log " + Quote(logPath)));
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            Process.Start(start);
            return 0;
#else
            if (silent) {
                Install(root, !args.Contains("--no-register"), !args.Contains("--no-shortcuts"));
                return 0;
            }
            Application.Run(new InstallerWindow(root));
            return 0;
#endif
        } catch (Exception error) {
            Log("ERROR: " + error);
            if (!silent) MessageBox.Show(error.Message, "ARCANUM — instalação", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }

    public static string DefaultRoot() {
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "ARCANUM");
    }
    static string Option(string[] args, string key) {
        int index = Array.IndexOf(args, key);
        return index >= 0 && index + 1 < args.Length ? args[index + 1] : null;
    }
    static string Quote(string value) { return "\"" + value.Replace("\"", "") + "\""; }
    static void Log(string text) {
        if (logPath != null) File.AppendAllText(logPath, DateTime.UtcNow.ToString("o") + " " + text + Environment.NewLine, Encoding.UTF8);
    }
    static string SafePath(string root, string relative) {
        string prefix = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        string target = Path.GetFullPath(Path.Combine(prefix, relative));
        if (!target.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) throw new IOException("Caminho inválido no pacote.");
        string current = Path.GetDirectoryName(target);
        while (current != null && current.Length >= prefix.Length - 1) {
            if (Directory.Exists(current) && (File.GetAttributes(current) & FileAttributes.ReparsePoint) != 0) throw new IOException("A pasta contém um redirecionamento de sistema; escolha uma pasta normal.");
            current = Path.GetDirectoryName(current);
        }
        return target;
    }

    public static void Install(string root, bool register, bool shortcuts) {
        root = Path.GetFullPath(root);
        if (root == Path.GetPathRoot(root) || root.Length < 8) throw new IOException("Escolha uma pasta de instalação válida.");
        if (Directory.Exists(root) && Directory.EnumerateFileSystemEntries(root).Any()) throw new IOException("A pasta de destino já contém arquivos. Desinstale a versão anterior ou escolha uma pasta vazia.");
        Directory.CreateDirectory(root);
        var installedFiles = new List<string>();
        try {
            using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("Arcanum.Payload.zip")) {
                if (stream == null) throw new IOException("O pacote de instalação não está disponível.");
                using (var archive = new ZipArchive(stream, ZipArchiveMode.Read)) {
                    foreach (var entry in archive.Entries) {
                        if (String.IsNullOrEmpty(entry.Name)) continue;
                        string destination = SafePath(root, entry.FullName);
                        Directory.CreateDirectory(Path.GetDirectoryName(destination));
                        using (Stream input = entry.Open())
                        using (var output = new FileStream(destination, FileMode.CreateNew, FileAccess.Write)) input.CopyTo(output);
                        installedFiles.Add(entry.FullName);
                    }
                }
            }
            var manifest = new InstallManifest { Files = installedFiles.ToArray(), Registered = register, Shortcuts = shortcuts };
            File.WriteAllText(Path.Combine(root, ManifestName), Json.Serialize(manifest), Encoding.UTF8);
            if (register) Register(root);
            if (shortcuts) CreateShortcuts(root);
            Log("INSTALL_OK " + root + " files=" + installedFiles.Count);
        } catch {
            // Roll back only files this process just created; never recurse into unknown data.
            foreach (string relative in installedFiles) { string file = SafePath(root, relative); if (File.Exists(file)) File.Delete(file); }
            throw;
        }
    }

    static void Register(string root) {
        using (RegistryKey key = Registry.CurrentUser.CreateSubKey(RegistryPath)) {
            key.SetValue("DisplayName", "ARCANUM");
            key.SetValue("DisplayVersion", "0.2.0");
            key.SetValue("Publisher", "ARCANUM");
            key.SetValue("InstallLocation", root);
            key.SetValue("DisplayIcon", Path.Combine(root, "runtime", "pythonw.exe"));
            key.SetValue("UninstallString", Quote(Path.Combine(root, "Uninstall.exe")));
            key.SetValue("QuietUninstallString", Quote(Path.Combine(root, "Uninstall.exe")) + " --silent");
            key.SetValue("NoModify", 1, RegistryValueKind.DWord);
            key.SetValue("NoRepair", 1, RegistryValueKind.DWord);
            long bytes = Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories).Sum(file => new FileInfo(file).Length);
            key.SetValue("EstimatedSize", (int)Math.Min(Int32.MaxValue, bytes / 1024), RegistryValueKind.DWord);
        }
    }
    static void CreateShortcut(string file, string root) {
        object shell = Activator.CreateInstance(Type.GetTypeFromProgID("WScript.Shell"));
        object shortcut = shell.GetType().InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { file });
        Type type = shortcut.GetType();
        type.InvokeMember("TargetPath", BindingFlags.SetProperty, null, shortcut, new object[] { Path.Combine(root, "runtime", "pythonw.exe") });
        type.InvokeMember("Arguments", BindingFlags.SetProperty, null, shortcut, new object[] { "-m desktop.app" });
        type.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, shortcut, new object[] { root });
        type.InvokeMember("Description", BindingFlags.SetProperty, null, shortcut, new object[] { "ARCANUM — sua mesa de RPG" });
        type.InvokeMember("Save", BindingFlags.InvokeMethod, null, shortcut, null);
        System.Runtime.InteropServices.Marshal.FinalReleaseComObject(shortcut);
        System.Runtime.InteropServices.Marshal.FinalReleaseComObject(shell);
    }
    static void CreateShortcuts(string root) {
        string menu = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "ARCANUM");
        Directory.CreateDirectory(menu);
        CreateShortcut(Path.Combine(menu, "ARCANUM.lnk"), root);
        CreateShortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "ARCANUM.lnk"), root);
    }

    static void Uninstall(string root) {
        root = Path.GetFullPath(root);
        string manifestPath = SafePath(root, ManifestName);
        if (!File.Exists(manifestPath)) throw new IOException("Manifesto de instalação não encontrado. Nenhum arquivo foi removido.");
        InstallManifest manifest = Json.Deserialize<InstallManifest>(File.ReadAllText(manifestPath, Encoding.UTF8));
        if (manifest == null || manifest.Product != "ARCANUM.Desktop" || manifest.Files == null) throw new IOException("Manifesto inválido. Nenhum arquivo foi removido.");
        // Validate the complete list before any removal.
        string[] managed = manifest.Files.Select(relative => SafePath(root, relative)).ToArray();
        foreach (string file in managed) if (File.Exists(file)) File.Delete(file);
        File.Delete(manifestPath);
        var ownedDirectories = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (string file in managed) {
            string directory = Path.GetDirectoryName(file);
            while (directory != null && directory.Length > root.Length) {
                ownedDirectories.Add(directory);
                directory = Path.GetDirectoryName(directory);
            }
        }
        foreach (string directory in ownedDirectories.OrderByDescending(value => value.Length))
            if (Directory.Exists(directory) && (File.GetAttributes(directory) & FileAttributes.ReparsePoint) == 0 && !Directory.EnumerateFileSystemEntries(directory).Any()) Directory.Delete(directory);
        if (!Directory.EnumerateFileSystemEntries(root).Any()) Directory.Delete(root);
        bool ownsRegistration = false;
        using (RegistryKey key = Registry.CurrentUser.OpenSubKey(RegistryPath)) {
            ownsRegistration = key != null && String.Equals(key.GetValue("InstallLocation") as string, root, StringComparison.OrdinalIgnoreCase);
        }
        if (manifest.Registered && ownsRegistration) {
            Registry.CurrentUser.DeleteSubKeyTree(RegistryPath, false);
            if (manifest.Shortcuts) {
                string menu = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "ARCANUM");
                foreach (string file in new[] { Path.Combine(menu, "ARCANUM.lnk"), Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "ARCANUM.lnk") })
                    if (File.Exists(file)) File.Delete(file);
                if (Directory.Exists(menu) && !Directory.EnumerateFileSystemEntries(menu).Any()) Directory.Delete(menu);
            }
        }
        Log("UNINSTALL_OK " + root + " user_data_preserved=true");
    }

    public static void Launch(string root) {
        var start = new ProcessStartInfo(Path.Combine(root, "runtime", "pythonw.exe"), "-m desktop.app");
        start.WorkingDirectory = root;
        start.UseShellExecute = false;
        Process.Start(start);
    }
}

public sealed class InstallerWindow : Form {
    readonly string installRoot;
    readonly Button install = new Button();
    readonly Label status = new Label();
    readonly CheckBox launch = new CheckBox();
    public InstallerWindow(string root) {
        installRoot = root;
        Text = "Instalar ARCANUM";
        ClientSize = new Size(600, 350);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        Font = new Font("Segoe UI", 11);
        BackColor = Color.FromArgb(23, 25, 31);
        ForeColor = Color.FromArgb(240, 236, 224);
        var title = new Label { Text = "ARCANUM", Font = new Font("Segoe UI", 26, FontStyle.Bold), Left = 28, Top = 22, AutoSize = true, ForeColor = Color.FromArgb(220, 186, 109) };
        var subtitle = new Label { Text = "Sua mesa de RPG, no Windows.", Left = 30, Top = 82, Width = 530, Height = 28 };
        var detail = new Label { Text = "Instalação para este usuário. Python já está incluído.\nDados, campanhas e livros permanecem na sua pasta pessoal.", Left = 30, Top = 124, Width = 535, Height = 58 };
        var destination = new TextBox { Text = root, Left = 30, Top = 193, Width = 535, ReadOnly = true, BackColor = Color.FromArgb(35, 38, 47), ForeColor = ForeColor, BorderStyle = BorderStyle.FixedSingle };
        launch.Text = "Abrir o ARCANUM ao concluir";
        launch.Left = 30; launch.Top = 236; launch.Width = 450; launch.Checked = true;
        status.Left = 30; status.Top = 282; status.Width = 370; status.Height = 44;
        install.Text = "Instalar"; install.Left = 436; install.Top = 280; install.Width = 130; install.Height = 42;
        install.BackColor = Color.FromArgb(220, 186, 109); install.ForeColor = Color.FromArgb(23, 25, 31); install.FlatStyle = FlatStyle.Flat;
        install.Click += async delegate {
            install.Enabled = false; status.Text = "Instalando…";
            try {
                await Task.Run(() => Setup.Install(installRoot, true, true));
                status.Text = "Instalação concluída."; install.Text = "Concluir";
                if (launch.Checked) Setup.Launch(installRoot);
                await Task.Delay(1200); Close();
            } catch (Exception error) {
                status.Text = "Não foi possível instalar.";
                MessageBox.Show(error.Message, "ARCANUM", MessageBoxButtons.OK, MessageBoxIcon.Error);
                install.Enabled = true;
            }
        };
        Controls.AddRange(new Control[] { title, subtitle, detail, destination, launch, status, install });
        AcceptButton = install;
    }
}

