# Portale Alloggi API Test Script

This directory contains test scripts to verify the Portale Alloggi API integration before implementing it in the main application.

## 📁 Files

- `test_portale_alloggi.py` - Basic test script with hardcoded credentials
- `test_portale_alloggi_enhanced.py` - Enhanced test script using configuration file
- `test_config.json` - Configuration file for credentials and test data
- `test_requirements.txt` - Python dependencies
- `TEST_PORTALE_ALLOGGI_README.md` - This documentation

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r test_requirements.txt
```

### 2. Configure Credentials

Edit `test_config.json` and replace the placeholder values:

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

## 🔧 Configuration

### Credentials

You need to obtain the following from Portale Alloggi:

- **Username**: Your login username
- **Password**: Your login password
- **WsKey**: Web service key (provided by Portale Alloggi)

### Test Data

The script uses sample guest data that you can modify in `test_config.json`:

```json
{
  "test_data": {
    "client": {
      "name": "Mario",
      "surname": "Rossi",
      "sesso": 1,
      "nazionalita": "IT",
      "birthday": "15/03/1985",
      "comune_nascita": "ROMA",
      "provincia_nascita": "RM",
      "stato_nascita": "IT",
      "cittadinanza": "IT",
      "document_number": "AB1234567",
      "luogo_emissione": "ROMA",
      "data_emissione": "01/01/2020",
      "data_scadenza": "01/01/2030",
      "autorita_rilascio": "COMUNE DI ROMA",
      "comune_residenza": "ROMA",
      "provincia_residenza": "RM",
      "stato_residenza": "IT"
    },
    "reservation": {
      "start_date": "15/01/2024",
      "end_date": "20/01/2024"
    }
  }
}
```

## 🧪 What the Test Does

### 1. Authentication Test

- Sends a `GenerateToken` SOAP request
- Verifies credentials with Portale Alloggi
- Extracts and stores the authentication token

### 2. Data Formatting Test

- Formats guest data into the required 168-character fixed-length string
- Validates all required fields are present
- Ensures proper date formatting (DD/MM/YYYY)

### 3. Guest Registration Test

- Sends a `Test` SOAP request with formatted guest data
- Verifies the data format is accepted by Portale Alloggi
- Returns validation results

## 📊 Expected Output

### Successful Test

```
🚀 Portale Alloggi API Test Script (Enhanced)
============================================================
👤 Test Guest: Mario Rossi
📅 Test Dates: 15/01/2024 to 20/01/2024

🔐 Testing authentication...
📡 Sending request to: https://alloggiatiweb.poliziadistato.it/service/service.asmx
Status Code: 200
✅ HTTP request successful
Response length: 1234 characters
✅ Authentication successful!
Token: abc123def456...

============================================================
🧪 Testing guest registration...
📝 Formatting schedina data...
✅ Schedina formatted: 168 characters
Preview: MARIO                ROSSI                1IT15/03/1985...
📡 Sending test request to: https://alloggiatiweb.poliziadistato.it/service/service.asmx
Status Code: 200
✅ HTTP request successful
Response length: 567 characters
✅ Test result: OK

============================================================
🎉 All tests completed successfully!
Your Portale Alloggi integration is working correctly.
```

### Failed Test

```
❌ Authentication failed. Please check your credentials in test_config.json
```

## 🔍 Troubleshooting

### Common Issues

1. **Invalid Credentials**

   - Verify username, password, and ws_key are correct
   - Check if your Portale Alloggi account is active

2. **Network Errors**

   - Ensure you have internet connectivity
   - Check if Portale Alloggi service is accessible
   - Verify firewall settings

3. **XML Parsing Errors**

   - Check if the response format has changed
   - Verify SOAP envelope structure

4. **Data Format Errors**
   - Ensure all required fields are present
   - Check date formats (must be DD/MM/YYYY)
   - Verify string lengths don't exceed limits

### Debug Mode

To see more detailed output, you can modify the script to print full responses:

```python
print("Full response:")
print(response.text)
```

## 📝 Notes

- This is a **TEST** script - it only validates data format, it doesn't actually submit guest registrations
- The `Test` operation is safe and doesn't create real records
- Use this script to verify your integration before implementing in production
- Keep your credentials secure and never commit them to version control

## 🔗 Related Documentation

- [Portale Alloggi Integration Guide](../PORTALE_ALLOGGI_INTEGRATION.md)
- [SOAP API Documentation](../SOAP_API_DOCUMENTATION.md)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your Portale Alloggi credentials
3. Contact Portale Alloggi support for API-related issues
4. Review the official Portale Alloggi documentation
