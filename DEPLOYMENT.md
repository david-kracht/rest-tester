# GitHub Actions Setup für PyPI Deployment

## Benötigte GitHub Secrets

Um die automatischen Deployments zu aktivieren, müssen Sie folgende Secrets in Ihrem GitHub Repository konfigurieren:

### 1. Test PyPI API Token
1. Gehen Sie zu https://test.pypi.org/account/login/
2. Loggen Sie sich ein oder erstellen Sie einen Account
3. Gehen Sie zu Account settings > API tokens
4. Erstellen Sie einen neuen Token mit dem Namen "GitHub Actions"
5. Kopieren Sie den Token und fügen Sie ihn als Secret `TEST_PYPI_API_TOKEN` hinzu

### 2. PyPI API Token  
1. Gehen Sie zu https://pypi.org/account/login/
2. Loggen Sie sich ein oder erstellen Sie einen Account
3. Gehen Sie zu Account settings > API tokens
4. Erstellen Sie einen neuen Token mit dem Namen "GitHub Actions"
5. Kopieren Sie den Token und fügen Sie ihn als Secret `PYPI_API_TOKEN` hinzu

### Secrets in GitHub hinzufügen:
1. Gehen Sie zu Ihrem Repository auf GitHub
2. Klicken Sie auf Settings > Secrets and variables > Actions
3. Klicken Sie auf "New repository secret"
4. Fügen Sie die folgenden Secrets hinzu:
   - Name: `TEST_PYPI_API_TOKEN`, Value: [Ihr Test PyPI Token]
   - Name: `PYPI_API_TOKEN`, Value: [Ihr PyPI Token]

## Workflow Verhalten

### Development Builds (alle Branches außer main/master)
- Wird bei jedem Push auf beliebigen Branch ausgelöst
- Erstellt eindeutige Entwicklungsversionen im Format: `{base_version}.dev{timestamp}+{commit_hash}`
- Beispiel: `0.1.0.dev20250806143022+abc1234`
- Uploaded auf Test PyPI: https://test.pypi.org/project/rest-tester/

### Release Builds
- Wird ausgelöst wenn ein Release/Tag erstellt wird
- Verwendet die Tag-Version (z.B. `v1.0.0` → `1.0.0`)
- Uploaded auf Production PyPI: https://pypi.org/project/rest-tester/

## Release erstellen

1. **Über GitHub UI:**
   ```
   Gehen Sie zu: Releases > Create a new release
   Tag: v1.0.0 (oder die gewünschte Version)
   Title: Version 1.0.0
   Beschreibung: Release notes...
   ```

2. **Über Git Tags:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   # Dann auf GitHub das Release aus dem Tag erstellen
   ```

## Installation der Test-Version
```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ rest-tester
```

## Installation der Release-Version
```bash
pip install rest-tester
```
