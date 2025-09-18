# 🧪 Portale Alloggi API Testing Guide

This guide provides comprehensive testing procedures for the Portale Alloggi API integration. Use these tests to verify your integration before deploying to production.

## 📁 Test Files

- `test_portale_alloggi_enhanced.py` - Enhanced test script with configuration file support
- `test_config.json` - Configuration file for credentials and test data
- `test_requirements.txt` - Python dependencies for testing
- `TEST_PORTALE_ALLOGGI_README.md` - This testing guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd test_portale_alloggi
pip install -r test_requirements.txt
```

### 2. Configure Credentials

Edit `test_config.json` and replace the placeholder values with your actual Portale Alloggi credentials:

```json
{
  "portale_alloggi": {
    "username": "your_actual_username",
    "password": "your_actual_password",
    "ws_key": "your_actual_ws_key",
    "test_mode": true
  }
}
```

### 3. Run the Test

```bash
python test_portale_alloggi_enhanced.py
```

## 🔧 Test Configuration

### Credentials Setup

You need to obtain the following from Portale Alloggi:

- **Username**: Your login username
- **Password**: Your login password
- **WsKey**: Web service key (provided by Portale Alloggi)

### Test Data Configuration

The test script uses configurable guest data. Modify the test data in `test_config.json`:

```json
{
  "test_data": {
    "client": {
      "name": "MARIO",
      "surname": "ROSSI",
      "tipo_alloggiato": "16",
      "sesso": 1,
      "birthday": "01/01/1990",
      "comune_nascita": "415063001",
      "provincia_nascita": "NA",
      "stato_nascita": "100000100",
      "cittadinanza": "100000100",
      "document_type": "IDENT",
      "document_number": "YA1234567",
      "luogo_rilascio": "100000100"
    },
    "reservation": {
      "start_date": "16/09/2025",
      "end_date": "21/09/2025"
    }
  }
}
```

## 🧪 Test Procedures

### Test 1: Authentication Verification

**Purpose**: Verify that your credentials work with the Portale Alloggi service.

**What it tests**:

- SOAP service connectivity
- Credential validation
- Token generation
- Token expiration handling

**Expected Success Output**:

```
🔐 Testing authentication...
📡 Sending request to: https://alloggiatiweb.poliziadistato.it/service/service.asmx
Status Code: 200
✅ HTTP request successful
✅ Authentication successful!
Token: abc123def456...
```

**Common Failures**:

- Invalid credentials → Check username/password/ws_key
- Network errors → Check internet connectivity
- Service unavailable → Check if Portale Alloggi is down

### Test 2: Data Formatting Validation

**Purpose**: Verify that guest data is correctly formatted into the required 168-character schedina format.

**What it tests**:

- Field positioning and padding
- Date format conversion (DD/MM/YYYY)
- String length validation
- Required field presence

**Expected Success Output**:

```
📝 Formatting schedina data...
✅ Schedina formatted: 168 characters
Preview: 16MARIO                ROSSI                1IT01/01/1990...
```

**Common Failures**:

- Wrong field lengths → Check padding functions
- Invalid date formats → Ensure DD/MM/YYYY format
- Missing required fields → Verify all mandatory data is present

### Test 3: SOAP Request Structure Validation

**Purpose**: Verify that the SOAP request is properly structured according to the API specification.

**What it tests**:

- SOAP envelope structure
- Namespace declarations
- Element hierarchy
- Content-Type headers

**Expected Success Output**:

```
📋 Generated SOAP Request Body:
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Test xmlns="AlloggiatiService">
      <Utente>username</Utente>
      <token>auth_token</token>
      <ElencoSchedine>
        <string>168-character-schedina</string>
      </ElencoSchedine>
    </Test>
  </soap:Body>
</soap:Envelope>
```

### Test 4: Guest Registration Validation

**Purpose**: Test the actual guest data submission to Portale Alloggi (Test operation only - no real data is submitted).

**What it tests**:

- Data acceptance by Portale Alloggi
- Field validation rules
- Error handling
- Response parsing

**Expected Success Output**:

```
🚀 Sending test request to Portale Alloggi...
✅ HTTP request successful!
Status Code: 200

📊 Test Results:
✅ Test Result: SUCCESS
📈 Valid Schedine: 1
✅ Service Operation: SUCCESS
```

**Common Failures**:

- Invalid guest type codes → Use valid codes (16-20)
- Invalid document types → Use valid codes (IDENT, PASOR, etc.)
- Invalid country codes → Use valid 9-digit codes
- Invalid municipality codes → Use valid ISTAT codes

## 📊 Test Scenarios

### Scenario 1: Single Guest (OSPITE SINGOLO)

```json
{
  "tipo_alloggiato": "16",
  "sesso": 1,
  "document_type": "IDENT",
  "stato_nascita": "100000100",
  "cittadinanza": "100000100"
}
```

**Use case**: Individual travelers, business guests

### Scenario 2: Family Head (CAPO FAMIGLIA)

```json
{
  "tipo_alloggiato": "17",
  "sesso": 1,
  "document_type": "IDENT",
  "stato_nascita": "100000100",
  "cittadinanza": "100000100"
}
```

**Use case**: Family bookings, group reservations

### Scenario 3: Group Leader (CAPO GRUPPO)

```json
{
  "tipo_alloggiato": "18",
  "sesso": 1,
  "document_type": "PASOR",
  "stato_nascita": "100000201",
  "cittadinanza": "100000201"
}
```

**Use case**: Tour groups, organized trips

### Scenario 4: Family Member (FAMILIARE)

```json
{
  "tipo_alloggiato": "19",
  "sesso": 2,
  "document_type": "IDENT",
  "stato_nascita": "100000100",
  "cittadinanza": "100000100"
}
```

**Use case**: Spouses, children in family bookings

### Scenario 5: Group Member (MEMBRO GRUPPO)

```json
{
  "tipo_alloggiato": "20",
  "sesso": 1,
  "document_type": "PASOR",
  "stato_nascita": "100000203",
  "cittadinanza": "100000203"
}
```

**Use case**: Tour group members, organized trip participants

## 🔍 Troubleshooting

### Authentication Issues

**Problem**: Authentication failed

```
❌ Authentication failed!
Error Code: INVALID_CREDENTIALS
Error Description: Username or password incorrect
```

**Solutions**:

1. Verify username and password in `test_config.json`
2. Check if your Portale Alloggi account is active
3. Contact Portale Alloggi support for credential issues
4. Ensure you're using the correct environment (test vs production)

### Network Issues

**Problem**: Connection timeout or network errors

```
❌ Network error during authentication: HTTPSConnectionPool...
```

**Solutions**:

1. Check internet connectivity
2. Verify firewall settings allow HTTPS to Portale Alloggi
3. Test with a different network
4. Check if Portale Alloggi service is accessible from your location

### Data Format Issues

**Problem**: Invalid schedina format

```
❌ Test Result: FAILED
Error Code: INVALID_FORMAT
Error Description: Schedina format not valid
```

**Solutions**:

1. Verify schedina is exactly 168 characters
2. Check date formats are DD/MM/YYYY
3. Ensure all required fields are present
4. Validate field lengths and padding

### SOAP Structure Issues

**Problem**: XML parsing errors or invalid SOAP structure

```
❌ XML parsing error: not well-formed (invalid token)
```

**Solutions**:

1. Check SOAP envelope structure
2. Verify namespace declarations
3. Ensure proper XML escaping
4. Validate element hierarchy

## 📋 Valid Codes Reference

### Guest Type Codes (Tipo Alloggiato)

| Code | Description    | Use Case          |
| ---- | -------------- | ----------------- |
| 16   | OSPITE SINGOLO | Individual guests |
| 17   | CAPO FAMIGLIA  | Family bookings   |
| 18   | CAPO GRUPPO    | Group leaders     |
| 19   | FAMILIARE      | Family members    |
| 20   | MEMBRO GRUPPO  | Group members     |

### Document Type Codes (Tipo Documento)

| Code  | Description            | Notes               |
| ----- | ---------------------- | ------------------- |
| IDENT | Carta di Identità      | Italian ID card     |
| PASOR | Passaporto Ordinario   | Ordinary passport   |
| PASDI | Passaporto Diplomatico | Diplomatic passport |
| PATEN | Patente di Guida       | Driver's license    |
| CIDIP | Carta ID. Diplomatica  | Diplomatic ID card  |

### Country Codes (Stati)

| Code      | Description    |
| --------- | -------------- |
| 100000100 | ITALIA         |
| 100000201 | ALBANIA        |
| 100000203 | AUSTRIA        |
| 100000206 | BELGIO         |
| 100000302 | ARABIA SAUDITA |
| 100000602 | ARGENTINA      |
| 100000701 | AUSTRALIA      |

### Municipality Codes (Comuni)

| Code      | Description | Province |
| --------- | ----------- | -------- |
| 415063001 | NAPOLI      | NA       |
| 58091001  | ROMA        | RM       |
| 15046001  | MILANO      | MI       |

### Province Codes (Province)

| Code | Description |
| ---- | ----------- |
| NA   | NAPOLI      |
| RM   | ROMA        |
| MI   | MILANO      |
| TO   | TORINO      |
| FI   | FIRENZE     |

## 📊 Schedina Format Validation

The schedina must be exactly **168 characters** with the following structure:

| Position | Length | Field             | Description                          | Validation          |
| -------- | ------ | ----------------- | ------------------------------------ | ------------------- |
| 0-1      | 2      | Tipo Alloggiato   | Guest type (16-20)                   | Required            |
| 2-11     | 10     | Data Arrivo       | Arrival date (DD/MM/YYYY)            | Required            |
| 12-13    | 2      | Giorni Permanenza | Stay duration (01-30)                | Required            |
| 14-63    | 50     | Cognome           | Surname (UPPERCASE, space-padded)    | Required            |
| 64-93    | 30     | Nome              | First name (UPPERCASE, space-padded) | Required            |
| 94       | 1      | Sesso             | Gender (1=M, 2=F)                    | Required            |
| 95-104   | 10     | Data Nascita      | Birth date (DD/MM/YYYY)              | Required            |
| 105-113  | 9      | Comune Nascita    | Birth municipality (ISTAT code)      | Required if Italian |
| 114-115  | 2      | Provincia Nascita | Birth province (2-letter code)       | Required if Italian |
| 116-124  | 9      | Stato Nascita     | Birth country (9-digit code)         | Required            |
| 125-133  | 9      | Cittadinanza      | Citizenship (9-digit code)           | Required            |
| 134-138  | 5      | Tipo Documento    | Document type (IDENT, PASOR, etc.)   | Required            |
| 139-158  | 20     | Numero Documento  | Document number (space-padded)       | Required            |
| 159-167  | 9      | Luogo Rilascio    | Document issue place (code)          | Required            |

## 🎯 Testing Best Practices

### 1. Test Environment Setup

- Always use test credentials first
- Verify `test_mode: true` in configuration
- Test with sample data before real data
- Keep production credentials secure

### 2. Data Validation

- Test with various guest types (16-20)
- Test with different document types
- Test with international guests
- Test with incomplete data to verify error handling

### 3. Error Handling

- Test network connectivity issues
- Test invalid credentials
- Test malformed data
- Test service unavailability

### 4. Performance Testing

- Test with multiple guests in one request
- Test response times
- Test concurrent requests (if applicable)
- Monitor memory usage

## 📝 Test Output Interpretation

### Successful Test Output

```
🚀 Portale Alloggi API Test Script (Enhanced)
============================================================
👤 Test Guest: MARIO ROSSI
📅 Test Dates: 16/09/2025 to 21/09/2025

🔐 Testing authentication...
✅ Authentication successful!
Token: abc123def456...

============================================================
🧪 Testing guest registration...
✅ Schedina formatted: 168 characters
✅ HTTP request successful!
✅ Test Result: SUCCESS
📈 Valid Schedine: 1
✅ Service Operation: SUCCESS

============================================================
🎉 All tests completed successfully!
Your Portale Alloggi integration is working correctly.
```

### Failed Test Output

```
❌ Authentication failed!
Error Code: INVALID_CREDENTIALS
Error Description: Username or password incorrect
Error Detail: Please verify your credentials

❌ Test Result: FAILED
Error Code: INVALID_FORMAT
Error Description: Schedina format not valid
Error Detail: Check field lengths and required data
```

## 🔗 Related Documentation

- [Portale Alloggi API Documentation](../ALLOGGIAT_WEB_SOAP_API_DOCUMENTATION.md) - Complete API reference
- [Integration Guide](../README.md) - Main integration documentation

## 🆘 Support

If you encounter issues during testing:

1. **Check this troubleshooting guide first**
2. **Verify your credentials and configuration**
3. **Contact Portale Alloggi support for API issues**
4. **Review the main API documentation for implementation details**

## ⚠️ Important Notes

- **This is a TEST script** - it only validates data format, it doesn't submit real guest registrations
- The `Test` operation is safe and doesn't create real records in Portale Alloggi
- Always test thoroughly before implementing in production
- Keep your credentials secure and never commit them to version control
- Monitor Portale Alloggi service status and API changes
