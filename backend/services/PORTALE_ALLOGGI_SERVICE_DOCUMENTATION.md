# Portale Alloggi Service Documentation

## Overview

The `PortaleAlloggiService` is a Python service that handles communication with the Italian Portale Alloggiati Web SOAP API. This service is responsible for submitting guest registration data to the Italian national accommodation registry as required by Italian law.

## Table of Contents

1. [Service Architecture](#service-architecture)
2. [Authentication](#authentication)
3. [Data Format](#data-format)
4. [API Methods](#api-methods)
5. [Development vs Production Modes](#development-vs-production-modes)
6. [Guest Type Classification](#guest-type-classification)
7. [Document Types](#document-types)
8. [Location Codes](#location-codes)
9. [Province Handling](#province-handling)
10. [Database Integration](#database-integration)
11. [Error Handling](#error-handling)
12. [Usage Examples](#usage-examples)
13. [Configuration](#configuration)
14. [Frontend Integration](#frontend-integration)

## Service Architecture

### Class: `PortaleAlloggiService`

The main service class that encapsulates all functionality for interacting with the Portale Alloggiati API.

#### Constructor Parameters

```python
def __init__(self, username: str, password: str, ws_key: str)
```

- **username** (str): Username for Portale Alloggi authentication
- **password** (str): Password for Portale Alloggi authentication
- **ws_key** (str): Web Service Key for API access

#### Service Endpoint

- **WSDL URL**: `https://alloggiatiweb.poliziadistato.it/service/service.asmx`

## Authentication

### Method: `authenticate()`

Authenticates with the Portale Alloggi service and obtains a session token.

#### Process Flow

1. Creates SOAP envelope with credentials
2. Sends POST request to authentication endpoint
3. Parses XML response for success/error status
4. Extracts and stores authentication token
5. Returns token on success, None on failure

#### SOAP Request Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GenerateToken xmlns="AlloggiatiService">
      <Utente>{username}</Utente>
      <Password>{password}</Password>
      <WsKey>{ws_key}</WsKey>
    </GenerateToken>
  </soap:Body>
</soap:Envelope>
```

#### Response Handling

- **Success**: Returns authentication token
- **Failure**: Logs error details and returns None
- **Network Errors**: Handles timeouts and connection issues
- **XML Parsing Errors**: Graceful error handling for malformed responses

## Data Format

### Schedina Format

The service formats guest data into a 168-character fixed-length string called a "schedina" according to the official Portale Alloggiati specification.

#### Schedina Structure (168 characters)

| Position | Length | Field             | Description               | Example      |
| -------- | ------ | ----------------- | ------------------------- | ------------ |
| 0-1      | 2      | Tipo Alloggiato   | Guest type code           | 16           |
| 2-11     | 10     | Data Arrivo       | Arrival date (DD/MM/YYYY) | 15/09/2025   |
| 12-13    | 2      | Giorni Permanenza | Stay duration (01-30)     | 03           |
| 14-63    | 50     | Cognome           | Surname                   | PASQUARIELLO |
| 64-93    | 30     | Nome              | First name                | GIOVANNI     |
| 94       | 1      | Sesso             | Gender (1=M, 2=F)         | 1            |
| 95-104   | 10     | Data Nascita      | Birth date (DD/MM/YYYY)   | 01/01/1990   |
| 105-113  | 9      | Comune Nascita    | Birth municipality code   | 100000100    |
| 114-115  | 2      | Provincia Nascita | Birth province code       | MI           |
| 116-124  | 9      | Stato Nascita     | Birth country code        | 100000100    |
| 125-133  | 9      | Cittadinanza      | Citizenship code          | 100000100    |
| 134-138  | 5      | Tipo Documento    | Document type code        | IDENT        |
| 139-158  | 20     | Numero Documento  | Document number           | AB1234567    |
| 159-167  | 9      | Luogo Rilascio    | Document issue location   | 100000100    |

## API Methods

### Method: `format_schedina(client_data, reservation_data)`

Formats client and reservation data into a 168-character schedina string.

#### Parameters

- **client_data** (Dict[str, Any]): Client information dictionary
- **reservation_data** (Dict[str, Any]): Reservation information dictionary

#### Returns

- **str**: 168-character formatted schedina string

#### Data Validation

- Date formatting: Converts various date formats to DD/MM/YYYY
- String padding: Ensures proper field lengths with space padding
- Default values: Provides fallback values for missing data

### Method: `test_schedine(schedine_lines)`

Tests schedine data without actually submitting it to the registry.

#### Parameters

- **schedine_lines** (List[str]): List of 168-character schedina strings

#### Returns

- **Dict[str, Any]**: Test results including validation status

#### Process Flow

1. Authenticates if no valid token exists
2. Creates SOAP envelope with test data
3. Sends test request to API
4. Parses response for validation results
5. Returns detailed test results

### Method: `send_schedine(schedine_lines)`

Submits schedine data to the Portale Alloggi registry.

#### Parameters

- **schedine_lines** (List[str]): List of 168-character schedina strings

#### Returns

- **Dict[str, Any]**: Submission results

#### Process Flow

1. Authenticates if no valid token exists
2. Creates SOAP envelope with submission data
3. Sends data to API
4. Parses response for submission results
5. Returns success/failure status

### Method: `submit_guest_registration(clients_data, reservation_data)`

High-level method for submitting guest registration data to **PRODUCTION**.

#### Parameters

- **clients_data** (List[Dict[str, Any]]): List of client data dictionaries
- **reservation_data** (Dict[str, Any]): Reservation information

#### Returns

- **Dict[str, Any]**: Submission results

#### Process Flow

1. Formats all clients into schedine lines
2. **Directly submits to production** using `send_schedine()`
3. Returns final results

### Method: `test_guest_registration(clients_data, reservation_data)`

High-level method for testing guest registration data using **TEST endpoint**.

#### Parameters

- **clients_data** (List[Dict[str, Any]]): List of client data dictionaries
- **reservation_data** (Dict[str, Any]): Reservation information

#### Returns

- **Dict[str, Any]**: Test results

#### Process Flow

1. Formats all clients into schedine lines
2. **Tests data using test endpoint** with `test_schedine()`
3. Returns test results without submitting to production

## Development vs Production Modes

### Development Mode Features

The service supports two distinct modes for development and production environments:

#### Test Mode (Development)

- **Endpoint**: Uses `Test` SOAP operation
- **Purpose**: Safe testing without affecting production data
- **Database**: Does not track submission status
- **UI**: Shows orange "Test (SOAP)" button
- **Behavior**: Can be used multiple times without disabling buttons

#### Production Mode

- **Endpoint**: Uses `Send` SOAP operation
- **Purpose**: Real data submission to Portale Alloggi
- **Database**: Tracks submission status and timestamps
- **UI**: Shows blue "Send (REAL)" button
- **Behavior**: Disables buttons after successful submission

### SOAP Operation Differences

#### Test Operation

```xml
<Test xmlns="AlloggiatiService">
  <Utente>{username}</Utente>
  <token>{token}</token>
  <ElencoSchedine>
    <string>schedina_data</string>
  </ElencoSchedine>
</Test>
```

#### Production Operation

```xml
<Send xmlns="AlloggiatiService">
  <Utente>{username}</Utente>
  <token>{token}</token>
  <ElencoSchedine>
    <string>schedina_data</string>
  </ElencoSchedine>
</Send>
```

### Environment Configuration

#### Development Environment

```typescript
export const environment = {
  baseUrl: "http://localhost:4200",
  production: false,
  apiBaseUrl: "http://127.0.0.1:5001",
  development: true, // Enables dual button mode
};
```

#### Production Environment

```typescript
export const environment = {
  baseUrl: "https://your-domain.com",
  production: true,
  apiBaseUrl: "https://api.your-domain.com",
  development: false, // Shows single button
};
```

## Guest Type Classification

Based on the `tipo_alloggiato.csv` file, the service supports the following guest types:

### Guest Type Codes

| Code | Description    | Usage         |
| ---- | -------------- | ------------- |
| 16   | OSPITE SINGOLO | Single guest  |
| 17   | CAPO FAMIGLIA  | Family head   |
| 18   | CAPO GRUPPO    | Group leader  |
| 19   | FAMILIARE      | Family member |
| 20   | MEMBRO GRUPPO  | Group member  |

### Classification Logic

The service should implement logic to automatically determine the appropriate guest type:

- **Single Guest**: Code 16 (OSPITE SINGOLO)
- **Family**:
  - First family member: Code 17 (CAPO FAMIGLIA)
  - Additional family members: Code 19 (FAMILIARE)
- **Group**:
  - Group leader: Code 18 (CAPO GRUPPO)
  - Group members: Code 20 (MEMBRO GRUPPO)

## Document Types

Based on the `documenti.csv` file, the service supports 97 different document types including:

### Common Document Types

| Code  | Description                 |
| ----- | --------------------------- |
| IDENT | CARTA DI IDENTITA'          |
| PASOR | PASSAPORTO ORDINARIO        |
| PASDI | PASSAPORTO DIPLOMATICO      |
| PASSE | PASSAPORTO DI SERVIZIO      |
| PATEN | PATENTE DI GUIDA            |
| IDELE | CARTA IDENTITA' ELETTRONICA |

### Implementation Requirements

- Store document type IDs in database
- Map frontend selections to appropriate codes
- Support all 97 document types from the CSV file
- Create JSON mapping for frontend conversion

## Location Codes

### Municipalities (Comuni)

Based on `comuni.csv` with 11,296 entries:

- **Format**: 9-digit code (e.g., 405028001)
- **Structure**: Code + Description + Province + End Date
- **Example**: 405028001,ABANO TERME,PD,

### Countries (Stati)

Based on `stati.csv` with 238 entries:

- **Format**: 9-digit code (e.g., 100000100)
- **Structure**: Code + Description + Province + End Date
- **Example**: 100000100,ITALIA,ES,

### Implementation Requirements

- Store all municipality and country codes in database
- Map frontend selections to appropriate codes
- Support all locations from CSV files
- Create JSON mapping for frontend conversion

## Province Handling

### Province Acronyms vs Municipality Codes

The service handles two different approaches for province data:

#### Province Acronyms (for Portale Alloggi)

- **Format**: 2-character codes (e.g., "NA", "MI", "RM")
- **Usage**: Required by Portale Alloggi for `provincia_nascita` and `provincia_residenza`
- **Source**: `province_acronyms.json` file
- **Example**: "NA" for Napoli, "MI" for Milano

#### Municipality Codes (for other fields)

- **Format**: 9-digit codes (e.g., "415061067")
- **Usage**: Used for `comune_nascita` and `luogo_emissione`
- **Source**: `municipalities.json` file
- **Example**: "415061067" for specific municipality

### Database Schema Updates

#### Client Table Changes

```sql
-- Updated province fields to store acronyms
ALTER TABLE client ALTER COLUMN provincia_nascita TYPE VARCHAR(2);
ALTER TABLE client ALTER COLUMN provincia_residenza TYPE VARCHAR(2);

-- Removed redundant fields
ALTER TABLE client DROP COLUMN city;
ALTER TABLE client DROP COLUMN province;
```

#### Reservation Table Additions

```sql
-- Portale Alloggi submission tracking
ALTER TABLE reservation ADD COLUMN portale_alloggi_sent BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE reservation ADD COLUMN portale_alloggi_sent_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE reservation ADD COLUMN portale_alloggi_response TEXT;
```

## Database Integration

### Submission Status Tracking

The service now tracks Portale Alloggi submission status in the database:

#### Status Fields

- **`portale_alloggi_sent`**: Boolean flag indicating if data has been sent
- **`portale_alloggi_sent_at`**: Timestamp of successful submission
- **`portale_alloggi_response`**: Response from Portale Alloggi service

#### API Endpoints

##### Test Submission

```
POST /api/admin/reservations/{id}/send-to-portale-alloggi
```

- Uses test SOAP endpoint
- Does not update submission status
- Returns test results only

##### Production Submission

```
POST /api/admin/reservations/{id}/send-to-portale-alloggi-real
```

- Uses production SOAP endpoint
- Updates submission status in database
- Tracks submission timestamp and response

##### Status Retrieval

```
GET /api/admin/reservations/{id}/portale-alloggi-status
```

- Returns current submission status
- Includes timestamp and response data

### Data Format Updates

#### Schedina Length Adjustment

The schedina format has been updated from 175 to 168 characters:

| Position | Length | Field             | Description               |
| -------- | ------ | ----------------- | ------------------------- |
| 0-1      | 2      | Tipo Alloggiato   | Guest type code           |
| 2-11     | 10     | Data Arrivo       | Arrival date (DD/MM/YYYY) |
| 12-13    | 2      | Giorni Permanenza | Stay duration (01-30)     |
| 14-63    | 50     | Cognome           | Surname                   |
| 64-93    | 30     | Nome              | First name                |
| 94       | 1      | Sesso             | Gender (1=M, 2=F)         |
| 95-104   | 10     | Data Nascita      | Birth date (DD/MM/YYYY)   |
| 105-113  | 9      | Comune Nascita    | Birth municipality code   |
| 114-115  | 2      | Provincia Nascita | Birth province acronym    |
| 116-124  | 9      | Stato Nascita     | Birth country code        |
| 125-133  | 9      | Cittadinanza      | Citizenship code          |
| 134-138  | 5      | Tipo Documento    | Document type code        |
| 139-158  | 20     | Numero Documento  | Document number           |
| 159-167  | 9      | Luogo Rilascio    | Document issue location   |

**Total: 168 characters**

## Error Handling

### Authentication Errors

- Invalid credentials
- Network connectivity issues
- Service unavailability
- Token expiration

### Data Validation Errors

- Invalid date formats
- Missing required fields
- Incorrect field lengths
- Invalid character encoding

### API Response Errors

- SOAP parsing errors
- Service-specific error codes
- Rate limiting
- Timeout errors

### Error Response Format

```python
{
    'success': False,
    'error': 'Error description',
    'error_code': 'ERROR_CODE',
    'error_description': 'Detailed error message',
    'error_detail': 'Additional error details'
}
```

## Frontend Integration

### Development Mode UI

In development mode, the frontend displays two buttons for Portale Alloggi submissions:

#### Test Button (Orange)

```html
<p-button
  [label]="'send-to-portale-alloggi-test-btn' | transloco"
  icon="pi pi-flask"
  severity="warn"
  (click)="sendToPortaleAlloggiTest()"
>
</p-button>
```

- **Color**: Orange (warning)
- **Icon**: Flask (test tube)
- **Behavior**: Does not disable buttons after use
- **Purpose**: Safe testing without affecting production

#### Real Button (Blue)

```html
<p-button
  [label]="'send-to-portale-alloggi-real-btn' | transloco"
  icon="pi pi-send"
  severity="info"
  (click)="sendToPortaleAlloggiReal()"
>
</p-button>
```

- **Color**: Blue (info)
- **Icon**: Send
- **Behavior**: Disables buttons after successful submission
- **Purpose**: Real data submission to production

### Production Mode UI

In production mode, only a single button is shown:

```html
<p-button
  [label]="'send-to-portale-alloggi-btn' | transloco"
  icon="pi pi-send"
  severity="info"
  (click)="openPortaleAlloggiModal()"
>
</p-button>
```

### Status Tracking UI

After successful submission, the UI shows:

```html
<p-button
  [label]="'data-sent-to-portale-alloggi' | transloco"
  icon="pi pi-check"
  severity="success"
  [disabled]="true"
>
</p-button>
```

### Translation Keys

#### English (`en.json`)

```json
{
  "send-to-portale-alloggi-test-btn": "Test (SOAP)",
  "send-to-portale-alloggi-real-btn": "Send (REAL)",
  "data-sent-to-portale-alloggi": "Data Sent to Portale Alloggi",
  "data-sent-success-test": "Data successfully sent to Portale Alloggi (TEST MODE)",
  "data-sent-success-real": "Data successfully sent to Portale Alloggi (PRODUCTION)"
}
```

#### Italian (`it.json`)

```json
{
  "send-to-portale-alloggi-test-btn": "Test (SOAP)",
  "send-to-portale-alloggi-real-btn": "Invia (REALE)",
  "data-sent-to-portale-alloggi": "Dati Inviati a Portale Alloggi",
  "data-sent-success-test": "Dati inviati con successo a Portale Alloggi (MODALITÀ TEST)",
  "data-sent-success-real": "Dati inviati con successo a Portale Alloggi (PRODUZIONE)"
}
```

## Usage Examples

### Development Mode Usage

```python
from services.portale_alloggi_service import PortaleAlloggiService

# Initialize service
service = PortaleAlloggiService(
    username="your_username",
    password="your_password",
    ws_key="your_ws_key"
)

# Prepare client data with province acronyms
client_data = {
    'tipo_alloggiato': '16',  # Single guest
    'surname': 'PASQUARIELLO',
    'name': 'GIOVANNI',
    'sesso': 1,  # Male
    'birthday': '01/01/1990',
    'comune_nascita': '415061067',  # 9-digit municipality code
    'provincia_nascita': 'NA',      # 2-character province acronym
    'stato_nascita': '100000100',
    'cittadinanza': '100000100',
    'document_type': 'IDENT',
    'document_number': 'AB1234567',
    'luogo_emissione': '415061067'  # 9-digit municipality code
}

# Prepare reservation data
reservation_data = {
    'start_date': '15/09/2025'
}

# Test registration (safe for development)
test_result = service.test_guest_registration([client_data], reservation_data)
print(f"Test result: {test_result}")

# Production registration (real submission)
if test_result['success']:
    submit_result = service.submit_guest_registration([client_data], reservation_data)
    print(f"Production result: {submit_result}")
```

### Family Registration

```python
# Family head
family_head = {
    'tipo_alloggiato': '17',  # Family head
    'surname': 'ROSSI',
    'name': 'MARIO',
    # ... other fields
}

# Family member
family_member = {
    'tipo_alloggiato': '19',  # Family member
    'surname': 'ROSSI',
    'name': 'ANNA',
    # ... other fields
}

# Submit family registration
family_data = [family_head, family_member]
result = service.submit_guest_registration(family_data, reservation_data)
```

### Group Registration

```python
# Group leader
group_leader = {
    'tipo_alloggiato': '18',  # Group leader
    'surname': 'BIANCHI',
    'name': 'LUCA',
    # ... other fields
}

# Group member
group_member = {
    'tipo_alloggiato': '20',  # Group member
    'surname': 'VERDI',
    'name': 'SARA',
    # ... other fields
}

# Submit group registration
group_data = [group_leader, group_member]
result = service.submit_guest_registration(group_data, reservation_data)
```

## Configuration

### Environment Variables

```bash
PORTALE_ALLOGGI_USERNAME=your_username
PORTALE_ALLOGGI_PASSWORD=your_password
PORTALE_ALLOGGI_WS_KEY=your_ws_key
```

### Frontend Environment Configuration

#### Development Environment

```typescript
// frontend/src/environments/environments.ts
export const environment = {
  baseUrl: "http://localhost:4200",
  production: false,
  apiBaseUrl: "http://127.0.0.1:5001",
  development: true, // Enables dual button mode
};
```

#### Production Environment

```typescript
// frontend/src/environments/environment.prod.ts
export const environment = {
  baseUrl: "https://your-domain.com",
  production: true,
  apiBaseUrl: "https://api.your-domain.com",
  development: false, // Shows single button
};
```

### Database Schema Updates

The service requires database tables to store:

1. **Guest Types**: Mapping of guest type codes to descriptions
2. **Document Types**: Mapping of document type codes to descriptions
3. **Municipalities**: Mapping of municipality codes to names and provinces
4. **Countries**: Mapping of country codes to names
5. **Province Acronyms**: Mapping of province acronyms to full names

### JSON Mapping Files

Create JSON files for frontend integration:

- `guest_types.json`: Guest type mappings
- `document_types.json`: Document type mappings
- `municipalities.json`: Municipality mappings (9-digit codes)
- `countries.json`: Country mappings
- `province_acronyms.json`: Province acronym mappings (2-character codes)

### Database Migration Scripts

#### Province Field Updates

```sql
-- Update province fields to store acronyms
ALTER TABLE client ALTER COLUMN provincia_nascita TYPE VARCHAR(2);
ALTER TABLE client ALTER COLUMN provincia_residenza TYPE VARCHAR(2);

-- Remove redundant fields
ALTER TABLE client DROP COLUMN city;
ALTER TABLE client DROP COLUMN province;
```

#### Submission Tracking

```sql
-- Add Portale Alloggi submission tracking
ALTER TABLE reservation ADD COLUMN portale_alloggi_sent BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE reservation ADD COLUMN portale_alloggi_sent_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE reservation ADD COLUMN portale_alloggi_response TEXT;
```

## Security Considerations

- Store credentials securely (environment variables or encrypted config)
- Use HTTPS for all API communications
- Implement proper error logging without exposing sensitive data
- Validate all input data before processing
- Implement rate limiting to prevent API abuse

## Monitoring and Logging

- Log all API requests and responses
- Monitor authentication token expiration
- Track submission success/failure rates
- Alert on service unavailability
- Maintain audit trail for compliance

## Compliance

This service implements the Italian Portale Alloggiati requirements for:

- Guest registration data submission
- Data format compliance (168-character schedina)
- Authentication and authorization
- Error handling and reporting
- Audit trail maintenance

## Completed Features

### ✅ Development vs Production Modes

- **Dual Button System**: Separate test and production buttons in development mode
- **Environment Detection**: Automatic UI adaptation based on environment configuration
- **Safe Testing**: Test mode doesn't affect production data or disable buttons

### ✅ Province Handling

- **Province Acronyms**: 2-character codes (NA, MI, RM) for Portale Alloggi requirements
- **Municipality Codes**: 9-digit codes for other location fields
- **Database Schema**: Updated to support both formats appropriately

### ✅ Submission Status Tracking

- **Database Integration**: Tracks submission status, timestamps, and responses
- **UI Status Display**: Shows submission status in admin interface
- **Button Management**: Prevents duplicate submissions with proper status tracking

### ✅ Data Format Compliance

- **Schedina Length**: Updated to 168 characters as per Portale Alloggi specification
- **Date Formatting**: Proper DD/MM/YYYY format for all date fields
- **Field Validation**: Comprehensive validation for all required fields

### ✅ Frontend Integration

- **Translation Support**: Full i18n support for English and Italian
- **Responsive UI**: Proper button states and loading indicators
- **Status Management**: Real-time status updates and button state management

## Future Enhancements

1. **Automatic Guest Type Detection**: Implement logic to automatically determine guest types based on reservation context
2. **Enhanced Data Validation**: Add comprehensive validation for all data fields
3. **Batch Processing**: Support for processing multiple reservations efficiently
4. **Retry Logic**: Implement automatic retry for failed submissions
5. **Caching**: Cache authentication tokens and reference data
6. **Webhook Support**: Add webhook notifications for submission results
7. **Audit Trail**: Enhanced logging and audit trail for compliance
8. **Performance Optimization**: Optimize data loading and processing for large datasets
