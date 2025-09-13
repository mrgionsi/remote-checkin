#!/usr/bin/env python3
"""
Enhanced test script for Portale Alloggi API integration
This script tests the SOAP API communication with the Italian police system
Uses configuration file for credentials and test data
"""

import requests
import xml.etree.ElementTree as ET
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
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <GenerateToken xmlns="https://alloggiatiweb.poliziadistato.it/service/">
            <WsKey>{self.ws_key}</WsKey>
            <Username>{self.username}</Username>
            <Password>{self.password}</Password>
        </GenerateToken>
    </soap:Body>
</soap:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'https://alloggiatiweb.poliziadistato.it/service/GenerateToken'
        }
        
        try:
            print(f"📡 Sending request to: {self.wsdl_url}")
            response = requests.post(self.wsdl_url, data=soap_envelope, headers=headers, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ HTTP request successful")
                print(f"Response length: {len(response.text)} characters")
                
                # Parse the response to extract token
                try:
                    root = ET.fromstring(response.text)
                    token_element = root.find('.//{https://alloggiatiweb.poliziadistato.it/service/}GenerateTokenResult')
                    
                    if token_element is not None and token_element.text:
                        self.token = token_element.text.strip()
                        print(f"✅ Authentication successful!")
                        print(f"Token: {self.token[:20]}...")
                        return True
                    else:
                        print("❌ No token found in response")
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
        
        Args:
            client_data (dict): Guest information
            reservation_data (dict): Reservation information
            
        Returns:
            str: 168-character formatted string
        """
        print("📝 Formatting schedina data...")
        
        # Extract data with defaults
        name = (client_data.get('name', '') or '').ljust(20)[:20]
        surname = (client_data.get('surname', '') or '').ljust(20)[:20]
        gender = str(client_data.get('sesso', '1'))[:1]
        nationality = (client_data.get('nazionalita', 'IT') or 'IT').ljust(2)[:2]
        
        # Handle birth date
        birth_date = client_data.get('birthday', '01/01/1990')
        if isinstance(birth_date, date):
            birth_date = birth_date.strftime('%d/%m/%Y')
        elif isinstance(birth_date, str) and '-' in birth_date:
            try:
                dt = datetime.strptime(birth_date, '%Y-%m-%d')
                birth_date = dt.strftime('%d/%m/%Y')
            except:
                birth_date = '01/01/1990'
        
        birth_municipality = (client_data.get('comune_nascita', 'ROMA') or 'ROMA').ljust(20)[:20]
        birth_province = (client_data.get('provincia_nascita', 'RM') or 'RM').ljust(2)[:2]
        birth_country = (client_data.get('stato_nascita', 'IT') or 'IT').ljust(2)[:2]
        citizenship = (client_data.get('cittadinanza', 'IT') or 'IT').ljust(2)[:2]
        document_type = '01'  # Default to identity card
        document_number = (client_data.get('document_number', '') or '').ljust(20)[:20]
        document_issue_place = (client_data.get('luogo_emissione', 'ROMA') or 'ROMA').ljust(20)[:20]
        
        # Document dates
        issue_date = client_data.get('data_emissione', '01/01/2020')
        if isinstance(issue_date, date):
            issue_date = issue_date.strftime('%d/%m/%Y')
        elif isinstance(issue_date, str) and '-' in issue_date:
            try:
                dt = datetime.strptime(issue_date, '%Y-%m-%d')
                issue_date = dt.strftime('%d/%m/%Y')
            except:
                issue_date = '01/01/2020'
        
        expiry_date = client_data.get('data_scadenza', '01/01/2030')
        if isinstance(expiry_date, date):
            expiry_date = expiry_date.strftime('%d/%m/%Y')
        elif isinstance(expiry_date, str) and '-' in expiry_date:
            try:
                dt = datetime.strptime(expiry_date, '%Y-%m-%d')
                expiry_date = dt.strftime('%d/%m/%Y')
            except:
                expiry_date = '01/01/2030'
        
        issuing_authority = (client_data.get('autorita_rilascio', 'COMUNE DI ROMA') or 'COMUNE DI ROMA').ljust(20)[:20]
        residence_municipality = (client_data.get('comune_residenza', 'ROMA') or 'ROMA').ljust(20)[:20]
        residence_province = (client_data.get('provincia_residenza', 'RM') or 'RM').ljust(2)[:2]
        residence_country = (client_data.get('stato_residenza', 'IT') or 'IT').ljust(2)[:2]
        
        # Reservation data
        arrival_date = reservation_data.get('start_date', '01/01/2024')
        if isinstance(arrival_date, date):
            arrival_date = arrival_date.strftime('%d/%m/%Y')
        elif isinstance(arrival_date, str) and '-' in arrival_date:
            try:
                dt = datetime.strptime(arrival_date, '%Y-%m-%d')
                arrival_date = dt.strftime('%d/%m/%Y')
            except:
                arrival_date = '01/01/2024'
        
        departure_date = reservation_data.get('end_date', '02/01/2024')
        if isinstance(departure_date, date):
            departure_date = departure_date.strftime('%d/%m/%Y')
        elif isinstance(departure_date, str) and '-' in departure_date:
            try:
                dt = datetime.strptime(departure_date, '%Y-%m-%d')
                departure_date = dt.strftime('%d/%m/%Y')
            except:
                departure_date = '02/01/2024'
        
        # Construct the 168-character schedina
        schedina = (
            name +                    # 20 chars - Name
            surname +                 # 20 chars - Surname  
            gender +                  # 1 char - Gender (1=Male, 2=Female)
            nationality +             # 2 chars - Nationality
            birth_date +              # 10 chars - Birth date (DD/MM/YYYY)
            birth_municipality +      # 20 chars - Birth municipality
            birth_province +          # 2 chars - Birth province
            birth_country +           # 2 chars - Birth country
            citizenship +             # 2 chars - Citizenship
            document_type +           # 2 chars - Document type
            document_number +         # 20 chars - Document number
            document_issue_place +    # 20 chars - Document issue place
            issue_date +              # 10 chars - Document issue date
            expiry_date +             # 10 chars - Document expiry date
            issuing_authority +       # 20 chars - Issuing authority
            residence_municipality +  # 20 chars - Residence municipality
            residence_province +      # 2 chars - Residence province
            residence_country +       # 2 chars - Residence country
            arrival_date +            # 10 chars - Arrival date
            departure_date            # 10 chars - Departure date
        )
        
        # Ensure exactly 168 characters
        schedina = schedina.ljust(168)[:168]
        
        print(f"✅ Schedina formatted: {len(schedina)} characters")
        print(f"Preview: {schedina[:50]}...")
        
        return schedina
    
    def test_guest_registration(self, client_data, reservation_data):
        """Test guest registration with Portale Alloggi"""
        print("🧪 Testing guest registration...")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        # Format the schedina
        schedina = self.format_schedina(client_data, reservation_data)
        
        # SOAP envelope for Test operation
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <Test xmlns="https://alloggiatiweb.poliziadistato.it/service/">
            <WsKey>{self.ws_key}</WsKey>
            <Token>{self.token}</Token>
            <ElencoSchedine>
                <string>{schedina}</string>
            </ElencoSchedine>
        </Test>
    </soap:Body>
</soap:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'https://alloggiatiweb.poliziadistato.it/service/Test'
        }
        
        try:
            print(f"📡 Sending test request to: {self.wsdl_url}")
            response = requests.post(self.wsdl_url, data=soap_envelope, headers=headers, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ HTTP request successful")
                print(f"Response length: {len(response.text)} characters")
                
                # Parse response
                try:
                    root = ET.fromstring(response.text)
                    result_element = root.find('.//{https://alloggiatiweb.poliziadistato.it/service/}TestResult')
                    
                    if result_element is not None:
                        result = result_element.text
                        print(f"✅ Test result: {result}")
                        return True
                    else:
                        print("❌ No test result found in response")
                        print("Response content:")
                        print(response.text)
                        return False
                except ET.ParseError as e:
                    print(f"❌ XML parsing error: {e}")
                    print("Response content:")
                    print(response.text)
                    return False
            else:
                print(f"❌ Test failed with status {response.status_code}")
                print("Response content:")
                print(response.text)
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error during test: {e}")
            return False

def main():
    """Main test function"""
    print("🚀 Portale Alloggi API Test Script (Enhanced)")
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
