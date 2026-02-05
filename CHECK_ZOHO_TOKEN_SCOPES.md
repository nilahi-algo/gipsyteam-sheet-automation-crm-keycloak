# How to Check Zoho Token Scopes and Fix Missing Workflow.READ

**Issue:** The production token cannot access `/settings/workflow_rules` endpoint  
**Error:** `INVALID_REQUEST_METHOD`  
**Missing Scope:** `ZohoCRM.settings.workflow.READ`

---

## Understanding the Problem

According to your manager's screenshot, the token has:
- ✅ `ZohoCRM.modules.READ`
- ✅ `ZohoCRM.settings.ALL`

But it's **missing**:
- ❌ `ZohoCRM.settings.workflow.READ`

**Note:** Even though `ZohoCRM.settings.ALL` sounds like it should include everything, Zoho requires the specific `workflow.READ` scope for workflow rules API access.

---

## Method 1: Check Token Scopes via API (Recommended)

You can check what scopes a token has by making an API call. Here's how:

### Step 1: Get an Access Token from the Refresh Token

Use one of your refresh tokens to get an access token:

```javascript
// In Google Apps Script or any HTTP client
const tokenUrl = 'https://accounts.zoho.com/oauth/v2/token';
const payload = {
  'refresh_token': 'YOUR_REFRESH_TOKEN_HERE',
  'client_id': 'YOUR_CLIENT_ID',
  'client_secret': 'YOUR_CLIENT_SECRET',
  'grant_type': 'refresh_token'
};

// Make POST request to get access token
const response = UrlFetchApp.fetch(tokenUrl, {
  'method': 'post',
  'payload': payload
});

const responseBody = JSON.parse(response.getContentText());
const accessToken = responseBody.access_token;
```

### Step 2: Check Token Info

Once you have the access token, check its details:

```javascript
// Check token info (this shows scopes)
const infoUrl = 'https://accounts.zoho.com/oauth/user/info';
const infoResponse = UrlFetchApp.fetch(infoUrl, {
  'method': 'get',
  'headers': {
    'Authorization': 'Zoho-oauthtoken ' + accessToken
  }
});

const info = JSON.parse(infoResponse.getContentText());
Logger.log('Token Scopes: ' + JSON.stringify(info));
```

### Step 3: Test Workflow Rules Access

Try to access the workflow rules endpoint:

```javascript
// Test workflow rules access
const workflowUrl = 'https://www.zohoapis.com/crm/v2/settings/workflow_rules';
const workflowResponse = UrlFetchApp.fetch(workflowUrl, {
  'method': 'get',
  'headers': {
    'Authorization': 'Zoho-oauthtoken ' + accessToken
  },
  'muteHttpExceptions': true
});

Logger.log('Response Code: ' + workflowResponse.getResponseCode());
Logger.log('Response Body: ' + workflowResponse.getContentText());
```

**If you get `INVALID_REQUEST_METHOD` or `401/403`:** The token is missing `ZohoCRM.settings.workflow.READ` scope.

---

## Method 2: Check During Token Generation

When you generate a new token, the scopes are specified during the OAuth authorization flow. Check:

1. **Zoho API Console** → Your Client App → **Scopes**
2. Look for: `ZohoCRM.settings.workflow.READ`

If it's not listed, that's why the token doesn't have it.

---

## How to Fix: Generate New Token with Correct Scopes

### Step 1: Go to Zoho API Console

1. Log in to **https://api-console.zoho.com/**
2. Select your **Zoho CRM** application
3. Go to **Client Details** or **OAuth Scopes**

### Step 2: Add Required Scopes

Ensure these scopes are selected:
- ✅ `ZohoCRM.modules.READ`
- ✅ `ZohoCRM.modules.ALL` (or specific write scopes you need)
- ✅ `ZohoCRM.settings.ALL`
- ✅ **`ZohoCRM.settings.workflow.READ`** ← **This is the missing one!**

### Step 3: Generate New Refresh Token

1. In the API Console, click **"Generate"** or **"Authorize"**
2. You'll be redirected to Zoho authorization page
3. Select the scopes (make sure `ZohoCRM.settings.workflow.READ` is checked)
4. Authorize the application
5. Copy the **refresh token** from the callback URL or response

### Step 4: Test the New Token

Use the new refresh token to get an access token and test:

```javascript
// Test with new token
const newAccessToken = getZohoAccessToken({
  zohoRefreshToken: 'NEW_REFRESH_TOKEN',
  zohoClientId: 'YOUR_CLIENT_ID',
  zohoClientSecret: 'YOUR_CLIENT_SECRET'
});

// Try accessing workflow rules
const testUrl = 'https://www.zohoapis.com/crm/v2/settings/workflow_rules';
const testResponse = UrlFetchApp.fetch(testUrl, {
  'method': 'get',
  'headers': {
    'Authorization': 'Zoho-oauthtoken ' + newAccessToken
  },
  'muteHttpExceptions': true
});

if (testResponse.getResponseCode() === 200) {
  Logger.log('✅ SUCCESS: Token has workflow.READ scope!');
} else {
  Logger.log('❌ FAILED: ' + testResponse.getResponseCode() + ' - ' + testResponse.getContentText());
}
```

---

## Quick Test Script for Google Apps Script

Add this function to your `ZohoCRM.gs` file to test both tokens:

```javascript
/**
 * Test if a refresh token has workflow.READ scope
 * 
 * @param {string} refreshToken - The refresh token to test
 * @returns {Object} Test result with scope information
 */
function testWorkflowScope(refreshToken) {
  Logger.log('=== Testing Workflow.READ Scope ===');
  
  const credentials = getCredentials();
  
  // Get access token
  const tokenUrl = 'https://accounts.zoho.com/oauth/v2/token';
  const payload = {
    'refresh_token': refreshToken || credentials.zohoRefreshToken,
    'client_id': credentials.zohoClientId,
    'client_secret': credentials.zohoClientSecret,
    'grant_type': 'refresh_token'
  };
  
  const response = UrlFetchApp.fetch(tokenUrl, {
    'method': 'post',
    'payload': payload,
    'muteHttpExceptions': true
  });
  
  const responseBody = JSON.parse(response.getContentText());
  
  if (!responseBody.access_token) {
    return {
      success: false,
      error: 'Failed to get access token',
      details: responseBody
    };
  }
  
  const accessToken = responseBody.access_token;
  
  // Test workflow rules access
  const workflowUrl = credentials.zohoApiDomain + '/crm/v2/settings/workflow_rules';
  const workflowResponse = UrlFetchApp.fetch(workflowUrl, {
    'method': 'get',
    'headers': {
      'Authorization': 'Zoho-oauthtoken ' + accessToken
    },
    'muteHttpExceptions': true
  });
  
  const responseCode = workflowResponse.getResponseCode();
  const responseText = workflowResponse.getContentText();
  
  if (responseCode === 200) {
    Logger.log('✅ Token HAS workflow.READ scope');
    return {
      success: true,
      hasWorkflowScope: true,
      responseCode: responseCode
    };
  } else {
    Logger.log('❌ Token MISSING workflow.READ scope');
    Logger.log('Response Code: ' + responseCode);
    Logger.log('Response: ' + responseText);
    return {
      success: false,
      hasWorkflowScope: false,
      responseCode: responseCode,
      error: responseText
    };
  }
}

/**
 * Test both tokens from 1Password
 * Run this to check which token(s) are missing the scope
 */
function testBothTokens() {
  Logger.log('=== Testing Token 1 ===');
  // Replace with your first token from 1Password
  const token1 = 'TOKEN_1_FROM_1PASSWORD';
  const result1 = testWorkflowScope(token1);
  
  Logger.log('=== Testing Token 2 ===');
  // Replace with your second token from 1Password
  const token2 = 'TOKEN_2_FROM_1PASSWORD';
  const result2 = testWorkflowScope(token2);
  
  Logger.log('\n=== SUMMARY ===');
  Logger.log('Token 1 has workflow.READ: ' + result1.hasWorkflowScope);
  Logger.log('Token 2 has workflow.READ: ' + result2.hasWorkflowScope);
  
  return {
    token1: result1,
    token2: result2
  };
}
```

---

## Required Scopes Summary

For accessing Zoho CRM Workflow Rules API, you need:

| Scope | Purpose | Required? |
|-------|---------|----------|
| `ZohoCRM.modules.READ` | Read CRM modules (Contacts, Deals, etc.) | ✅ Yes |
| `ZohoCRM.settings.ALL` | General settings access | ✅ Yes |
| `ZohoCRM.settings.workflow.READ` | **Read workflow rules** | ✅ **Yes (Missing!)** |

---

## Next Steps

1. **Test both tokens** using the script above
2. **Identify which token(s) are missing** the `workflow.READ` scope
3. **Generate new token(s)** with the correct scopes from Zoho API Console
4. **Update the token** in your 1Password vault
5. **Test again** to confirm it works

---

## Reference Links

- [Zoho CRM API - Workflow Rules](https://www.zoho.com/crm/developer/docs/api/v2/workflow-rules.html)
- [Zoho OAuth Scopes Documentation](https://www.zoho.com/crm/developer/docs/api/v2/oauth-overview.html)
- [Zoho API Console](https://api-console.zoho.com/)
