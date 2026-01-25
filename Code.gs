/**
 * Code.gs
 * 
 * Main script file containing the core automation logic.
 * This script monitors a Google Sheet for new subscription entries and:
 * 1. Creates subscription transactions in Zoho CRM
 * 2. Updates user roles in Keycloak
 * 3. Sends notifications to Slack
 */

// Column indices (0-based)
var COLUMNS = {
  ID: 0,              // Column A
  EMAIL: 1,           // Column B
  TRANSACTION_TYPE: 2, // Column C
  SUBSCRIPTION_TYPE: 3, // Column D
  BILLING_CYCLE: 4,   // Column E
  TRANSACTION_DATE: 5, // Column F
  RENEWAL_DATE: 6,    // Column G
  PROCESSED: 7,       // Column H
  NOTES: 8            // Column I
};

// Delay in milliseconds before processing a row (3 minutes)
var PROCESSING_DELAY_MS = 3 * 60 * 1000;

/**
 * Main function that processes sheet updates.
 * This function is triggered by a time-based trigger every 5 minutes.
 */
function processSheetUpdates() {
  Logger.log('Starting processSheetUpdates...');
  
  // Validate credentials first
  const validation = validateCredentials();
  if (!validation.isValid) {
    Logger.log('Missing credentials: ' + validation.missingProperties.join(', '));
    return;
  }
  
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const dataRange = sheet.getDataRange();
  const data = dataRange.getValues();
  
  // Skip header row (row 1)
  if (data.length <= 1) {
    Logger.log('No data rows to process');
    return;
  }
  
  const now = new Date().getTime();
  let processedCount = 0;
  let errorCount = 0;
  
  // Get the last edit timestamps for each row
  // Note: Google Sheets doesn't provide per-row edit timestamps,
  // so we use a timestamp column or process all unprocessed rows after initial delay
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const rowNumber = i + 1; // 1-based row number
    
    // Check if row should be processed
    if (!shouldProcessRow(row, sheet, rowNumber)) {
      continue;
    }
    
    // Extract row data
    const rowData = extractRowData(row);
    
    Logger.log('Processing row ' + rowNumber + ' for email: ' + rowData.email);
    
    try {
      // Step 1: Create Zoho CRM subscription transaction
      Logger.log('Step 1: Creating Zoho subscription...');
      const zohoResult = createZohoSubscription(rowData);
      Logger.log('Zoho subscription created: ' + zohoResult.recordId);
      
      // Step 2: Update Keycloak user role
      Logger.log('Step 2: Updating Keycloak role...');
      const keycloakResult = updateKeycloakUserRole(rowData);
      Logger.log('Keycloak role updated: ' + keycloakResult.action);
      
      // Step 3: Mark as processed
      Logger.log('Step 3: Marking row as processed...');
      markRowAsProcessed(sheet, rowNumber);
      
      // Step 4: Send success notification
      Logger.log('Step 4: Sending success notification...');
      sendSlackSuccessNotification(rowData);
      
      processedCount++;
      Logger.log('Row ' + rowNumber + ' processed successfully');
      
    } catch (error) {
      errorCount++;
      Logger.log('Error processing row ' + rowNumber + ': ' + error.message);
      
      // Log error to Notes column
      logErrorToSheet(sheet, rowNumber, error.message);
      
      // Send error notification
      sendSlackErrorNotification(rowData, error);
      
      // Continue processing other rows
    }
  }
  
  Logger.log('Processing complete. Processed: ' + processedCount + ', Errors: ' + errorCount);
}

/**
 * Checks if a row should be processed.
 * 
 * @param {Array} row - The row data array
 * @param {Sheet} sheet - The Google Sheet
 * @param {number} rowNumber - The 1-based row number
 * @returns {boolean} True if the row should be processed
 */
function shouldProcessRow(row, sheet, rowNumber) {
  // Check if already processed (Column H checkbox)
  const isProcessed = row[COLUMNS.PROCESSED];
  if (isProcessed === true) {
    return false;
  }
  
  // Check if Transaction Date is present (Column F)
  const transactionDate = row[COLUMNS.TRANSACTION_DATE];
  if (!transactionDate) {
    return false;
  }
  
  // Check if email is present (Column B)
  const email = row[COLUMNS.EMAIL];
  if (!email || email.toString().trim() === '') {
    return false;
  }
  
  // Check if Transaction Type is present (Column C)
  const transactionType = row[COLUMNS.TRANSACTION_TYPE];
  if (!transactionType || transactionType.toString().trim() === '') {
    return false;
  }
  
  // Check if Subscription Type is present for non-cancellation transactions (Column D)
  const subscriptionType = row[COLUMNS.SUBSCRIPTION_TYPE];
  if (transactionType !== 'Refund/Cancellation' && (!subscriptionType || subscriptionType.toString().trim() === '')) {
    return false;
  }
  
  // Check 3-minute delay requirement
  // We use a script property to track when rows were first seen
  const rowKey = 'row_first_seen_' + rowNumber;
  const properties = PropertiesService.getScriptProperties();
  const firstSeenStr = properties.getProperty(rowKey);
  const now = new Date().getTime();
  
  if (!firstSeenStr) {
    // First time seeing this row - record the timestamp
    properties.setProperty(rowKey, now.toString());
    Logger.log('Row ' + rowNumber + ' first seen - will process after 3 minutes');
    return false;
  }
  
  const firstSeen = parseInt(firstSeenStr, 10);
  const elapsed = now - firstSeen;
  
  if (elapsed < PROCESSING_DELAY_MS) {
    Logger.log('Row ' + rowNumber + ' waiting for 3-minute delay (' + Math.round(elapsed / 1000) + 's elapsed)');
    return false;
  }
  
  return true;
}

/**
 * Extracts row data into a structured object.
 * 
 * @param {Array} row - The row data array
 * @returns {Object} Structured row data
 */
function extractRowData(row) {
  return {
    id: row[COLUMNS.ID],
    email: row[COLUMNS.EMAIL].toString().trim(),
    transactionType: row[COLUMNS.TRANSACTION_TYPE].toString().trim(),
    subscriptionType: row[COLUMNS.SUBSCRIPTION_TYPE] ? row[COLUMNS.SUBSCRIPTION_TYPE].toString().trim() : null,
    billingCycle: row[COLUMNS.BILLING_CYCLE] ? row[COLUMNS.BILLING_CYCLE].toString().trim() : null,
    transactionDate: row[COLUMNS.TRANSACTION_DATE],
    renewalDate: row[COLUMNS.RENEWAL_DATE] || null,
    notes: row[COLUMNS.NOTES] || ''
  };
}

/**
 * Marks a row as processed by checking the checkbox in Column H.
 * Also cleans up the first-seen tracking property.
 * 
 * @param {Sheet} sheet - The Google Sheet
 * @param {number} rowNumber - The 1-based row number
 */
function markRowAsProcessed(sheet, rowNumber) {
  // Set the checkbox in Column H (index 8, or column 8 in 1-based)
  const cell = sheet.getRange(rowNumber, COLUMNS.PROCESSED + 1); // +1 because getRange uses 1-based columns
  cell.setValue(true);
  
  // Clean up the first-seen tracking property
  const rowKey = 'row_first_seen_' + rowNumber;
  PropertiesService.getScriptProperties().deleteProperty(rowKey);
}

/**
 * Logs an error message to the Notes column (Column I).
 * 
 * @param {Sheet} sheet - The Google Sheet
 * @param {number} rowNumber - The 1-based row number
 * @param {string} errorMessage - The error message to log
 */
function logErrorToSheet(sheet, rowNumber, errorMessage) {
  const cell = sheet.getRange(rowNumber, COLUMNS.NOTES + 1); // +1 because getRange uses 1-based columns
  const timestamp = new Date().toISOString();
  const currentNotes = cell.getValue();
  const newNote = '[' + timestamp + '] ERROR: ' + errorMessage;
  
  // Append to existing notes if any
  const updatedNotes = currentNotes ? currentNotes + '\n' + newNote : newNote;
  cell.setValue(updatedNotes);
}

/**
 * Test function to manually trigger the main process.
 * Run this function to test the automation before setting up the automatic trigger.
 */
function testProcessSheetUpdates() {
  Logger.log('=== MANUAL TEST RUN ===');
  processSheetUpdates();
  Logger.log('=== TEST COMPLETE ===');
}

/**
 * Clears all first-seen tracking properties.
 * Useful for resetting the 3-minute delay tracking during testing.
 */
function clearFirstSeenTracking() {
  const properties = PropertiesService.getScriptProperties();
  const allProperties = properties.getProperties();
  
  let clearedCount = 0;
  for (const key in allProperties) {
    if (key.indexOf('row_first_seen_') === 0) {
      properties.deleteProperty(key);
      clearedCount++;
    }
  }
  
  Logger.log('Cleared ' + clearedCount + ' first-seen tracking properties');
}

/**
 * Installs the time-based trigger to run every 5 minutes.
 * Run this function once to set up the automation.
 */
function installTrigger() {
  // First, remove any existing triggers for this function
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === 'processSheetUpdates') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Create new trigger
  ScriptApp.newTrigger('processSheetUpdates')
    .timeBased()
    .everyMinutes(5)
    .create();
  
  Logger.log('Trigger installed: processSheetUpdates will run every 5 minutes');
}

/**
 * Removes the time-based trigger.
 * Run this function to stop the automation.
 */
function removeTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  let removed = false;
  
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === 'processSheetUpdates') {
      ScriptApp.deleteTrigger(trigger);
      removed = true;
    }
  });
  
  if (removed) {
    Logger.log('Trigger removed: processSheetUpdates automation stopped');
  } else {
    Logger.log('No trigger found for processSheetUpdates');
  }
}
