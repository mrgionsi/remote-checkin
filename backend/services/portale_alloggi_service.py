#pylint: disable=W0718,R0902,R0914,C0301,C0303
"""
Portale Alloggi Service for Italian accommodation registry integration.

This service handles communication with the Portale Alloggiati Web SOAP API
for submitting guest data to the Italian national accommodation registry.
"""

import os
import json
import xml.etree.ElementTree as ET
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests

logger = logging.getLogger(__name__)

# Guest type constants based on guest_types.json
GUEST_TYPE_SINGLE = "16"  # OSPITE SINGOLO
GUEST_TYPE_FAMILY_HEAD = "17"  # CAPO FAMIGLIA
GUEST_TYPE_GROUP_LEADER = "18"  # CAPO GRUPPO
GUEST_TYPE_FAMILY_MEMBER = "19"  # FAMILIARE
GUEST_TYPE_GROUP_MEMBER = "20"  # MEMBRO GRUPPO

# Default document type
DEFAULT_DOCUMENT_TYPE = "IDENT"  # CARTA DI IDENTITA'

# Default location codes
DEFAULT_COUNTRY_CODE = "100000100"  # ITALIA
DEFAULT_MUNICIPALITY_CODE = "100000100"  # Default municipality

# SOAP constants
SOAP_CONTENT_TYPE = "text/xml; charset=utf-8"
ESITO_XPATH = ".//{AlloggiatiService}esito"
ERROR_CODE_XPATH = ".//{AlloggiatiService}ErroreCod"
ERROR_DESC_XPATH = ".//{AlloggiatiService}ErroreDes"
ERROR_DETAIL_XPATH = ".//{AlloggiatiService}ErroreDettaglio"

# Date constants
DEFAULT_DATE = "01/01/1990"
DATE_FORMAT_ISO = "%Y-%m-%d"
DATE_FORMAT_ITALIAN = "%d/%m/%Y"


class PortaleAlloggiService:
    """
    Service for interacting with the Portale Alloggiati Web SOAP API.

    This service provides methods for authentication, data validation,
    and submission of guest data to the Italian accommodation registry.
    """

    def __init__(self, username: str, password: str, ws_key: str, json_data_path: Optional[str] = None):
        """
        Initialize the Portale Alloggi service.

        Args:
            username (str): Username for Portale Alloggi authentication
            password (str): Password for Portale Alloggi authentication
            ws_key (str): Web Service Key for API access
            json_data_path (Optional[str]): Path to directory containing JSON reference files
        """
        self.username = username
        self.password = password
        self.ws_key = ws_key
        self.wsdl_url = "https://alloggiatiweb.poliziadistato.it/service/service.asmx"
        self.token = None
        self.token_expires = None

        # Load reference data from JSON files
        self.json_data_path = json_data_path or os.path.join(os.path.dirname(__file__), 'mappings')
        self.document_types = {}
        self.municipalities = {}
        self.countries = {}
        self._load_reference_data()

    def _load_reference_data(self):
        """Load reference data from JSON files."""
        try:
            # Load document types
            self._load_json_data('document_types.json', self.document_types)

            # Load municipalities
            self._load_json_data('municipalities.json', self.municipalities)

            # Load countries
            self._load_json_data('countries.json', self.countries)

            logger.info("Loaded reference data: %d document types, %d municipalities, %d countries",
                       len(self.document_types), len(self.municipalities), len(self.countries))
        except Exception as e:
            logger.warning("Could not load reference data from JSON files: %s", e)
            # Initialize with default data
            self._initialize_default_data()

    def _load_json_data(self, filename: str, target_dict: Dict):
        """Load data from a JSON file into a dictionary."""
        filepath = os.path.join(self.json_data_path, filename)
        if not os.path.exists(filepath):
            logger.warning("JSON file not found: %s", filepath)
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, dict):
                    target_dict.update(data)
                else:
                    logger.error("Invalid JSON format in %s: expected dict, got %s", filename, type(data))
        except json.JSONDecodeError as e:
            logger.error("JSON decode error in %s: %s", filename, e)
        except Exception as e:
            logger.error("Error loading JSON file %s: %s", filename, e)

    def _initialize_default_data(self):
        """Initialize with default reference data if JSON files are not available."""
        self.document_types = {
            DEFAULT_DOCUMENT_TYPE: "CARTA DI IDENTITA'",
            "PASOR": "PASSAPORTO ORDINARIO",
            "PASDI": "PASSAPORTO DIPLOMATICO",
            "PASSE": "PASSAPORTO DI SERVIZIO",
            "PATEN": "PATENTE DI GUIDA",
            "IDELE": "CARTA IDENTITA' ELETTRONICA"
        }

        self.countries = {
            DEFAULT_COUNTRY_CODE: "ITALIA"
        }

    def _calculate_duration(self, reservation_data: Dict[str, Any]) -> int:
        """
        Calculate duration in days from start_date and end_date.
        
        Args:
            reservation_data (Dict[str, Any]): Reservation data containing dates
            
        Returns:
            int: Duration in days
        """
        try:
            start_date = reservation_data.get('start_date')
            end_date = reservation_data.get('end_date')
            
            # If both dates are provided, calculate the difference
            if start_date and end_date:
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)
                
                if start_dt and end_dt:
                    duration = (end_dt - start_dt).days
                    return max(1, duration)  # Ensure at least 1 day
            
            # Fallback to provided duration or default
            return reservation_data.get('duration', 1)
            
        except (ValueError, TypeError) as e:
            logger.warning("Error calculating duration from dates: %s. Using fallback duration.", str(e))
            return reservation_data.get('duration', 1)

    def _parse_date(self, date_input) -> Optional[datetime]:
        """
        Parse date input into datetime object.
        
        Args:
            date_input: Date input (string or datetime object)
            
        Returns:
            Optional[datetime]: Parsed datetime object or None if parsing fails
        """
        if not date_input:
            return None
            
        if isinstance(date_input, str):
            if '-' in date_input:
                return datetime.strptime(date_input, DATE_FORMAT_ISO)
            elif '/' in date_input:
                return datetime.strptime(date_input, DATE_FORMAT_ITALIAN)
            return None
        elif hasattr(date_input, 'date'):
            # Handle date objects
            return datetime.combine(date_input, datetime.min.time())
        elif isinstance(date_input, datetime):
            return date_input
            
        return None

    def determine_guest_type(self, clients_data: List[Dict[str, Any]], client_index: int = 0) -> str:
        """
        Determine the appropriate guest type code based on the reservation context.

        Args:
            clients_data (List[Dict[str, Any]]): List of all clients in the reservation
            client_index (int): Index of the current client in the list

        Returns:
            str: Guest type code
        """
        total_clients = len(clients_data)

        if total_clients == 1:
            # Single guest
            return GUEST_TYPE_SINGLE

        if total_clients > 1:
            # Multiple guests - determine if family or group
            if self._is_family_reservation(clients_data):
                if client_index == 0:
                    return GUEST_TYPE_FAMILY_HEAD
                return GUEST_TYPE_FAMILY_MEMBER

            if client_index == 0:
                return GUEST_TYPE_GROUP_LEADER
            return GUEST_TYPE_GROUP_MEMBER

        # Default fallback
        return GUEST_TYPE_SINGLE

    def _is_family_reservation(self, clients_data: List[Dict[str, Any]]) -> bool:
        """
        Determine if the reservation is for a family based on client data.

        Args:
            clients_data (List[Dict[str, Any]]): List of client data

        Returns:
            bool: True if this appears to be a family reservation
        """
        if len(clients_data) < 2:
            return False

        # Check if clients share the same surname (common family indicator)
        surnames = [client.get('surname', '').upper().strip() for client in clients_data]
        unique_surnames = set(surnames)

        # If more than 50% share the same surname, consider it a family
        if len(unique_surnames) <= len(clients_data) // 2:
            return True

        # Additional family indicators could be added here:
        # - Age relationships (parent/child)
        # - Explicit family relationship fields
        # - Booking context indicators

        return False

    def get_document_type_code(self, document_type: str) -> str:
        """
        Get the document type code for a given document type.

        Args:
            document_type (str): Document type name or code

        Returns:
            str: Document type code
        """
        # If it's already a code, return it
        if document_type in self.document_types:
            return document_type

        # Search for matching description
        for code, description in self.document_types.items():
            if description.upper() == document_type.upper():
                return code

        # Default fallback
        return DEFAULT_DOCUMENT_TYPE

    def get_location_code(self, location_name: str, location_type: str = 'municipality') -> str:
        """
        Get the location code for a given location name.

        Args:
            location_name (str): Location name
            location_type (str): Type of location ('municipality' or 'country')

        Returns:
            str: Location code
        """
        if location_type == 'municipality':
            target_dict = self.municipalities
            default_code = DEFAULT_MUNICIPALITY_CODE
        else:
            target_dict = self.countries
            default_code = DEFAULT_COUNTRY_CODE

        # If it's already a code, return it
        if location_name in target_dict:
            return location_name

        # Search for matching description
        for code, description in target_dict.items():
            if description.upper() == location_name.upper():
                return code

        # Default fallback
        return default_code

    def create_json_mappings(self, output_dir: str = None) -> Dict[str, str]:
        """
        Create JSON mapping files for frontend use.

        Args:
            output_dir (str): Directory to save JSON files

        Returns:
            Dict[str, str]: Dictionary mapping file types to file paths
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), 'mappings')

        os.makedirs(output_dir, exist_ok=True)

        mappings = {}

        # Create guest types mapping (using constants)
        guest_types_data = {
            GUEST_TYPE_SINGLE: "OSPITE SINGOLO",
            GUEST_TYPE_FAMILY_HEAD: "CAPO FAMIGLIA",
            GUEST_TYPE_GROUP_LEADER: "CAPO GRUPPO",
            GUEST_TYPE_FAMILY_MEMBER: "FAMILIARE",
            GUEST_TYPE_GROUP_MEMBER: "MEMBRO GRUPPO"
        }
        guest_types_file = os.path.join(output_dir, 'guest_types.json')
        with open(guest_types_file, 'w', encoding='utf-8') as f:
            json.dump(guest_types_data, f, ensure_ascii=False, indent=2)
        mappings['guest_types'] = guest_types_file

        # Create document types mapping
        document_types_file = os.path.join(output_dir, 'document_types.json')
        with open(document_types_file, 'w', encoding='utf-8') as f:
            json.dump(self.document_types, f, ensure_ascii=False, indent=2)
        mappings['document_types'] = document_types_file

        # Create municipalities mapping
        municipalities_file = os.path.join(output_dir, 'municipalities.json')
        with open(municipalities_file, 'w', encoding='utf-8') as f:
            json.dump(self.municipalities, f, ensure_ascii=False, indent=2)
        mappings['municipalities'] = municipalities_file

        # Create countries mapping
        countries_file = os.path.join(output_dir, 'countries.json')
        with open(countries_file, 'w', encoding='utf-8') as f:
            json.dump(self.countries, f, ensure_ascii=False, indent=2)
        mappings['countries'] = countries_file

        logger.info("Created JSON mapping files in %s", output_dir)
        return mappings

    def authenticate(self) -> Optional[str]:
        """
        Authenticate with the Portale Alloggi service and obtain a token.

        Returns:
            Optional[str]: Authentication token if successful, None otherwise
        """
        try:
            soap_envelope = self._create_auth_soap_envelope()
            headers = self._create_auth_headers()

            response = requests.post(self.wsdl_url, data=soap_envelope, headers=headers, timeout=30)
            response.raise_for_status()

            return self._parse_auth_response(response.text)

        except requests.exceptions.RequestException as e:
            logger.error("Network error during authentication: %s", str(e))
            return None
        except ET.ParseError as e:
            logger.error("XML parsing error during authentication: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during authentication: %s", str(e))
            return None

    def _create_auth_soap_envelope(self) -> str:
        """Create SOAP envelope for authentication."""
        return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GenerateToken xmlns="AlloggiatiService">
      <Utente>{self.username}</Utente>
      <Password>{self.password}</Password>
      <WsKey>{self.ws_key}</WsKey>
    </GenerateToken>
  </soap:Body>
</soap:Envelope>"""

    def _create_auth_headers(self) -> Dict[str, str]:
        """Create headers for authentication request."""
        return {
            'Content-Type': SOAP_CONTENT_TYPE,
            'SOAPAction': 'AlloggiatiService/GenerateToken'
        }

    def _parse_auth_response(self, response_text: str) -> Optional[str]:
        """Parse authentication response and extract token."""
        root = ET.fromstring(response_text)
        result_element = root.find('.//{AlloggiatiService}result')

        if result_element is None:
            logger.error("No result element found in authentication response")
            return None

        # Check if authentication was successful
        esito = result_element.find(ESITO_XPATH)
        if esito is not None and esito.text == 'true':
            # Look for token at root level (as per test script)
            token_element = root.find('.//{AlloggiatiService}token')
            if token_element is not None and token_element.text:
                self.token = token_element.text.strip()
                logger.info("Successfully authenticated with Portale Alloggi")
                return self.token
            
            logger.error("Success response but no token found")
            return None
        
        # Handle authentication failure
        self._log_auth_error(result_element)
        return None


    def _log_auth_error(self, result_element):
        """Log authentication error details."""
        error_code = result_element.find(ERROR_CODE_XPATH)
        error_desc = result_element.find(ERROR_DESC_XPATH)
        error_detail = result_element.find(ERROR_DETAIL_XPATH)

        logger.error("Authentication failed - Code: %s, Description: %s, Detail: %s",
                   error_code.text if error_code is not None and error_code.text else 'Unknown',
                   error_desc.text if error_desc is not None and error_desc.text else 'Unknown',
                   error_detail.text if error_detail is not None and error_detail.text else 'Unknown')

    def format_schedina(self, client_data: Dict[str, Any], reservation_data: Dict[str, Any],
                       clients_data: List[Dict[str, Any]] = None, client_index: int = 0) -> str:
        """
        Format client data into a 168-character fixed-length schedina string.
        Based on the working format that was accepted before.

        Args:
            client_data (Dict[str, Any]): Client information
            reservation_data (Dict[str, Any]): Reservation information
            clients_data (List[Dict[str, Any]], optional): All clients in reservation for guest type determination
            client_index (int, optional): Index of current client in the list

        Returns:
            str: 168-character formatted schedina string
        """
        try:
            def pad_string(value, length, char=' '):
                return str(value)[:length].ljust(length, char)

            def format_date(date_input):
                if isinstance(date_input, str):
                    if '-' in date_input:
                        try:
                            dt = datetime.strptime(date_input, DATE_FORMAT_ISO)
                            return dt.strftime(DATE_FORMAT_ITALIAN)
                        except ValueError:
                            return DEFAULT_DATE
                    elif '/' in date_input:
                        return date_input
                elif hasattr(date_input, 'strftime'):
                    # Handle Python date/datetime objects
                    return date_input.strftime(DATE_FORMAT_ITALIAN)
                return DEFAULT_DATE

            # Determine guest type automatically if not provided
            if clients_data is not None:
                guest_type = self.determine_guest_type(clients_data, client_index)
            else:
                guest_type = client_data.get('tipo_alloggiato', GUEST_TYPE_SINGLE)

            # Get document type code
            document_type = self.get_document_type_code(
                client_data.get('document_type', DEFAULT_DOCUMENT_TYPE)
            )

            # Get location codes
            comune_nascita = self.get_location_code(
                client_data.get('comune_nascita', ''), 'municipality'
            )
            stato_nascita = self.get_location_code(
                client_data.get('stato_nascita', ''), 'country'
            )
            cittadinanza = self.get_location_code(
                client_data.get('cittadinanza', ''), 'country'
            )
            luogo_rilascio = self.get_location_code(
                client_data.get('luogo_emissione', ''), 'municipality'
            )

            # Build schedina according to official format (168 characters)
            schedina = ""
            schedina += pad_string(guest_type, 2)  # 0-1: Tipo Alloggiato
            start_date = reservation_data.get('start_date', '15/09/2025')
            start_date_formatted = format_date(start_date)
            schedina += start_date_formatted  # 2-11: Data Arrivo
            
            # Calculate duration from start_date and end_date
            duration = self._calculate_duration(reservation_data)
            duration_formatted = str(duration).zfill(2)
            logger.debug("Calculated duration: %s days (formatted: %s)", duration, duration_formatted)
            schedina += duration_formatted  # 12-13: Giorni Permanenza (zero-padded to 2 digits)
            schedina += pad_string(client_data.get('surname', ''), 50)  # 14-63: Cognome
            schedina += pad_string(client_data.get('name', ''), 30)  # 64-93: Nome
            schedina += str(client_data.get('sesso', 1))  # 94: Sesso (1=M, 2=F)
            birthday = client_data.get('birthday', DEFAULT_DATE)
            birthday_formatted = format_date(birthday)
            schedina += birthday_formatted  # 95-104: Data Nascita
            schedina += pad_string(comune_nascita, 9)  # 105-113: Comune Nascita
            schedina += pad_string(client_data.get('provincia_nascita', ''), 2)  # 114-115: Provincia Nascita (acronym)
            schedina += pad_string(stato_nascita, 9)  # 116-124: Stato Nascita
            schedina += pad_string(cittadinanza, 9)  # 125-133: Cittadinanza
            schedina += pad_string(document_type, 5)  # 134-138: Tipo Documento
            schedina += pad_string(client_data.get('document_number', ''), 20)  # 139-158: Numero Documento
            schedina += pad_string(luogo_rilascio, 9)  # 159-167: Luogo Rilascio Documento

            return schedina[:168]  # Ensure exactly 168 characters

        except Exception as e:
            logger.error("Error formatting schedina: %s", str(e))
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
            # Ensure we have a valid token
            if not self.token:
                auth_result = self.authenticate()
                if not auth_result:
                    return {'success': False, 'error': 'Authentication failed'}

            # Create SOAP envelope for Test with proper namespaces
            schedine_xml = '\n'.join([f'<string>{line}</string>' for line in schedine_lines])
            logger.debug("Schedine XML: %s", schedine_xml)
            soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <Test xmlns="AlloggiatiService">
            <Utente>{self.username}</Utente>
            <token>{self.token}</token>
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
            test_result_element = root.find('.//{AlloggiatiService}TestResult')
            result_element = root.find('.//{AlloggiatiService}result')
            if test_result_element is not None and result_element is not None:
                return self._parse_test_response(test_result_element, result_element)

            return {'success': False, 'error': 'No test result found'}

        except Exception as e:
            logger.error("Error testing schedine: %s", str(e))
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

            # Create SOAP envelope for Send with correct structure
            schedine_xml = '\n'.join([f'<string>{line}</string>' for line in schedine_lines])

            soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Send xmlns="AlloggiatiService">
      <Utente>{self.username}</Utente>
      <token>{self.token}</token>
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
            result_element = root.find('.//{AlloggiatiService}SendResult')
            if result_element is not None:
                return self._parse_send_response(result_element)

            return {'success': False, 'error': 'No submission result found'}

        except Exception as e:
            logger.error("Error sending schedine: %s", str(e))
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
            for i, client_data in enumerate(clients_data):
                schedina = self.format_schedina(client_data, reservation_data, clients_data, i)
                schedine_lines.append(schedina)

            if not schedine_lines:
                return {'success': False, 'error': 'No client data to submit'}

            # Send the data directly to production
            return self.send_schedine(schedine_lines)

        except Exception as e:
            logger.error("Error submitting guest registration: %s", str(e))
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
            for i, client_data in enumerate(clients_data):
                schedina = self.format_schedina(client_data, reservation_data, clients_data, i)
                schedine_lines.append(schedina)

            if not schedine_lines:
                return {'success': False, 'error': 'No client data to test'}

            # Test the data
            return self.test_schedine(schedine_lines)

        except Exception as e:
            logger.error("Error testing guest registration: %s", str(e))
            return {'success': False, 'error': str(e)}

    def _parse_test_response(self, test_result_element, result_element) -> Dict[str, Any]:
        """
        Parse the test response from the SOAP service.

        Args:
            test_result_element: XML element containing test result
            result_element: XML element containing result details

        Returns:
            Dict[str, Any]: Parsed test results
        """
        try:
            esito_element = test_result_element.find(ESITO_XPATH)
            if esito_element is None:
                return {'success': False, 'error': 'No test result found'}

            if esito_element.text == 'true':
                return self._handle_successful_test(result_element)
            return self._handle_failed_test(test_result_element)

        except Exception as e:
            logger.error("Error parsing test response: %s", str(e))
            return {'success': False, 'error': f'Parse error: {str(e)}'}

    def _handle_successful_test(self, result_element) -> Dict[str, Any]:
        """Handle successful test response."""
        schedine_valide = result_element.find('.//{AlloggiatiService}SchedineValide')
        valid_count = schedine_valide.text if schedine_valide is not None else '0'
        service_success = self._check_service_success(result_element)

        return {
            'success': True,
            'message': 'Test passed',
            'valid_schedine': int(valid_count),
            'service_success': service_success
        }

    def _check_service_success(self, result_element) -> bool:
        """Check if service operation was successful."""
        dettaglio = result_element.find('.//{AlloggiatiService}Dettaglio')
        if dettaglio is None:
            return True

        esito_servizio = dettaglio.find('.//{AlloggiatiService}EsitoOperazioneServizio')
        if esito_servizio is None:
            return True

        esito_serv = esito_servizio.find(ESITO_XPATH)
        return esito_serv is None or esito_serv.text != 'false'

    def _handle_failed_test(self, test_result_element) -> Dict[str, Any]:
        """Handle failed test response."""
        errore_cod = test_result_element.find(ERROR_CODE_XPATH)
        errore_des = test_result_element.find(ERROR_DESC_XPATH)
        errore_dettaglio = test_result_element.find(ERROR_DETAIL_XPATH)

        return {
            'success': False,
            'error': 'Test failed',
            'error_code': errore_cod.text if errore_cod is not None else 'Unknown',
            'error_description': errore_des.text if errore_des is not None else 'Unknown',
            'error_detail': errore_dettaglio.text if errore_dettaglio is not None else 'Unknown'
        }

    def _parse_send_response(self, result_element) -> Dict[str, Any]:
        """
        Parse the send response from the SOAP service.

        Args:
            result_element: XML element containing send results

        Returns:
            Dict[str, Any]: Parsed submission results
        """
        try:
            # Check if submission was successful
            esito_element = result_element.find(ESITO_XPATH)
            if esito_element is not None:
                if esito_element.text == 'true':
                    return {
                        'success': True,
                        'message': 'Data submitted successfully'
                    }

                # Get error details
                errore_cod = result_element.find('.//{AlloggiatiService}ErroreCod')
                errore_des = result_element.find('.//{AlloggiatiService}ErroreDes')
                errore_dettaglio = result_element.find('.//{AlloggiatiService}ErroreDettaglio')

                return {
                    'success': False,
                    'error': 'Submission failed',
                    'error_code': errore_cod.text if errore_cod is not None else 'Unknown',
                    'error_description': errore_des.text if errore_des is not None else 'Unknown',
                    'error_detail': errore_dettaglio.text if errore_dettaglio is not None else 'Unknown'
                }

            return {'success': False, 'error': 'No submission result found'}
        except Exception as e:
            logger.error("Error parsing send response: %s", str(e))
            return {'success': False, 'error': f'Parse error: {str(e)}'}
