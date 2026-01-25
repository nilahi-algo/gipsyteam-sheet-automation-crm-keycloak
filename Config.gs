/**
 * Config.gs
 * 
 * Handles retrieval of API credentials from Script Properties.
 * All sensitive credentials are stored securely in Script Properties
 * and never hardcoded in the source code.
 */

/**
 * Retrieves all API credentials from Script Properties.
 * 
 * @returns {Object} An object containing all API credentials and configuration.
 * @property {string} zohoClientId - Zoho OAuth Client ID
 * @property {string} zohoClientSecret - Zoho OAuth Client Secret
 * @property {string} zohoRefreshToken - Zoho OAuth Refresh Token
 * @property {string} zohoApiDomain - Zoho API domain (e.g., https://www.zohoapis.com)
 * @property {string} keycloakServerUrl - Keycloak server base URL
 * @property {string} keycloakRealm - Keycloak realm name
 * @property {string} keycloakClientId - Keycloak client ID
 * @property {string} keycloakClientSecret - Keycloak client secret
 * @property {string} slackWebhookUrl - Slack incoming webhook URL
 */
function getCredentials() {
  const properties = PropertiesService.getScriptProperties();
  
  return {
    // Zoho CRM credentials
    zohoClientId: properties.getProperty('ZOHO_CLIENT_ID'),
    zohoClientSecret: properties.getProperty('ZOHO_CLIENT_SECRET'),
    zohoRefreshToken: properties.getProperty('ZOHO_REFRESH_TOKEN'),
    zohoApiDomain: properties.getProperty('ZOHO_API_DOMAIN') || 'https://www.zohoapis.com',
    
    // Keycloak credentials
    keycloakServerUrl: properties.getProperty('KEYCLOAK_SERVER_URL') || 'https://accounts.algosoftware.io',
    keycloakRealm: properties.getProperty('KEYCLOAK_REALM') || 'GametrainerTest',
    keycloakClientId: properties.getProperty('KEYCLOAK_CLIENT_ID') || 'gametrainertest',
    keycloakClientSecret: properties.getProperty('KEYCLOAK_CLIENT_SECRET'),
    
    // Slack credentials
    slackWebhookUrl: properties.getProperty('SLACK_WEBHOOK_URL')
  };
}

/**
 * Validates that all required credentials are present.
 * 
 * @returns {Object} Validation result with isValid boolean and array of missing properties.
 */
function validateCredentials() {
  const credentials = getCredentials();
  const missingProperties = [];
  
  const requiredProperties = [
    { key: 'zohoClientId', name: 'ZOHO_CLIENT_ID' },
    { key: 'zohoClientSecret', name: 'ZOHO_CLIENT_SECRET' },
    { key: 'zohoRefreshToken', name: 'ZOHO_REFRESH_TOKEN' },
    { key: 'keycloakClientSecret', name: 'KEYCLOAK_CLIENT_SECRET' },
    { key: 'slackWebhookUrl', name: 'SLACK_WEBHOOK_URL' }
  ];
  
  requiredProperties.forEach(function(prop) {
    if (!credentials[prop.key]) {
      missingProperties.push(prop.name);
    }
  });
  
  return {
    isValid: missingProperties.length === 0,
    missingProperties: missingProperties
  };
}

/**
 * Test function to verify credentials are properly configured.
 * Run this function manually to check your setup.
 */
function testCredentialsSetup() {
  const validation = validateCredentials();
  
  if (validation.isValid) {
    Logger.log('✅ All required credentials are configured.');
  } else {
    Logger.log('❌ Missing credentials: ' + validation.missingProperties.join(', '));
    Logger.log('Please add these properties in Project Settings > Script Properties');
  }
  
  return validation;
}
