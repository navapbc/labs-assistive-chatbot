# API Specification: Assistive Chatbot Integration

This API enables integration of the Assistive Chatbot with other products.

## Endpoint: `POST /query`

Accepts a user query and responds with a generated answer from the chatbot, along with relevant citations. Each response includes optional auditing fields to monitor usage by user, organization, and end-customer.

### `/query` request parameters

Optional identifiers (for auditing and usage tracking):

- **user_id** _(string, optional)_: Unique identifier for the user making the request.
- **org_id** _(string, optional)_: Identifier for the organization the user belongs to.
- **customer_id** _(string, optional)_: Anonymized ID for an end-customer associated with the query, if applicable and distinct from `user_id`.

Required fields:

- **session_id** _(string, required)_: Unique identifier for the current session, used to track prior messages in the conversation.
- **new_session** _(bool, required)_: Whether the `session_id` is expected to be new to the server.
- **message** _(string, required)_: The user's question for the chatbot, plus any prior messages in the conversation.

### `/query` responses

Success response body (200 OK):

```json
{
  "response_id": "string",                   // Unique identifier for the chatbot response
  "response_text": "string",                 // Generated answer from the chatbot in Markdown format
  "citations": [                             // Ordered list of citations with mappings to the Markdown response text
    {
      "citation_id": "string",               // Unique ID for each citation
      "source_id": "string",                 // Identifier for the source document
      "source_name": "string",               // Name of the source document
      "page_number": "integer" | null,       // Page number where the citation is found, if available
      "uri": "string",                       // URL link to the source, if available
      "headings": ["string"],                // Headings within the document, if available
      "citation_text": "string"              // Extracted citation text
    }
  ]
}
```

Error responses:

- **400 Bad Request**: Missing or invalid parameters.
- **500 Internal Server Error**: Generic server error.

### `/query` example

Request:

```json
{
  "user_id": "user12345",
  "org_id": "org789",
  "customer_id": "cust001",
  "session_id": "sess2024A",
  "new_session": true,
  "message": "How do I reset my account password?"
}
```

Response:

```json
{
  "response_id": "resp6789",
  "response_text": "To reset your account password:\n\n- Navigate to the login page and click **Forgot password**.(citation-1)\n- Enter the email address associated with your account and follow the instructions sent to your inbox.(citation-2)",
  "citations": [
    {
      "citation_id": "citation-1",
      "source_id": "doc543",
      "source_name": "Account Management Guide",
      "uri": "https://example.com/docs/account-management",
      "headings": ["Account Management", "Password Reset"],
      "citation_text": "Click the Forgot password link on the login page to begin the reset flow."
    },
    {
      "citation_id": "citation-2",
      "source_id": "doc1313",
      "source_name": "Support FAQ",
      "uri": "https://example.com/support/faq",
      "headings": ["FAQ", "Login Issues"],
      "citation_text": "You will receive an email with a link to set a new password."
    }
  ]
}
```

## Endpoint: `POST /feedback`

Accepts feedback from a user about a chatbot response.

### `/feedback` request parameters

- **session_id** _(string, required)_: Unique identifier for the current session.
- **response_id** _(string, required)_: Unique identifier for the chatbot response being rated.
- **is_positive** _(bool, required)_: Whether the chatbot response was helpful to the user.
- **user_id** _(string, optional)_: Unique identifier for the user providing feedback.
- **comment** _(string, optional)_: The user's free-text feedback comment.

### `/feedback` responses

- **200 OK**: Feedback recorded successfully.
- **400 Bad Request**: Missing or invalid parameters.
- **500 Internal Server Error**: Generic server error.

### `/feedback` example

Request:

```json
{
  "user_id": "user12345",
  "session_id": "sess2024A",
  "response_id": "resp6789",
  "is_positive": true,
  "comment": "This response was clear and helpful."
}
```
