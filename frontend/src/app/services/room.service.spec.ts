import { TestBed } from '@angular/core/testing';
import { HttpTestingController, HttpClientTestingModule } from '@angular/common/http/testing';
import { RoomService } from './room.service';  // Adjust the import as needed
import { environment } from '../../environments/environments';

describe('RoomService', () => {
  let service: RoomService;
  let httpMock: HttpTestingController;  // HTTP testing controller for mocking requests

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [],
      imports: [HttpClientTestingModule],  // Provide the HttpClientTestingModule
      providers: [RoomService]  // Provide the RoomService
    });

    service = TestBed.inject(RoomService);  // Inject the RoomService
    httpMock = TestBed.inject(HttpTestingController);  // Inject the HTTP testing controller
  });

  it('should retrieve rooms', () => {
    const dummyRooms = [
      { id: 1, name: 'Room 1', capacity: 2, id_structure: 1 },
      { id: 2, name: 'Room 2', capacity: 3, id_structure: 1 }
    ];

    service.getRooms().subscribe(rooms => {
      expect(rooms.length).toBe(2);
      expect(rooms).toEqual(dummyRooms);
    });

    // Mock the HTTP request
    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/rooms`);
    expect(req.request.method).toBe('GET');

    req.flush(dummyRooms);  // Simulate the response
  });

  afterEach(() => {
    httpMock.verify();  // Ensure no pending requests after each test
  });
});
