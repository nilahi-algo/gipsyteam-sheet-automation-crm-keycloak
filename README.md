# Google Sheet Subscription Automation

This script automates the process of updating Zoho CRM and Keycloak based on new entries in a Google Sheet.

## Overview

When a new subscription entry is detected in the Google Sheet, this automation will:
1. Create a new "Subscription Transaction" record in Zoho CRM
2. Update the user's roles in Keycloak based on the subscription type
3. Send a success or failure notification to Slack
4. Mark the row in the Google Sheet as "Processed"

## Google Sheet Structure

Your Google Sheet must have the following columns:

| Column | Field Name          | Data Type  | Description                                      |
|--------|---------------------|------------|--------------------------------------------------|
| A      | ID                  | Number     | Unique identifier                                |
| B      | Email               | Text       | User email address (primary identifier)          |
| C      | Transaction Type    | Dropdown   | New Subscription, Renewal, Upgrade, Refund/Cancellation, Extension |
| D      | Subscription Type   | Dropdown   | Low Stakes, Mid Stakes, High Stakes              |
| E      | Billing Cycle       | Dropdown   | Monthly, Annual, Custom                          |
| F      | Transaction Date    | Date       | Date of the transaction                          |
| G      | Renewal Date        | Date       | Date of renewal                                  |
| H      | Processed           | Checkbox   | Marks if the row has been processed              |
| I      | Notes               | Text       | For error messages or additional notes           |

## Setup Instructions

### Step 1: Open the Script Editor

In your Google Sheet, go to `Extensions > Apps Script`.

### Step 2: Create the Script Files

Create the following files in the Apps Script editor:
- `Code.gs`
- `Config.gs`
- `ZohoCRM.gs`
- `Keycloak.gs`
- `Slack.gs`

Copy the code from each corresponding file in this repository.

### Step 3: Configure Script Properties

1. In the Apps Script editor, go to `Project Settings` (the gear icon ⚙️).
2. Scroll down to **Script Properties** and click **"Add script property"**.
3. Add the following properties with your credentials:

| Property Name             | Value                                                    |
|---------------------------|----------------------------------------------------------|
| `ZOHO_CLIENT_ID`          | Your Zoho Client ID                                      |
| `ZOHO_CLIENT_SECRET`      | Your Zoho Client Secret                                  |
| `ZOHO_REFRESH_TOKEN`      | Your Zoho Refresh Token                                  |
| `ZOHO_API_DOMAIN`         | `https://www.zohoapis.com`                               |
| `KEYCLOAK_SERVER_URL`     | `https://accounts.algosoftware.io`                       |
| `KEYCLOAK_REALM`          | `GametrainerTest`                                        |
| `KEYCLOAK_CLIENT_ID`      | `gametrainertest`                                        |
| `KEYCLOAK_CLIENT_SECRET`  | Your Keycloak Client Secret                              |
| `SLACK_WEBHOOK_URL`       | Your Slack Webhook URL                                   |

### Step 4: Set Up the Trigger

1. In the Apps Script editor, go to `Triggers` (the clock icon ⏰).
2. Click **"+ Add Trigger"**.
3. Configure the trigger as follows:
   - **Choose which function to run**: `processSheetUpdates`
   - **Select event source**: `Time-driven`
   - **Select type of time-based trigger**: `Minutes timer`
   - **Select minute interval**: `Every 5 minutes`
4. Click **"Save"**.

### Step 5: Authorize the Script

The first time you run the script (or set up the trigger), Google will ask you to authorize it. Follow the on-screen instructions to grant the necessary permissions.

Your automation is now live!

---

## Testing Guide

### Testing the Zoho CRM Connection

1. In the Apps Script editor, create a temporary test function:

```javascript
function testZohoConnection() {
  const credentials = getCredentials();
  const accessToken = getZohoAccessToken(credentials);
  Logger.log('Zoho Access Token: ' + (accessToken ? 'SUCCESS' : 'FAILED'));
  
  // Test finding a contact
  const testEmail = 'test@example.com'; // Replace with a real email
  const contactId = findZohoContactByEmail(accessToken, testEmail, credentials);
  Logger.log('Contact ID: ' + contactId);
}
```

2. Run the function and check the **Logs** (`View > Logs`).

### Testing the Keycloak Connection

1. Create a temporary test function:

```javascript
function testKeycloakConnection() {
  const credentials = getCredentials();
  const accessToken = getKeycloakAccessToken(credentials);
  Logger.log('Keycloak Access Token: ' + (accessToken ? 'SUCCESS' : 'FAILED'));
  
  // Test finding a user
  const testEmail = 'test@example.com'; // Replace with a real email
  const userId = findKeycloakUserByEmail(accessToken, testEmail, credentials);
  Logger.log('User ID: ' + userId);
}
```

2. Run the function and check the **Logs**.

### Testing the Slack Notification

1. Create a temporary test function:

```javascript
function testSlackNotification() {
  const testData = {
    email: 'test@example.com',
    transactionType: 'New Subscription',
    subscriptionType: 'Mid Stakes',
    billingCycle: 'Monthly',
    transactionDate: new Date()
  };
  
  sendSlackSuccessNotification(testData);
  Logger.log('Slack notification sent!');
}
```

2. Run the function and check your Slack channel.

### Manual Trigger Test

Before setting up the automatic trigger, you can manually test the full workflow:

1. Add a test row to your Google Sheet with all required data.
2. Make sure the "Processed" checkbox is unchecked.
3. Wait 3 minutes (to satisfy the delay requirement).
4. In the Apps Script editor, select `processSheetUpdates` from the function dropdown.
5. Click the **Run** button (▶️).
6. Check the **Logs** and your Slack channel for results.

---

## Troubleshooting

### Common Issues

1. **"Invalid grant" error from Zoho**: Your refresh token may have expired. Generate a new one from the Zoho API Console.

2. **"401 Unauthorized" from Keycloak**: Check that your client credentials are correct and the client has the proper service account roles.

3. **Rows not being processed**: Ensure the Transaction Date (Column F) is filled and the row was modified more than 3 minutes ago.

4. **Slack notifications not arriving**: Verify your webhook URL is correct and the Slack app is properly installed.

### Checking Logs

To view execution logs:
1. Go to `Executions` in the Apps Script editor
2. Click on a specific execution to see detailed logs
3. Use `Logger.log()` statements for debugging

---

## Important Notes

- **All contacts must exist in Zoho CRM**: The script assumes the contact already exists.
- **All users must exist in Keycloak**: The script assumes the user already exists.
- **New transactions only**: The script always creates new Subscription Transaction records, never updates existing ones.
- **Role protection**: The `default-roles-gametrainertest` role is never removed from users.
- **3-minute delay**: Rows are only processed if they were last modified more than 3 minutes ago.

---

## Support

If you encounter issues, please check:
1. The execution logs in Apps Script
2. The Notes column (Column I) for error messages
3. Your Slack channel for error notifications
