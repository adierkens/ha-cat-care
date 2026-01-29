# Cat Care Tracker for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration for tracking cat care activities (feeding, insulin, water, blood glucose) with Google Sheets as the backend database.

![Cat Care Tracker Card](https://github.com/user-attachments/assets/5334d8fc-9904-4221-bda2-72dde45fa75b)

## Features

- 🍽️ **Track Feedings** - Log when your cat is fed
- 💉 **Track Insulin** - Log insulin injections with timestamps
- 💧 **Track Water** - Log water bowl refills
- 🩸 **Track Blood Glucose** - Log blood glucose measurements
- 🔐 **OAuth2 Login** - Secure Google authentication during setup (no service account needed!)

### Dashboard Card

A beautiful custom Lovelace card that shows:
- Today's counts for each activity type
- Quick action buttons for logging activities
- Recent entries timeline
- Blood glucose input modal

### Google Sheets Integration

All data is synced with your Google Sheets spreadsheet, matching your existing column structure:
- `Timestamp` - When the entry was added
- `Date` - The date/time of the activity
- `Checkin Type` - Multi-select (Food, Water, Insulin, Blood Glucose Measurement)
- `Water Refill` - Optional water amount
- `BG (mg/dL)` - Optional blood glucose level

## Installation

### HACS Installation (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS → Integrations → Custom repositories
3. Add this repository URL: `https://github.com/adierkens/ha-google-sheets`
4. Select category: "Integration"
5. Install "Cat Care Tracker"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/cat_care_tracker` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Prerequisites

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the **Google Sheets API**

2. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Select "Web application" as the application type
   - Add `https://my.home-assistant.io/redirect/oauth` to "Authorized redirect URIs"
   - Download or copy the Client ID and Client Secret

3. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Configure the consent screen (can be "External" for personal use)
   - Add your email to test users if in testing mode

### Setup in Home Assistant

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Cat Care Tracker"
3. You'll be prompted to enter your OAuth credentials (Client ID and Secret from Google Cloud)
4. Click through to **authorize with Google** - you'll be redirected to Google's login page
5. After authorization, enter:
   - **Google Spreadsheet ID**: The ID from your sheet URL (e.g., `https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit`)
   - **Cat's Name**: Your cat's name (used for sensor naming)

### Add the Dashboard Card

1. Edit your dashboard
2. Add a new card
3. Select "Cat Care Tracker Card"
4. Configure:
   ```yaml
   type: custom:cat-care-tracker-card
   entity: sensor.YOUR_CAT_NAME_todays_entries
   name: "Your Cat's Name Care Tracker"
   show_recent: true
   show_quick_actions: true
   ```

Or add the Lovelace resource manually:
1. Go to Settings → Dashboards → Resources
2. Add resource: `/cat_care_tracker_static/cat-care-tracker-card.js`
3. Type: JavaScript Module

## Services

The integration provides the following services:

### `cat_care_tracker.log_entry`
Log any combination of activities.

```yaml
service: cat_care_tracker.log_entry
data:
  checkin_types:
    - Food
    - Insulin
  time: "08:30"  # Optional
```

### `cat_care_tracker.log_feeding`
Quick log a feeding.

```yaml
service: cat_care_tracker.log_feeding
data:
  time: "08:30"  # Optional
```

### `cat_care_tracker.log_insulin`
Quick log an insulin injection.

```yaml
service: cat_care_tracker.log_insulin
data:
  time: "08:30"  # Optional
```

### `cat_care_tracker.log_water`
Log a water refill.

```yaml
service: cat_care_tracker.log_water
data:
  water_refill: "250ml"  # Optional
  time: "08:30"  # Optional
```

### `cat_care_tracker.log_blood_glucose`
Log a blood glucose measurement.

```yaml
service: cat_care_tracker.log_blood_glucose
data:
  bg_level: 120  # Required, in mg/dL
  time: "08:30"  # Optional
```

## Sensors

The integration creates the following sensors:

| Sensor | Description |
|--------|-------------|
| `sensor.{cat_name}_last_feeding` | Timestamp of last feeding |
| `sensor.{cat_name}_last_insulin` | Timestamp of last insulin |
| `sensor.{cat_name}_last_water` | Timestamp of last water refill |
| `sensor.{cat_name}_last_bg` | Timestamp of last BG measurement |
| `sensor.{cat_name}_daily_feedings` | Count of feedings today |
| `sensor.{cat_name}_daily_insulin` | Count of insulin today |
| `sensor.{cat_name}_todays_entries` | All entries for today |

## Example Automations

### Morning Feeding Reminder

```yaml
automation:
  - alias: "Morning Feeding Reminder"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: state
        entity_id: sensor.whiskers_daily_feedings
        state: "0"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Cat Care Reminder"
          message: "Time to feed Whiskers!"
```

### Insulin Reminder (After Feeding)

```yaml
automation:
  - alias: "Insulin After Feeding Reminder"
    trigger:
      - platform: state
        entity_id: sensor.whiskers_daily_feedings
    condition:
      - condition: template
        value_template: "{{ states('sensor.whiskers_daily_feedings') | int > states('sensor.whiskers_daily_insulin') | int }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Insulin Reminder"
          message: "Don't forget to give Whiskers their insulin!"
```

## Screenshots

### Dashboard Card
The card shows today's activity counts and provides quick action buttons:

![Card Preview](https://github.com/user-attachments/assets/5334d8fc-9904-4221-bda2-72dde45fa75b)

## Troubleshooting

### Integration not showing in "Add Integration" list
- The integration requires Application Credentials to be configured first
- Go to **Settings** → **Devices & Services** → **Application Credentials**
- Add credentials for "Cat Care Tracker" with your Google OAuth Client ID and Secret
- After adding credentials, the integration will appear in the "Add Integration" list

### "Spreadsheet not found" error
- Double-check the Spreadsheet ID from your Google Sheets URL
- The ID is the long string between `/d/` and `/edit` in the URL
- Example: `https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID_HERE/edit`
- Make sure you're copying just the ID, without any extra spaces or characters

### "You don't have permission to access this spreadsheet"
- Ensure you authenticated with the correct Google account during OAuth
- Verify that the Google account has access to the spreadsheet (check sharing settings)
- The account needs at least "Editor" permissions on the spreadsheet
- Try removing and re-adding the integration to authenticate with a different account

### "Failed to connect to Google Sheets"
- Check your internet connection
- Verify the Google Sheets API is enabled in your Google Cloud project
- Make sure your OAuth credentials are valid and not expired

### "OAuth authentication error"
- Ensure your OAuth redirect URI is set correctly: `https://my.home-assistant.io/redirect/oauth`
- Make sure the Google Sheets API is enabled in your Google Cloud project
- If using "External" OAuth consent screen, ensure your email is added as a test user
- Verify your Client ID and Client Secret are correct

### Card not showing
- Ensure you've added the card as a Lovelace resource
- Clear your browser cache
- Check the browser console for errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details
