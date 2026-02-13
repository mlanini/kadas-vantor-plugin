# Installation Guide

## Quick Install (Recommended)

### From ZIP File
1. Download the latest release `kadas-vantor-plugin-v0.2.0.zip` from [Releases](https://github.com/mlanini/kadas-vantor-plugin/releases)
2. In KADAS: `Plugins → Manage and Install Plugins → Install from ZIP`
3. Select the downloaded ZIP file
4. Restart KADAS
5. Enable the plugin: `Plugins → Manage and Install Plugins → Installed`

## Manual Installation

### Windows
```powershell
# Navigate to KADAS plugins directory
cd $env:APPDATA\kadas-albireo2\python\plugins

# Clone the repository (folder name MUST be kadas_maxar)
git clone https://github.com/mlanini/kadas-vantor-plugin.git kadas_maxar

# Or download and extract ZIP manually
```

### Linux
```bash
# Navigate to KADAS plugins directory
cd ~/.local/share/kadas-albireo2/python/plugins

# Clone the repository
git clone https://github.com/mlanini/kadas-vantor-plugin.git kadas_maxar
```

### macOS
```bash
# Navigate to KADAS plugins directory
cd ~/Library/Application\ Support/kadas-albireo2/python/plugins

# Clone the repository
git clone https://github.com/mlanini/kadas-vantor-plugin.git kadas_maxar
```

## Installation Verification

After installation:
1. Restart KADAS completely
2. Check `Plugins → Manage and Install Plugins → Installed`
3. Look for "KADAS Vantor Open Data"
4. Enable if not already enabled
5. Check `View → Panels` for "Vantor Open Data"
6. Or look for the "EO" tab in the ribbon bar

## Troubleshooting

### Plugin not visible
- Verify the folder name is exactly `kadas_maxar`
- Check that `metadata.txt` exists in the plugin folder
- Restart KADAS completely (close all windows)

### Import errors
- Ensure KADAS Albireo 2.x is installed
- Verify Python 3.9+ is available (included in KADAS)
- Check that QGIS core libraries are accessible

### Connection issues
- Verify internet connection
- Check that GitHub (raw.githubusercontent.com) is accessible
- Verify AWS S3 (maxar-opendata.s3.amazonaws.com) is accessible
- Check firewall/proxy settings in `Settings → Options → Network`
- Consult the log file: `~/.kadas/maxar.log`

### Timeout during footprints loading
- The plugin uses 180 second timeout for large GeoJSON files
- Verify connection speed
- Check the log file for network errors
- Use "Settings" to increase timeout if necessary

## Uninstallation

### Via KADAS interface
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
```powershell
# Windows - Clone to development location
git clone https://github.com/mlanini/kadas-vantor-plugin.git

# Create symlink to plugins directory (Run as Administrator)
New-Item -ItemType SymbolicLink -Path "$env:APPDATA\kadas-albireo2\python\plugins\kadas_maxar" -Target "C:\path\to\kadas-vantor-plugin\kadas_maxar"
```

```bash
# Linux/macOS
git clone https://github.com/mlanini/kadas-vantor-plugin.git
ln -s /path/to/kadas-vantor-plugin/kadas_maxar ~/.local/share/kadas-albireo2/python/plugins/kadas_maxar
```

## Next Steps

See [QUICKSTART.md](QUICKSTART.md) to start using the plugin.
