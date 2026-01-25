/**
 * Keycloak.gs
 * 
 * Library file for all Keycloak related functions.
 * Handles authentication, user lookup, and role management.
 */

// Role mapping constants
var ROLE_MAPPING = {
  'Low Stakes': 'flophero-browse-postflopquota-low',
  'Mid Stakes': 'flophero-browse-postflopquota-mid',
  'High Stakes': 'flophero-browse-postflopquota-high'
};

// Protected role that should never be removed
var PROTECTED_ROLE = 'default-roles-gametrainertest';

// Pattern for quota roles that can be managed
var QUOTA_ROLE_PREFIX = 'flophero-browse-postflopquota-';

/**
 * Gets an admin access token from Keycloak using client credentials.
 * 
 * @param {Object} credentials - The credentials object from getCredentials()
 * @returns {string} The access token
 * @throws {Error} If token retrieval fails
 */
function getKeycloakAccessToken(credentials) {
  const tokenUrl = credentials.keycloakServerUrl + '/realms/' + credentials.keycloakRealm + '/protocol/openid-connect/token';
  
  const payload = {
    'grant_type': 'client_credentials',
    'client_id': credentials.keycloakClientId,
    'client_secret': credentials.keycloakClientSecret
  };
  
  const options = {
    'method': 'post',
    'headers': {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    'payload': payload,
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(tokenUrl, options);
  const responseCode = response.getResponseCode();
  const responseBody = JSON.parse(response.getContentText());
  
  if (responseCode !== 200 || responseBody.error) {
    const errorMessage = responseBody.error_description || responseBody.error || 'Failed to get Keycloak access token';
    Logger.log('Keycloak token error: ' + JSON.stringify(responseBody));
    throw new Error('Keycloak OAuth Error: ' + errorMessage);
  }
  
  return responseBody.access_token;
}

/**
 * Finds a user in Keycloak by email address.
 * 
 * @param {string} accessToken - Valid Keycloak access token
 * @param {string} email - Email address to search for
 * @param {Object} credentials - The credentials object
 * @returns {string} The user ID
 * @throws {Error} If user is not found
 */
function findKeycloakUserByEmail(accessToken, email, credentials) {
  const searchUrl = credentials.keycloakServerUrl + '/admin/realms/' + credentials.keycloakRealm + '/users?email=' + encodeURIComponent(email);
  
  const options = {
    'method': 'get',
    'headers': {
      'Authorization': 'Bearer ' + accessToken
    },
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(searchUrl, options);
  const responseCode = response.getResponseCode();
  const responseBody = JSON.parse(response.getContentText());
  
  if (responseCode !== 200) {
    Logger.log('Keycloak search error: ' + JSON.stringify(responseBody));
    throw new Error('Failed to search for user in Keycloak');
  }
  
  if (!responseBody || responseBody.length === 0) {
    throw new Error('User not found in Keycloak for email: ' + email);
  }
  
  return responseBody[0].id;
}

/**
 * Gets the current realm roles assigned to a user.
 * 
 * @param {string} accessToken - Valid Keycloak access token
 * @param {string} userId - The Keycloak user ID
 * @param {Object} credentials - The credentials object
 * @returns {Array} Array of role objects with id and name
 */
function getUserRealmRoles(accessToken, userId, credentials) {
  const rolesUrl = credentials.keycloakServerUrl + '/admin/realms/' + credentials.keycloakRealm + '/users/' + userId + '/role-mappings/realm';
  
  const options = {
    'method': 'get',
    'headers': {
      'Authorization': 'Bearer ' + accessToken
    },
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(rolesUrl, options);
  const responseCode = response.getResponseCode();
  const responseBody = JSON.parse(response.getContentText());
  
  if (responseCode !== 200) {
    Logger.log('Keycloak get roles error: ' + JSON.stringify(responseBody));
    throw new Error('Failed to get user roles from Keycloak');
  }
  
  return responseBody;
}

/**
 * Gets all available realm roles.
 * 
 * @param {string} accessToken - Valid Keycloak access token
 * @param {Object} credentials - The credentials object
 * @returns {Array} Array of all realm role objects
 */
function getAllRealmRoles(accessToken, credentials) {
  const rolesUrl = credentials.keycloakServerUrl + '/admin/realms/' + credentials.keycloakRealm + '/roles';
  
  const options = {
    'method': 'get',
    'headers': {
      'Authorization': 'Bearer ' + accessToken
    },
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(rolesUrl, options);
  const responseCode = response.getResponseCode();
  const responseBody = JSON.parse(response.getContentText());
  
  if (responseCode !== 200) {
    Logger.log('Keycloak get all roles error: ' + JSON.stringify(responseBody));
    throw new Error('Failed to get realm roles from Keycloak');
  }
  
  return responseBody;
}

/**
 * Removes roles from a user.
 * 
 * @param {string} accessToken - Valid Keycloak access token
 * @param {string} userId - The Keycloak user ID
 * @param {Array} roles - Array of role objects to remove
 * @param {Object} credentials - The credentials object
 */
function removeUserRoles(accessToken, userId, roles, credentials) {
  if (!roles || roles.length === 0) {
    Logger.log('No roles to remove');
    return;
  }
  
  const rolesUrl = credentials.keycloakServerUrl + '/admin/realms/' + credentials.keycloakRealm + '/users/' + userId + '/role-mappings/realm';
  
  const options = {
    'method': 'delete',
    'headers': {
      'Authorization': 'Bearer ' + accessToken,
      'Content-Type': 'application/json'
    },
    'payload': JSON.stringify(roles),
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(rolesUrl, options);
  const responseCode = response.getResponseCode();
  
  if (responseCode !== 204 && responseCode !== 200) {
    const responseBody = response.getContentText();
    Logger.log('Keycloak remove roles error: ' + responseBody);
    throw new Error('Failed to remove roles from user in Keycloak');
  }
  
  Logger.log('Successfully removed roles: ' + roles.map(function(r) { return r.name; }).join(', '));
}

/**
 * Assigns roles to a user.
 * 
 * @param {string} accessToken - Valid Keycloak access token
 * @param {string} userId - The Keycloak user ID
 * @param {Array} roles - Array of role objects to assign
 * @param {Object} credentials - The credentials object
 */
function assignUserRoles(accessToken, userId, roles, credentials) {
  if (!roles || roles.length === 0) {
    Logger.log('No roles to assign');
    return;
  }
  
  const rolesUrl = credentials.keycloakServerUrl + '/admin/realms/' + credentials.keycloakRealm + '/users/' + userId + '/role-mappings/realm';
  
  const options = {
    'method': 'post',
    'headers': {
      'Authorization': 'Bearer ' + accessToken,
      'Content-Type': 'application/json'
    },
    'payload': JSON.stringify(roles),
    'muteHttpExceptions': true
  };
  
  const response = UrlFetchApp.fetch(rolesUrl, options);
  const responseCode = response.getResponseCode();
  
  if (responseCode !== 204 && responseCode !== 200) {
    const responseBody = response.getContentText();
    Logger.log('Keycloak assign roles error: ' + responseBody);
    throw new Error('Failed to assign roles to user in Keycloak');
  }
  
  Logger.log('Successfully assigned roles: ' + roles.map(function(r) { return r.name; }).join(', '));
}

/**
 * Updates the Keycloak user's roles based on the subscription data.
 * 
 * @param {Object} rowData - The data from the Google Sheet row
 * @param {string} rowData.email - User's email address
 * @param {string} rowData.transactionType - Type of transaction
 * @param {string} rowData.subscriptionType - Type of subscription (Low/Mid/High Stakes)
 * @returns {Object} Result object with success status
 * @throws {Error} If role update fails
 */
function updateKeycloakUserRole(rowData) {
  const credentials = getCredentials();
  
  // Step 1: Get access token
  Logger.log('Getting Keycloak access token...');
  const accessToken = getKeycloakAccessToken(credentials);
  
  // Step 2: Find user by email
  Logger.log('Finding user for email: ' + rowData.email);
  const userId = findKeycloakUserByEmail(accessToken, rowData.email, credentials);
  Logger.log('Found user ID: ' + userId);
  
  // Step 3: Get user's current roles
  Logger.log('Getting current user roles...');
  const currentRoles = getUserRealmRoles(accessToken, userId, credentials);
  Logger.log('Current roles: ' + currentRoles.map(function(r) { return r.name; }).join(', '));
  
  // Step 4: Get all available realm roles (for looking up role IDs)
  Logger.log('Getting all available realm roles...');
  const allRoles = getAllRealmRoles(accessToken, credentials);
  
  // Step 5: Identify quota roles to remove (never remove protected role)
  const rolesToRemove = currentRoles.filter(function(role) {
    return role.name.indexOf(QUOTA_ROLE_PREFIX) === 0 && role.name !== PROTECTED_ROLE;
  });
  
  // Step 6: Remove old quota roles
  if (rolesToRemove.length > 0) {
    Logger.log('Removing old quota roles...');
    removeUserRoles(accessToken, userId, rolesToRemove, credentials);
  }
  
  // Step 7: For Refund/Cancellation, we're done (no new role to add)
  if (rowData.transactionType === 'Refund/Cancellation') {
    Logger.log('Transaction is Refund/Cancellation - no new role to assign');
    return {
      success: true,
      action: 'roles_removed',
      removedRoles: rolesToRemove.map(function(r) { return r.name; })
    };
  }
  
  // Step 8: For other transaction types, assign the new role
  const newRoleName = ROLE_MAPPING[rowData.subscriptionType];
  
  if (!newRoleName) {
    throw new Error('Unknown subscription type: ' + rowData.subscriptionType);
  }
  
  // Find the role object from available roles
  const newRole = allRoles.find(function(role) {
    return role.name === newRoleName;
  });
  
  if (!newRole) {
    throw new Error('Role not found in Keycloak: ' + newRoleName);
  }
  
  Logger.log('Assigning new role: ' + newRoleName);
  assignUserRoles(accessToken, userId, [{ id: newRole.id, name: newRole.name }], credentials);
  
  return {
    success: true,
    action: 'role_updated',
    removedRoles: rolesToRemove.map(function(r) { return r.name; }),
    assignedRole: newRoleName
  };
}
