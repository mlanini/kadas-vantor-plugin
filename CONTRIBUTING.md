# Contributing to the Project

Thank you for your interest in contributing to the KADAS Vantor Open Data Plugin!

## How to Contribute

### Report Bugs
1. Check that the bug hasn't already been reported in [Issues](https://github.com/mlanini/kadas-vantor-plugin/issues)
2. Open a new issue including:
   - Detailed description of the problem
   - Steps to reproduce the bug
   - Expected behavior vs observed behavior
   - Screenshots if applicable
   - KADAS version and operating system
   - Log file content (`~/.kadas/maxar.log`)

### Request Features
1. Open an issue with "enhancement" tag
2. Describe the use case and added value
3. Provide usage examples if possible

### Submit Pull Requests

#### Development Environment Setup
```powershell
# Clone the repository
git clone https://github.com/mlanini/kadas-vantor-plugin.git
cd kadas-vantor-plugin

# Create symlink to KADAS plugins directory (as Administrator)
New-Item -ItemType SymbolicLink -Path "$env:APPDATA\kadas-albireo2\python\plugins\kadas_maxar" -Target "$PWD\kadas_maxar"

# Install test dependencies (optional)
pip install pytest pytest-cov
```

#### Workflow
1. Create a branch for your feature: `git checkout -b feature/my-feature`
2. Make changes to the code
3. **Test your changes**: 
   - Run tests: `python -m pytest`
   - Test manually in KADAS
   - Check logs for errors
4. Commit with descriptive messages: `git commit -m "Add: feature description"`
5. Push the branch: `git push origin feature/my-feature`
6. Open a Pull Request on GitHub

#### Code Standards

**Python Conventions**:
- Follow PEP 8 for code style
- Use docstrings for functions and classes
- Comments in English for international collaboration

**KADAS-specific Patterns**:
```python
# ✅ Correct - use KadasPluginInterface
from kadas.kadasgui import *
self.iface = KadasPluginInterface.cast(iface)

# ✅ Correct - network with QgsNetworkAccessManager
nam = QgsNetworkAccessManager.instance()
reply = nam.get(QNetworkRequest(QUrl(url)))

# ✅ Correct - logging
from kadas_maxar.logger import get_logger
self.log = get_logger()
self.log.info("Informational message")
```

**Avoid**:
```python
# ❌ Wrong - uses QGIS instead of KADAS
from qgis.gui import QgisInterface

# ❌ Wrong - requests doesn't respect KADAS proxy
import requests
response = requests.get(url)
```

#### Testing
- Write tests for new features
- Tests go in `kadas_maxar/tests/`
- Use `conftest.py` for Qt/QGIS stubs
- Run all tests before PR: `python -m pytest`

#### Documentation
- Update README.md if you change features
- Add entry in CHANGELOG.md
- Document breaking changes in INSTALL.md
- Use docstrings for new functions

## Project Structure

```
kadas_maxar/
├── __init__.py              # Entry point (classFactory)
├── kadas_maxar.py           # Main plugin
├── logger.py                # Custom logging system
├── metadata.txt             # QGIS/KADAS metadata
├── dialogs/
│   ├── maxar_dock.py        # Main UI + DataFetchWorker
│   └── settings_dock.py     # Settings panel
├── icons/                   # SVG resources
└── tests/                   # Test suite with pytest
    └── conftest.py          # Stubs for tests without Qt
```

## Priority Areas

Particularly useful contributions:

1. **Testing**: Expand test coverage, integration tests
2. **Performance**: Optimize loading of large GeoJSON files
3. **UI/UX**: Interface improvements, user feedback
4. **Documentation**: Screenshots, video tutorials, translations
5. **Features**: Support for other STAC datasets, selection export, batch download

## General Guidelines

- **Maintain compatibility**: Plugin must work on KADAS Albireo 2.x
- **Don't add external dependencies**: Use only libraries included in KADAS
- **Test on Windows**: It's the primary platform for target users
- **Adequate logging**: Use `get_logger()` for debug
- **Error handling**: Always use try/except for network and I/O operations
- **UI language**: Keep consistency with target users (Italian UI maintained)

## Review Process

Pull Requests are reviewed for:
- Functional correctness
- Adherence to code standards
- Presence of tests
- Adequate documentation
- KADAS compatibility

## License

By contributing to the project, you agree that your code will be released under the MIT license.

## Contact

- Issues: [GitHub Issues](https://github.com/mlanini/kadas-vantor-plugin/issues)
- Email: mlanini(at)proton(dot)me

Thank you for your contribution! 🚀
