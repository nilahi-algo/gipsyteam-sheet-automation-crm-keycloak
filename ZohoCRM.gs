/**
 * ZohoCRM.gs
 * 
 * Library file for all Zoho CRM related functions.
 * Handles OAuth authentication, contact lookup, and subscription transaction creation.
 */

/**
 * Gets an access token from Zoho using the refresh token.
 * 
 * @param {Object} credentials - The credentials object from getCredentials()
 * @returns {string} The access token
 * @throws {Error} If token retrieval fails
 */
function getZohoAccessToken(credentials) {
  const tokenUrl = 'https://accounts.zoho.com/oauth/v2/token';
  
  const payload = {
    'refresh_token': credentials.zohoRefreshToken,
    'client_id': credentials.zohoClientId,
    'client_secret': credentials.zohoClientSecret,
    'grant_type': 'refresh_token'
  };
  
  const options = {
    'method': 'post',
    'payload': payload,
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(tokenUrl, options);
  const responseCode = response.getResponseCode();
  const responseBody = JSON.parse(response.getContentText());
  
  if (responseCode !== 200 || responseBody.error) {
    const errorMessage = responseBody.error || 'Failed to get Zoho access token';
    Logger.log('Zoho token error: ' + JSON.stringify(responseBody));
    throw new Error('Zoho OAuth Error: ' + errorMessage);
  }
  
  return responseBody.access_token;
}

/**
 * Finds a contact in Zoho CRM by email address.
 * 
 * @param {string} accessToken - Valid Zoho access token
 * @param {string} email - Email address to search for
 * @param {Object} credentials - The credentials object
 * @returns {string} The contact ID
 * @throws {Error} If contact is not found
 */
function findZohoContactByEmail(accessToken, email, credentials) {
  const searchUrl = credentials.zohoApiDomain + '/crm/v2/Contacts/search?email=' + encodeURIComponent(email);
  
  const options = {
    'method': 'get',
    'headers': {
      'Authorization': 'Zoho-oauthtoken ' + accessToken
    },
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(searchUrl, options);
  const responseCode = response.getResponseCode();
  const responseBody = JSON.parse(response.getContentText());
  
  if (responseCode !== 200) {
    Logger.log('Zoho search error: ' + JSON.stringify(responseBody));
    throw new Error('Failed to search for contact in Zoho CRM');
  }
  
  if (!responseBody.data || responseBody.data.length === 0) {
    throw new Error('Contact not found in Zoho CRM for email: ' + email);
  }
  
  return responseBody.data[0].id;
}

/**
 * Finds a product in Zoho CRM by combining subscription type and billing cycle.
 * 
 * @param {string} accessToken - Valid Zoho access token
 * @param {string} subscriptionType - Subscription type (Low Stakes, Mid Stakes, High Stakes)
 * @param {string} billingCycle - Billing cycle (Monthly, Annual, Custom)
 * @param {Object} credentials - The credentials object
 * @returns {Object} An object with product id and name: {id: string, name: string}
 * @throws {Error} If product is not found
 */
function findZohoProductBySubscriptionAndCycle(accessToken, subscriptionType, billingCycle, credentials) {
  // Handle "Custom" billing cycle - default to Monthly
  let actualBillingCycle = billingCycle;
  if (billingCycle === 'Custom') {
    Logger.log('Billing cycle is "Custom" - defaulting to "Monthly"');
    actualBillingCycle = 'Monthly';
  }
  
  // Build the product name based on subscription type and billing cycle
  // Format: "{Subscription Type} - {Monthly|Annually}"
  const billingFrequency = actualBillingCycle === 'Monthly' ? 'Monthly' : 'Annually';
  const productName = subscriptionType + ' - ' + billingFrequency;
  
  Logger.log('Looking for product: ' + productName);
  
  // Search for the product
  const searchUrl = credentials.zohoApiDomain + '/crm/v2/Products/search?criteria=(Product_Name:equals:' + encodeURIComponent(productName) + ')';
  
  const options = {
    'method': 'get',
    'headers': {
      'Authorization': 'Zoho-oauthtoken ' + accessToken
    },
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(searchUrl, options);
  const responseCode = response.getResponseCode();
  
  // If no results, try fetching all products and searching manually
  if (responseCode === 204) {
    Logger.log('Search returned no results, fetching all products...');
    const allProductsUrl = credentials.zohoApiDomain + '/crm/v2/Products';
    const allResponse = UrlFetchApp.fetch(allProductsUrl, options);
    const allResponseBody = JSON.parse(allResponse.getContentText());
    
    if (allResponseBody.data) {
      const matchingProduct = allResponseBody.data.find(function(product) {
        return product.Product_Name === productName;
      });
      
      if (matchingProduct) {
        Logger.log('Found product ID: ' + matchingProduct.id);
        return {
          id: matchingProduct.id,
          name: matchingProduct.Product_Name
        };
      }
    }
    
    throw new Error('Product not found in Zoho CRM: ' + productName);
  }
  
  const responseBody = JSON.parse(response.getContentText());
  
  if (!responseBody.data || responseBody.data.length === 0) {
    throw new Error('Product not found in Zoho CRM: ' + productName);
  }
  
  Logger.log('Found product ID: ' + responseBody.data[0].id);
  return {
    id: responseBody.data[0].id,
    name: responseBody.data[0].Product_Name
  };
}

/**
 * Creates a new Subscription Transaction record in Zoho CRM.
 * 
 * @param {Object} rowData - The data from the Google Sheet row
 * @param {string} rowData.email - User's email address
 * @param {string} rowData.transactionType - Type of transaction
 * @param {string} rowData.subscriptionType - Type of subscription (Low/Mid/High Stakes)
 * @param {string} rowData.billingCycle - Billing cycle (Monthly/Annual/Custom)
 * @param {Date} rowData.transactionDate - Date of transaction
 * @param {Date} rowData.renewalDate - Date of renewal
 * @returns {Object} Result object with success status and record ID
 * @throws {Error} If creation fails
 */
function createZohoSubscription(rowData) {
  const credentials = getCredentials();
  
  // Step 1: Get access token
  Logger.log('Getting Zoho access token...');
  const accessToken = getZohoAccessToken(credentials);
  
  // Step 2: Find contact by email
  Logger.log('Finding contact for email: ' + rowData.email);
  const contactId = findZohoContactByEmail(accessToken, rowData.email, credentials);
  Logger.log('Found contact ID: ' + contactId);
  
  // Step 3: Find product by subscription type AND billing cycle
  Logger.log('Finding product for: ' + rowData.subscriptionType + ' - ' + rowData.billingCycle);
  const productInfo = findZohoProductBySubscriptionAndCycle(
    accessToken, 
    rowData.subscriptionType, 
    rowData.billingCycle, 
    credentials
  );
  const productId = productInfo.id;
  const productName = productInfo.name;
  Logger.log('Found product ID: ' + productId);
  Logger.log('Found product Name: ' + productName);
  
  // Step 4: Format dates
  const transactionDateFormatted = formatDateForZoho(rowData.transactionDate);
  const renewalDateFormatted = rowData.renewalDate ? formatDateForZoho(rowData.renewalDate) : null;
  
  // Step 5: Create the subscription transaction name (use product name)
  const transactionName = productName; // Use the product name directly
  
  // Step 6: Build the payload
  const payload = {
    'data': [
      {
        'Name': transactionName,
        'Contact': {
          'id': contactId
        },
        'Transaction_Type': rowData.transactionTypeForZoho,  // Use mapped value
        'Plan_Name': {
          'id': productId
        },
        'Frequency': rowData.billingCycle,
        'Transaction_Date': transactionDateFormatted,
        'Subscription_Renewal_Date': renewalDateFormatted,
        'Plan_Type': rowData.planTypeForZoho,  // Add the mapped Plan Type
        'Subscription_Transaction_Date': transactionDateFormatted  // Add the transaction date
      }
    ]
  };
  
  // Step 7: Create the record
  const createUrl = credentials.zohoApiDomain + '/crm/v2/Subscription_Transactions';
  
  const options = {
    'method': 'post',
    'headers': {
      'Authorization': 'Zoho-oauthtoken ' + accessToken,
      'Content-Type': 'application/json'
    },
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };
  
  Logger.log('Creating subscription transaction...');
  const response = UrlFetchApp.fetch(createUrl, options);
  const responseCode = response.getResponseCode();
  const responseBody = JSON.parse(response.getContentText());
  
  if (responseCode !== 200 && responseCode !== 201) {
    Logger.log('Zoho create error: ' + JSON.stringify(responseBody));
    const errorDetails = responseBody.data && responseBody.data[0] && responseBody.data[0].details 
      ? JSON.stringify(responseBody.data[0].details) 
      : JSON.stringify(responseBody);
    throw new Error('Failed to create subscription transaction in Zoho CRM: ' + errorDetails);
  }
  
  // Check for record-level errors
  if (responseBody.data && responseBody.data[0] && responseBody.data[0].status === 'error') {
    throw new Error('Zoho CRM Error: ' + responseBody.data[0].message);
  }
  
  const recordId = responseBody.data[0].details.id;
  Logger.log('Successfully created subscription transaction. ID: ' + recordId);
  
  return {
    success: true,
    recordId: recordId
  };
}

/**
 * Formats a date for Zoho CRM API (YYYY-MM-DD format).
 * 
 * @param {Date|string} date - The date to format
 * @returns {string} Formatted date string
 */
function formatDateForZoho(date) {
  if (!date) return null;
  
  const dateObj = (date instanceof Date) ? date : new Date(date);
  
  if (isNaN(dateObj.getTime())) {
    return null;
  }
  
  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, '0');
  const day = String(dateObj.getDate()).padStart(2, '0');
  
  return year + '-' + month + '-' + day;
}

/**
 * Test function to verify if the Zoho refresh token is valid and working.
 * This function only checks the token validity - it does NOT make any changes to Zoho data.
 * 
 * @param {string} refreshToken - Optional refresh token to test. If not provided, uses token from Script Properties.
 * @returns {Object} Test result with status, token type, expiration info, and details
 */
function testZohoRefreshToken(refreshToken) {
  Logger.log('=== Testing Zoho Refresh Token ===');
  
  const credentials = getCredentials();
  
  // Use provided token or get from credentials
  const tokenToTest = refreshToken || credentials.zohoRefreshToken;
  
  if (!tokenToTest) {
    Logger.log('❌ ERROR: No refresh token provided or found in Script Properties');
    return {
      status: 'error',
      message: 'No refresh token found',
      isRefreshToken: false,
      isValid: false
    };
  }
  
  Logger.log('Token length: ' + tokenToTest.length + ' characters');
  Logger.log('Token preview: ' + tokenToTest.substring(0, 20) + '...');
  
  // Check token format (Zoho refresh tokens are typically long alphanumeric strings)
  const tokenPattern = /^[A-Za-z0-9_-]+$/;
  const isValidFormat = tokenPattern.test(tokenToTest);
  
  Logger.log('Token format valid: ' + isValidFormat);
  
  // Try to use the token to get an access token
  const tokenUrl = 'https://accounts.zoho.com/oauth/v2/token';
  
  const payload = {
    'refresh_token': tokenToTest,
    'client_id': credentials.zohoClientId,
    'client_secret': credentials.zohoClientSecret,
    'grant_type': 'refresh_token'
  };
  
  const options = {
    'method': 'post',
    'payload': payload,
    'muteHttpExceptions': true
  };
  
  Logger.log('Attempting to exchange refresh token for access token...');
  
  try {
    const response = UrlFetchApp.fetch(tokenUrl, options);
    const responseCode = response.getResponseCode();
    const responseBody = JSON.parse(response.getContentText());
    
    if (responseCode === 200 && responseBody.access_token) {
      Logger.log('✅ SUCCESS: Refresh token is VALID and WORKING');
      Logger.log('Access token obtained successfully');
      Logger.log('Token expires in: ' + (responseBody.expires_in || 'N/A') + ' seconds');
      
      return {
        status: 'success',
        isRefreshToken: true,
        isValid: true,
        expires: false, // Refresh tokens don't expire unless revoked
        expiresIn: null, // Refresh tokens don't have expiration
        accessTokenExpiresIn: responseBody.expires_in || null,
        message: 'Refresh token is valid and working. Refresh tokens do not expire unless revoked.',
        details: {
          tokenLength: tokenToTest.length,
          canGetAccessToken: true,
          accessTokenExpiresIn: responseBody.expires_in + ' seconds'
        }
      };
    } else {
      // Check for specific error codes
      const errorCode = responseBody.error;
      const errorDescription = responseBody.error_description || responseBody.error || 'Unknown error';
      
      Logger.log('❌ ERROR: Failed to get access token');
      Logger.log('Response code: ' + responseCode);
      Logger.log('Error: ' + errorCode);
      Logger.log('Error description: ' + errorDescription);
      
      let expires = false;
      let message = '';
      
      if (errorCode === 'invalid_grant' || errorCode === 'invalid_client') {
        message = 'Refresh token is invalid or has been revoked. It may have expired or been regenerated.';
        expires = true; // Effectively expired/revoked
      } else if (errorCode === 'invalid_request') {
        message = 'Invalid request - check client ID and client secret.';
      } else {
        message = 'Token validation failed: ' + errorDescription;
      }
      
      return {
        status: 'error',
        isRefreshToken: true, // It's a refresh token format, but invalid
        isValid: false,
        expires: expires,
        message: message,
        errorCode: errorCode,
        errorDescription: errorDescription,
        details: {
          tokenLength: tokenToTest.length,
          canGetAccessToken: false,
          httpStatusCode: responseCode
        }
      };
    }
  } catch (error) {
    Logger.log('❌ EXCEPTION: ' + error.message);
    return {
      status: 'error',
      isRefreshToken: true,
      isValid: false,
      expires: false,
      message: 'Exception occurred while testing token: ' + error.message,
      details: {
        tokenLength: tokenToTest.length,
        exception: error.message
      }
    };
  }
}

/**
 * Test if a refresh token has workflow.READ scope by attempting to access workflow rules API.
 * 
 * @param {string} refreshToken - Optional refresh token to test. If not provided, uses token from Script Properties.
 * @returns {Object} Test result with workflow scope information
 */
function testZohoWorkflowScope(refreshToken) {
  Logger.log('=== Testing Zoho Workflow.READ Scope ===');
  
  const credentials = getCredentials();
  
  // Use provided token or get from credentials
  const tokenToTest = refreshToken || credentials.zohoRefreshToken;
  
  if (!tokenToTest) {
    Logger.log('❌ ERROR: No refresh token provided or found in Script Properties');
    return {
      status: 'error',
      hasWorkflowScope: false,
      message: 'No refresh token found'
    };
  }
  
  try {
    // Step 1: Get access token
    Logger.log('Getting access token...');
    const accessToken = getZohoAccessToken({
      zohoRefreshToken: tokenToTest,
      zohoClientId: credentials.zohoClientId,
      zohoClientSecret: credentials.zohoClientSecret,
      zohoApiDomain: credentials.zohoApiDomain
    });
    
    if (!accessToken) {
      return {
        status: 'error',
        hasWorkflowScope: false,
        message: 'Failed to get access token'
      };
    }
    
    // Step 2: Test workflow rules access
    Logger.log('Testing workflow rules API access...');
    const workflowUrl = credentials.zohoApiDomain + '/crm/v2/settings/workflow_rules';
    
    const options = {
      'method': 'get',
      'headers': {
        'Authorization': 'Zoho-oauthtoken ' + accessToken
      },
      'muteHttpExceptions': true
    };
    
    const response = UrlFetchApp.fetch(workflowUrl, options);
    const responseCode = response.getResponseCode();
    const responseBody = response.getContentText();
    
    if (responseCode === 200) {
      Logger.log('✅ SUCCESS: Token HAS workflow.READ scope!');
      Logger.log('Workflow rules accessible');
      return {
        status: 'success',
        hasWorkflowScope: true,
        responseCode: responseCode,
        message: 'Token has ZohoCRM.settings.workflow.READ scope'
      };
    } else {
      Logger.log('❌ FAILED: Token MISSING workflow.READ scope');
      Logger.log('Response Code: ' + responseCode);
      Logger.log('Response: ' + responseBody);
      
      let errorMessage = 'Token does not have ZohoCRM.settings.workflow.READ scope';
      if (responseCode === 400 || responseBody.includes('INVALID_REQUEST_METHOD')) {
        errorMessage = 'INVALID_REQUEST_METHOD - Missing ZohoCRM.settings.workflow.READ scope';
      } else if (responseCode === 401 || responseCode === 403) {
        errorMessage = 'Unauthorized/Forbidden - Missing required scope';
      }
      
      return {
        status: 'error',
        hasWorkflowScope: false,
        responseCode: responseCode,
        error: responseBody,
        message: errorMessage
      };
    }
  } catch (error) {
    Logger.log('❌ EXCEPTION: ' + error.message);
    return {
      status: 'error',
      hasWorkflowScope: false,
      message: 'Exception occurred: ' + error.message
    };
  }
}

/**
 * Test both tokens to identify which one(s) are missing workflow.READ scope.
 * Replace TOKEN_1 and TOKEN_2 with your actual tokens from 1Password.
 * 
 * @returns {Object} Test results for both tokens
 */
function testBothZohoTokens() {
  Logger.log('=== Testing Both Zoho Tokens for Workflow.READ Scope ===\n');
  
  // TODO: Replace these with your actual tokens from 1Password
  const TOKEN_1 = 'REPLACE_WITH_TOKEN_1_FROM_1PASSWORD';
  const TOKEN_2 = 'REPLACE_WITH_TOKEN_2_FROM_1PASSWORD';
  
  Logger.log('=== Testing Token 1 ===');
  const result1 = testZohoWorkflowScope(TOKEN_1);
  
  Logger.log('\n=== Testing Token 2 ===');
  const result2 = testZohoWorkflowScope(TOKEN_2);
  
  Logger.log('\n=== SUMMARY ===');
  Logger.log('Token 1 has workflow.READ scope: ' + (result1.hasWorkflowScope ? '✅ YES' : '❌ NO'));
  if (!result1.hasWorkflowScope) {
    Logger.log('Token 1 Error: ' + result1.message);
  }
  
  Logger.log('Token 2 has workflow.READ scope: ' + (result2.hasWorkflowScope ? '✅ YES' : '❌ NO'));
  if (!result2.hasWorkflowScope) {
    Logger.log('Token 2 Error: ' + result2.message);
  }
  
  return {
    token1: result1,
    token2: result2,
    summary: {
      token1HasScope: result1.hasWorkflowScope,
      token2HasScope: result2.hasWorkflowScope,
      bothHaveScope: result1.hasWorkflowScope && result2.hasWorkflowScope,
      bothMissingScope: !result1.hasWorkflowScope && !result2.hasWorkflowScope
    }
  };
}
