"""
Portale Alloggi Service for Italian accommodation registry integration.

This service handles communication with the Portale Alloggiati Web SOAP API
for submitting guest data to the Italian national accommodation registry.
"""

import logging
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PortaleAlloggiService:
    """
    Service for interacting with the Portale Alloggiati Web SOAP API.
    
    This service provides methods for authentication, data validation,
    and submission of guest data to the Italian accommodation registry.
    """
    
    def __init__(self, username: str, password: str, ws_key: str):
        """
        Initialize the Portale Alloggi service.
        
        Args:
            username (str): Username for Portale Alloggi authentication
            password (str): Password for Portale Alloggi authentication
            ws_key (str): Web Service Key for API access
        """
        self.username = username
        self.password = password
        self.ws_key = ws_key
        self.wsdl_url = "https://alloggiatiweb.poliziadistato.it/service/service.asmx"
        self.token = None
        self.token_expires = None
        
    def authenticate(self) -> Optional[str]:
        """
        Authenticate with the Portale Alloggi service and obtain a token.
        
        Returns:
            Optional[str]: Authentication token if successful, None otherwise
        """
        try:
            # SOAP envelope for GenerateToken
            soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <GenerateToken xmlns="AlloggiatiService">
            <WsKey>{self.ws_key}</WsKey>
            <Username>{self.username}</Username>
            <Password>{self.password}</Password>
        </GenerateToken>
    </soap:Body>
</soap:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'AlloggiatiService/GenerateToken'
            }
            
            response = requests.post(self.wsdl_url, data=soap_envelope, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse the SOAP response
            root = ET.fromstring(response.text)
            
            # Extract token from response
            token_element = root.find('.//{AlloggiatiService}GenerateTokenResult')
            if token_element is not None and token_element.text:
                self.token = token_element.text.strip()
                logger.info("Successfully authenticated with Portale Alloggi")
                return self.token
            else:
                logger.error("No token found in authentication response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during authentication: {str(e)}")
            return None
        except ET.ParseError as e:
            logger.error(f"XML parsing error during authentication: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return None
    
    def format_schedina(self, client_data: Dict[str, Any], reservation_data: Dict[str, Any]) -> str:
        """
        Format client data into a 168-character fixed-length schedina string.
        
        Args:
            client_data (Dict[str, Any]): Client information
            reservation_data (Dict[str, Any]): Reservation information
            
        Returns:
            str: 168-character formatted schedina string
        """
        try:
            # Format dates (DD/MM/YYYY)
            def format_date(date_obj):
                if isinstance(date_obj, str):
                    try:
                        date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
                    except ValueError:
                        return '00/00/0000'
                if hasattr(date_obj, 'strftime'):
                    return date_obj.strftime('%d/%m/%Y')
                return '00/00/0000'
            
            # Extract and format data with proper padding
            # This is a simplified version - the actual format should match
            # the official Portale Alloggi specifications
            
            name = (client_data.get('name', '') or '').ljust(20)[:20]
            surname = (client_data.get('surname', '') or '').ljust(20)[:20]
            birthday = format_date(client_data.get('birthday', ''))
            document_type = (client_data.get('document_type', '') or '').ljust(10)[:10]
            document_number = (client_data.get('document_number', '') or '').ljust(20)[:20]
            cf = (client_data.get('cf', '') or '').ljust(16)[:16]
            gender = str(client_data.get('sesso', '1'))[:1]  # 1=Male, 2=Female
            nationality = (client_data.get('nazionalita', 'IT') or 'IT').ljust(3)[:3]
            
            # Create the 168-character schedina
            # This is a placeholder format - should be updated with actual specifications
            schedina = f"{name}{surname}{birthday}{document_type}{document_number}{cf}{gender}{nationality}".ljust(168)
            
            return schedina[:168]  # Ensure exactly 168 characters
            
        except Exception as e:
            logger.error(f"Error formatting schedina: {str(e)}")
            return ' ' * 168  # Return empty schedina on error
    
    def test_schedine(self, schedine_lines: List[str]) -> Dict[str, Any]:
        """
        Test schedine data without actually submitting it.
        
        Args:
            schedine_lines (List[str]): List of 168-character schedina strings
            
        Returns:
            Dict[str, Any]: Test results
        """
        try:
            if not self.token:
                auth_result = self.authenticate()
                if not auth_result:
                    return {'success': False, 'error': 'Authentication failed'}
            
            # Create SOAP envelope for Test
            schedine_xml = '\n'.join([f'<string>{line}</string>' for line in schedine_lines])
            
            soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <Test xmlns="AlloggiatiService">
            <WsKey>{self.ws_key}</WsKey>
            <Token>{self.token}</Token>
            <ElencoSchedine>
                {schedine_xml}
            </ElencoSchedine>
        </Test>
    </soap:Body>
</soap:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'AlloggiatiService/Test'
            }
            
            response = requests.post(self.wsdl_url, data=soap_envelope, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse response
            root = ET.fromstring(response.text)
            
            # Extract test results
            esito_element = root.find('.//{AlloggiatiService}TestResult')
            if esito_element is not None:
                # Parse the result structure
                return self._parse_test_response(esito_element.text)
            
            return {'success': False, 'error': 'No test result found'}
            
        except Exception as e:
            logger.error(f"Error testing schedine: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def send_schedine(self, schedine_lines: List[str]) -> Dict[str, Any]:
        """
        Submit schedine data to the Portale Alloggi service.
        
        Args:
            schedine_lines (List[str]): List of 168-character schedina strings
            
        Returns:
            Dict[str, Any]: Submission results
        """
        try:
            if not self.token:
                auth_result = self.authenticate()
                if not auth_result:
                    return {'success': False, 'error': 'Authentication failed'}
            
            # Create SOAP envelope for Send
            schedine_xml = '\n'.join([f'<string>{line}</string>' for line in schedine_lines])
            
            soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <Send xmlns="AlloggiatiService">
            <WsKey>{self.ws_key}</WsKey>
            <Token>{self.token}</Token>
            <ElencoSchedine>
                {schedine_xml}
            </ElencoSchedine>
        </Send>
    </soap:Body>
</soap:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'AlloggiatiService/Send'
            }
            
            response = requests.post(self.wsdl_url, data=soap_envelope, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse response
            root = ET.fromstring(response.text)
            
            # Extract submission results
            esito_element = root.find('.//{AlloggiatiService}SendResult')
            if esito_element is not None:
                return self._parse_send_response(esito_element.text)
            
            return {'success': False, 'error': 'No submission result found'}
            
        except Exception as e:
            logger.error(f"Error sending schedine: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def submit_guest_registration(self, clients_data: List[Dict[str, Any]], reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit guest registration data for multiple clients.
        
        Args:
            clients_data (List[Dict[str, Any]]): List of client data dictionaries
            reservation_data (Dict[str, Any]): Reservation information
            
        Returns:
            Dict[str, Any]: Submission results
        """
        try:
            # Format all clients into schedine lines
            schedine_lines = []
            for client_data in clients_data:
                schedina = self.format_schedina(client_data, reservation_data)
                schedine_lines.append(schedina)
            
            if not schedine_lines:
                return {'success': False, 'error': 'No client data to submit'}
            
            # Test first
            test_result = self.test_schedine(schedine_lines)
            if not test_result.get('success', False):
                return test_result
            
            # If test passes, send the data
            return self.send_schedine(schedine_lines)
            
        except Exception as e:
            logger.error(f"Error submitting guest registration: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def test_guest_registration(self, clients_data: List[Dict[str, Any]], reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test guest registration data without submitting it.
        
        Args:
            clients_data (List[Dict[str, Any]]): List of client data dictionaries
            reservation_data (Dict[str, Any]): Reservation information
            
        Returns:
            Dict[str, Any]: Test results
        """
        try:
            # Format all clients into schedine lines
            schedine_lines = []
            for client_data in clients_data:
                schedina = self.format_schedina(client_data, reservation_data)
                schedine_lines.append(schedina)
            
            if not schedine_lines:
                return {'success': False, 'error': 'No client data to test'}
            
            # Test the data
            return self.test_schedine(schedine_lines)
            
        except Exception as e:
            logger.error(f"Error testing guest registration: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _parse_test_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the test response from the SOAP service.
        
        Args:
            response_text (str): Raw response text
            
        Returns:
            Dict[str, Any]: Parsed test results
        """
        try:
            # This is a simplified parser - should be updated based on actual response format
            if 'success' in response_text.lower() or 'ok' in response_text.lower():
                return {'success': True, 'message': 'Test passed'}
            else:
                return {'success': False, 'error': 'Test failed', 'details': response_text}
        except Exception as e:
            logger.error(f"Error parsing test response: {str(e)}")
            return {'success': False, 'error': f'Parse error: {str(e)}'}
    
    def _parse_send_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the send response from the SOAP service.
        
        Args:
            response_text (str): Raw response text
            
        Returns:
            Dict[str, Any]: Parsed submission results
        """
        try:
            # This is a simplified parser - should be updated based on actual response format
            if 'success' in response_text.lower() or 'ok' in response_text.lower():
                return {'success': True, 'message': 'Data submitted successfully'}
            else:
                return {'success': False, 'error': 'Submission failed', 'details': response_text}
        except Exception as e:
            logger.error(f"Error parsing send response: {str(e)}")
            return {'success': False, 'error': f'Parse error: {str(e)}'}
