// IaC-Compliance-Assurance-Engine infrastructure template.
// Resource behavior stays in this file; deployment-time values are supplied by ./main.bicepparam.

// Deployment inputs: values are explicit, reviewable, and environment-specific.

param location string

// Resource vault: declares Microsoft.KeyVault/vaults@2023-07-01 and its security settings.
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-compliant-example'
  location: location
  properties: {
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enablePurgeProtection: true
    publicNetworkAccess: 'Disabled'
    sku: {
      family: 'A'
      name: 'standard'
    }
  }
}
