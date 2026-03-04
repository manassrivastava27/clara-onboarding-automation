Here's a changelog summarizing the updates:

**Changelog:**

*   **Emergency Routing Rules:**
    *   **Added a fallback number** for emergency transfers: `403-555-9999`.
    *   The `emergency_routing_rules.order` was updated to reflect this new fallback, changing from "Immediate transfer to 403-870-8494" to "Immediate transfer to 403-870-8494, fallback to 403-555-9999".
    *   This resolves the previous "Fallback plan for emergency transfers if the primary contact doesn't answer" question.
*   **Non-Emergency Routing Rules:**
    *   **Defined specific instructions** for unsupported services: "For unsupported services like facility maintenance, do not transfer calls; inform the caller that the service is not provided."
    *   This resolves the previous "Non-emergency routing rules" question.