# Agent Task: Subscription Automation Script

My task is to build a Google Apps Script automation with the following components:

### Part 1: Main Trigger (`Code.gs`)
- Create a main function `processSheetUpdates()`.
- This function will be triggered by a time-based trigger every 5 minutes.
- The script should get the active sheet.
- It should iterate through all rows that have content.
- **Trigger Condition**: Process a row only if:
    - The 'Processed' checkbox (Column H) is **unchecked**.
    - The 'Transaction Date' (Column F) is not empty.
    - The row was last updated more than 3 minutes ago to ensure all data has been entered.

### Part 2: Core Workflow (`Code.gs`)
For each row that meets the trigger condition:
1.  Wrap the entire process for a single row in a `try...catch` block for error handling.
2.  Read all the necessary data from the row (Email, Transaction Type, etc.).
3.  **Call the Zoho CRM function**: `createZohoSubscription(rowData)`.
4.  **Call the Keycloak function**: `updateKeycloakUserRole(rowData)`.
5.  If both are successful, **mark the 'Processed' checkbox** in Column H as checked.
6.  **Call the Slack notification function**: `sendSlackSuccessNotification(rowData)`.
7.  If any part fails, log the error message to the 'Notes' column (Column I) and call `sendSlackErrorNotification(rowData, error)`. The 'Processed' checkbox should remain unchecked.

### Part 3: Configuration (`Config.gs`)
- Create a function `getCredentials()` that retrieves all API keys and URLs from `PropertiesService.getScriptProperties()`.
- This function will return an object containing all credentials.

### Part 4: Zoho CRM Logic (`ZohoCRM.gs`)
- Create a function `createZohoSubscription(rowData)`.
- It must first get an access token using the refresh token.
- Find the Contact ID in Zoho CRM using the email address from the sheet.
- **Assumption**: The contact will always exist.
- Construct a payload to create a **new** 'Subscription Transaction' record. Map the columns from the Google Sheet to the corresponding fields in Zoho CRM.
- Make a POST request to the Zoho CRM API to create the record.

### Part 5: Keycloak Logic (`Keycloak.gs`)
- Create a function `updateKeycloakUserRole(rowData)`.
- It must first get an admin access token from Keycloak using the Client ID and Secret.
- Find the user's ID in Keycloak using the email address.
- Get the user's currently assigned realm roles.
- **Role Update Logic**:
    - **For 'Refund/Cancellation'**: Remove all `flophero-browse-postflopquota-*` roles from the user. Keep the `default-roles-gametrainertest` role.
    - **For all other transaction types**: 
        1. Remove all existing `flophero-browse-postflopquota-*` roles.
        2. Add the new role based on the 'Subscription Type' (Column D).
- The `default-roles-gametrainertest` role must never be removed.

### Part 6: Slack Logic (`Slack.gs`)
- Create two functions: `sendSlackSuccessNotification(rowData)` and `sendSlackErrorNotification(rowData, error)`.
- These functions will construct a payload with the required message format and send a POST request to the Slack Webhook URL.

---

## Role Mapping Reference

| Subscription Type | Keycloak Role                       |
|-------------------|-------------------------------------|
| Low Stakes        | `flophero-browse-postflopquota-low` |
| Mid Stakes        | `flophero-browse-postflopquota-mid` |
| High Stakes       | `flophero-browse-postflopquota-high`|

## Transaction Type Rules

| Transaction Type     | Action                                                        |
|----------------------|---------------------------------------------------------------|
| New Subscription     | Remove old quota roles, assign new role                       |
| Renewal              | Remove old quota roles, assign new role                       |
| Upgrade              | Remove old quota roles, assign new role                       |
| Extension            | Remove old quota roles, assign new role                       |
| Refund/Cancellation  | Remove all quota roles, keep only default role                |
