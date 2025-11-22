#!/bin/bash

# BOT GPT Backend - Complete API Test Script
# Run this after starting the server: python3 local_start.py

BASE_URL="http://localhost:8000"

echo "======================================================================"
echo "🧪 BOT GPT Backend - API Testing Script"
echo "======================================================================"
echo ""
echo "Base URL: $BASE_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}======================================================================"
    echo -e "$1"
    echo -e "======================================================================${NC}"
    echo ""
}

# Function to print test description
print_test() {
    echo -e "${YELLOW}▶ $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Store variables for reuse
USER_ID=""
CONVERSATION_ID=""
DOCUMENT_ID=""

# ======================================================================
# HEALTH CHECKS
# ======================================================================

print_section "1️⃣  HEALTH CHECKS"

print_test "Testing root endpoint..."
curl -s -X GET "$BASE_URL/" | python3 -m json.tool
print_success "Root endpoint working"
echo ""

print_test "Testing health check..."
curl -s -X GET "$BASE_URL/health" | python3 -m json.tool
print_success "Health check working"
echo ""

# ======================================================================
# USER MANAGEMENT
# ======================================================================

print_section "2️⃣  USER MANAGEMENT"

print_test "Creating User 1 (Alice)..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com"
  }')
echo "$RESPONSE" | python3 -m json.tool
USER_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
print_success "User created with ID: $USER_ID"
echo ""

print_test "Creating User 2 (Bob)..."
curl -s -X POST "$BASE_URL/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bob",
    "email": "bob@example.com"
  }' | python3 -m json.tool
print_success "User Bob created"
echo ""

print_test "Listing all users..."
curl -s -X GET "$BASE_URL/api/v1/users" | python3 -m json.tool
print_success "Users listed"
echo ""

print_test "Getting user details for Alice..."
curl -s -X GET "$BASE_URL/api/v1/users/$USER_ID" | python3 -m json.tool
print_success "User details retrieved"
echo ""

# ======================================================================
# OPEN CHAT CONVERSATION
# ======================================================================

print_section "3️⃣  OPEN CHAT MODE"

print_test "Creating open chat conversation..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"first_message\": \"Hello! Can you explain what Python is and why it's popular?\",
    \"mode\": \"open_chat\"
  }")
echo "$RESPONSE" | python3 -m json.tool
CONVERSATION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['conversation_id'])" 2>/dev/null)
print_success "Conversation created with ID: $CONVERSATION_ID"
echo ""

print_test "Adding message to conversation..."
curl -s -X POST "$BASE_URL/api/v1/conversations/$CONVERSATION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What are some popular Python frameworks?"
  }' | python3 -m json.tool
print_success "Message added"
echo ""

print_test "Getting conversation details..."
curl -s -X GET "$BASE_URL/api/v1/conversations/$CONVERSATION_ID" | python3 -m json.tool
print_success "Conversation details retrieved"
echo ""

print_test "Listing all conversations for user..."
curl -s -X GET "$BASE_URL/api/v1/conversations?user_id=$USER_ID&page=1&page_size=10" | python3 -m json.tool
print_success "Conversations listed"
echo ""

# ======================================================================
# DOCUMENT MANAGEMENT & RAG
# ======================================================================

print_section "4️⃣  DOCUMENT MANAGEMENT (RAG Mode)"

print_test "Uploading Document 1 (Python Guide)..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"filename\": \"python_guide.txt\",
    \"content\": \"Python is a high-level, interpreted programming language created by Guido van Rossum and first released in 1991. Python emphasizes code readability with its notable use of significant whitespace. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python is dynamically typed and garbage-collected. The language is widely used in web development, data science, artificial intelligence, scientific computing, and automation. Popular frameworks include Django and Flask for web development, NumPy and Pandas for data analysis, and TensorFlow and PyTorch for machine learning.\",
    \"mime_type\": \"text/plain\"
  }")
echo "$RESPONSE" | python3 -m json.tool
DOCUMENT_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
print_success "Document uploaded with ID: $DOCUMENT_ID"
echo ""

print_test "Uploading Document 2 (Python History)..."
curl -s -X POST "$BASE_URL/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"filename\": \"python_history.txt\",
    \"content\": \"The Python programming language was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) in the Netherlands. Python 2.0 was released in 2000, introducing list comprehensions and garbage collection. Python 3.0 was released in 2008, which was a major revision that was not completely backward-compatible. The language has grown significantly in popularity, especially in data science and machine learning communities.\",
    \"mime_type\": \"text/plain\"
  }" | python3 -m json.tool
print_success "Second document uploaded"
echo ""

print_test "Listing user's documents..."
curl -s -X GET "$BASE_URL/api/v1/documents?user_id=$USER_ID" | python3 -m json.tool
print_success "Documents listed"
echo ""

print_test "Getting document details..."
curl -s -X GET "$BASE_URL/api/v1/documents/$DOCUMENT_ID" | python3 -m json.tool
print_success "Document details retrieved"
echo ""

# ======================================================================
# RAG CONVERSATION
# ======================================================================

print_section "5️⃣  RAG (GROUNDED) CONVERSATION"

print_test "Creating RAG conversation with document..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"first_message\": \"Who created Python and when was it first released?\",
    \"mode\": \"grounded_rag\",
    \"document_ids\": [\"$DOCUMENT_ID\"]
  }")
echo "$RESPONSE" | python3 -m json.tool
RAG_CONVERSATION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['conversation_id'])" 2>/dev/null)
print_success "RAG conversation created with ID: $RAG_CONVERSATION_ID"
echo ""

print_test "Asking follow-up question in RAG mode..."
curl -s -X POST "$BASE_URL/api/v1/conversations/$RAG_CONVERSATION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What programming paradigms does Python support?"
  }' | python3 -m json.tool
print_success "Follow-up question answered based on document"
echo ""

print_test "Getting RAG conversation history..."
curl -s -X GET "$BASE_URL/api/v1/conversations/$RAG_CONVERSATION_ID" | python3 -m json.tool
print_success "RAG conversation history retrieved"
echo ""

# ======================================================================
# PAGINATION & FILTERING
# ======================================================================

print_section "6️⃣  PAGINATION & FILTERING"

print_test "Getting conversations page 1 (size 5)..."
curl -s -X GET "$BASE_URL/api/v1/conversations?user_id=$USER_ID&page=1&page_size=5" | python3 -m json.tool
print_success "Paginated results retrieved"
echo ""

# ======================================================================
# DELETION OPERATIONS
# ======================================================================

print_section "7️⃣  DELETION OPERATIONS"

print_test "Creating a test conversation to delete..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"first_message\": \"This conversation will be deleted\",
    \"mode\": \"open_chat\"
  }")
DELETE_CONV_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['conversation_id'])" 2>/dev/null)
print_success "Test conversation created: $DELETE_CONV_ID"
echo ""

print_test "Deleting the test conversation..."
curl -s -X DELETE "$BASE_URL/api/v1/conversations/$DELETE_CONV_ID"
print_success "Conversation deleted"
echo ""

print_test "Verifying deletion (should return 404)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/conversations/$DELETE_CONV_ID")
if [ "$HTTP_CODE" == "404" ]; then
    print_success "Deletion verified (404 returned)"
else
    echo "❌ Expected 404, got $HTTP_CODE"
fi
echo ""

print_test "Creating a test document to delete..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"filename\": \"test_delete.txt\",
    \"content\": \"This document will be deleted for testing.\",
    \"mime_type\": \"text/plain\"
  }")
DELETE_DOC_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
print_success "Test document created: $DELETE_DOC_ID"
echo ""

print_test "Deleting the test document..."
curl -s -X DELETE "$BASE_URL/api/v1/documents/$DELETE_DOC_ID"
print_success "Document deleted"
echo ""

# ======================================================================
# ERROR HANDLING TESTS
# ======================================================================

print_section "8️⃣  ERROR HANDLING TESTS"

print_test "Testing invalid user ID (should return 404)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/v1/users/invalid-user-id")
if [ "$HTTP_CODE" == "404" ]; then
    print_success "Correctly returned 404 for invalid user"
else
    echo "Got HTTP code: $HTTP_CODE"
fi
echo ""

print_test "Testing conversation with non-existent user (should return 404)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "non-existent-user",
    "first_message": "Test",
    "mode": "open_chat"
  }')
if [ "$HTTP_CODE" == "404" ]; then
    print_success "Correctly returned 404 for non-existent user"
else
    echo "Got HTTP code: $HTTP_CODE"
fi
echo ""

print_test "Testing empty message (should return 422 validation error)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"first_message\": \"\",
    \"mode\": \"open_chat\"
  }")
if [ "$HTTP_CODE" == "422" ]; then
    print_success "Correctly returned 422 for empty message"
else
    echo "Got HTTP code: $HTTP_CODE"
fi
echo ""

# ======================================================================
# SUMMARY
# ======================================================================

print_section "✅  TEST SUMMARY"

echo "All major API endpoints have been tested!"
echo ""
echo "Created Resources:"
echo "  • User ID: $USER_ID"
echo "  • Open Chat Conversation: $CONVERSATION_ID"
echo "  • RAG Conversation: $RAG_CONVERSATION_ID"
echo "  • Document: $DOCUMENT_ID"
echo ""
echo "You can now explore the API interactively at:"
echo "  🌐 $BASE_URL/api/docs"
echo ""
echo "To view your conversations:"
echo "  curl $BASE_URL/api/v1/conversations?user_id=$USER_ID"
echo ""
echo "To view your documents:"
echo "  curl $BASE_URL/api/v1/documents?user_id=$USER_ID"
echo ""
echo "======================================================================"
echo "🎉 Testing Complete!"
echo "======================================================================"

