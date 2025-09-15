# Configuration Guide

This document provides comprehensive information about configuring the API Server Manager application, including multi-language support and UI customization.

## Table of Contents

1. [Multi-Language Support](#multi-language-support)
2. [UI Configuration](#ui-configuration)
3. [Server Configuration](#server-configuration)
4. [Adding New Translations](#adding-new-translations)

## Multi-Language Support

The API Server Manager supports multiple languages through a comprehensive translation system. The application currently supports:

- **English (en)** - Default language
- **Turkish (tr)** - Full translation
- **German (de)** - Full translation  
- **French (fr)** - Full translation

### Supported UI Components

All UI components now support multi-language functionality:

#### Main Window
- Menu bars (File, Server, View, Help)
- System tray context menu
- Status bar messages
- Window titles and dialogs

#### Dashboard Tab
- System overview section
- Statistics panels (User, Server)
- System metrics display
- Recent activities table
- All labels, headers, and status indicators

#### Server Tab
- Server control buttons (Start, Stop, Restart)
- Server status indicators
- Configuration forms (Host, Port, SSL settings)
- Console output panel
- Validation messages and tooltips

#### Users Tab
- User management interface
- User list table headers
- Add/Edit/Delete user dialogs
- Role and permission management
- Search and filter controls

#### Console Widget
- Log level filters
- Search and filtering controls
- Export functionality
- Status indicators and counters

#### Other Tabs
- API Tab - API management interface
- Monitor Tab - System monitoring displays
- Logs Tab - Log viewing and analysis
- Settings Tab - Application configuration
- About Tab - Application information

### Language Files Location

Translation files are located in `/data/locale/`:

```
data/locale/
├── en.json    # English (default)
├── tr.json    # Turkish
├── de.json    # German
└── fr.json    # French
```

### Translation Key Structure

The translation system uses a hierarchical key structure:

```json
{
  "app": {
    "name": "API Server Manager",
    "version": "1.0.0",
    "description": "API Server Management System"
  },
  "common": {
    "ok": "OK",
    "cancel": "Cancel",
    "save": "Save",
    "delete": "Delete"
  },
  "navigation": {
    "dashboard": "Dashboard",
    "server": "Server",
    "users": "Users"
  },
  "ui": {
    "dashboard": {
      "system_overview": "System Overview",
      "server_status": "Server Status"
    },
    "server": {
      "server_control": "Server Control",
      "start_server": "Start Server"
    }
  }
}
```

### Runtime Language Switching

The application supports runtime language switching without requiring a restart:

1. **Language Manager**: Handles language changes and notifies all UI components
2. **Callback System**: All UI components register for language change notifications
3. **Automatic Updates**: UI elements automatically refresh when language changes

### Fallback Logic

The translation system includes robust fallback logic:

1. **Primary**: Try to get translation from current language
2. **Secondary**: Fall back to default language (English) if key not found
3. **Tertiary**: Return the translation key itself if no translation exists

## UI Configuration

### Theme Support

The application supports multiple themes that work with all languages:

- Dark theme
- Light theme  
- Custom themes via CSS

### Window Settings

Configurable window properties:
- Window size and position
- Always on top setting
- Remember window state
- Splash screen settings

### Auto-refresh Settings

Configurable refresh intervals for:
- Dashboard metrics
- Server status
- Log updates
- User activity

## Adding New Translations

### For Existing Languages

To update translations for existing languages:

1. **Edit the language file** (e.g., `/data/locale/fr.json`)
2. **Add new keys** following the hierarchical structure
3. **Test the translations** by switching to that language

Example:
```json
{
  "ui": {
    "new_feature": {
      "title": "Nouvelle Fonctionnalité",
      "description": "Description de la nouvelle fonctionnalité"
    }
  }
}
```

### For New Languages

To add support for a new language:

1. **Update LanguageManager** in `/src/core/language.py`:
   ```python
   class SupportedLanguage(Enum):
       TURKISH = "tr"
       ENGLISH = "en"
       GERMAN = "de"
       FRENCH = "fr"
       SPANISH = "es"  # Add new language
   ```

2. **Create language file** `/data/locale/es.json` with complete translations

3. **Update native name mapping**:
   ```python
   def _get_native_name(self, language: SupportedLanguage) -> str:
       native_names = {
           # ... existing mappings
           SupportedLanguage.SPANISH: "Español"
       }
   ```

### Translation Guidelines

When adding translations:

1. **Maintain consistency** with existing key structures
2. **Use descriptive keys** that indicate the UI element's purpose
3. **Include context** in key names (e.g., `ui.server.start_server` vs just `start`)
4. **Test thoroughly** with different text lengths
5. **Consider cultural differences** in UI layouts

### Key Naming Conventions

- `app.*` - Application metadata
- `common.*` - Common buttons and actions
- `navigation.*` - Tab and menu navigation
- `auth.*` - Authentication related
- `server.*` - Server operations
- `ui.*` - UI-specific text organized by component
- `messages.*` - User messages and notifications
- `settings.*` - Configuration options

### Variable Substitution

The translation system supports variable substitution:

```json
{
  "ui": {
    "server": {
      "invalid_port": "Invalid port number: {port}. Port must be between 1-65535."
    }
  }
}
```

Usage in code:
```python
language_manager.translate("ui.server.invalid_port", port=8080)
```

## Testing Translations

### Manual Testing

1. **Change language** in the settings
2. **Verify all UI elements** update immediately
3. **Test edge cases** like long text strings
4. **Check tooltips and status messages**

### Automated Testing

The language system includes logging for:
- Missing translation keys
- Failed variable substitutions
- Language loading errors

Check application logs for translation-related issues.

## Best Practices

### For Developers

1. **Always use translations** - Never hardcode UI strings
2. **Use descriptive keys** - Make keys self-documenting
3. **Group related keys** - Use hierarchical structure
4. **Test with long text** - Some languages require more space
5. **Register for language changes** - Use callback system for custom components

### For Translators

1. **Maintain consistency** in terminology
2. **Consider UI constraints** - Some text has length limits
3. **Test in context** - See how translations look in the actual UI
4. **Use appropriate formality** - Match the application's tone
5. **Preserve formatting** - Keep HTML tags and special characters

## Troubleshooting

### Common Issues

1. **Missing translations**: Check application logs for untranslated keys
2. **UI layout issues**: Some languages may need longer text space
3. **Special characters**: Ensure UTF-8 encoding in JSON files
4. **Runtime switching**: Verify components register for language change callbacks

### Debug Mode

Enable debug logging to see translation system activity:
```python
# In application logs, look for:
# "Translation not found for key: ..."
# "Language changed from ... to ..."
# "Failed to load language file: ..."
```

## Future Enhancements

Planned improvements to the multi-language system:

1. **Right-to-left language support** (Arabic, Hebrew)
2. **Pluralization support** for count-dependent translations
3. **Date and number formatting** per locale
4. **Dynamic font selection** based on language requirements
5. **Translation management tools** for easier maintenance

---

For more information about specific configuration options, refer to the individual component documentation or check the application's built-in help system.