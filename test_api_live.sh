#!/bin/bash
# Live end-to-end test of every API endpoint from the assignment.
set -e
BASE="http://127.0.0.1:8000"
PY="/d/PROJECTS/WhatBytes assignment/.venv/Scripts/python"

jget() { "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d$1)"; }

# Wait for server
for i in $(seq 1 30); do curl -s -o /dev/null "$BASE/admin/" && break; sleep 1; done

echo "== 1. Register alice =="
curl -s -X POST "$BASE/api/auth/register/" -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"alicepass123"}' | "$PY" -m json.tool

echo "== 2. Register bob =="
curl -s -X POST "$BASE/api/auth/register/" -H "Content-Type: application/json" \
  -d '{"name":"Bob","email":"bob@example.com","password":"bobpass123"}' | "$PY" -m json.tool

echo "== 3. Duplicate email rejected =="
curl -s -X POST "$BASE/api/auth/register/" -H "Content-Type: application/json" \
  -d '{"name":"Alice2","email":"alice@example.com","password":"alicepass123"}' | "$PY" -m json.tool

echo "== 4. Invalid register (no name, short password) =="
curl -s -X POST "$BASE/api/auth/register/" -H "Content-Type: application/json" \
  -d '{"email":"x@example.com","password":"short"}' | "$PY" -m json.tool

echo "== 5. Login alice -> JWT =="
LOGIN=$(curl -s -X POST "$BASE/api/auth/login/" -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"alicepass123"}')
echo "$LOGIN" | "$PY" -m json.tool
ACCESS=$(echo "$LOGIN" | jget "['access']")

echo "== 6. Wrong password rejected =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "$BASE/api/auth/login/" -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"wrongpass1"}'

echo "== 7. Patients without token -> 401 =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$BASE/api/patients/"

AUTH="Authorization: Bearer $ACCESS"
CT="Content-Type: application/json"

echo "== 8. Alice creates patient =="
PAT=$(curl -s -X POST "$BASE/api/patients/" -H "$AUTH" -H "$CT" \
  -d '{"name":"John Doe","age":45,"gender":"male","phone":"9876543210","address":"12 Main St","medical_history":"Diabetes"}')
echo "$PAT" | "$PY" -m json.tool
PATID=$(echo "$PAT" | jget "['id']")

echo "== 9. Invalid patient (age 999, bad phone) -> 400 =="
curl -s -X POST "$BASE/api/patients/" -H "$AUTH" -H "$CT" \
  -d '{"name":"Bad","age":999,"gender":"male","phone":"abc"}' | "$PY" -m json.tool

echo "== 10. GET all patients (alice) =="
curl -s "$BASE/api/patients/" -H "$AUTH" | "$PY" -m json.tool

echo "== 11. GET patient detail =="
curl -s "$BASE/api/patients/$PATID/" -H "$AUTH" | "$PY" -m json.tool

echo "== 12. PUT update patient =="
curl -s -X PUT "$BASE/api/patients/$PATID/" -H "$AUTH" -H "$CT" \
  -d '{"name":"John Doe Jr","age":46,"gender":"male","phone":"9876543211","address":"12 Main St","medical_history":"Diabetes, controlled"}' | "$PY" -m json.tool

echo "== 13. Bob cannot see Alice's patient -> 404 =="
LOGIN_B=$(curl -s -X POST "$BASE/api/auth/login/" -H "$CT" -d '{"email":"bob@example.com","password":"bobpass123"}')
ACCESS_B=$(echo "$LOGIN_B" | jget "['access']")
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$BASE/api/patients/$PATID/" -H "Authorization: Bearer $ACCESS_B"

echo "== 14. Bob creates doctor =="
DOC=$(curl -s -X POST "$BASE/api/doctors/" -H "Authorization: Bearer $ACCESS_B" -H "$CT" \
  -d '{"name":"Dr. Smith","specialization":"Cardiology","phone":"1234567890","email":"smith@hospital.com"}')
echo "$DOC" | "$PY" -m json.tool
DOCID=$(echo "$DOC" | jget "['id']")

echo "== 15. GET all doctors (alice sees Bob's doctor) =="
curl -s "$BASE/api/doctors/" -H "$AUTH" | "$PY" -m json.tool

echo "== 16. GET doctor detail =="
curl -s "$BASE/api/doctors/$DOCID/" -H "$AUTH" | "$PY" -m json.tool

echo "== 17. Alice cannot edit Bob's doctor -> 403 =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X PUT "$BASE/api/doctors/$DOCID/" -H "$AUTH" -H "$CT" \
  -d '{"name":"Dr. Smith","specialization":"Neurology"}'

echo "== 18. Alice creates her own doctor and updates it =="
DOC2=$(curl -s -X POST "$BASE/api/doctors/" -H "$AUTH" -H "$CT" \
  -d '{"name":"Dr. Lee","specialization":"Dermatology"}')
DOC2ID=$(echo "$DOC2" | jget "['id']")
curl -s -X PUT "$BASE/api/doctors/$DOC2ID/" -H "$AUTH" -H "$CT" \
  -d '{"name":"Dr. Lee","specialization":"Pediatrics"}' | "$PY" -m json.tool

echo "== 19. Assign Dr. Smith to John =="
MAP=$(curl -s -X POST "$BASE/api/mappings/" -H "$AUTH" -H "$CT" \
  -d "{\"patient\":$PATID,\"doctor\":$DOCID}")
echo "$MAP" | "$PY" -m json.tool
MAPID=$(echo "$MAP" | jget "['id']")

echo "== 20. Duplicate mapping -> 400 =="
curl -s -X POST "$BASE/api/mappings/" -H "$AUTH" -H "$CT" \
  -d "{\"patient\":$PATID,\"doctor\":$DOCID}" | "$PY" -m json.tool

echo "== 21. Alice cannot map Bob's patient -> 400 =="
PBOB=$(curl -s -X POST "$BASE/api/patients/" -H "Authorization: Bearer $ACCESS_B" -H "$CT" \
  -d '{"name":"Bob Patient","age":20,"gender":"female"}')
PBOBID=$(echo "$PBOB" | jget "['id']")
curl -s -X POST "$BASE/api/mappings/" -H "$AUTH" -H "$CT" \
  -d "{\"patient\":$PBOBID,\"doctor\":$DOCID}" | "$PY" -m json.tool

echo "== 22. GET all mappings (alice) =="
curl -s "$BASE/api/mappings/" -H "$AUTH" | "$PY" -m json.tool

echo "== 23. GET doctors for patient $PATID =="
curl -s "$BASE/api/mappings/$PATID/" -H "$AUTH" | "$PY" -m json.tool

echo "== 24. DELETE mapping $MAPID =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X DELETE "$BASE/api/mappings/$MAPID/" -H "$AUTH"

echo "== 25. Mappings now empty =="
curl -s "$BASE/api/mappings/$PATID/" -H "$AUTH" | "$PY" -m json.tool

echo "== 26. DELETE patient =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X DELETE "$BASE/api/patients/$PATID/" -H "$AUTH"

echo "== 27. DELETE doctor (alice's own) =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X DELETE "$BASE/api/doctors/$DOC2ID/" -H "$AUTH"

echo "== 28. Bob cannot delete... alice's doctor already deleted; check Bob's doctor delete by alice -> 403 =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X DELETE "$BASE/api/doctors/$DOCID/" -H "$AUTH"

echo "ALL CHECKS DONE"
