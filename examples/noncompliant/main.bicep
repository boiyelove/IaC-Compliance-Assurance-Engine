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
