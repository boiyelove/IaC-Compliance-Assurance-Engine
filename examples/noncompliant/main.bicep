// IaC-Compliance-Assurance-Engine infrastructure template.
// Resource behavior stays in this file; deployment-time values are supplied by ./main.bicepparam.

// This intentionally unsafe scanner fixture has no deployment inputs; its literals are test evidence.

// Resource unsafeVault: declares Microsoft.KeyVault/vaults@2023-07-01 and its security settings.
resource unsafeVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'unsafe-example'
  location: resourceGroup().location
  properties: {
    tenantId: subscription().tenantId
    enablePurgeProtection: false
    publicNetworkAccess: 'Enabled'
    sku: {
      family: 'A'
      name: 'standard'
    }
  }
}
