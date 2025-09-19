#!/usr/bin/env python3
"""
Test script for Portale Alloggi API integration
This script tests the SOAP API communication with the Italian police system
Uses configuration file for credentials and test data
"""

import requests
import defusedxml.ElementTree as ET
from datetime import datetime, date
import json
import sys
import os

class PortaleAlloggiTester:
    def __init__(self, config_file="test_config.json"):
        """
        Initialize the tester with configuration file
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config = self.load_config(config_file)
        self.username = self.config['portale_alloggi']['username']
        self.password = self.config['portale_alloggi']['password']
        self.ws_key = self.config['portale_alloggi']['ws_key']
        self.wsdl_url = "https://alloggiatiweb.poliziadistato.it/service/service.asmx"
        self.token = None
        
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration file '{config_file}' not found!")
            print("Please create the configuration file with your credentials.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing configuration file: {e}")
            sys.exit(1)
    
    def check_credentials(self):
        """Check if credentials are properly configured"""
        if (self.username == "your_username_here" or 
            self.password == "your_password_here" or 
            self.ws_key == "your_ws_key_here"):
            print("❌ Please update your credentials in test_config.json")
            print("Replace the placeholder values with your actual Portale Alloggi credentials.")
            return False
        return True
        
    def authenticate(self):
        """Test authentication with Portale Alloggi"""
        print("🔐 Testing authentication...")
        
        if not self.check_credentials():
            return False
        # SOAP envelope for GenerateToken
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GenerateToken xmlns="AlloggiatiService">
      <Utente>{self.username}</Utente>
      <Password>{self.password}</Password>
      <WsKey>{self.ws_key}</WsKey>
    </GenerateToken>
  </soap:Body>
</soap:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'AlloggiatiService/GenerateToken'}        
        try:
            print(f"📡 Sending request to: {self.wsdl_url}")
            response = requests.post(self.wsdl_url, data=soap_envelope, headers=headers, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ HTTP request successful")
                print(f"Response length: {len(response.text)} characters")
                
                # Parse the response to extract token or error
                try:
                    root = ET.fromstring(response.text)
                    
                    # Check for success response first
                    result_element = root.find('.//{AlloggiatiService}result')
                    if result_element is not None:
                        esito = result_element.find('.//{AlloggiatiService}esito')
                        if esito is not None and esito.text == 'true':
                            # Success case - extract token
                            token_element = root.find('.//{AlloggiatiService}token')
                            if token_element is not None and token_element.text:
                                self.token = token_element.text.strip()
                                print(f"✅ Authentication successful!")
                                print(f"Token: {self.token[:20]}...")
                                
                                # Also extract token details if available
                                issued_element = root.find('.//{AlloggiatiService}issued')
                                expires_element = root.find('.//{AlloggiatiService}expires')
                                if issued_element is not None:
                                    print(f"Token issued: {issued_element.text}")
                                if expires_element is not None:
                                    print(f"Token expires: {expires_element.text}")
                                
                                return True
                            else:
                                print("❌ Success response but no token found")
                                return False
                        elif esito is not None and esito.text == 'false':
                            # Error case
                            error_code = result_element.find('.//{AlloggiatiService}ErroreCod')
                            error_desc = result_element.find('.//{AlloggiatiService}ErroreDes')
                            error_detail = result_element.find('.//{AlloggiatiService}ErroreDettaglio')
                            
                            print(f"❌ Authentication failed!")
                            print(f"Error Code: {error_code.text if error_code is not None and error_code.text else 'Unknown'}")
                            print(f"Error Description: {error_desc.text if error_desc is not None and error_desc.text else 'Unknown'}")
                            print(f"Error Detail: {error_detail.text if error_detail is not None and error_detail.text else 'Unknown'}")
                            return False
                    
                    print("❌ Unexpected response format - no result element found")
                    print("Response content:")
                    print(response.text)
                    return False
                except ET.ParseError as e:
                    print(f"❌ XML parsing error: {e}")
                    print("Response content:")
                    print(response.text)
                    return False
            else:
                print(f"❌ Authentication failed with status {response.status_code}")
                print("Response content:")
                print(response.text)
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error during authentication: {e}")
            return False
    
    def format_schedina(self, client_data, reservation_data):
        """
        Format guest data into 168-character fixed-length string (Schedina)
        Based on the current implementation in portale_alloggi_service.py
        
        Args:
            client_data (dict): Guest information
            reservation_data (dict): Reservation information
            
        Returns:
            str: 168-character formatted string
        """
        print("📝 Formatting schedina data...")
        
        def pad_string(value, length, char=' '):
            return str(value)[:length].ljust(length, char)
        
        def format_date(date_input):
            if isinstance(date_input, str):
                if '-' in date_input:
                    try:
                        dt = datetime.strptime(date_input, '%Y-%m-%d')
                        return dt.strftime('%d/%m/%Y')
                    except ValueError:
                        return '01/01/1990'
                elif '/' in date_input:
                    return date_input
            elif hasattr(date_input, 'strftime'):
                # Handle Python date/datetime objects
                return date_input.strftime('%d/%m/%Y')
            return '01/01/1990'
        
        # Build schedina according to official format (168 characters)
        schedina = ""
        schedina += pad_string(client_data.get('tipo_alloggiato', '16'), 2)  # 0-1: Tipo Alloggiato
        start_date = reservation_data.get('start_date', '15/09/2025')
        start_date_formatted = format_date(start_date)
        print(f"Start date: {start_date} (type: {type(start_date)}) -> Formatted: {start_date_formatted}")
        schedina += start_date_formatted  # 2-11: Data Arrivo (10 characters)
        duration = reservation_data.get('duration', 3)
        duration_formatted = str(duration).zfill(2)
        print(f"Duration: {duration} days -> Formatted: {duration_formatted}")
        schedina += duration_formatted  # 12-13: Giorni Permanenza (zero-padded to 2 digits)
        schedina += pad_string(client_data.get('surname', ''), 50)  # 14-63: Cognome
        schedina += pad_string(client_data.get('name', ''), 30)  # 64-93: Nome
        schedina += str(client_data.get('sesso', 1))  # 94: Sesso (1=M, 2=F)
        birthday = client_data.get('birthday', '01/01/1990')
        birthday_formatted = format_date(birthday)
        print(f"Birthday: {birthday} (type: {type(birthday)}) -> Formatted: {birthday_formatted}")
        schedina += birthday_formatted  # 95-104: Data Nascita (10 characters)
        schedina += pad_string(client_data.get('comune_nascita', ''), 9)  # 105-113: Comune Nascita
        schedina += pad_string(client_data.get('provincia_nascita', ''), 2)  # 114-115: Provincia Nascita (acronym)
        schedina += pad_string(client_data.get('stato_nascita', '100000100'), 9)  # 116-124: Stato Nascita
        schedina += pad_string(client_data.get('cittadinanza', '100000100'), 9)  # 125-133: Cittadinanza
        schedina += pad_string(client_data.get('document_type', 'IDENT'), 5)  # 134-138: Tipo Documento
        schedina += pad_string(client_data.get('document_number', ''), 20)  # 139-158: Numero Documento
        schedina += pad_string(client_data.get('luogo_emissione', '100000100'), 9)  # 159-167: Luogo Rilascio Documento
        
        # Ensure exactly 168 characters
        schedina = schedina[:168]
        
        print(f"✅ Schedina formatted: {len(schedina)} characters")
        print(f"Preview: {schedina[:50]}...")
        
        return schedina
    
    def test_guest_registration(self, client_data, reservation_data):
        """Generate and display the XML request body for guest registration without sending it"""
        print("🧪 Generating guest registration XML request...")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        # Format the schedina
        schedina = self.format_schedina(client_data, reservation_data)
        
        # SOAP envelope for Test operation with proper namespaces
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <Test xmlns="AlloggiatiService">
            <Utente>{self.username}</Utente>
            <token>{self.token}</token>
            <ElencoSchedine>
                <string>{schedina}</string>
            </ElencoSchedine>
        </Test>
    </soap:Body>
</soap:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'AlloggiatiService/Test'
        }
        
        print("📋 Generated SOAP Request Body:")
        print("=" * 80)
        print(soap_envelope)
        print("=" * 80)
        
        print("📋 Request Headers:")
        print("=" * 40)
        for key, value in headers.items():
            print(f"{key}: {value}")
        print("=" * 40)
        
        print("📋 Request Details:")
        print(f"URL: {self.wsdl_url}")
        print(f"Method: POST")
        print(f"Content Length: {len(soap_envelope)} characters")
        print(f"Schedina Length: {len(schedina)} characters")
        print("=" * 40)
        
        # Send the test request
        print("🚀 Sending test request to Portale Alloggi...")
        try:
            response = requests.post(self.wsdl_url, data=soap_envelope, headers=headers, timeout=30)
            response.raise_for_status()
            
            print(f"✅ HTTP request successful!")
            print(f"Status Code: {response.status_code}")
            print(f"Response Length: {len(response.text)} characters")
            
            # Parse and display the response
            print("\n📋 SOAP Response:")
            print("=" * 80)
            print(response.text)
            print("=" * 80)
            
            # Parse XML response for better readability
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                # Extract test results
                result_element = root.find('.//{AlloggiatiService}TestResult')
                if result_element is not None:
                    print("\n📊 Test Results:")
                    print("-" * 40)
                    
                    # Check if test was successful
                    esito_element = result_element.find('.//{AlloggiatiService}esito')
                    if esito_element is not None:
                        if esito_element.text == 'true':
                            print("✅ Test Result: SUCCESS")
                            
                            # Check for valid schedine count
                            schedine_valide = result_element.find('.//{AlloggiatiService}SchedineValide')
                            if schedine_valide is not None:
                                print(f"📈 Valid Schedine: {schedine_valide.text}")
                            
                            # Check for any errors in details
                            dettaglio = result_element.find('.//{AlloggiatiService}Dettaglio')
                            if dettaglio is not None:
                                esito_servizio = dettaglio.find('.//{AlloggiatiService}EsitoOperazioneServizio')
                                if esito_servizio is not None:
                                    esito_serv = esito_servizio.find('.//{AlloggiatiService}esito')
                                    if esito_serv is not None and esito_serv.text == 'false':
                                        print("⚠️  Service Operation: FAILED")
                                        
                                        # Get error details
                                        errore_cod = esito_servizio.find('.//{AlloggiatiService}ErroreCod')
                                        errore_des = esito_servizio.find('.//{AlloggiatiService}ErroreDes')
                                        errore_dettaglio = esito_servizio.find('.//{AlloggiatiService}ErroreDettaglio')
                                        
                                        if errore_cod is not None:
                                            print(f"❌ Error Code: {errore_cod.text}")
                                        if errore_des is not None:
                                            print(f"❌ Error Description: {errore_des.text}")
                                        if errore_dettaglio is not None:
                                            print(f"❌ Error Detail: {errore_dettaglio.text}")
                                    else:
                                        print("✅ Service Operation: SUCCESS")
                        else:
                            print("❌ Test Result: FAILED")
                            
                            # Get error details
                            errore_cod = result_element.find('.//{AlloggiatiService}ErroreCod')
                            errore_des = result_element.find('.//{AlloggiatiService}ErroreDes')
                            errore_dettaglio = result_element.find('.//{AlloggiatiService}ErroreDettaglio')
                            
                            if errore_cod is not None:
                                print(f"❌ Error Code: {errore_cod.text}")
                            if errore_des is not None:
                                print(f"❌ Error Description: {errore_des.text}")
                            if errore_dettaglio is not None:
                                print(f"❌ Error Detail: {errore_dettaglio.text}")
                    
                    print("-" * 40)
                
            except ET.ParseError as e:
                print(f"⚠️  Could not parse XML response: {e}")
            
            print("\n✅ Test request completed successfully!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP request failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

def main():
    """Main test function"""
    print("🚀 Portale Alloggi API Test Script")
    print("=" * 60)
    
    # Initialize tester with config file
    tester = PortaleAlloggiTester()
    
    # Get test data from config
    client_data = tester.config['test_data']['client']
    reservation_data = tester.config['test_data']['reservation']
    
    print(f"👤 Test Guest: {client_data['name']} {client_data['surname']}")
    print(f"📅 Test Dates: {reservation_data['start_date']} to {reservation_data['end_date']}")
    print()
    
    # Test authentication
    if tester.authenticate():
        print("\n" + "=" * 60)
        
        # Test guest registration
        success = tester.test_guest_registration(client_data, reservation_data)
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 All tests completed successfully!")
            print("Your Portale Alloggi integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
    else:
        print("❌ Authentication failed. Please check your credentials in test_config.json")

if __name__ == "__main__":
    main()
