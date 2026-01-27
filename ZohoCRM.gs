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
 * @returns {string} The product ID
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
        return matchingProduct.id;
      }
    }
    
    throw new Error('Product not found in Zoho CRM: ' + productName);
  }
  
  const responseBody = JSON.parse(response.getContentText());
  
  if (!responseBody.data || responseBody.data.length === 0) {
    throw new Error('Product not found in Zoho CRM: ' + productName);
  }
  
  Logger.log('Found product ID: ' + responseBody.data[0].id);
  return responseBody.data[0].id;
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
  const productId = findZohoProductBySubscriptionAndCycle(
    accessToken, 
    rowData.subscriptionType, 
    rowData.billingCycle, 
    credentials
  );
  Logger.log('Found product ID: ' + productId);
  
  // Step 4: Format dates
  const transactionDateFormatted = formatDateForZoho(rowData.transactionDate);
  const renewalDateFormatted = rowData.renewalDate ? formatDateForZoho(rowData.renewalDate) : null;
  
  // Step 5: Create the subscription transaction name
  const transactionName = rowData.email + ' - ' + rowData.transactionType + ' - ' + transactionDateFormatted;
  
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
