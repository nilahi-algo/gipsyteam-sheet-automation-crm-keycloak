/**
 * Slack.gs
 * 
 * Library file for Slack notification functions.
 * Sends success and error notifications to a designated Slack channel.
 */

/**
 * Sends a success notification to Slack.
 * 
 * @param {Object} rowData - The data from the Google Sheet row
 * @param {string} rowData.email - User's email address
 * @param {string} rowData.transactionType - Type of transaction
 * @param {string} rowData.subscriptionType - Type of subscription (Low/Mid/High Stakes)
 * @param {string} rowData.billingCycle - Billing cycle (Monthly/Annual/Custom)
 * @param {Date} rowData.transactionDate - Date of transaction
 */
function sendSlackSuccessNotification(rowData) {
  const credentials = getCredentials();
  
  if (!credentials.slackWebhookUrl) {
    Logger.log('Slack webhook URL not configured - skipping notification');
    return;
  }
  
  // Format the transaction date
  const transactionDateStr = formatDateForSlack(rowData.transactionDate);
  
  const message = '✅ Subscription Update Successful\n\n' +
    'Email: ' + rowData.email + '\n' +
    'Transaction Type: ' + rowData.transactionType + '\n' +
    'Subscription Plan: ' + rowData.subscriptionType + '\n' +
    'Billing Cycle: ' + rowData.billingCycle + '\n' +
    'Transaction Date: ' + transactionDateStr + '\n\n' +
    'Status: Updated in both Zoho CRM and Keycloak';
  
  const payload = {
    'text': message
  };
  
  sendSlackMessage(payload, credentials.slackWebhookUrl);
  Logger.log('Success notification sent to Slack');
}

/**
 * Sends an error notification to Slack.
 * 
 * @param {Object} rowData - The data from the Google Sheet row
 * @param {string} rowData.email - User's email address
 * @param {string} rowData.transactionType - Type of transaction
 * @param {string} rowData.subscriptionType - Type of subscription (Low/Mid/High Stakes)
 * @param {Error|string} error - The error that occurred
 */
function sendSlackErrorNotification(rowData, error) {
  const credentials = getCredentials();
  
  if (!credentials.slackWebhookUrl) {
    Logger.log('Slack webhook URL not configured - skipping notification');
    return;
  }
  
  // Extract error message
  const errorMessage = (error instanceof Error) ? error.message : String(error);
  
  const message = '❌ Subscription Update Failed\n\n' +
    'Email: ' + rowData.email + '\n' +
    'Transaction Type: ' + rowData.transactionType + '\n' +
    'Subscription Plan: ' + rowData.subscriptionType + '\n\n' +
    'Error: ' + errorMessage + '\n' +
    'Status: Update failed - please check manually';
  
  const payload = {
    'text': message
  };
  
  sendSlackMessage(payload, credentials.slackWebhookUrl);
  Logger.log('Error notification sent to Slack');
}

/**
 * Sends a message to Slack via webhook.
 * 
 * @param {Object} payload - The message payload
 * @param {string} webhookUrl - The Slack webhook URL
 */
function sendSlackMessage(payload, webhookUrl) {
  const options = {
    'method': 'post',
    'headers': {
      'Content-Type': 'application/json'
    },
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(webhookUrl, options);
  const responseCode = response.getResponseCode();
  
  if (responseCode !== 200) {
    const responseBody = response.getContentText();
    Logger.log('Slack notification error: ' + responseBody);
    // Don't throw error for Slack failures - just log it
    // We don't want Slack issues to break the main workflow
  }
}

/**
 * Formats a date for display in Slack messages.
 * 
 * @param {Date|string} date - The date to format
 * @returns {string} Formatted date string (YYYY-MM-DD)
 */
function formatDateForSlack(date) {
  if (!date) return 'N/A';
  
  const dateObj = (date instanceof Date) ? date : new Date(date);
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date';
  }
  
  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, '0');
  const day = String(dateObj.getDate()).padStart(2, '0');
  
  return year + '-' + month + '-' + day;
}
