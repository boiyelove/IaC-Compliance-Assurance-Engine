resource "azurerm_storage_account" "unsafe" {
  name                          = "stunsafeexample"
  resource_group_name           = "rg-unsafe"
  location                      = "westeurope"
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  public_network_access_enabled = true
  shared_access_key_enabled     = true
  min_tls_version               = "TLS1_0"
}
