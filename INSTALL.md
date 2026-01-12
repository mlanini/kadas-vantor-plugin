# Installation Guide

## Quick Install (Recommended)

### From ZIP Release
1. Download the latest `kadas-vantor-plugin-v0.1.0.zip` from [Releases](https://github.com/mlanini/kadas-vantor-plugin/releases)
2. In KADAS: `Plugins → Manage and Install Plugins → Install from ZIP`
3. Select downloaded ZIP file
4. Restart KADAS
5. Enable plugin: `Plugins → Manage and Install Plugins → Installed`

## Manual Installation

### Windows
```powershell
# Navigate to KADAS plugins directory
cd %APPDATA%\kadas-albireo2\python\plugins

# Clone repository
git clone https://github.com/mlanini/kadas-vantor-plugin.git kadas_maxar

# Or download and extract ZIP manually
```

### Linux
```bash
# Navigate to KADAS plugins directory
cd ~/.local/share/kadas-albireo2/python/plugins

# Clone repository
git clone https://github.com/mlanini/kadas-vantor-plugin.git kadas_maxar
```

### macOS
```bash
# Navigate to KADAS plugins directory
cd ~/Library/Application\ Support/kadas-albireo2/python/plugins

# Clone repository
git clone https://github.com/mlanini/kadas-vantor-plugin.git kadas_maxar
```

## Verification

After installation:
1. Restart KADAS
2. Check `Plugins → Manage and Install Plugins → Installed`
3. Look for "KADAS Vantor Open Data"
4. Enable if not already enabled
5. Check `View → Panels` for "Vantor EO Data"

## Troubleshooting

### Plugin not showing
- Verify plugin folder name is exactly `kadas_maxar`
- Check `metadata.txt` exists in plugin folder
- Restart KADAS completely

### Import errors
- Ensure KADAS 2.x is installed
- Check Python 3.7+ is available
- Verify QGIS core libraries are accessible

### Connection issues
- Check internet connection
- Verify GitHub and AWS S3 are accessible
- Check firewall/proxy settings

## Uninstallation

### Via KADAS UI
1. `Plugins → Manage and Install Plugins`
2. Select "KADAS Vantor Open Data"
3. Click "Uninstall plugin"

### Manual
Delete the plugin folder:
- Windows: `%APPDATA%\kadas-albireo2\python\plugins\kadas_maxar`
- Linux: `~/.local/share/kadas-albireo2/python/plugins/kadas_maxar`
- macOS: `~/Library/Application Support/kadas-albireo2/python/plugins/kadas_maxar`

## Development Installation

For plugin development:
```bash
# Clone to development location
git clone https://github.com/mlanini/kadas-vantor-plugin.git

# Create symlink to plugins directory
# Windows (as Administrator)
mklink /D "%APPDATA%\kadas-albireo2\python\plugins\kadas_maxar" "C:\path\to\kadas-vantor-plugin\kadas_maxar"

# Linux/macOS
ln -s /path/to/kadas-vantor-plugin/kadas_maxar ~/.local/share/kadas-albireo2/python/plugins/kadas_maxar
```

## Next Steps

See [README.md](README.md) for usage instructions.
