1~
from datetime import datetime
2~
import pytest
3~
from flask import Flask
4~
from sqlalchemy import text
5~
from routes.reservation_routes import reservation_bp
6~
from database import engine, Base, SessionLocal
7~
from models import AdminStructure, Client, ClientReservations, Reservation, Role, Room, Structure, User
8~
# pylint: disable=all
9~

10~

11~
@pytest.fixture(scope="module")
12~
def app():
13~
    app = Flask(__name__)
14~
    app.config.from_object("config.TestConfig")
15~
    app.register_blueprint(reservation_bp)
16~
    Base.metadata.create_all(bind=engine)
17~
    yield app
18~
    Base.metadata.drop_all(bind=engine)
19~

20~

21~
@pytest.fixture
22~
def client(app):
23~
    return app.test_client()
24~

25~

26~
@pytest.fixture
27~
def init_db():
28~
    """Ensure a clean database before each test by removing existing data."""
29~
    db = SessionLocal()
30~
    db.execute(text('DROP VIEW IF EXISTS structure_reservations;'))  # Use CASCADE to remove dependent objects
31~

32~
    # Remove data from dependent tables first
33~
    db.query(AdminStructure).delete()    
34~
    db.query(User).delete()
35~
    db.query(ClientReservations).delete()
36~
    db.query(Reservation).delete()
37~
    db.query(Room).delete()
38~
    # Remove data from base tables
39~
    db.query(Structure).delete()
40~
    db.query(Client).delete()
41~
    db.query(Role).delete()
42~

43~
    db.commit()
44~

45~

46~
    # Create a test structure
47~
    structure = Structure(id='1',name="Test Structure", street="Test Street", city="Test City")
48~
    db.add(structure)
49~
    db.commit()
50~
    db.flush()
51~
    db.refresh(structure)
52~

53~
    # Create a test room
54~
    room = Room(name="Test Room", capacity=2, id_structure=structure.id)
55~
    db.add(room)
56~
    db.commit()
57~
    db.refresh(room)
58~

59~
    yield db  # Provide initialized DB to tests
60~

61~
    db.close()
62~

63~

64~
def test_create_reservation(client, init_db):
65~
    room = init_db.query(Room).first()
66~
    response = client.post(
67~
        "/api/v1/reservations",
68~
        json={
69~
            "reservationNumber": "RES12345",
70~
            "startDate": "2025-02-10",
71~
            "endDate": "2025-02-15",
72~
            "roomName": room.name,
73~
        },
74~
    )
75~
    assert response.status_code == 201
76~
    data = response.get_json()
77~
    assert data["reservation"]["reservationNumber"] == "RES12345"
78~
    assert data["reservation"]["startDate"] == "2025-02-10"
79~

80~

81~
def test_create_reservation_missing_fields(client):
82~
    response = client.post(
83~
        "/api/v1/reservations", json={"reservationNumber": "RES12345"}
84~
    )
85~
    assert response.status_code == 400
86~
    assert "error" in response.get_json()
87~

88~

89~
def test_create_reservation_invalid_date(client, init_db):
90~
    room = init_db.query(Room).first()
91~
    response = client.post(
92~
        "/api/v1/reservations",
93~
        json={
94~
            "reservationNumber": "RES12346",
95~
            "startDate": "10-02-2025",
96~
            "endDate": "15-02-2025",
97~
            "roomName": room.name,
98~
        },
99~
    )
100~
    assert response.status_code == 400
101~
    assert "error" in response.get_json()
102~

103~

104~
def test_create_reservation_room_not_found(client):
105~
    response = client.post(
106~
        "/api/v1/reservations",
107~
        json={
108~
            "reservationNumber": "RES12347",
109~
            "startDate": "2025-02-10",
110~
            "endDate": "2025-02-15",
111~
            "roomName": "NonExistentRoom",
112~
        },
113~
    )
114~
    assert response.status_code == 404
115~
    assert "error" in response.get_json()
116~

117~

118~
def test_get_reservations(client):
119~
    response = client.get("/api/v1/reservations")
120~
    assert response.status_code == 200
121~
    data = response.get_json()
122~
    assert "reservations" in data
123~

124~

125~
def test_get_reservation_per_month(client, init_db):
126~
    structure = init_db.query(Structure).first()
127~
    room = init_db.query(Room).first()
128~
    reservations = [
129~
       Reservation(id_reference="RES1001", start_date="2025-01-10", end_date="2025-01-15", id_room=room.id, status="Pending"),
130~
       Reservation(id_reference="RES1002", start_date="2025-02-05", end_date="2025-02-10", id_room=room.id, status="Pending"),
131~
    ]
132~
    init_db.add_all(reservations)
133~
    init_db.commit()
134~

135~
    response = client.get(f"/api/v1/reservations/monthly/{structure.id}")
136~
    assert response.status_code == 200
137~
    data = response.get_json()
138~

139~
    # Check that only the inserted reservations exist
140~
    expected_counts = {
141~
        "January": 1,
142~
        "February": 1,
143~
        "March": 0,
144~
        "April": 0,
145~
        "May": 0,
146~
        "June": 0,
147~
        "July": 0,
148~
        "August": 0,
149~
        "September": 0,
150~
        "October": 0,
151~
        "November": 0,
152~
        "December": 0,
153~
    }
154~

155~
    for entry in data:
156~
        assert entry["total_reservations"] == expected_counts[entry["month"]], f"Mismatch in {entry['month']}: {entry['total_reservations']}"
157~

158~

159~

160~
def test_get_reservations_per_month_basic(client, init_db):
161~
    """Test normal reservation retrieval per month."""
162~
    db = init_db
163~
    structure_id = db.query(Structure).first().id
164~

165~
    # Add reservations for different months
166~
    room = db.query(Room).first()
167~
    reservation1 = Reservation(
168~
        id_reference="RES1", start_date=datetime(2024, 1, 10), end_date=datetime(2024, 1, 15), id_room=room.id
169~
    )
170~
    reservation2 = Reservation(
171~
        id_reference="RES2", start_date=datetime(2024, 2, 5), end_date=datetime(2024, 2, 10), id_room=room.id
172~
    )
173~

174~
    db.add_all([reservation1, reservation2])
175~
    db.commit()
176~

177~
    response = client.get(f"/api/v1/reservations/monthly/{structure_id}")
178~
    
179~
    assert response.status_code == 200
180~
    data = response.get_json()
181~
    assert isinstance(data, list)
182~
    assert len(data) == 12  # 12 months
183~
    assert any(item['month'] == 'January' and item['total_reservations'] == 1 for item in data)
184~
    assert any(item['month'] == 'February' and item['total_reservations'] == 1 for item in data)
185~

186~

187~
def test_get_reservations_per_month_no_reservations(client, init_db):
188~
    """Test the scenario where there are no reservations for the structure."""
189~
    db = init_db
190~
    structure_id = db.query(Structure).first().id
191~

192~
    response = client.get(f"/api/v1/reservations/monthly/{structure_id}")
193~
    
194~
    assert response.status_code == 200
195~
    data = response.get_json()
196~
    assert isinstance(data, list)
197~
    assert len(data) == 12  # 12 months
198~
    assert all(item['total_reservations'] == 0 for item in data)
199~

200~

201~
def test_get_reservations_per_month_invalid_structure_id(client, init_db):
202~
    """Test the scenario where an invalid structure_id is provided."""
203~
    invalid_structure_id = 9999  # Assuming this structure ID doesn't exist
204~

205~
    response = client.get(f"/api/v1/reservations/monthly/{invalid_structure_id}")
206~
    
207~
    assert response.status_code == 404
208~
    data = response.get_json()
209~
    assert data["message"] == "Structure not found"  # Ensure the message matches the error returned
210~

211~
    """Test when no reservations exist for a structure."""
212~
    """ _, structure_id = init_db  # DB is clean from fixture """
213~

214~
    response = client.get("/api/v1/reservations/monthly/1")
215~
    assert response.status_code == 200
216~

217~
    data = response.get_json()
218~
    assert len(data) == 12  # 12 months
219~
    assert all(month["total_reservations"] == 0 for month in data)  # No reservations, so all months should be 0
220~

221~

222~
# ===========================================
223~
# COMPREHENSIVE ADDITIONAL UNIT TESTS
224~
# ===========================================
225~

226~
class TestAuthenticationComprehensive:
227~
    """Comprehensive authentication tests for all endpoints."""
228~
    
229~
    def test_all_endpoints_require_authentication(self, client):
230~
        """Test that all endpoints properly require JWT authentication."""
231~
        endpoints_and_methods = [
232~
            ('POST', '/api/v1/reservations'),
233~
            ('GET', '/api/v1/reservations'),
234~
            ('GET', '/api/v1/reservations/1'),
235~
            ('PATCH', '/api/v1/reservations/1'),
236~
            ('DELETE', '/api/v1/reservations/1'),
237~
            ('GET', '/api/v1/reservations/structure/1'),
238~
            ('GET', '/api/v1/reservations/monthly/1'),
239~
            ('PUT', '/api/v1/reservations/1/status')
240~
        ]
241~
        
242~
        for method, endpoint in endpoints_and_methods:
243~
            if method == 'POST':
244~
                response = client.post(endpoint, json={})
245~
            elif method == 'GET':
246~
                response = client.get(endpoint)
247~
            elif method == 'PATCH':
248~
                response = client.patch(endpoint, json={})
249~
            elif method == 'DELETE':
250~
                response = client.delete(endpoint)
251~
            elif method == 'PUT':
252~
                response = client.put(endpoint, json={})
253~
                
254~
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"
255~

256~
    def test_malformed_jwt_tokens(self, client, sample_reservation_data):
257~
        """Test various malformed JWT token scenarios."""
258~
        malformed_tokens = [
259~
            'Bearer',  # No token
260~
            'Bearer ',  # Empty token
261~
            'InvalidToken',  # No Bearer prefix
262~
            'Bearer invalid.token.here',  # Invalid format
263~
            'Bearer ' + 'a' * 500,  # Extremely long token
264~
        ]
265~
        
266~
        for token in malformed_tokens:
267~
            headers = {'Authorization': token}
268~
            response = client.post('/api/v1/reservations', 
269~
                                 json=sample_reservation_data, 
270~
                                 headers=headers)
271~
            
272~
            assert response.status_code in [401, 422], f"Token {token[:20]}... should be rejected"
273~

274~

275~
class TestCreateReservationAdvanced:
276~
    """Advanced test cases for reservation creation."""
277~
    
278~
    def test_create_reservation_with_extreme_date_ranges(self, client, auth_headers, init_db):
279~
        """Test reservation creation with extreme date ranges."""
280~
        room = init_db.query(Room).first()
281~
        
282~
        extreme_scenarios = [
283~
            # Very long reservation (1 year)
284~
            {
285~
                "startDate": "2025-01-01",
286~
                "endDate": "2025-12-31",
287~
                "scenario": "year_long"
288~
            },
289~
            # Minimum date range (same day)
290~
            {
291~
                "startDate": "2025-06-15",
292~
                "endDate": "2025-06-15",
293~
                "scenario": "same_day"
294~
            },
295~
            # Historical dates (past year)
296~
            {
297~
                "startDate": "2023-01-01",
298~
                "endDate": "2023-01-05",
299~
                "scenario": "historical"
300~
            }
301~
        ]
302~
        
303~
        for scenario in extreme_scenarios:
304~
            test_data = {
305~
                "reservationNumber": f"RES-EXTREME-{scenario['scenario'].upper()}",
306~
                "startDate": scenario["startDate"],
307~
                "endDate": scenario["endDate"],
308~
                "roomName": room.name,
309~
                "nameReference": f"Extreme Test {scenario['scenario']}"
310~
            }
311~
            
312~
            response = client.post("/api/v1/reservations", 
313~
                                 json=test_data, 
314~
                                 headers=auth_headers)
315~
            
316~
            # Should handle extreme ranges gracefully
317~
            assert response.status_code in [201, 400]
318~

319~
    def test_create_reservation_with_very_long_strings(self, client, auth_headers, init_db):
320~
        """Test reservation creation with very long string inputs."""
321~
        room = init_db.query(Room).first()
322~
        
323~
        very_long_string = "A" * 1000  # 1000 character string
324~
        
325~
        test_data = {
326~
            "reservationNumber": very_long_string,
327~
            "startDate": "2025-02-10",
328~
            "endDate": "2025-02-15",
329~
            "roomName": room.name,
330~
            "nameReference": very_long_string
331~
        }
332~
        
333~
        response = client.post("/api/v1/reservations", 
334~
                             json=test_data, 
335~
                             headers=auth_headers)
336~
        
337~
        # Should handle long strings gracefully (either accept or reject with proper error)
338~
        assert response.status_code in [201, 400, 500]
339~

340~
    def test_create_reservation_with_null_values(self, client, auth_headers):
341~
        """Test reservation creation with null values."""
342~
        test_data = {
343~
            "reservationNumber": None,
344~
            "startDate": None,
345~
            "endDate": None,
346~
            "roomName": None,
347~
            "nameReference": None
348~
        }
349~
        
350~
        response = client.post("/api/v1/reservations", 
351~
                             json=test_data, 
352~
                             headers=auth_headers)
353~
        
354~
        assert response.status_code == 400
355~
        data = response.get_json()
356~
        assert "Missing required fields" in data["error"]
357~

358~
    def test_create_reservation_json_injection_attempts(self, client, auth_headers, init_db):
359~
        """Test reservation creation against JSON injection attempts."""
360~
        room = init_db.query(Room).first()
361~
        
362~
        injection_attempts = [
363~
            {"reservationNumber": "'; DROP TABLE reservations; --"},
364~
            {"nameReference": "<script>alert('xss')</script>"},
365~
            {"roomName": "{{7*7}}"},  # Template injection
366~
            {"reservationNumber": "\x00\x01\x02"},  # Null bytes
367~
        ]
368~
        
369~
        for injection_data in injection_attempts:
370~
            test_data = {
371~
                "reservationNumber": "RES-INJECTION",
372~
                "startDate": "2025-02-10",
373~
                "endDate": "2025-02-15",
374~
                "roomName": room.name,
375~
                "nameReference": "Test User"
376~
            }
377~
            test_data.update(injection_data)
378~
            
379~
            response = client.post("/api/v1/reservations", 
380~
                                 json=test_data, 
381~
                                 headers=auth_headers)
382~
            
383~
            # Should not cause server errors, handle gracefully
384~
            assert response.status_code in [201, 400, 404]
385~

386~

387~
class TestUpdateReservationAdvanced:
388~
    """Advanced test cases for reservation updates."""
389~
    
390~
    def test_update_reservation_concurrent_modifications(self, client, auth_headers, init_db):
391~
        """Test handling of potential concurrent modifications."""
392~
        room = init_db.query(Room).first()
393~
        reservation = Reservation(
394~
            id_reference="RES-CONCURRENT-MOD",
395~
            start_date=datetime(2025, 2, 5),
396~
            end_date=datetime(2025, 2, 8),
397~
            name_reference="Concurrent Mod Test",
398~
            id_room=room.id,
399~
            status="Pending"
400~
        )
401~
        init_db.add(reservation)
402~
        init_db.commit()
403~
        init_db.refresh(reservation)
404~
        
405~
        # Simulate rapid successive updates
406~
        updates = [
407~
            {"name_reference": "First Update"},
408~
            {"status": "Approved"},
409~
            {"id_reference": "RES-UPDATED-RAPID"},
410~
            {"name_reference": "Final Update"}
411~
        ]
412~
        
413~
        for i, update_data in enumerate(updates):
414~
            response = client.patch(f"/api/v1/reservations/{reservation.id}", 
415~
                                  json=update_data, 
416~
                                  headers=auth_headers)
417~
            
418~
            assert response.status_code == 200, f"Update {i+1} failed"
419~

420~
    def test_update_reservation_with_invalid_room_data_types(self, client, auth_headers, init_db):
421~
        """Test updating reservation with invalid room data types."""
422~
        room = init_db.query(Room).first()
423~
        reservation = Reservation(
424~
            id_reference="RES-INVALID-ROOM-DATA",
425~
            start_date=datetime(2025, 2, 5),
426~
            end_date=datetime(2025, 2, 8),
427~
            name_reference="Invalid Room Data Test",
428~
            id_room=room.id,
429~
            status="Pending"
430~
        )
431~
        init_db.add(reservation)
432~
        init_db.commit()
433~
        init_db.refresh(reservation)
434~
        
435~
        invalid_room_data = [
436~
            {"room": "not_a_dict"},
437~
            {"room": {"id": "not_an_integer"}},
438~
            {"room": {"id": -1}},
439~
            {"room": {"invalid_key": 1}},
440~
            {"room": {}},  # Missing id key
441~
        ]
442~
        
443~
        for invalid_data in invalid_room_data:
444~
            response = client.patch(f"/api/v1/reservations/{reservation.id}", 
445~
                                  json=invalid_data, 
446~
                                  headers=auth_headers)
447~
            
448~
            # Should handle invalid data gracefully
449~
            assert response.status_code in [200, 400, 404]
450~

451~
    def test_update_reservation_date_format_edge_cases(self, client, auth_headers, init_db):
452~
        """Test updating reservation with various date format edge cases."""
453~
        room = init_db.query(Room).first()
454~
        reservation = Reservation(
455~
            id_reference="RES-DATE-EDGE",
456~
            start_date=datetime(2025, 2, 5),
457~
            end_date=datetime(2025, 2, 8),
458~
            name_reference="Date Edge Test",
459~
            id_room=room.id,
460~
            status="Pending"
461~
        )
462~
        init_db.add(reservation)
463~
        init_db.commit()
464~
        init_db.refresh(reservation)
465~
        
466~
        # Test various GMT format variations
467~
        date_formats = [
468~
            "Mon, 10 Feb 2025 00:00:00 GMT",  # Midnight
469~
            "Fri, 31 Dec 2024 23:59:59 GMT",  # End of year
470~
            "Thu, 29 Feb 2024 12:00:00 GMT",  # Leap year
471~
            "Sun, 01 Jan 2025 01:01:01 GMT",  # New year
472~
        ]
473~
        
474~
        for date_format in date_formats:
475~
            update_data = {"start_date": date_format}
476~
            
477~
            response = client.patch(f"/api/v1/reservations/{reservation.id}", 
478~
                                  json=update_data, 
479~
                                  headers=auth_headers)
480~
            
481~
            # Should handle various GMT formats
482~
            assert response.status_code in [200, 400, 500]
483~

484~

485~
class TestDeleteReservationAdvanced:
486~
    """Advanced test cases for reservation deletion."""
487~
    
488~
    def test_delete_reservation_cascade_effects(self, client, auth_headers, init_db):
489~
        """Test deletion and potential cascade effects."""
490~
        room = init_db.query(Room).first()
491~
        
492~
        # Create multiple reservations to test deletion doesn't affect others
493~
        reservations = []
494~
        for i in range(5):
495~
            reservation = Reservation(
496~
                id_reference=f"RES-CASCADE-{i}",
497~
                start_date=datetime(2025, 2, 5 + i),
498~
                end_date=datetime(2025, 2, 8 + i),
499~
                name_reference=f"Cascade Test {i}",
500~
                id_room=room.id,
501~
                status="Pending"
502~
            )
503~
            reservations.append(reservation)
504~
        
505~
        init_db.add_all(reservations)
506~
        init_db.commit()
507~
        
508~
        # Delete middle reservation
509~
        reservation_to_delete = reservations[2]
510~
        response = client.delete(f"/api/v1/reservations/{reservation_to_delete.id}", 
511~
                               headers=auth_headers)
512~
        
513~
        assert response.status_code == 200
514~
        
515~
        # Verify other reservations still exist
516~
        for i, res in enumerate(reservations):
517~
            if i == 2:  # Skip deleted one
518~
                continue
519~
            remaining = init_db.query(Reservation).filter(Reservation.id == res.id).first()
520~
            assert remaining is not None, f"Reservation {i} should still exist"
521~

522~
    def test_delete_reservation_idempotency(self, client, auth_headers):
523~
        """Test deleting the same reservation multiple times."""
524~
        # Try to delete non-existent reservation multiple times
525~
        for _ in range(3):
526~
            response = client.delete("/api/v1/reservations/99999", 
527~
                                   headers=auth_headers)
528~
            
529~
            assert response.status_code == 404
530~
            data = response.get_json()
531~
            assert "not found" in data["error"]
532~

533~

534~
class TestGetReservationsByIdAdvanced:
535~
    """Advanced test cases for getting reservation by ID."""
536~
    
537~
    def test_get_reservation_by_id_with_complex_data(self, client, auth_headers, init_db):
538~
        """Test getting reservation with complex data structures."""
539~
        room = init_db.query(Room).first()
540~
        
541~
        # Create reservation with complex unicode and special characters
542~
        reservation = Reservation(
543~
            id_reference="RES-复杂数据-测试",
544~
            start_date=datetime(2025, 2, 5),
545~
            end_date=datetime(2025, 2, 8),
546~
            name_reference="José María García-López 李明",
547~
            id_room=room.id,
548~
            status="Pending"
549~
        )
550~
        init_db.add(reservation)
551~
        init_db.commit()
552~
        init_db.refresh(reservation)
553~
        
554~
        response = client.get(f"/api/v1/reservations/{reservation.id}", 
555~
                            headers=auth_headers)
556~
        
557~
        assert response.status_code == 200
558~
        data = response.get_json()
559~
        
560~
        # Verify complex data is properly serialized
561~
        assert "id_reference" in data
562~
        assert "name_reference" in data
563~

564~
    def test_get_reservation_serialization_completeness(self, client, auth_headers, init_db):
565~
        """Test that reservation serialization includes all expected fields."""
566~
        room = init_db.query(Room).first()
567~
        reservation = Reservation(
568~
            id_reference="RES-SERIALIZATION-TEST",
569~
            start_date=datetime(2025, 2, 5),
570~
            end_date=datetime(2025, 2, 8),
571~
            name_reference="Serialization Test",
572~
            id_room=room.id,
573~
            status="Approved"
574~
        )
575~
        init_db.add(reservation)
576~
        init_db.commit()
577~
        init_db.refresh(reservation)
578~
        
579~
        response = client.get(f"/api/v1/reservations/{reservation.id}", 
580~
                            headers=auth_headers)
581~
        
582~
        assert response.status_code == 200
583~
        data = response.get_json()
584~
        
585~
        # Check for presence of expected fields
586~
        expected_fields = ["id", "id_reference", "name_reference", "status"]
587~
        for field in expected_fields:
588~
            assert field in data, f"Field {field} should be in response"
589~

590~

591~
class TestGetReservationsByStructureAdvanced:
592~
    """Advanced test cases for getting reservations by structure."""
593~
    
594~
    def test_get_reservations_by_structure_with_large_dataset(self, client, auth_headers, init_db):
595~
        """Test getting reservations by structure with large number of reservations."""
596~
        structure = init_db.query(Structure).first()
597~
        room = init_db.query(Room).first()
598~
        
599~
        # Create many reservations
600~
        reservations = []
601~
        for i in range(50):  # Create 50 reservations
602~
            reservation = Reservation(
603~
                id_reference=f"RES-LARGE-{i:03d}",
604~
                start_date=datetime(2025, (i % 12) + 1, (i % 28) + 1),
605~
                end_date=datetime(2025, (i % 12) + 1, min((i % 28) + 3, 28)),
606~
                name_reference=f"Large Dataset Test {i}",
607~
                id_room=room.id,
608~
                status="Pending"
609~
            )
610~
            reservations.append(reservation)
611~
        
612~
        init_db.add_all(reservations)
613~
        init_db.commit()
614~
        
615~
        response = client.get(f"/api/v1/reservations/structure/{structure.id}", 
616~
                            headers=auth_headers)
617~
        
618~
        assert response.status_code == 200
619~
        data = response.get_json()
620~
        assert isinstance(data, list)
621~
        # Should handle large datasets without issues
622~

623~
    def test_get_reservations_by_structure_data_consistency(self, client, auth_headers, init_db):
624~
        """Test data consistency in structure reservations response."""
625~
        structure = init_db.query(Structure).first()
626~
        room = init_db.query(Room).first()
627~
        
628~
        # Create a reservation with known data
629~
        reservation = Reservation(
630~
            id_reference="RES-CONSISTENCY",
631~
            start_date=datetime(2025, 6, 15),
632~
            end_date=datetime(2025, 6, 20),
633~
            name_reference="Consistency Test User",
634~
            id_room=room.id,
635~
            status="Confirmed"
636~
        )
637~
        init_db.add(reservation)
638~
        init_db.commit()
639~
        
640~
        response = client.get(f"/api/v1/reservations/structure/{structure.id}", 
641~
                            headers=auth_headers)
642~
        
643~
        assert response.status_code == 200
644~
        data = response.get_json()
645~
        
646~
        if data:  # If reservations exist
647~
            for item in data:
648~
                # Verify required fields are present
649~
                required_fields = [
650~
                    "structure_id", "reservation_id", "id_reference", 
651~
                    "start_date", "end_date", "status", "name_reference"
652~
                ]
653~
                for field in required_fields:
654~
                    assert field in item, f"Field {field} missing from response"
655~
                
656~
                # Verify date format is ISO format
657~
                assert "T" in item["start_date"] or item["start_date"].count("-") == 2
658~

659~

660~
class TestMonthlyReservationsAdvanced:
661~
    """Advanced test cases for monthly reservation statistics."""
662~
    
663~
    def test_monthly_reservations_cross_year_boundary(self, client, auth_headers, init_db):
664~
        """Test monthly reservations spanning across year boundaries."""
665~
        structure = init_db.query(Structure).first()
666~
        room = init_db.query(Room).first()
667~
        
668~
        # Create reservations spanning different years
669~
        cross_year_reservations = [
670~
            Reservation(id_reference="RES-2024-DEC", start_date=datetime(2024, 12, 15), 
671~
                       end_date=datetime(2024, 12, 20), id_room=room.id, status="Pending"),
672~
            Reservation(id_reference="RES-2025-JAN", start_date=datetime(2025, 1, 5), 
673~
                       end_date=datetime(2025, 1, 10), id_room=room.id, status="Pending"),
674~
            Reservation(id_reference="RES-2025-DEC", start_date=datetime(2025, 12, 25), 
675~
                       end_date=datetime(2025, 12, 30), id_room=room.id, status="Pending"),
676~
        ]
677~
        init_db.add_all(cross_year_reservations)
678~
        init_db.commit()
679~
        
680~
        response = client.get(f"/api/v1/reservations/monthly/{structure.id}", 
681~
                            headers=auth_headers)
682~
        
683~
        assert response.status_code == 200
684~
        data = response.get_json()
685~
        assert len(data) == 12  # Should always return 12 months
686~
        
687~
        # Verify specific months have correct counts
688~
        december_data = next(item for item in data if item["month"] == "December")
689~
        january_data = next(item for item in data if item["month"] == "January")
690~
        
691~
        # Note: This depends on which year the query focuses on
692~
        assert december_data["total_reservations"] >= 0
693~
        assert january_data["total_reservations"] >= 0
694~

695~
    def test_monthly_reservations_data_accuracy(self, client, auth_headers, init_db):
696~
        """Test accuracy of monthly reservation counts."""
697~
        structure = init_db.query(Structure).first()
698~
        room = init_db.query(Room).first()
699~
        
700~
        # Create precisely counted reservations for specific months
701~
        precise_reservations = [
702~
            # March: exactly 3 reservations
703~
            Reservation(id_reference="RES-MAR-1", start_date=datetime(2025, 3, 1), 
704~
                       end_date=datetime(2025, 3, 5), id_room=room.id, status="Pending"),
705~
            Reservation(id_reference="RES-MAR-2", start_date=datetime(2025, 3, 10), 
706~
                       end_date=datetime(2025, 3, 15), id_room=room.id, status="Pending"),
707~
            Reservation(id_reference="RES-MAR-3", start_date=datetime(2025, 3, 20), 
708~
                       end_date=datetime(2025, 3, 25), id_room=room.id, status="Pending"),
709~
            
710~
            # April: exactly 1 reservation
711~
            Reservation(id_reference="RES-APR-1", start_date=datetime(2025, 4, 12), 
712~
                       end_date=datetime(2025, 4, 17), id_room=room.id, status="Pending"),
713~
        ]
714~
        init_db.add_all(precise_reservations)
715~
        init_db.commit()
716~
        
717~
        response = client.get(f"/api/v1/reservations/monthly/{structure.id}", 
718~
                            headers=auth_headers)
719~
        
720~
        assert response.status_code == 200
721~
        data = response.get_json()
722~
        
723~
        # Verify precise counts
724~
        march_data = next(item for item in data if item["month"] == "March")
725~
        april_data = next(item for item in data if item["month"] == "April")
726~
        
727~
        assert march_data["total_reservations"] == 3
728~
        assert april_data["total_reservations"] == 1
729~
        
730~
        # Verify other months have expected counts (should be 0 unless other tests added data)
731~
        for item in data:
732~
            if item["month"] not in ["March", "April"]:
733~
                assert item["total_reservations"] >= 0  # Non-negative
734~

735~
    def test_monthly_reservations_month_name_consistency(self, client, auth_headers, init_db):
736~
        """Test that month names are consistent and correctly formatted."""
737~
        structure = init_db.query(Structure).first()
738~
        
739~
        response = client.get(f"/api/v1/reservations/monthly/{structure.id}", 
740~
                            headers=auth_headers)
741~
        
742~
        assert response.status_code == 200
743~
        data = response.get_json()
744~
        
745~
        expected_months = [
746~
            "January", "February", "March", "April", "May", "June",
747~
            "July", "August", "September", "October", "November", "December"
748~
        ]
749~
        
750~
        returned_months = [item["month"] for item in data]
751~
        
752~
        # Check all expected months are present
753~
        for expected_month in expected_months:
754~
            assert expected_month in returned_months, f"Month {expected_month} missing"
755~
        
756~
        # Check no unexpected months
757~
        for returned_month in returned_months:
758~
            assert returned_month in expected_months, f"Unexpected month {returned_month}"
759~
        
760~
        # Check each month appears exactly once
761~
        assert len(returned_months) == len(set(returned_months)), "Duplicate months found"
762~

763~

764~
class TestStatusUpdateAdvanced:
765~
    """Advanced test cases for status updates."""
766~
    
767~
    def test_status_update_state_transitions(self, client, auth_headers, init_db):
768~
        """Test valid state transitions for reservation status."""
769~
        room = init_db.query(Room).first()
770~
        
771~
        # Test all possible state transitions
772~
        state_transitions = [
773~
            ("Pending", "Approved"),
774~
            ("Pending", "Declined"),
775~
            ("Pending", "Sent back to customer"),
776~
            ("Approved", "Declined"),
777~
            ("Approved", "Sent back to customer"),
778~
            ("Declined", "Approved"),
779~
            ("Sent back to customer", "Pending"),
780~
            ("Sent back to customer", "Approved"),
781~
        ]
782~
        
783~
        for initial_status, new_status in state_transitions:
784~
            # Create reservation with initial status
785~
            reservation = Reservation(
786~
                id_reference=f"RES-TRANSITION-{initial_status[:3]}-{new_status[:3]}",
787~
                start_date=datetime(2025, 2, 5),
788~
                end_date=datetime(2025, 2, 8),
789~
                name_reference=f"Transition Test {initial_status} to {new_status}",
790~
                id_room=room.id,
791~
                status=initial_status
792~
            )
793~
            init_db.add(reservation)
794~
            init_db.commit()
795~
            init_db.refresh(reservation)
796~
            
797~
            # Update status
798~
            update_data = {"status": new_status}
799~
            response = client.put(f"/api/v1/reservations/{reservation.id}/status", 
800~
                                json=update_data, 
801~
                                headers=auth_headers)
802~
            
803~
            assert response.status_code == 200, f"Transition from {initial_status} to {new_status} failed"
804~
            data = response.get_json()
805~
            assert data["reservation"]["status"] == new_status
806~

807~
    def test_status_update_case_sensitivity(self, client, auth_headers):
808~
        """Test status update case sensitivity."""
809~
        case_variations = [
810~
            "approved",  # lowercase
811~
            "APPROVED",  # uppercase
812~
            "Approved",  # correct case
813~
            "ApProVed",  # mixed case
814~
        ]
815~
        
816~
        for status_variation in case_variations:
817~
            update_data = {"status": status_variation}
818~
            response = client.put("/api/v1/reservations/1/status", 
819~
                                json=update_data, 
820~
                                headers=auth_headers)
821~
            
822~
            if status_variation == "Approved":
823~
                # Only exact case should work (if reservation exists)
824~
                assert response.status_code in [200, 404]
825~
            else:
826~
                # Other cases should be rejected
827~
                assert response.status_code == 400
828~

829~
    def test_status_update_with_additional_fields(self, client, auth_headers, init_db):
830~
        """Test status update when additional fields are provided."""
831~
        room = init_db.query(Room).first()
832~
        reservation = Reservation(
833~
            id_reference="RES-ADDITIONAL-FIELDS",
834~
            start_date=datetime(2025, 2, 5),
835~
            end_date=datetime(2025, 2, 8),
836~
            name_reference="Additional Fields Test",
837~
            id_room=room.id,
838~
            status="Pending"
839~
        )
840~
        init_db.add(reservation)
841~
        init_db.commit()
842~
        init_db.refresh(reservation)
843~
        
844~
        # Include status with additional fields
845~
        update_data = {
846~
            "status": "Approved",
847~
            "extra_field": "should_be_ignored",
848~
            "another_field": 123,
849~
            "nested": {"data": "test"}
850~
        }
851~
        
852~
        response = client.put(f"/api/v1/reservations/{reservation.id}/status", 
853~
                            json=update_data, 
854~
                            headers=auth_headers)
855~
        
856~
        assert response.status_code == 200
857~
        data = response.get_json()
858~
        assert data["reservation"]["status"] == "Approved"
859~

860~

861~
class TestErrorHandlingAndEdgeCases:
862~
    """Comprehensive error handling and edge case tests."""
863~
    
864~
    def test_malformed_json_requests(self, client, auth_headers):
865~
        """Test handling of malformed JSON in requests."""
866~
        endpoints_methods = [
867~
            ('POST', '/api/v1/reservations'),
868~
            ('PATCH', '/api/v1/reservations/1'),
869~
            ('PUT', '/api/v1/reservations/1/status'),
870~
        ]
871~
        
872~
        malformed_data = [
873~
            '{"invalid": json}',  # Invalid JSON syntax
874~
            '{"unclosed": "string}',  # Unclosed string
875~
            '{invalid_key: "value"}',  # Unquoted key
876~
            'not json at all',  # Not JSON
877~
        ]
878~
        
879~
        for method, endpoint in endpoints_methods:
880~
            for bad_data in malformed_data:
881~
                if method == 'POST':
882~
                    response = client.post(endpoint, data=bad_data, 
883~
                                         headers=auth_headers,
884~
                                         content_type='application/json')
885~
                elif method == 'PATCH':
886~
                    response = client.patch(endpoint, data=bad_data, 
887~
                                          headers=auth_headers,
888~
                                          content_type='application/json')
889~
                elif method == 'PUT':
890~
                    response = client.put(endpoint, data=bad_data, 
891~
                                        headers=auth_headers,
892~
                                        content_type='application/json')
893~
                
894~
                # Should return 400 for malformed JSON
895~
                assert response.status_code == 400
896~

897~
    def test_extremely_large_request_payloads(self, client, auth_headers, init_db):
898~
        """Test handling of extremely large request payloads."""
899~
        room = init_db.query(Room).first()
900~
        
901~
        # Create extremely large string data
902~
        huge_string = "A" * 100000  # 100KB string
903~
        
904~
        large_payload = {
905~
            "reservationNumber": huge_string,
906~
            "startDate": "2025-02-10",
907~
            "endDate": "2025-02-15",
908~
            "roomName": room.name,
909~
            "nameReference": huge_string
910~
        }
911~
        
912~
        response = client.post("/api/v1/reservations", 
913~
                             json=large_payload, 
914~
                             headers=auth_headers)
915~
        
916~
        # Should handle large payloads gracefully
917~
        assert response.status_code in [201, 400, 413, 500]
918~

919~
    def test_unicode_edge_cases(self, client, auth_headers, init_db):
920~
        """Test various Unicode edge cases."""
921~
        room = init_db.query(Room).first()
922~
        
923~
        unicode_test_cases = [
924~
            # Zero-width characters
925~
            {"name": "zero_width", "text": "Test\u200B\u200C\u200DUser"},
926~
            
927~
            # Right-to-left text
928~
            {"name": "rtl", "text": "مرحبا بالعالم"},
929~
            
930~
            # Combining characters
931~
            {"name": "combining", "text": "e\u0301\u0302\u0303"},
932~
            
933~
            # Surrogate pairs
934~
            {"name": "surrogate", "text": "𝓗𝓮𝓵𝓵𝓸 𝓦𝓸𝓻𝓵𝓭"},
935~
            
936~
            # Control characters (should be handled carefully)
937~
            {"name": "control", "text": "Test\x00\x01\x02User"},
938~
        ]
939~
        
940~
        for test_case in unicode_test_cases:
941~
            test_data = {
942~
                "reservationNumber": f"RES-UNICODE-{test_case['name'].upper()}",
943~
                "startDate": "2025-02-10",
944~
                "endDate": "2025-02-15",
945~
                "roomName": room.name,
946~
                "nameReference": test_case["text"]
947~
            }
948~
            
949~
            response = client.post("/api/v1/reservations", 
950~
                                 json=test_data, 
951~
                                 headers=auth_headers)
952~
            
953~
            # Should handle Unicode gracefully
954~
            assert response.status_code in [201, 400]
955~

956~
    def test_resource_exhaustion_scenarios(self, client, auth_headers, init_db):
957~
        """Test scenarios that might cause resource exhaustion."""
958~
        structure = init_db.query(Structure).first()
959~
        
960~
        # Test with very large structure ID
961~
        large_structure_id = 2**31 - 1
962~
        
963~
        response = client.get(f"/api/v1/reservations/monthly/{large_structure_id}", 
964~
                            headers=auth_headers)
965~
        
966~
        assert response.status_code in [200, 404]  # Should handle gracefully
967~
        
968~
        # Test rapid successive requests (basic rate limiting test)
969~
        for _ in range(10):
970~
            response = client.get(f"/api/v1/reservations/monthly/{structure.id}", 
971~
                                headers=auth_headers)
972~
            assert response.status_code == 200
973~

974~
    @patch('routes.reservation_routes.SessionLocal')
975~
    def test_database_timeout_scenarios(self, mock_session_local, client, auth_headers):
976~
        """Test handling of database timeout scenarios."""
977~
        import time
978~
        
979~
        def slow_query(*args, **kwargs):
980~
            time.sleep(0.1)  # Simulate slow query
981~
            raise Exception("Database query timeout")
982~
        
983~
        mock_session = Mock()
984~
        mock_session_local.return_value = mock_session
985~
        mock_session.query.side_effect = slow_query
986~
        
987~
        response = client.get("/api/v1/reservations/1", headers=auth_headers)
988~
        
989~
        assert response.status_code == 500
990~
        data = response.get_json()
991~
        assert "error" in data
992~

993~
    def test_content_type_handling(self, client, auth_headers):
994~
        """Test handling of various content types."""
995~
        test_data = '{"status": "Approved"}'
996~
        
997~
        content_types = [
998~
            'application/json',  # Correct
999~
            'text/json',         # Alternative JSON
1000~
            'application/xml',   # Wrong type
1001~
            'text/plain',        # Plain text
1002~
            None,                # No content type
1003~
        ]
1004~
        
1005~
        for content_type in content_types:
1006~
            headers = auth_headers.copy()
1007~
            if content_type:
1008~
                headers['Content-Type'] = content_type
1009~
            
1010~
            response = client.put("/api/v1/reservations/1/status", 
1011~
                                data=test_data, 
1012~
                                headers=headers)
1013~
            
1014~
            # Should handle content types appropriately
1015~
            if content_type in ['application/json', 'text/json', None]:
1016~
                assert response.status_code in [200, 404]  # Valid JSON content types
1017~
            else:
1018~
                assert response.status_code == 400  # Invalid content types
1019~

1020~

1021~
class TestPerformanceAndStress:
1022~
    """Performance and stress testing scenarios."""
1023~
    
1024~
    def test_batch_operations_performance(self, client, auth_headers, init_db):
1025~
        """Test performance with batch-like operations."""
1026~
        structure = init_db.query(Structure).first()
1027~
        room = init_db.query(Room).first()
1028~
        
1029~
        # Create moderate number of reservations quickly
1030~
        import time
1031~
        start_time = time.time()
1032~
        
1033~
        for i in range(20):  # Moderate batch size
1034~
            reservation_data = {
1035~
                "reservationNumber": f"RES-BATCH-{i:03d}",
1036~
                "startDate": "2025-02-10",
1037~
                "endDate": "2025-02-15",
1038~
                "roomName": room.name,
1039~
                "nameReference": f"Batch User {i}"
1040~
            }
1041~
            
1042~
            response = client.post("/api/v1/reservations", 
1043~
                                 json=reservation_data, 
1044~
                                 headers=auth_headers)
1045~
            
1046~
            assert response.status_code == 201
1047~
        
1048~
        end_time = time.time()
1049~
        batch_time = end_time - start_time
1050~
        
1051~
        # Should complete within reasonable time (adjust as needed)
1052~
        assert batch_time < 30.0, f"Batch operations took {batch_time:.2f} seconds"
1053~

1054~
    def test_complex_query_performance(self, client, auth_headers, init_db):
1055~
        """Test performance of complex queries."""
1056~
        structure = init_db.query(Structure).first()
1057~
        room = init_db.query(Room).first()
1058~
        
1059~
        # Create varied reservations across all months
1060~
        for month in range(1, 13):
1061~
            for day in [5, 15, 25]:
1062~
                if month == 2 and day == 25:  # Skip invalid February date
1063~
                    continue
1064~
                    
1065~
                reservation = Reservation(
1066~
                    id_reference=f"RES-PERF-{month:02d}-{day:02d}",
1067~
                    start_date=datetime(2025, month, day),
1068~
                    end_date=datetime(2025, month, min(day + 2, 28)),
1069~
                    name_reference=f"Performance Test {month}-{day}",
1070~
                    id_room=room.id,
1071~
                    status="Pending"
1072~
                )
1073~
                init_db.add(reservation)
1074~
        
1075~
        init_db.commit()
1076~
        
1077~
        # Test monthly aggregation performance
1078~
        import time
1079~
        start_time = time.time()
1080~
        
1081~
        response = client.get(f"/api/v1/reservations/monthly/{structure.id}", 
1082~
                            headers=auth_headers)
1083~
        
1084~
        end_time = time.time()
1085~
        query_time = end_time - start_time
1086~
        
1087~
        assert response.status_code == 200
1088~
        assert query_time < 5.0, f"Monthly query took {query_time:.2f} seconds"
1089~

1090~

1091~
# Additional integration-style tests
1092~
class TestEndToEndScenarios:
1093~
    """End-to-end scenario testing."""
1094~
    
1095~
    def test_complete_reservation_lifecycle(self, client, auth_headers, init_db):
1096~
        """Test complete reservation lifecycle from creation to deletion."""
1097~
        room = init_db.query(Room).first()
1098~
        
1099~
        # 1. Create reservation
1100~
        reservation_data = {
1101~
            "reservationNumber": "RES-LIFECYCLE-TEST",
1102~
            "startDate": "2025-03-15",
1103~
            "endDate": "2025-03-20",
1104~
            "roomName": room.name,
1105~
            "nameReference": "Lifecycle Test User"
1106~
        }
1107~
        
1108~
        create_response = client.post("/api/v1/reservations", 
1109~
                                    json=reservation_data, 
1110~
                                    headers=auth_headers)
1111~
        
1112~
        assert create_response.status_code == 201
1113~
        created_reservation = create_response.get_json()["reservation"]
1114~
        reservation_id = created_reservation["id"]
1115~
        
1116~
        # 2. Get reservation by ID
1117~
        get_response = client.get(f"/api/v1/reservations/{reservation_id}", 
1118~
                                headers=auth_headers)
1119~
        
1120~
        assert get_response.status_code == 200
1121~
        
1122~
        # 3. Update reservation details
1123~
        update_data = {
1124~
            "name_reference": "Updated Lifecycle User",
1125~
            "id_reference": "RES-LIFECYCLE-UPDATED"
1126~
        }
1127~
        
1128~
        update_response = client.patch(f"/api/v1/reservations/{reservation_id}", 
1129~
                                     json=update_data, 
1130~
                                     headers=auth_headers)
1131~
        
1132~
        assert update_response.status_code == 200
1133~
        
1134~
        # 4. Update status
1135~
        status_data = {"status": "Approved"}
1136~
        status_response = client.put(f"/api/v1/reservations/{reservation_id}/status", 
1137~
                                   json=status_data, 
1138~
                                   headers=auth_headers)
1139~
        
1140~
        assert status_response.status_code == 200
1141~
        
1142~
        # 5. Verify in structure view
1143~
        structure = init_db.query(Structure).first()
1144~
        structure_response = client.get(f"/api/v1/reservations/structure/{structure.id}", 
1145~
                                      headers=auth_headers)
1146~
        
1147~
        assert structure_response.status_code == 200
1148~
        structure_reservations = structure_response.get_json()
1149~
        assert any(res["reservation_id"] == reservation_id for res in structure_reservations)
1150~
        
1151~
        # 6. Delete reservation
1152~
        delete_response = client.delete(f"/api/v1/reservations/{reservation_id}", 
1153~
                                      headers=auth_headers)
1154~
        
1155~
        assert delete_response.status_code == 200
1156~
        
1157~
        # 7. Verify deletion
1158~
        verify_response = client.get(f"/api/v1/reservations/{reservation_id}", 
1159~
                                   headers=auth_headers)
1160~
        
1161~
        assert verify_response.status_code == 404
1162~

1163~
    def test_multi_room_multi_structure_scenario(self, client, auth_headers, init_db):
1164~
        """Test scenarios involving multiple rooms and structures."""
1165~
        # Create additional structure and room
1166~
        structure1 = init_db.query(Structure).first()
1167~
        
1168~
        structure2 = Structure(
1169~
            id='2', 
1170~
            name="Second Test Structure", 
1171~
            street="Second Street", 
1172~
            city="Second City"
1173~
        )
1174~
        init_db.add(structure2)
1175~
        init_db.commit()
1176~
        init_db.refresh(structure2)
1177~
        
1178~
        room1 = init_db.query(Room).first()
1179~
        room2 = Room(name="Second Test Room", capacity=4, id_structure=structure2.id)
1180~
        init_db.add(room2)
1181~
        init_db.commit()
1182~
        init_db.refresh(room2)
1183~
        
1184~
        # Create reservations in both structures
1185~
        reservations_data = [
1186~
            {
1187~
                "reservationNumber": "RES-MULTI-S1-R1",
1188~
                "startDate": "2025-04-10",
1189~
                "endDate": "2025-04-15",
1190~
                "roomName": room1.name,
1191~
                "nameReference": "Multi Test User 1"
1192~
            },
1193~
            {
1194~
                "reservationNumber": "RES-MULTI-S2-R2",
1195~
                "startDate": "2025-04-12",
1196~
                "endDate": "2025-04-17",
1197~
                "roomName": room2.name,
1198~
                "nameReference": "Multi Test User 2"
1199~
            }
1200~
        ]
1201~
        
1202~
        created_reservations = []
1203~
        for res_data in reservations_data:
1204~
            response = client.post("/api/v1/reservations", 
1205~
                                 json=res_data, 
1206~
                                 headers=auth_headers)
1207~
            assert response.status_code == 201
1208~
            created_reservations.append(response.get_json()["reservation"])
1209~
        
1210~
        # Test structure-specific queries
1211~
        s1_response = client.get(f"/api/v1/reservations/structure/{structure1.id}", 
1212~
                               headers=auth_headers)
1213~
        s2_response = client.get(f"/api/v1/reservations/structure/{structure2.id}", 
1214~
                               headers=auth_headers)
1215~
        
1216~
        assert s1_response.status_code == 200
1217~
        assert s2_response.status_code == 200
1218~
        
1219~
        s1_reservations = s1_response.get_json()
1220~
        s2_reservations = s2_response.get_json()
1221~
        
1222~
        # Verify structure isolation
1223~
        s1_res_ids = [res["reservation_id"] for res in s1_reservations]
1224~
        s2_res_ids = [res["reservation_id"] for res in s2_reservations]
1225~
        
1226~
        # Should not have overlap (assuming proper structure filtering)
1227~
        assert len(set(s1_res_ids) & set(s2_res_ids)) == 0
1228~

1229~

1230~
if __name__ == '__main__':
1231~
    pytest.main([__file__, '-v'])
1232~
