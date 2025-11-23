<!--
SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>

SPDX-License-Identifier: GPL-3.0-only
-->

# Barrierefreiheitsmodus (Accessibility Mode)

## Übersicht

Der Barrierefreiheitsmodus verbessert die Zugänglichkeit des QGIS-Plugins durch erweiterte Konfigurationsmöglichkeiten der Benutzeroberfläche.

Dies ist eine technische Dokumentation und ersetzt keine Schulung / Anleitung, wie der Barrieremodus zu benutzen ist.

## Funktionsweise

### Konfigurationsdatei
- Dateiname: `accessibility_mode.ini`
- Konfigurationsdatei im Plugin-Verzeichnis
- Wird automatisch erstellt, wenn der Barrierefreiheitsmodus zum ersten Mal aktiviert wird
- Enthält Einstellungen zur Aktivierung und Farbdefinitionen

### Automatische Aktivierung
- Der Barrierefreiheitsmodus wird beim Plugin-Start automatisch geladen, falls dieser aktiviert ist

### Visuelle Verbesserungen
Der Modus wendet spezielle Fokus-Styles auf verschiedenste UI-Elemente an

### Standard-Fokusfarbe
- **RGB-Werte**: 190, 0, 90 (Magenta-Ton)

## Aktivierung/Deaktivierung

1. Öffne das Plugin-Menü
2. Suche den Menüpunkt "Barrierefreiheitsmodus aktivieren" oder "Barrierefreiheitsmodus deaktivieren"
3. Klicke auf den Menüpunkt, um den Modus zu wechseln
4. Das Plugin wird automatisch neugestartet, um die Änderungen anzuwenden


Hierbei wird der Wert [accessibility][enable] geändert in der `accessibility_mode.ini`:
```ini
[accessibility]
enable = true  # oder false zum Deaktivieren
```

## Konfiguration

### Dateistruktur
Die Konfiguration erfolgt über die `accessibility_mode.ini` Datei im Plugin-Verzeichnis:

```ini
[accessibility]
enable = true
enhanced-borders = true

[QWidget.QLineEdit]
focus = 190,0,90

[QWidget.QComboBox]
focus = 190,0,90

[QWidget.QSpinBox]
focus = 190,0,90

[QWidget.QCheckBox]
focus = 190,0,90

[QWidget.QPushButton]
focus = 190,0,90
```

### Anpassung der Fokusfarben
Es können individuelle Farben für jeden Widget-Typ definieren:
- Format: `R,G,B`
- Wertebereich: 0-255 pro Farbkanal
- Beispiel für dunkelgrün Fokus: `0,100,0`

### Automatische Konfigurationserstellung
- Fehlende Sektionen werden automatisch mit Standardwerten erstellt
- Die Konfigurationsdatei wird bei Bedarf aktualisiert
- Standard-Fokusfarbe: 190,0,90 (Magenta)

## Technische Details

### Qt Style Sheets
Das System wendet folgende Qt Style Sheets an:
```css
QLineEdit:focus {
    border: {border_width}px solid rgb{focus_color};
    outline-color: rgb{focus_color};
}
/* Ähnliche Styles für andere Widget-Typen */
```

### Implementierung
- **Modulübergreifend**: Funktioniert in allen Modulen, die die `UiModuleBase` als Basis verwenden
- **Automatische Erkennung**: Findet alle relevanten UI-Widgets
- **Parent-Widget Styling**: Wendet Styles auf Parent-Container an

## Weiterentwicklung

### Integration in neue Module
Neue UI-Module erhalten automatisch Accessibility-Support durch Vererbung von `UiModuleBase`

### Erweiterung um neue Widget-Typen
Erweitern der `setup_line_edit_accessibility()` in `UiModuleBase`

