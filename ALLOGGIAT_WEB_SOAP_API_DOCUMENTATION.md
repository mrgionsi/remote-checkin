# 📋 Portale Alloggiati Web SOAP API - Complete Technical Documentation

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication System](#authentication-system)
3. [SOAP Message Structure](#soap-message-structure)
4. [Data Format Specification](#data-format-specification)
5. [API Operations](#api-operations)
6. [Response Handling](#response-handling)
7. [Error Management](#error-management)
8. [Implementation Architecture](#implementation-architecture)
9. [Service Integration](#service-integration)
10. [Security Considerations](#security-considerations)

---

## API Overview

The **Portale Alloggiati Web** is the official Italian State Police service for managing guest registration data in accommodation establishments. The system uses SOAP web services for secure communication and data exchange.

### Service Architecture

- **Protocol**: HTTPS with SOAP 1.1/1.2
- **Endpoint**: `https://alloggiatiweb.poliziadistato.it/service/service.asmx`
- **Authentication**: Token-based with expiration
- **Data Format**: Fixed-length string records (168 characters)
- **Namespace**: `AlloggiatiService`
- **Character Encoding**: UTF-8

### Service Purpose

The Portale Alloggiati Web service enables accommodation providers to:

- Submit guest registration data to Italian authorities
- Validate guest information before submission
- Retrieve reference data (countries, document types, etc.)
- Manage authentication and authorization

---

## Authentication System

### Token-Based Authentication

The service uses a token-based authentication system where:

1. Client authenticates with credentials to obtain a token
2. Token is included in subsequent requests
3. Tokens have expiration times for security
4. Tokens must be refreshed when expired

### GenerateToken Request

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GenerateToken xmlns="AlloggiatiService">
      <Utente>username</Utente>
      <Password>password</Password>
      <WsKey>webservice_key</WsKey>
    </GenerateToken>
  </soap:Body>
</soap:Envelope>
```

**Response Structure:**

```xml
<GenerateTokenResponse>
  <GenerateTokenResult>
    <issued>2024-01-15T10:30:00</issued>
    <expires>2024-01-15T18:30:00</expires>
    <token>auth_token_string</token>
  </GenerateTokenResult>
  <result>
    <esito>true</esito>
    <ErroreCod></ErroreCod>
    <ErroreDes></ErroreDes>
  </result>
</GenerateTokenResponse>
```

---

## SOAP Request Structure

### 1. Test Request (Validate Data)

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Test xmlns="AlloggiatiService">
      <Utente>username</Utente>
      <token>auth_token</token>
      <ElencoSchedine>
        <string>schedina_line_1</string>
        <string>schedina_line_2</string>
      </ElencoSchedine>
    </Test>
  </soap:Body>
</soap:Envelope>
```

### 2. Send Request (Submit Data)

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Send xmlns="AlloggiatiService">
      <Utente>username</Utente>
      <token>auth_token</token>
      <ElencoSchedine>
        <string>schedina_line_1</string>
        <string>schedina_line_2</string>
      </ElencoSchedine>
      <result>
        <SchedineValide>100</SchedineValide>
        <Dettaglio>
          <EsitoOperazioneServizio>
            <esito>true</esito>
            <ErroreCod>string</ErroreCod>
            <ErroreDes>string</ErroreDes>
            <ErroreDettaglio>string</ErroreDettaglio>
          </EsitoOperazioneServizio>
        </Dettaglio>
      </result>
    </Send>
  </soap:Body>
</soap:Envelope>
```

### 3. Tabella Request (Get Reference Data)

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Tabella xmlns="AlloggiatiService">
      <Utente>username</Utente>
      <token>auth_token</token>
      <tipo>Tipi_Alloggiato</tipo>
    </Tabella>
  </soap:Body>
</soap:Envelope>
```

**Available Table Types:**

- `Luoghi` - Places/Countries
- `Tipi_Documento` - Document Types
- `Tipi_Alloggiato` - Guest Types
- `TipoErrore` - Error Types
- `ListaAppartamenti` - Apartment List

---

## Data Format Specification

### Schedina Structure (168 characters fixed-length)

The schedina is the core data structure representing guest information. It must be exactly 168 characters with fixed field positions:

| Position | Field Name        | Length | Format     | Description                          | Example                 |
| -------- | ----------------- | ------ | ---------- | ------------------------------------ | ----------------------- |
| 1-2      | Tipo Alloggiato   | 2      | Numeric    | Guest type code (16-20)              | "16"                    |
| 3-12     | Data Arrivo       | 10     | dd/mm/yyyy | Arrival date                         | "15/09/2025"            |
| 13-14    | Giorni Permanenza | 2      | Numeric    | Stay duration (01-30)                | "03"                    |
| 15-64    | Cognome           | 50     | String     | Last name (UPPERCASE, space-padded)  | "ROSSI" + 45 spaces     |
| 65-94    | Nome              | 30     | String     | First name (UPPERCASE, space-padded) | "MARIO" + 25 spaces     |
| 95       | Sesso             | 1      | Numeric    | Gender (1=Male, 2=Female)            | "1"                     |
| 96-105   | Data Nascita      | 10     | dd/mm/yyyy | Birth date                           | "01/01/1990"            |
| 106-114  | Comune Nascita    | 9      | String     | Birth municipality code              | "415063001"             |
| 115-116  | Provincia Nascita | 2      | String     | Birth province code                  | "NA"                    |
| 117-125  | Stato Nascita     | 9      | String     | Birth country code                   | "100000100"             |
| 126-134  | Cittadinanza      | 9      | String     | Citizenship code                     | "100000100"             |
| 135-139  | Tipo Documento    | 5      | String     | Document type code                   | "IDENT"                 |
| 140-159  | Numero Documento  | 20     | String     | Document number (space-padded)       | "YA1234567" + 12 spaces |
| 160-168  | Luogo Rilascio    | 9      | String     | Document issue place code            | "100000100"             |

### Field Formatting Rules

#### String Fields

- **Uppercase**: All text must be in UPPERCASE
- **Space Padding**: Fields must be left-padded with spaces to exact length
- **No Special Characters**: Avoid accents, diacritics, and special characters

#### Date Fields

- **Format**: DD/MM/YYYY
- **Example**: "15/09/2025" for September 15, 2025
- **Validation**: Must be valid dates

#### Numeric Fields

- **Zero Padding**: Numeric fields are zero-padded (e.g., "01", "02", "30")
- **Range Validation**: Days of stay must be 01-30

---

## API Operations

### 1. GenerateToken

**Purpose**: Authenticate and obtain access token

**Request**:

```xml
<GenerateToken xmlns="AlloggiatiService">
  <Utente>username</Utente>
  <Password>password</Password>
  <WsKey>webservice_key</WsKey>
</GenerateToken>
```

**Response**:

```xml
<GenerateTokenResponse>
  <GenerateTokenResult>
    <issued>timestamp</issued>
    <expires>timestamp</expires>
    <token>token_string</token>
  </GenerateTokenResult>
  <result>
    <esito>true|false</esito>
    <ErroreCod>error_code</ErroreCod>
    <ErroreDes>error_description</ErroreDes>
    <ErroreDettaglio>error_detail</ErroreDettaglio>
  </result>
</GenerateTokenResponse>
```

### 2. Test

**Purpose**: Validate schedine data without submitting

**Request**:

```xml
<Test xmlns="AlloggiatiService">
  <Utente>username</Utente>
  <token>auth_token</token>
  <ElencoSchedine>
    <string>schedina_line_1</string>
    <string>schedina_line_2</string>
  </ElencoSchedine>
</Test>
```

**Response**:

```xml
<TestResponse>
  <TestResult>
    <esito>true|false</esito>
    <ErroreCod>error_code</ErroreCod>
    <ErroreDes>error_description</ErroreDes>
    <ErroreDettaglio>error_detail</ErroreDettaglio>
  </TestResult>
  <result>
    <SchedineValide>count</SchedineValide>
    <Dettaglio>
      <EsitoOperazioneServizio>
        <esito>true|false</esito>
        <ErroreCod>error_code</ErroreCod>
        <ErroreDes>error_description</ErroreDes>
        <ErroreDettaglio>error_detail</ErroreDettaglio>
      </EsitoOperazioneServizio>
    </Dettaglio>
  </result>
</TestResponse>
```

### 3. Send

**Purpose**: Submit validated schedine data

**Request**:

```xml
<Send xmlns="AlloggiatiService">
  <Utente>username</Utente>
  <token>auth_token</token>
  <ElencoSchedine>
    <string>schedina_line_1</string>
    <string>schedina_line_2</string>
  </ElencoSchedine>
  <result>
    <SchedineValide>100</SchedineValide>
    <Dettaglio>
      <EsitoOperazioneServizio>
        <esito>true</esito>
        <ErroreCod>string</ErroreCod>
        <ErroreDes>string</ErroreDes>
        <ErroreDettaglio>string</ErroreDettaglio>
      </EsitoOperazioneServizio>
    </Dettaglio>
  </result>
</Send>
```

**Response**:

```xml
<SendResponse>
  <SendResult>
    <esito>true|false</esito>
    <ErroreCod>error_code</ErroreCod>
    <ErroreDes>error_description</ErroreDes>
    <ErroreDettaglio>error_detail</ErroreDettaglio>
  </SendResult>
  <result>
    <SchedineValide>count</SchedineValide>
    <Dettaglio>
      <EsitoOperazioneServizio>
        <esito>true|false</esito>
        <ErroreCod>error_code</ErroreCod>
        <ErroreDes>error_description</ErroreDes>
        <ErroreDettaglio>error_detail</ErroreDettaglio>
      </EsitoOperazioneServizio>
    </Dettaglio>
  </result>
</SendResponse>
```

### 4. Tabella

**Purpose**: Retrieve reference data

**Request**:

```xml
<Tabella xmlns="AlloggiatiService">
  <Utente>username</Utente>
  <token>auth_token</token>
  <tipo>table_type</tipo>
</Tabella>
```

**Available Table Types**:

- `Luoghi` - Places/Countries
- `Tipi_Documento` - Document Types
- `Tipi_Alloggiato` - Guest Types
- `TipoErrore` - Error Types
- `ListaAppartamenti` - Apartment List

---

## Response Handling

### Success Response Structure

All successful responses follow this pattern:

```xml
<OperationResponse>
  <OperationResult>
    <esito>true</esito>
    <ErroreCod></ErroreCod>
    <ErroreDes></ErroreDes>
    <ErroreDettaglio></ErroreDettaglio>
  </OperationResult>
  <result>
    <!-- Operation-specific data -->
  </result>
</OperationResponse>
```

### Error Response Structure

All error responses follow this pattern:

```xml
<OperationResponse>
  <OperationResult>
    <esito>false</esito>
    <ErroreCod>ERROR_CODE</ErroreCod>
    <ErroreDes>Error Description</ErroreDes>
    <ErroreDettaglio>Detailed Error Information</ErroreDettaglio>
  </OperationResult>
</OperationResponse>
```

### Response Parsing Logic

1. **Check Operation Result**: First check the `esito` field in the operation result
2. **Extract Data**: If successful, extract data from the `result` element
3. **Handle Errors**: If failed, extract error details from the operation result
4. **Validate Service Operation**: Check `EsitoOperazioneServizio` for additional validation

---

## Error Management

### Error Categories

#### Authentication Errors

- **INVALID_CREDENTIALS**: Username/password incorrect
- **INVALID_WSKEY**: Web service key invalid
- **TOKEN_EXPIRED**: Authentication token expired
- **ACCOUNT_LOCKED**: Account temporarily locked

#### Data Validation Errors

- **INVALID_FORMAT**: Schedina format incorrect
- **INVALID_FIELD**: Specific field validation failed
- **MISSING_REQUIRED**: Required field missing
- **INVALID_DATE**: Date format or value invalid

#### System Errors

- **SERVICE_UNAVAILABLE**: Service temporarily unavailable
- **RATE_LIMIT_EXCEEDED**: Too many requests
- **INTERNAL_ERROR**: Server-side error

### Error Handling Strategy

1. **Retry Logic**: Implement exponential backoff for transient errors
2. **Token Refresh**: Automatically refresh expired tokens
3. **Data Validation**: Validate data before submission
4. **Logging**: Log all errors for debugging and monitoring
5. **User Feedback**: Provide meaningful error messages to users

---

## Implementation Architecture

### Service Layer Architecture

```python
class PortaleAlloggiService:
    """
    Main service class for Portale Alloggi integration
    """

    def __init__(self, username: str, password: str, ws_key: str):
        """Initialize service with credentials"""

    def authenticate(self) -> Optional[str]:
        """Generate authentication token"""

    def format_schedina(self, client_data: Dict, reservation_data: Dict) -> str:
        """Format guest data into 168-character schedina"""

    def test_schedine(self, schedine_lines: List[str]) -> Dict[str, Any]:
        """Validate schedine data without submitting"""

    def send_schedine(self, schedine_lines: List[str]) -> Dict[str, Any]:
        """Submit validated schedine data"""

    def submit_guest_registration(self, clients_data: List[Dict], reservation_data: Dict) -> Dict[str, Any]:
        """Complete guest registration workflow"""
```

### Data Flow

1. **Authentication**: Obtain token from GenerateToken operation
2. **Data Formatting**: Convert guest data to 168-character schedina format
3. **Validation**: Use Test operation to validate data format
4. **Submission**: Use Send operation to submit validated data
5. **Error Handling**: Process and handle any errors or exceptions

---

## Security Considerations

### Data Protection

#### Sensitive Data Handling

- **Encryption**: Encrypt sensitive data at rest and in transit
- **Access Control**: Implement role-based access control
- **Audit Logging**: Log all data access and modifications
- **Data Retention**: Follow data retention policies

#### Authentication Security

- **Credential Storage**: Store credentials securely (environment variables, key vaults)
- **Token Management**: Implement secure token storage and rotation
- **Session Management**: Handle session timeouts appropriately
- **Rate Limiting**: Implement rate limiting to prevent abuse

### Compliance Requirements

#### GDPR Compliance

- **Data Minimization**: Collect only necessary data
- **Consent Management**: Obtain proper consent for data processing
- **Right to Erasure**: Implement data deletion capabilities
- **Data Portability**: Support data export functionality

#### Italian Legal Requirements

- **Guest Registration**: Comply with Italian accommodation laws
- **Data Retention**: Follow Italian data retention requirements
- **Reporting Obligations**: Meet reporting deadlines and requirements
- **Privacy Protection**: Protect guest privacy rights

---

## Conclusion

The Portale Alloggiati Web SOAP API provides a robust and secure method for Italian accommodation providers to comply with guest registration requirements. This documentation covers all aspects of the API integration, from basic authentication to advanced error handling and security considerations.

Key takeaways:

- Always test data format before submission
- Implement proper error handling and retry logic
- Follow security best practices for credential management
- Monitor service health and performance
- Keep documentation and tests up to date

For testing procedures and scenarios, refer to the [Testing Guide](test_portale_alloggi/TEST_PORTALE_ALLOGGI_README.md).

---

## References

- [Official Portale Alloggiati Documentation](https://alloggiatiweb.poliziadistato.it/)
- [SOAP 1.1 Specification](https://www.w3.org/TR/soap11/)
- [SOAP 1.2 Specification](https://www.w3.org/TR/soap12/)
- [Italian Data Protection Authority (Garante)](https://www.garanteprivacy.it/)
- [GDPR Compliance Guide](https://gdpr.eu/)
