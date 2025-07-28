--- a/backend/tests/test_room_routes.py
+++ b/backend/tests/test_room_routes.py
@@ def test_add_room_database_commit_error(self, mock_get_db, client, valid_jwt_token):
-            with pytest.raises(Exception):
+            with pytest.raises(Exception, match="Database connection failed"):
@@ def test_get_rooms_database_query_error(self, mock_get_db, client, valid_jwt_token):
-        with pytest.raises(Exception):
+        with pytest.raises(Exception, match="Database connection failed"):
@@ def test_update_room_database_commit_error(self, mock_get_db, client, mock_room, valid_jwt_token):
-        with pytest.raises(Exception):
+        with pytest.raises(Exception, match="Database connection failed"):
@@ def test_delete_room_database_commit_error(self, mock_get_db, client, mock_room, valid_jwt_token):
-        with pytest.raises(Exception):
+        with pytest.raises(Exception, match="Database connection failed"):